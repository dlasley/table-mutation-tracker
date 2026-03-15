"""Normalization utilities for SIS data extraction."""

import re
from datetime import datetime


FLAG_NAMES = ("collected", "late", "missing", "exempt", "absent", "incomplete", "excluded")


def normalize_date(date_str: str) -> str:
    """Convert MM/DD/YYYY to ISO YYYY-MM-DD format."""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str.strip(), "%m/%d/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return date_str.strip()


def parse_score(score_text: str) -> tuple[float | None, float | None]:
    """Parse a score like '10/20' or '--/20' into (points_earned, points_possible)."""
    if "/" not in score_text:
        return None, None
    parts = score_text.split("/", 1)
    earned_str = parts[0].strip()
    possible_str = parts[1].strip()

    earned = None
    if earned_str != "--":
        try:
            earned = float(earned_str)
        except ValueError:
            pass

    possible = None
    try:
        possible = float(possible_str)
    except ValueError:
        pass

    return earned, possible


def parse_percent(pct_text: str) -> float | None:
    """Parse a percentage string to float, or None if empty."""
    pct_text = pct_text.strip()
    if not pct_text:
        return None
    try:
        return float(pct_text)
    except ValueError:
        return None


def parse_final_grade(raw: str) -> tuple[str | None, float | None]:
    """Split a combined grade string like 'F30%' or 'B+89%' into (letter, percent).

    Also handles '--' (no grade) and cases like 'A100%'.
    """
    raw = raw.strip()
    if not raw or raw == "--":
        return None, None

    # Match letter grade (A-F with optional + or -) followed by optional number and %
    match = re.match(r"^([A-F][+-]?)(\d+(?:\.\d+)?)?%?$", raw, re.IGNORECASE)
    if match:
        letter = match.group(1)
        pct = float(match.group(2)) if match.group(2) else None
        return letter, pct

    return raw, None
