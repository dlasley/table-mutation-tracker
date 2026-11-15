"""HTTP API that n8n calls to run scrapes and maintain the rolling index."""

import hmac
import logging
import os
import re
import sys
import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, FastAPI, HTTPException, Request, Security
from fastapi.routing import APIRoute
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from src.config import load_config
from src.lib.github_store import GitHubStore
from src.lib.snapshot_store import OutOfOrderError
from src.main import run_scrape
from src.scraper.base import Assignment, ClassMetadata

logger = logging.getLogger(__name__)
# uvicorn configures only its own loggers; this routes this module's logs to stdout.
if not logger.handlers:
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.INFO)


class AppendIndexBody(BaseModel):
    date: str = Field(
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Snapshot date, `YYYY-MM-DD`.",
        examples=["2026-06-05"],
    )
    time: str = Field(
        pattern=r"^\d{6}$",
        description="Snapshot time, `HHMMSS`.",
        examples=["153000"],
    )


# Response models below document the 200 bodies only. Handlers return plain dicts and are not
# validated against them, so n8n receives the payloads unchanged.


class ErrorResponse(BaseModel):
    status: Literal["error"]
    error: str = Field(
        description="Exception message with URLs replaced by `<url>`. The full message is in "
        "the scraper logs."
    )
    error_id: str = Field(
        description="Short id that locates the full stack trace in the scraper logs."
    )


class ScrapedClass(BaseModel):
    slug: str = Field(description="Class slug from `config/sources.json`.")
    assignments: list[Assignment]
    metadata: ClassMetadata


class ScrapeMetadata(BaseModel):
    scrape_timestamp: str = Field(description="ISO 8601 timestamp of the scrape.")
    source: str = Field(description="Source key, always `sis`.")
    classes: dict[str, ClassMetadata] = Field(
        description="Class metadata keyed by class slug. Committed as `metadata.json`."
    )


class ScrapeData(BaseModel):
    date: str = Field(description="Snapshot date, `YYYY-MM-DD`.")
    time: str = Field(description="Snapshot time, `HHMMSS`.")
    scrape_timestamp: str = Field(description="ISO 8601 timestamp of the scrape.")
    classes: list[ScrapedClass]
    metadata: ScrapeMetadata


class ScrapeSuccess(BaseModel):
    status: Literal["success"]
    data: ScrapeData


class IndexChanges(BaseModel):
    class_level: int = Field(description="Class-level changes, such as a final grade change.")
    added: int = Field(description="Assignments added since the previous snapshot.")
    modified: int = Field(description="Assignments modified since the previous snapshot.")
    deleted: int = Field(description="Assignments deleted since the previous snapshot.")
    total: int = Field(description="Assignment changes: added + modified + deleted.")


class IndexClassSummary(BaseModel):
    course: str = Field(description="Course name.")
    final_grade: str | None = Field(description="Final letter grade, or null when not posted.")
    final_percent: float | None = Field(description="Final percent, or null when not posted.")
    assignment_count: int = Field(description="Number of assignments in the class.")


class IndexEntry(BaseModel):
    date: str = Field(description="Snapshot date, `YYYY-MM-DD`.")
    time: str = Field(description="Snapshot time, `HHMMSS`.")
    scrape_timestamp: str | None = Field(description="ISO 8601 timestamp of the scrape.")
    previous_snapshot: str | None = Field(
        description="Previous snapshot as `YYYY-MM-DD/HHMMSS`, or null for the first."
    )
    changes: IndexChanges
    classes: dict[str, IndexClassSummary] = Field(description="Keyed by class slug.")
    gpa: float | None = Field(description="Weighted GPA, or null when it cannot be computed.")


class AppendIndexSuccess(BaseModel):
    status: Literal["success"]
    snapshots: int = Field(description="Number of entries in the rolling index.")
    entry: IndexEntry | None = Field(description="The entry for the appended snapshot.")


class RebuildIndexSuccess(BaseModel):
    status: Literal["success"]
    snapshots: int = Field(description="Number of entries in the rolling index.")
    total_changes: int = Field(description="Assignment changes summed across all entries.")


class HealthOk(BaseModel):
    status: Literal["ok"]


ScrapeResponse = Annotated[ScrapeSuccess | ErrorResponse, Field(discriminator="status")]
AppendIndexResponse = Annotated[
    AppendIndexSuccess | ErrorResponse, Field(discriminator="status")
]
RebuildIndexResponse = Annotated[
    RebuildIndexSuccess | ErrorResponse, Field(discriminator="status")
]


app = FastAPI(
    title="Table Mutation Tracker scraper API",
    version="1.0.0",
    description="Called by the n8n orchestrator. Not intended for direct public use.",
    docs_url=None,
    redoc_url=None,
)

# auto_error=False so a missing header reaches _verify_secret and returns 401, not FastAPI's 403.
_webhook_secret = APIKeyHeader(
    name="X-Webhook-Secret",
    auto_error=False,
    description="Shared secret configured as `WEBHOOK_SECRET` on the scraper and as a "
    "Header Auth credential in n8n.",
)

_AUTH_RESPONSES = {
    401: {"description": "Missing or invalid `X-Webhook-Secret` header."},
    500: {"description": "`WEBHOOK_SECRET`, `GITHUB_TOKEN`, or `DATA_REPO` is not configured."},
}

_REQUIRED_ENV_VARS = [
    "WEBHOOK_SECRET",
    "SIS_USERNAME",
    "SIS_PASSWORD",
    "GITHUB_TOKEN",
    "DATA_REPO",
]


def _check_env() -> list[str]:
    return [v for v in _REQUIRED_ENV_VARS if not os.environ.get(v)]


