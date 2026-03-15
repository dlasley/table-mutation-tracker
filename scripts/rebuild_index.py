#!/usr/bin/env python3
"""Rebuild the rolling index from existing snapshots in the data repo.

Scans all snapshots, diffs consecutive pairs, and writes updated change
counts. Use this to backfill accurate change data after fixing diff logic.

Usage:
    python scripts/rebuild_index.py
    python scripts/rebuild_index.py --start-date 2026-03-01 --end-date 2026-03-31
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from scripts.lib.github_store import GitHubStore


def main():
    parser = argparse.ArgumentParser(description="Rebuild rolling index from existing snapshots")
    parser.add_argument("--start-date", help="Only include snapshots on or after this date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Only include snapshots on or before this date (YYYY-MM-DD)")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("DATA_REPO")
    if not token or not repo:
        print("Error: GITHUB_TOKEN and DATA_REPO must be set (in .env or environment)")
        sys.exit(1)

    store = GitHubStore(repo=repo, token=token)

    print(f"Rebuilding rolling index for {repo}...")
    index = asyncio.run(store.rebuild_rolling_index())

    # Filter by date range if specified
    if args.start_date or args.end_date:
        original_count = len(index["snapshots"])
        filtered = index["snapshots"]
        if args.start_date:
            filtered = [s for s in filtered if s["date"] >= args.start_date]
        if args.end_date:
            filtered = [s for s in filtered if s["date"] <= args.end_date]
        index["snapshots"] = filtered
        asyncio.run(store.write_rolling_index(index))
        print(f"  Filtered {original_count} -> {len(filtered)} snapshots")

    total_changes = sum(s["changes"]["total"] for s in index["snapshots"])
    print(f"  Indexed {len(index['snapshots'])} snapshots, {total_changes} total changes detected")


if __name__ == "__main__":
    main()
