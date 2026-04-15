"""HTTP endpoint for n8n to trigger scrape runs on Cloud Run."""

import hmac
import os
import traceback

from fastapi import FastAPI, Header, HTTPException

from src.config import load_config
from src.lib.github_store import GitHubStore
from src.main import run_scrape

app = FastAPI(title="SIS Assignment Tracker", docs_url=None, redoc_url=None)

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


@app.post("/scrape")
async def scrape(x_webhook_secret: str | None = Header(default=None)):
    """Run a full scrape and return structured results.

    Auth: Cloud Run IAM gates network access, X-Webhook-Secret header
    provides app-level verification. n8n sends both: IAM identity token
    in Authorization header, webhook secret in X-Webhook-Secret.
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


@app.post("/rebuild-index")
async def rebuild_index(x_webhook_secret: str | None = Header(default=None)):
    """Rebuild the rolling index by diffing all existing snapshots.

    Scans every snapshot in the data repo, diffs consecutive pairs,
    and writes updated change counts to rolling_index.json.
    Called by n8n after each scrape to backfill accurate diff data.
    """
    _verify_secret(x_webhook_secret)

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("DATA_REPO")
    if not token or not repo:
        raise HTTPException(
            status_code=500,
            detail="GITHUB_TOKEN and DATA_REPO must be configured",
        )

    try:
        cfg = load_config()
        class_weights = {
            cls.slug: {"weight": cls.gpa_weight, "override_grade": cls.gpa_override_grade}
            for source in cfg.sources.values()
            for cls in source.classes
        }
        store = GitHubStore(repo=repo, token=token)
        index = await store.rebuild_rolling_index(class_weights=class_weights)
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


@app.get("/health")
async def health():
    """Health check. Returns 500 if any required env vars are missing."""
    missing = _check_env()
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing required env vars: {', '.join(missing)}",
        )
    return {"status": "ok"}
