#!/usr/bin/env python3
"""Generate synthetic snapshot data for frontend testing.

Creates N days of synthetic snapshots (2 per day) with realistic inter-snapshot
variance: new assignments, grading, backdated score changes, rare deletions.

Usage:
    GITHUB_TOKEN=$(gh auth token) python scripts/generate_synthetic.py --days 14
"""

import argparse
import asyncio
import copy
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lib.github_store import GitHubStore

SEED = 42
REFERENCE_DATE = date(2026, 3, 10)
TIMES = ["083000", "153000"]

GRADE_SCALE = [
    (93, "A"),
    (90, "A-"),
    (87, "B+"),
    (83, "B"),
    (80, "B-"),
    (78, "C+"),
]


def percent_to_grade(pct: float) -> str:
    for threshold, letter in GRADE_SCALE:
        if pct >= threshold:
            return letter
    return "C+"


def score_raw(earned: float, possible: float) -> str:
    e = int(earned) if earned == int(earned) else earned
    p = int(possible) if possible == int(possible) else possible
    return f"{e}/{p}"


def make_assignment(
    name: str, due_date: str, category: str, points_possible: float,
    rng: random.Random, graded: bool = True,
) -> dict:
    a = {
        "due_date": due_date,
        "category": category,
        "name": name,
        "flags": {
            "collected": False, "late": False, "missing": False,
            "exempt": False, "absent": False, "incomplete": False,
            "excluded": False,
        },
        "score_raw": f"--/{int(points_possible) if points_possible == int(points_possible) else points_possible}",
        "points_earned": None,
        "points_possible": points_possible,
        "percent": None,
        "grade": None,
        "has_comments": False,
    }
    if graded:
        pct = rng.uniform(78, 97)
        pe = round(pct / 100 * points_possible, 1)
        a["points_earned"] = pe
        a["percent"] = round(pe / points_possible * 100, 2)
        a["grade"] = percent_to_grade(a["percent"])
        a["score_raw"] = score_raw(pe, points_possible)
    return a


def compute_final_grade(assignments: list[dict]) -> tuple[float | None, str | None]:
    graded = [a for a in assignments
              if a["points_earned"] is not None and a["points_possible"]]
    if not graded:
        return None, None
    total_earned = sum(a["points_earned"] for a in graded)
    total_possible = sum(a["points_possible"] for a in graded)
    if total_possible == 0:
        return None, None
    pct = round(total_earned / total_possible * 100, 1)
    return pct, percent_to_grade(pct)


# ---------------------------------------------------------------------------
# Class metadata (mirrors real data)
# ---------------------------------------------------------------------------

CLASS_META = {
    "geometry": {
        "course": "Geometry",
        "teacher": "Burrell Jr., John",
        "teacher_email": "john.burrell@aimsk12.org",
        "expression": "1(A)",
        "term": "S2",
    },
    "ap_world_history": {
        "course": "AP World History",
        "teacher": "Krishnan, Rohit",
        "teacher_email": "Rohit.Krishnan@aimsk12.org",
        "expression": "2(A)",
        "term": "S2",
    },
    "physical_education": {
        "course": "Physical Education",
        "teacher": "Esola, Michael",
        "teacher_email": "mike.esola@aimsk12.org",
        "expression": "3(A)",
        "term": "S2",
    },
    "english_10_honors": {
        "course": "English 10 (Honors)",
        "teacher": "Carroll, Colleen",
        "teacher_email": "colleen.carroll@aimsk12.org",
        "expression": "4(A)",
        "term": "S2",
    },
    "ap_environmental_science": {
        "course": "AP Environmental Science",
        "teacher": "Ibrahem, Osama",
        "teacher_email": "osama.ibrahem@aimsk12.org",
        "expression": "5(A)",
        "term": "S2",
    },
    "french_i": {
        "course": "French I",
        "teacher": "Ayon, Estevan",
        "teacher_email": "Estevan.Ayon@aimsk12.org",
        "expression": "6(A)",
        "term": "S2",
    },
}

# ---------------------------------------------------------------------------
# Base assignments per class (the starting state for day 1, snapshot 1)
# Each tuple: (name, category, points_possible)
# ---------------------------------------------------------------------------

