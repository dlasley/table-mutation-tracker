"""Auth and spec tests for the scraper API. None of these reach the SIS or GitHub."""

import pytest
from fastapi.testclient import TestClient

from scripts.export_openapi import OUTPUT, render
from src.webhook import app

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
