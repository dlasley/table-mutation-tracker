"""Tests for _diff_assignments and its parity with frontend/lib/diff.ts."""

import re
from pathlib import Path

from src.lib.snapshot_store import DIFF_FIELDS, _diff_assignments

DIFF_TS = Path(__file__).resolve().parent.parent / "frontend" / "lib" / "diff.ts"

FLAGS_OFF = {
    "collected": False,
    "late": False,
    "missing": False,
    "exempt": False,
    "absent": False,
    "incomplete": False,
    "excluded": False,
}


def _assignment(**overrides) -> dict:
    a = {
        "name": "Essay 1",
        "due_date": "2026-05-10",
        "category": "Writing",
        "score_raw": "8/10",
        "points_earned": 8.0,
        "points_possible": 10.0,
        "percent": 80.0,
        "grade": "B",
        "has_comments": False,
        "flags": dict(FLAGS_OFF),
    }
    a.update(overrides)
    return a


def test_diff_fields_match_frontend():
    match = re.search(r"const DIFF_FIELDS = \[(.*?)\]", DIFF_TS.read_text(), re.DOTALL)
    assert match, "DIFF_FIELDS not found in frontend/lib/diff.ts"
    ts_fields = re.findall(r'"([^"]+)"', match.group(1))
    assert ts_fields == list(DIFF_FIELDS)


def test_flag_change_reported_per_flag():
    prev = [_assignment()]
    cur = [_assignment(flags={**FLAGS_OFF, "missing": True, "late": True})]

    changes = _diff_assignments("english_10", cur, prev)

    assert len(changes) == 1
    assert changes[0]["type"] == "modified"
    assert changes[0]["changes"] == [
        {"field": "late", "old": False, "new": True},
        {"field": "missing", "old": False, "new": True},
    ]


def test_has_comments_change_detected():
    prev = [_assignment()]
    cur = [_assignment(has_comments=True)]

    changes = _diff_assignments("english_10", cur, prev)

    assert len(changes) == 1
    assert changes[0]["changes"] == [{"field": "has_comments", "old": False, "new": True}]


def test_unchanged_assignment_produces_no_change():
    assert _diff_assignments("english_10", [_assignment()], [_assignment()]) == []