BASE_ASSIGNMENTS = {
    "geometry": [
        ("Do Now Assessment 2/10/26", "Quizzes", 25),
        ("Do Now Assessment 2/17/26", "Quizzes", 25),
        ("Do Now Assessment 2/24/26", "Quizzes", 25),
        ("HW Labeling Triangle Congruence", "Homework", 20),
        ("HW Pythagorean Theorem Practice", "Homework", 20),
        ("IXL M7Q to 80", "Homework", 20),
        ("IXL Y9C to 80", "Homework", 20),
        ("Assessment Pythagorean Th on Rt. Triangles", "Quizzes", 30),
        ("Assessment Circumcenter and Incenter", "Quizzes", 25),
        ("HW Triangle Inequality", "Homework", 20),
        ("Chapter 7 Test", "Chapter Tests/Project Based", 50),
    ],
    "ap_world_history": [
        ("DBQ Practice: Silk Road Trade", "Homework", 25),
        ("Reading Response Ch 14", "Homework", 20),
        ("Reading Response Ch 15", "Homework", 20),
        ("Unit 3 Test: Land-Based Empires", "Chapter Tests/Project Based", 50),
        ("SAQ Practice: Columbian Exchange", "Quizzes", 15),
        ("Stamp Act Primary Source Analysis", "Homework", 20),
        ("Timeline Project: Age of Exploration", "Chapter Tests/Project Based", 40),
    ],
    "physical_education": [
        ("Fitness Test February", "Participation", 30),
        ("Daily Participation Week 6", "Participation", 10),
        ("Daily Participation Week 7", "Participation", 10),
    ],
    "english_10_honors": [
        ("The Lottery Reading Questions", "Homework", 20),
        ("Vocabulary Unit 5", "Quizzes", 25),
        ("Essay Draft 1: Symbolism Analysis", "Chapter Tests/Project Based", 50),
        ("Parade Participation", "Participation", 10),
        ("The Machine Packet", "Homework", 30),
        ("Grammar Review: Semicolons", "Homework", 15),
        ("Class Discussion: Lord of the Flies Ch 1-3", "Participation", 10),
    ],
    "ap_environmental_science": [
        ("Lab Report: Soil pH Testing", "Chapter Tests/Project Based", 50),
        ("Chapter 8 Quiz: Aquatic Biomes", "Quizzes", 20),
        ("FRQ Practice: Biodiversity", "Homework", 25),
        ("Textbook Questions 8.1-8.3", "Homework", 15),
        ("Chapter 7 Quiz: Atmospheric Science", "Quizzes", 20),
        ("Lab Report: Air Quality Monitoring", "Chapter Tests/Project Based", 50),
        ("Ecosystem Services Worksheet", "Homework", 15),
        ("Unit 2 Exam", "Chapter Tests/Project Based", 60),
    ],
    "french_i": [
        ("Vocabulary Quiz Ch 6", "Quizzes", 25),
        ("Conjugation Practice: etre/avoir", "Homework", 15),
        ("Oral Assessment: Self Introduction", "Chapter Tests/Project Based", 30),
        ("Vocabulary Quiz Ch 7", "Quizzes", 25),
        ("Listening Comprehension Ex 4", "Homework", 20),
        ("Written Response: Ma Famille", "Homework", 20),
    ],
}

# Assignments that start ungraded in the base snapshot.
# (class_slug, assignment_name)
START_UNGRADED = {
    ("english_10_honors", "Parade Participation"),
    ("english_10_honors", "The Machine Packet"),
    ("physical_education", "Daily Participation Week 7"),
    ("ap_world_history", "Timeline Project: Age of Exploration"),
    ("geometry", "Chapter 7 Test"),
}

# ---------------------------------------------------------------------------
# Pool of new assignments that can be added over time.
# Each tuple: (name, category, points_possible)
# These cycle through as snapshots progress.
# ---------------------------------------------------------------------------

