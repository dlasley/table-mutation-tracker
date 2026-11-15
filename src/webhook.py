"""HTTP API that n8n calls to run scrapes and maintain the rolling index."""

import hmac
import os
import traceback

from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from src.config import load_config
from src.lib.github_store import GitHubStore
from src.lib.snapshot_store import OutOfOrderError
from src.main import run_scrape


class AppendIndexBody(BaseModel):
    date: str = Field(description="Snapshot date, `YYYY-MM-DD`.", examples=["2026-06-05"])
    time: str = Field(description="Snapshot time, `HHMMSS`.", examples=["153000"])


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
    if not hmac.compare_digest(webhook_secret, secret):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


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


@app.post("/scrape", summary="Run a scrape", tags=["Scraping"], responses=_AUTH_RESPONSES)
async def scrape(x_webhook_secret: str | None = Security(_webhook_secret)):
    """Log in to the SIS portal, scrape every configured class, and return the
    normalized snapshot as JSON.

    Writes nothing. n8n commits the returned data to the data repo. Scrape
    failures return HTTP 200 with `status: "error"` so n8n can branch on the body.
    """
    _verify_secret(x_webhook_secret)

    try:
        result = await run_scrape()
        return {
            "status": "success",
            "data": result.to_dict(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@app.post(
    "/append-index",
    summary="Append a snapshot to the rolling index",
    tags=["Rolling index"],
    responses={
        **_AUTH_RESPONSES,
        409: {
            "description": "The snapshot is older than the newest index entry. "
            "The body is `{\"detail\": {\"status\": \"needs-rebuild\", \"reason\": ...}}`; "
            "call `/rebuild-index`."
        },
    },
)
async def append_index(
    body: AppendIndexBody,
    x_webhook_secret: str | None = Security(_webhook_secret),
):
    """Diff one snapshot against the previous index entry and append the result
    to `rolling_index.json`.

    Called by n8n after each scrape. Re-appending a snapshot already in the index
    replaces its entry in place.
    """
    _verify_secret(x_webhook_secret)
    store = _github_store()
    class_weights = _class_weights()

    try:
        index = await store.append_to_rolling_index(
            body.date, body.time, class_weights=class_weights
        )
    except OutOfOrderError as e:
        raise HTTPException(
            status_code=409,
            detail={"status": "needs-rebuild", "reason": str(e)},
        )
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    new_entry = next(
        (s for s in index["snapshots"] if s["date"] == body.date and s["time"] == body.time),
        None,
    )
    return {
        "status": "success",
        "snapshots": len(index["snapshots"]),
        "entry": new_entry,
    }


@app.post(
    "/rebuild-index",
    summary="Rebuild the rolling index",
    tags=["Rolling index"],
    responses=_AUTH_RESPONSES,
)
async def rebuild_index(x_webhook_secret: str | None = Security(_webhook_secret)):
    """Diff every consecutive pair of snapshots in the data repo and rewrite
    `rolling_index.json` from scratch.

    n8n calls this when `/append-index` returns 409. Run time grows with the
    number of snapshots; for large backfills use `scripts/rebuild_index.py`.
    """
    _verify_secret(x_webhook_secret)
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
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@app.get(
    "/health",
    summary="Health check",
    tags=["Operations"],
    responses={500: {"description": "One or more required environment variables are missing."}},
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
