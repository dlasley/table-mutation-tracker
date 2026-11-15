"""Committed exports must not carry deployment identifiers or personal data.

The n8n workflow reads these values from `$env` on the n8n host, so an export
straight from the live instance is safe to commit.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN = {
    "App Runner host": re.compile(r"awsapprunner\.com"),
    "personal email": re.compile(r"[\w.+-]+@(gmail|yahoo|outlook|hotmail|icloud)\.com", re.I),
    "data repo path": re.compile(r"[\w-]+/table-mutation-data(?![\w-])"),
    "n8n host": re.compile(r"davebrot\.com"),
}

PUBLIC_FILES = [
    *sorted((ROOT / "n8n").glob("*.json")),
    *sorted((ROOT / "docs").rglob("*.mdx")),
    ROOT / "docs" / "docs.json",
    ROOT / "docs" / "openapi.json",
]


def test_public_files_exist():
    assert any(p.parent.name == "n8n" for p in PUBLIC_FILES)


def test_public_files_have_no_deployment_identifiers():
    leaks = [
        f"{path.relative_to(ROOT)}: {label} ({match.group(0)})"
        for path in PUBLIC_FILES
        for label, pattern in FORBIDDEN.items()
        for match in pattern.finditer(path.read_text())
    ]
    assert not leaks, "\n".join(leaks)