NEW_ASSIGNMENT_POOL = {
    "geometry": [
        ("Do Now Assessment 3/3/26", "Quizzes", 25),
        ("HW Angle Bisector Theorem", "Homework", 20),
        ("IXL Z4B to 80", "Homework", 20),
        ("Do Now Assessment 3/10/26", "Quizzes", 25),
        ("HW Midsegment Theorem", "Homework", 20),
        ("Assessment Triangle Similarity", "Quizzes", 30),
        ("HW Proportions in Triangles", "Homework", 20),
        ("Chapter 8 Test", "Chapter Tests/Project Based", 50),
        ("IXL A2R to 80", "Homework", 20),
        ("Do Now Assessment 3/17/26", "Quizzes", 25),
    ],
    "ap_world_history": [
        ("Reading Response Ch 16", "Homework", 20),
        ("DBQ Practice: Atlantic Slave Trade", "Homework", 25),
        ("SAQ Practice: Maritime Empires", "Quizzes", 15),
        ("Reading Response Ch 17", "Homework", 20),
        ("Unit 4 Test: Transoceanic Connections", "Chapter Tests/Project Based", 50),
        ("LEQ Practice: Comparison of Empires", "Homework", 25),
        ("Reading Response Ch 18", "Homework", 20),
        ("Primary Source: Bartolome de las Casas", "Homework", 20),
    ],
    "physical_education": [
        ("Daily Participation Week 8", "Participation", 10),
        ("Fitness Test March", "Participation", 30),
        ("Daily Participation Week 9", "Participation", 10),
        ("Daily Participation Week 10", "Participation", 10),
        ("Basketball Skills Assessment", "Participation", 20),
        ("Daily Participation Week 11", "Participation", 10),
    ],
    "english_10_honors": [
        ("Vocabulary Unit 6", "Quizzes", 25),
        ("Essay Draft 2: Symbolism Analysis", "Chapter Tests/Project Based", 50),
        ("Class Discussion: Lord of the Flies Ch 4-6", "Participation", 10),
        ("Grammar Review: Colons", "Homework", 15),
        ("Reading Questions: Lord of the Flies Ch 7-9", "Homework", 20),
        ("Vocabulary Unit 7", "Quizzes", 25),
        ("Essay Final: Symbolism Analysis", "Chapter Tests/Project Based", 100),
        ("Class Discussion: Lord of the Flies Ch 10-12", "Participation", 10),
    ],
    "ap_environmental_science": [
        ("Lab Report: Water Quality Analysis", "Chapter Tests/Project Based", 50),
        ("Chapter 9 Quiz: Land Use", "Quizzes", 20),
        ("FRQ Practice: Human Impact", "Homework", 25),
        ("Textbook Questions 9.1-9.3", "Homework", 15),
        ("Lab Report: Stream Ecology", "Chapter Tests/Project Based", 50),
        ("Chapter 10 Quiz: Energy Resources", "Quizzes", 20),
        ("Renewable Energy Worksheet", "Homework", 15),
        ("Unit 3 Exam", "Chapter Tests/Project Based", 60),
    ],
    "french_i": [
        ("Vocabulary Quiz Ch 8", "Quizzes", 25),
        ("Conjugation Practice: Regular -ir verbs", "Homework", 15),
        ("Written Response: Mon Ecole", "Homework", 20),
        ("Vocabulary Quiz Ch 9", "Quizzes", 25),
        ("Oral Assessment: Ordering Food", "Chapter Tests/Project Based", 30),
        ("Listening Comprehension Ex 5", "Homework", 20),
        ("Conjugation Practice: Irregular verbs", "Homework", 15),
        ("Written Response: Les Vacances", "Homework", 20),
    ],
}


# ---------------------------------------------------------------------------
# Snapshot generation
# ---------------------------------------------------------------------------

def build_base_state(rng: random.Random) -> dict[str, list[dict]]:
    """Create the initial assignment state for all classes."""
    ref = REFERENCE_DATE.isoformat()
    state = {}
    for slug, defs in BASE_ASSIGNMENTS.items():
        assignments = []
        for name, category, pp in defs:
            graded = (slug, name) not in START_UNGRADED
            a = make_assignment(name, ref, category, pp, rng, graded=graded)
            assignments.append(a)
        state[slug] = assignments
    return state


def mutate_snapshot(
    state: dict[str, list[dict]],
    rng: random.Random,
    pool_cursors: dict[str, int],
    snapshot_date: str,
    is_afternoon: bool,
) -> dict[str, list[dict]]:
    """Apply small mutations to produce the next snapshot state.

    Afternoon snapshots get fewer changes than morning ones.
    """
    new_state = copy.deepcopy(state)

    for slug, assignments in new_state.items():
        pool = NEW_ASSIGNMENT_POOL[slug]
        cursor = pool_cursors[slug]

        # --- Grade an ungraded assignment ---
        ungraded = [a for a in assignments if a["points_earned"] is None]
        grade_chance = 0.25 if is_afternoon else 0.45
        if ungraded and rng.random() < grade_chance:
            a = rng.choice(ungraded)
            pct = rng.uniform(78, 97)
            pe = round(pct / 100 * a["points_possible"], 1)
            a["points_earned"] = pe
            a["percent"] = round(pe / a["points_possible"] * 100, 2)
            a["grade"] = percent_to_grade(a["percent"])
            a["score_raw"] = score_raw(pe, a["points_possible"])

        # --- Add a new assignment from the pool ---
        add_chance = 0.15 if is_afternoon else 0.35
        if cursor < len(pool) and rng.random() < add_chance:
            name, category, pp = pool[cursor]
            # ~60% chance new assignment arrives already graded
            graded = rng.random() < 0.6
            new_a = make_assignment(name, snapshot_date, category, pp, rng, graded=graded)
            assignments.insert(0, new_a)
            pool_cursors[slug] = cursor + 1

        # --- Modify an existing graded assignment (backdated change) ---
        graded_list = [a for a in assignments
                       if a["points_earned"] is not None and a["points_possible"]]
        mod_chance = 0.10 if is_afternoon else 0.22
        if graded_list and rng.random() < mod_chance:
            a = rng.choice(graded_list)
            # Shift grade by -5 to +8 percentage points
            old_pct = a["percent"]
            delta = rng.uniform(-5, 8)
            new_pct = max(78, min(97, old_pct + delta))
            pe = round(new_pct / 100 * a["points_possible"], 1)
            a["points_earned"] = pe
            a["percent"] = round(pe / a["points_possible"] * 100, 2)
            a["grade"] = percent_to_grade(a["percent"])
            a["score_raw"] = score_raw(pe, a["points_possible"])

        # --- Delete an assignment (rare) ---
        del_chance = 0.02 if is_afternoon else 0.05
        if len(assignments) > 3 and rng.random() < del_chance:
            idx = rng.randint(0, len(assignments) - 1)
            assignments.pop(idx)

    return new_state


