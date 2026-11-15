#!/usr/bin/env python3
"""Write the scraper API's OpenAPI spec to docs/openapi.json for the Mintlify API reference.

Usage:
    python scripts/export_openapi.py

tests/test_webhook.py::test_docs_openapi_json_is_current fails when docs/openapi.json is out of date.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.webhook import app

OUTPUT = PROJECT_ROOT / "docs" / "openapi.json"

# Placeholder host: the real scraper URL is not published, and the docs playground is disabled.
SERVERS = [{"url": "https://scraper.example.com", "description": "Your scraper deployment"}]


def build_spec() -> dict:
    spec = app.openapi()
    spec["servers"] = SERVERS
    return spec


def render() -> str:
    return json.dumps(build_spec(), indent=2) + "\n"


def main() -> None:
    OUTPUT.write_text(render())
    print(f"Wrote {OUTPUT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
