"""Auth and spec tests for the scraper API. None of these reach the SIS or GitHub."""

import re
from dataclasses import asdict

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter, ValidationError

from scripts.export_openapi import OUTPUT, render
from src import webhook
from src.main import ClassResult, ScrapeResult
from src.scraper.base import Assignment, ClassMetadata
from src.webhook import app
from tests.conftest import FakeStore

client = TestClient(app)


@pytest.fixture(autouse=True)
def _secret(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "test-secret")


@pytest.mark.parametrize("path", ["/scrape", "/append-index", "/rebuild-index"])
def test_missing_secret_returns_401(path):
    response = client.post(path, json={"date": "2026-06-05", "time": "153000"})
    assert response.status_code == 401


@pytest.mark.parametrize("path", ["/scrape", "/append-index", "/rebuild-index"])
def test_wrong_secret_returns_401(path):
    response = client.post(
        path,
        json={"date": "2026-06-05", "time": "153000"},
        headers={"X-Webhook-Secret": "wrong"},
    )
    assert response.status_code == 401


INVALID_BODIES = [
    pytest.param({"json": {"date": "not-a-date", "time": "x"}}, id="schema-invalid"),
    pytest.param({"json": {}}, id="missing-fields"),
    pytest.param(
        {"content": b"{not json", "headers": {"Content-Type": "application/json"}},
        id="malformed-json",
    ),
]


@pytest.mark.parametrize("request_kwargs", INVALID_BODIES)
def test_missing_secret_with_invalid_body_returns_401(request_kwargs):
    response = client.post("/append-index", **request_kwargs)
    assert response.status_code == 401


@pytest.mark.parametrize("request_kwargs", INVALID_BODIES)
def test_wrong_secret_with_invalid_body_returns_401(request_kwargs):
    headers = {**request_kwargs.get("headers", {}), "X-Webhook-Secret": "wrong"}
    response = client.post("/append-index", **{**request_kwargs, "headers": headers})
    assert response.status_code == 401


@pytest.mark.parametrize("path", ["/scrape", "/append-index", "/rebuild-index"])
def test_non_ascii_secret_returns_401(path):
    response = client.post(
        path,
        json={"date": "2026-06-05", "time": "153000"},
        headers={"X-Webhook-Secret": "sécret".encode("latin-1")},
    )
    assert response.status_code == 401


