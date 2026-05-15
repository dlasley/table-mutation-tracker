"""Shared pytest fixtures and an in-memory SnapshotStore for tests."""

from src.lib.snapshot_store import SnapshotStore


class FakeStore(SnapshotStore):
    """In-memory SnapshotStore used by tests. Stores everything in dicts."""

    def __init__(self) -> None:
        self.metadata: dict[tuple[str, str], dict] = {}
        self.assignments: dict[tuple[str, str, str], list[dict]] = {}
        self.rolling: dict | None = None

    async def write_assignments(self, date, time, slug, assignments):
        self.assignments[(date, time, slug)] = assignments

    async def write_metadata(self, date, time, metadata):
        self.metadata[(date, time)] = metadata

    async def write_rolling_index(self, index):
        self.rolling = index

    async def read_assignments(self, date, time, slug):
        return self.assignments.get((date, time, slug))

    async def read_metadata(self, date, time):
        return self.metadata.get((date, time))

    async def read_rolling_index(self):
        return self.rolling

    async def list_snapshots(self):
        return sorted(self.metadata.keys())