def _verify_secret(webhook_secret: str | None) -> None:
    """Verify the X-Webhook-Secret header matches WEBHOOK_SECRET."""
    secret = os.environ.get("WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="WEBHOOK_SECRET not configured")
    if not webhook_secret:
        raise HTTPException(status_code=401, detail="Missing X-Webhook-Secret header")
    if not hmac.compare_digest(webhook_secret.encode(), secret.encode()):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


class SecretRoute(APIRoute):
    """Checks the secret before FastAPI parses the body, so a bad body never beats a 401.

    A route dependency is not enough: FastAPI decodes the JSON body first, and malformed JSON
    returns 422 before any dependency runs.
    """

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def authenticated(request: Request):
            _verify_secret(request.headers.get(_webhook_secret.model.name))
            return await handler(request)

        return authenticated


# The Security dependency only publishes the apiKey scheme in the OpenAPI spec; SecretRoute
# enforces it.
secured = APIRouter(route_class=SecretRoute, dependencies=[Security(_webhook_secret)])


_URL = re.compile(r"https?://\S+")
# Playwright appends its action log, which can echo typed text such as the SIS password.
_PLAYWRIGHT_CALL_LOG = re.compile(r"\nCall log:.*", re.DOTALL)


def _client_message(exc: Exception) -> str:
    message = _PLAYWRIGHT_CALL_LOG.sub("", str(exc))
    return _URL.sub("<url>", message)


def _error_response(endpoint: str, exc: Exception) -> dict:
    """Log the exception with a fresh id and return a sanitized message plus the id."""
    error_id = uuid.uuid4().hex[:12]
    logger.exception("%s failed (error_id=%s)", endpoint, error_id)
    return {"status": "error", "error": _client_message(exc), "error_id": error_id}


def _class_weights() -> dict[str, dict]:
    cfg = load_config()
    return {
        cls.slug: {"weight": cls.gpa_weight, "override_grade": cls.gpa_override_grade}
        for source in cfg.sources.values()
        for cls in source.classes
    }


def _github_store() -> GitHubStore:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("DATA_REPO")
    if not token or not repo:
        raise HTTPException(
            status_code=500,
            detail="GITHUB_TOKEN and DATA_REPO must be configured",
        )
    return GitHubStore(repo=repo, token=token)


@secured.post(
    "/scrape",
    summary="Run a scrape",
    tags=["Scraping"],
    responses={**_AUTH_RESPONSES, 200: {"model": ScrapeResponse}},
)
async def scrape():
    """Log in to the SIS portal, scrape every configured class, and return the
    normalized snapshot as JSON.

    Writes nothing. n8n commits the returned data to the data repo. Scrape
    failures return HTTP 200 with `status: "error"` so n8n can branch on the body.
    """
    try:
        result = await run_scrape()
        return {
            "status": "success",
            "data": result.to_dict(),
        }
    except Exception as e:
        return _error_response("/scrape", e)


@secured.post(
    "/append-index",
    summary="Append a snapshot to the rolling index",
    tags=["Rolling index"],
    responses={
        **_AUTH_RESPONSES,
        200: {"model": AppendIndexResponse},
        409: {
            "description": "The snapshot is older than the newest index entry. "
            "The body is `{\"detail\": {\"status\": \"needs-rebuild\", \"reason\": ...}}`; "
            "call `/rebuild-index`."
        },
    },
)
async def append_index(body: AppendIndexBody):
    """Diff one snapshot against the previous index entry and append the result
    to `rolling_index.json`.

    Called by n8n after each scrape. Re-appending a snapshot already in the index
    replaces its entry in place.
    """
    try:
        store = _github_store()
        class_weights = _class_weights()
        index = await store.append_to_rolling_index(
            body.date, body.time, class_weights=class_weights
        )
    except OutOfOrderError as e:
        raise HTTPException(
            status_code=409,
            detail={"status": "needs-rebuild", "reason": str(e)},
        )
    except HTTPException:
        raise
    except Exception as e:
        return _error_response("/append-index", e)

    new_entry = next(
        (s for s in index["snapshots"] if s["date"] == body.date and s["time"] == body.time),
        None,
    )
    return {
        "status": "success",
        "snapshots": len(index["snapshots"]),
        "entry": new_entry,
    }


@secured.post(
    "/rebuild-index",
    summary="Rebuild the rolling index",
    tags=["Rolling index"],
    responses={**_AUTH_RESPONSES, 200: {"model": RebuildIndexResponse}},
)
async def rebuild_index():
    """Diff every consecutive pair of snapshots in the data repo and rewrite
    `rolling_index.json` from scratch.

    n8n calls this when `/append-index` returns 409. Run time grows with the
    number of snapshots; for large backfills use `scripts/rebuild_index.py`.
    """
    store = _github_store()

    try:
        index = await store.rebuild_rolling_index(class_weights=_class_weights())
        total_changes = sum(s["changes"]["total"] for s in index["snapshots"])
        return {
            "status": "success",
            "snapshots": len(index["snapshots"]),
            "total_changes": total_changes,
        }
    except Exception as e:
        return _error_response("/rebuild-index", e)


app.include_router(secured)


@app.get(
    "/health",
    summary="Health check",
    tags=["Operations"],
    responses={
        200: {"model": HealthOk},
        500: {"description": "One or more required environment variables are missing."},
    },
)
async def health():
    """Return `{"status": "ok"}` when every required environment variable is set.
    Does not contact the SIS or GitHub."""
    missing = _check_env()
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing required env vars: {', '.join(missing)}",
        )
    return {"status": "ok"}