def test_header_name_is_case_insensitive(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    response = client.post(
        "/rebuild-index",
        headers={"x-webhook-secret": "test-secret"},
    )
    # Past auth; fails on the missing GitHub config instead.
    assert response.status_code == 500
    assert "GITHUB_TOKEN" in response.json()["detail"]


def test_spec_declares_webhook_secret_scheme():
    spec = app.openapi()
    scheme = spec["components"]["securitySchemes"]["APIKeyHeader"]
    assert scheme == {**scheme, "type": "apiKey", "in": "header", "name": "X-Webhook-Secret"}
    assert spec["paths"]["/append-index"]["post"]["security"] == [{"APIKeyHeader": []}]


def test_docs_openapi_json_is_current():
    assert OUTPUT.read_text() == render(), (
        "docs/openapi.json is stale; run: .venv/bin/python scripts/export_openapi.py"
    )


# --- Response documentation and error contract ---

POST_PATHS = ["/scrape", "/append-index", "/rebuild-index"]
SECRET_HEADERS = {"X-Webhook-Secret": "test-secret"}


def _ok_schema(path, method):
    response = app.openapi()["paths"][path][method]["responses"]["200"]
    return response["content"]["application/json"]["schema"]


def test_every_200_response_documents_a_schema():
    for path, operations in app.openapi()["paths"].items():
        for method, operation in operations.items():
            label = f"{method.upper()} {path}"
            assert "200" in operation["responses"], f"{label} documents no 200 response"
            content = operation["responses"]["200"].get("content", {})
            assert "application/json" in content, f"{label} documents no JSON 200 body"
            assert content["application/json"]["schema"], f"{label} has an empty 200 schema"


@pytest.mark.parametrize("path", POST_PATHS)
def test_post_200_is_success_or_error_discriminated_on_status(path):
    schema = _ok_schema(path, "post")
    assert len(schema["oneOf"]) == 2
    assert all("$ref" in option for option in schema["oneOf"])
    assert schema["discriminator"]["propertyName"] == "status"
    assert any(option["$ref"].endswith("/ErrorResponse") for option in schema["oneOf"])


@pytest.fixture
def broken_store(monkeypatch):
    """Route handlers use a FakeStore whose index operations raise unexpectedly."""
    store = FakeStore()

    async def boom(*args, **kwargs):
        raise RuntimeError("store exploded")

    store.append_to_rolling_index = boom
    store.rebuild_rolling_index = boom
    monkeypatch.setattr(webhook, "_github_store", lambda: store)
    monkeypatch.setattr(webhook, "_class_weights", lambda: {})
    monkeypatch.setattr(webhook, "run_scrape", boom)


@pytest.mark.parametrize("path", POST_PATHS)
def test_unexpected_failure_returns_error_id_and_logs_the_stack_trace(
    path, broken_store, caplog
):
    response = client.post(
        path, json={"date": "2026-06-05", "time": "153000"}, headers=SECRET_HEADERS
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "error"
    assert body["error"] == "store exploded"
    assert re.fullmatch(r"[0-9a-f]{12}", body["error_id"])
    assert "traceback" not in body
    logged = [r for r in caplog.records if body["error_id"] in r.getMessage()]
    assert logged, "error_id was not logged"
    assert logged[0].exc_info is not None
    assert logged[0].exc_info[0] is RuntimeError


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (
            RuntimeError("Login failed at https://sis.example.edu/guardian/home.html?x=1 today"),
            "Login failed at <url> today",
        ),
        (
            RuntimeError(
                "Locator.type: Timeout 30000ms exceeded.\n"
                'Call log:\n  - elementHandle.type("hunter2")\n'
                '  - navigating to "https://sis.example.edu/login"'
            ),
            "Locator.type: Timeout 30000ms exceeded.",
        ),
    ],
)
def test_client_error_message_hides_urls_and_playwright_call_log(
    raised, expected, broken_store, monkeypatch, caplog
):
    async def fail(*args, **kwargs):
        raise raised

    monkeypatch.setattr(webhook, "run_scrape", fail)

    body = client.post("/scrape", headers=SECRET_HEADERS).json()

    assert body["error"] == expected
    assert "sis.example.edu" not in body["error"]
    assert "hunter2" not in body["error"]
    logged = [r for r in caplog.records if body["error_id"] in r.getMessage()]
    assert logged[0].exc_info[1] is raised
    assert "sis.example.edu" in str(logged[0].exc_info[1])


