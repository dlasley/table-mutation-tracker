"""Tests for SnapshotStore.append_to_rolling_index."""

import pytest

from src.lib.snapshot_store import OutOfOrderError
from tests.conftest import FakeStore


async def test_append_to_empty_index_no_previous():
    store = FakeStore()
    await store.write_metadata(
        "2026-05-15",
        "230002",
        {"classes": {"english_10": {"course": "English 10", "final_grade": "B"}}},
    )

    index = await store.append_to_rolling_index("2026-05-15", "230002")

    assert len(index["snapshots"]) == 1
    entry = index["snapshots"][0]
    assert entry["date"] == "2026-05-15"
    assert entry["time"] == "230002"
    assert entry["previous_snapshot"] is None
    assert entry["changes"]["total"] == 0


async def test_append_after_existing_diffs_against_last():
    store = FakeStore()

    # Snapshot 1: one assignment in English
    await store.write_metadata(
        "2026-05-14",
        "150000",
        {"classes": {"english_10": {"course": "English 10", "final_grade": "B"}}},
    )
    await store.write_assignments(
        "2026-05-14",
        "150000",
        "english_10",
        [{"name": "Essay 1", "due_date": "2026-05-10", "grade": "B"}],
    )
    await store.rebuild_rolling_index()

    # Snapshot 2: original + one new assignment
    await store.write_metadata(
        "2026-05-15",
        "230002",
        {"classes": {"english_10": {"course": "English 10", "final_grade": "B"}}},
    )
    await store.write_assignments(
        "2026-05-15",
        "230002",
        "english_10",
        [
            {"name": "Essay 1", "due_date": "2026-05-10", "grade": "B"},
            {"name": "Essay 2", "due_date": "2026-05-17", "grade": None},
        ],
    )

    index = await store.append_to_rolling_index("2026-05-15", "230002")

    assert len(index["snapshots"]) == 2
    new_entry = index["snapshots"][-1]
    assert new_entry["date"] == "2026-05-15"
    assert new_entry["previous_snapshot"] == "2026-05-14/150000"
    assert new_entry["changes"]["added"] == 1
    assert new_entry["changes"]["total"] == 1


async def test_append_is_idempotent_replaces_in_place():
    store = FakeStore()
    await store.write_metadata(
        "2026-05-15",
        "230002",
        {"classes": {"english_10": {"course": "English 10", "final_grade": "B"}}},
    )

    await store.append_to_rolling_index("2026-05-15", "230002")
    index = await store.append_to_rolling_index("2026-05-15", "230002")

    assert len(index["snapshots"]) == 1


async def test_append_out_of_order_raises():
    store = FakeStore()
    await store.write_metadata("2026-05-15", "150000", {"classes": {}})
    await store.rebuild_rolling_index()

    # Now try to append a snapshot dated earlier than what's in the index
    await store.write_metadata("2026-05-14", "150000", {"classes": {}})

    with pytest.raises(OutOfOrderError):
        await store.append_to_rolling_index("2026-05-14", "150000")


async def test_append_passes_class_weights_to_gpa():
    store = FakeStore()
    await store.write_metadata(
        "2026-05-15",
        "230002",
        {
            "classes": {
                "english_10": {
                    "course": "English 10",
                    "final_grade": "A",
                    "final_percent": "95",
                    "assignment_count": 3,
                }
            }
        },
    )

    class_weights = {"english_10": {"weight": "honors", "override_grade": None}}
    index = await store.append_to_rolling_index(
        "2026-05-15", "230002", class_weights=class_weights
    )

    # English A (4.0) + honors bonus (0.5) = 4.5, divided by 1 class
    assert index["snapshots"][0]["gpa"] == 4.5