def build_metadata(
    snapshot_date: str, time: str, class_assignments: dict[str, list[dict]],
    previous_snapshot: str | None,
) -> dict:
    meta = {
        "date": snapshot_date,
        "time": time,
        "scrape_timestamp": f"{snapshot_date}T{'08:30:00' if time == '083000' else '15:30:00'}-08:00",
        "source": "sis",
        "previous_snapshot": previous_snapshot,
        "classes": {},
    }
    for slug, info in CLASS_META.items():
        pct, grade = compute_final_grade(class_assignments.get(slug, []))
        meta["classes"][slug] = {
            **info,
            "final_grade": grade,
            "final_percent": pct,
            "assignment_count": len(class_assignments.get(slug, [])),
            "last_updated": f"{int(snapshot_date[5:7])}/{int(snapshot_date[8:10])}/{snapshot_date[:4]}",
        }
    return meta


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def write_snapshot(
    store: GitHubStore, snapshot_date: str, time: str,
    metadata: dict, class_assignments: dict[str, list[dict]],
) -> None:
    for slug, assignments in class_assignments.items():
        await store.write_assignments(snapshot_date, time, slug, assignments)
    await store.write_metadata(snapshot_date, time, metadata)


def _build_store():
    import os

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("DATA_REPO", "dlasley/table-mutation-data")
    if not token:
        print("ERROR: GITHUB_TOKEN env var required")
        print("  Hint: GITHUB_TOKEN=$(gh auth token) python scripts/generate_synthetic.py --days 7")
        sys.exit(1)

    return GitHubStore(
        repo=repo,
        token=token,
        snapshot_prefix="snapshots/synthetic",
        index_prefix="index/synthetic",
    )


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic snapshot data")
    parser.add_argument("--days", type=int, required=True,
                        help="Number of days to generate (1-30)")
    args = parser.parse_args()

    if not 1 <= args.days <= 30:
        print("ERROR: --days must be between 1 and 30")
        sys.exit(1)

    rng = random.Random(SEED)
    store = _build_store()

    # Generate dates from (days-1) ago through reference date
    dates = [
        (REFERENCE_DATE - timedelta(days=args.days - 1 - i)).isoformat()
        for i in range(args.days)
    ]

    # Build base state
    state = build_base_state(rng)
    pool_cursors = {slug: 0 for slug in CLASS_META}

    prev_snapshot = None
    total_snapshots = 0

    for snapshot_date in dates:
        for time in TIMES:
            is_afternoon = time == "153000"

            # First snapshot uses base state; all others mutate
            if total_snapshots > 0:
                state = mutate_snapshot(
                    state, rng, pool_cursors, snapshot_date, is_afternoon,
                )

            metadata = build_metadata(snapshot_date, time, state, prev_snapshot)

            print(f"  Writing {snapshot_date}/{time}...")
            asyncio.run(write_snapshot(store, snapshot_date, time, metadata, state))

            prev_snapshot = f"{snapshot_date}/{time}"
            total_snapshots += 1

    # Rebuild rolling index
    print("Rebuilding rolling index...")
    index = asyncio.run(store.rebuild_rolling_index())
    print(f"  Indexed {len(index['snapshots'])} snapshots")

    print(f"\nDone: {total_snapshots} snapshots across {args.days} days pushed to GitHub")
    print("  Set DATA_PREFIX=synthetic on Vercel to use it")


if __name__ == "__main__":
    main()