def test_append_index_missing_config_returns_documented_error(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(webhook, "_github_store", lambda: FakeStore())

    response = client.post(
        "/append-index",
        json={"date": "2026-06-05", "time": "153000"},
        headers=SECRET_HEADERS,
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "error"
    assert re.fullmatch(r"[0-9a-f]{12}", body["error_id"])


def test_append_index_missing_github_config_keeps_its_500(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    response = client.post(
        "/append-index",
        json={"date": "2026-06-05", "time": "153000"},
        headers=SECRET_HEADERS,
    )

    assert response.status_code == 500
    assert "GITHUB_TOKEN" in response.json()["detail"]


def test_error_ids_are_unique_per_failure(broken_store):
    ids = {
        client.post("/rebuild-index", headers=SECRET_HEADERS).json()["error_id"]
        for _ in range(3)
    }
    assert len(ids) == 3


# --- Documented models stay in step with runtime payloads ---


def _scrape_result():
    assignment = Assignment(
        due_date="2026-06-01",
        category="Homework",
        name="Essay 1",
        flags={"late": True, "missing": False},
        score_raw="9/10",
        points_earned=9.0,
        points_possible=10.0,
        percent=90.0,
        grade="A",
        has_comments=True,
    )
    meta = ClassMetadata(
        course="English 10",
        teacher="Teacher, A",
        expression="1(A)",
        term="S2",
        final_grade="A",
        final_percent=93.5,
        assignment_count=1,
        last_updated="2026-06-01",
    )
    cls = ClassResult(slug="english_10", assignments=[asdict(assignment)], metadata=asdict(meta))
    return ScrapeResult(
        date="2026-06-05",
        time="153000",
        scrape_timestamp="2026-06-05T15:30:00-05:00",
        classes=[cls],
        metadata={
            "scrape_timestamp": "2026-06-05T15:30:00-05:00",
            "source": "sis",
            "classes": {"english_10": asdict(meta)},
        },
    )


def _assert_round_trips(adapter, payload):
    """Validation succeeds and drops nothing, so no payload field is undocumented."""
    assert adapter.validate_python(payload).model_dump() == payload


def test_scrape_success_payload_matches_documented_model():
    payload = {"status": "success", "data": _scrape_result().to_dict()}
    _assert_round_trips(TypeAdapter(webhook.ScrapeResponse), payload)


def test_scrape_success_model_rejects_a_missing_assignment_field():
    payload = {"status": "success", "data": _scrape_result().to_dict()}
    del payload["data"]["classes"][0]["assignments"][0]["has_comments"]
    with pytest.raises(ValidationError):
        TypeAdapter(webhook.ScrapeResponse).validate_python(payload)


async def _seeded_store(snapshots):
    """FakeStore holding one english_10 class per (date, time, assignment names) snapshot."""
    store = FakeStore()
    classes = {"english_10": {"course": "English 10", "final_grade": "B", "final_percent": 85.0,
                              "assignment_count": 1}}
    for date, time, names in snapshots:
        await store.write_metadata(
            date, time, {"scrape_timestamp": f"{date}T{time}", "classes": classes}
        )
        await store.write_assignments(
            date,
            time,
            "english_10",
            [{"name": n, "due_date": "2026-06-01", "grade": "B"} for n in names],
        )
    return store


async def test_rebuild_index_success_payload_matches_documented_model(monkeypatch):
    store = await _seeded_store(
        [
            ("2026-06-04", "150000", ["Essay 1"]),
            ("2026-06-05", "153000", ["Essay 1", "Essay 2"]),
        ]
    )
    monkeypatch.setattr(webhook, "_github_store", lambda: store)
    monkeypatch.setattr(
        webhook,
        "_class_weights",
        lambda: {"english_10": {"weight": "regular", "override_grade": None}},
    )

    response = client.post("/rebuild-index", headers=SECRET_HEADERS)

    body = response.json()
    assert body["status"] == "success"
    assert body["snapshots"] == 2
    assert body["total_changes"] == 1
    _assert_round_trips(TypeAdapter(webhook.RebuildIndexResponse), body)


async def test_append_index_first_snapshot_payload_matches_documented_model(monkeypatch):
    store = await _seeded_store([("2026-06-05", "153000", ["Essay 1"])])
    monkeypatch.setattr(webhook, "_github_store", lambda: store)
    monkeypatch.setattr(webhook, "_class_weights", lambda: {})

    response = client.post(
        "/append-index",
        json={"date": "2026-06-05", "time": "153000"},
        headers=SECRET_HEADERS,
    )

    body = response.json()
    assert body["status"] == "success"
    assert body["entry"]["previous_snapshot"] is None
    assert body["entry"]["gpa"] is None
    _assert_round_trips(TypeAdapter(webhook.AppendIndexResponse), body)


async def test_append_index_success_payload_matches_documented_model(monkeypatch):
    store = await _seeded_store(
        [
            ("2026-06-04", "150000", ["Essay 1"]),
            ("2026-06-05", "153000", ["Essay 1", "Essay 2"]),
        ]
    )
    await store.rebuild_rolling_index()
    monkeypatch.setattr(webhook, "_github_store", lambda: store)
    monkeypatch.setattr(
        webhook,
        "_class_weights",
        lambda: {"english_10": {"weight": "regular", "override_grade": None}},
    )

    response = client.post(
        "/append-index",
        json={"date": "2026-06-05", "time": "153000"},
        headers=SECRET_HEADERS,
    )

    body = response.json()
    assert body["entry"]["changes"]["added"] == 1
    assert body["entry"]["gpa"] is not None
    _assert_round_trips(TypeAdapter(webhook.AppendIndexResponse), body)


# --- AppendIndexBody validation ---


@pytest.mark.parametrize(
    "payload",
    [
        {"date": "2026-6-5", "time": "153000"},
        {"date": "2026-06-05", "time": "15300"},
        {"date": "2026-06-05", "time": "15300a"},
    ],
)
def test_append_index_rejects_malformed_date_or_time_before_touching_the_store(
    payload, monkeypatch
):
    def fail():
        raise AssertionError("store must not be built for an invalid body")

    monkeypatch.setattr(webhook, "_github_store", fail)

    response = client.post("/append-index", json=payload, headers=SECRET_HEADERS)

    assert response.status_code == 422
