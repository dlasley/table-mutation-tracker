"""Abstract base class for snapshot persistence."""

from abc import ABC, abstractmethod


class SnapshotStore(ABC):
    """Storage interface for snapshot data.

    Implementations handle where/how data is persisted (local filesystem,
    GitHub repo, etc). The store uses (date, time, slug) coordinates to
    address snapshot data, keeping implementations free of path assumptions.
    """

    # --- Write ---

    @abstractmethod
    async def write_assignments(
        self, date: str, time: str, slug: str, assignments: list[dict]
    ) -> None:
        """Persist assignment data for a single class."""
        ...

    @abstractmethod
    async def write_metadata(
        self, date: str, time: str, metadata: dict
    ) -> None:
        """Persist scrape-level metadata for a snapshot."""
        ...

    @abstractmethod
    async def write_rolling_index(self, index: dict) -> None:
        """Persist the rolling index used by the frontend calendar."""
        ...

    # --- Read ---

    @abstractmethod
    async def read_assignments(
        self, date: str, time: str, slug: str
    ) -> list[dict] | None:
        """Load assignment data for a single class. Returns None if not found."""
        ...

    @abstractmethod
    async def read_metadata(
        self, date: str, time: str
    ) -> dict | None:
        """Load scrape-level metadata. Returns None if not found."""
        ...

    @abstractmethod
    async def read_rolling_index(self) -> dict | None:
        """Load the rolling index."""
        ...

    # --- Discovery ---

    @abstractmethod
    async def list_snapshots(self) -> list[tuple[str, str]]:
        """List all available snapshots as (date, time) tuples, sorted chronologically."""
        ...

    # --- Computed (concrete) ---
    # Canonical diff logic, mirrored in frontend/lib/diff.ts for client-side display.
    # Used by the /rebuild-index Cloud Run endpoint (called by n8n after each scrape)
    # and by generate_synthetic.py for building test data indexes.

    async def compute_changelog(
        self,
        current: tuple[str, str],
        previous: tuple[str, str] | None,
    ) -> dict:
        """Compute changelog between two snapshots.

        Compares all classes in the current snapshot against the previous one.
        Returns a changelog dict with class_changes and assignment_changes.
        """
        if previous is None:
            return {"class_changes": [], "assignment_changes": []}

        cur_meta = await self.read_metadata(*current)
        prev_meta = await self.read_metadata(*previous)
        if not cur_meta or not prev_meta:
            return {"class_changes": [], "assignment_changes": []}

        cur_slugs = set(cur_meta.get("classes", {}).keys())
        prev_slugs = set(prev_meta.get("classes", {}).keys())

        class_changes = []
        assignment_changes = []

        # Detect added/removed classes
        for slug in cur_slugs - prev_slugs:
            class_changes.append({"class": slug, "type": "added"})
        for slug in prev_slugs - cur_slugs:
            class_changes.append({"class": slug, "type": "deleted"})

        # Compare assignments for classes present in both
        for slug in cur_slugs & prev_slugs:
            cur_assignments = await self.read_assignments(*current, slug) or []
            prev_assignments = await self.read_assignments(*previous, slug) or []

            changes = _diff_assignments(slug, cur_assignments, prev_assignments)
            assignment_changes.extend(changes)

            # Check for class-level grade changes
            cur_cls = cur_meta["classes"].get(slug, {})
            prev_cls = prev_meta["classes"].get(slug, {})
            if cur_cls.get("final_grade") != prev_cls.get("final_grade"):
                class_changes.append({
                    "class": slug,
                    "type": "modified",
                    "field": "final_grade",
                    "old": prev_cls.get("final_grade"),
                    "new": cur_cls.get("final_grade"),
                })

        return {
            "class_changes": class_changes,
            "assignment_changes": assignment_changes,
        }

    async def rebuild_rolling_index(self) -> dict:
        """Scan all snapshots and rebuild the rolling index.

        Computes changelogs on the fly by diffing consecutive snapshots.
        Writes the result via write_rolling_index.
        """
        all_snapshots = await self.list_snapshots()
        snapshots_list = []

        for i, (date, time) in enumerate(all_snapshots):
            metadata = await self.read_metadata(date, time) or {}

            # Compute changelog against previous snapshot
            previous = all_snapshots[i - 1] if i > 0 else None
            changelog = await self.compute_changelog((date, time), previous)

            class_changes = changelog.get("class_changes", [])
            assignment_changes = changelog.get("assignment_changes", [])

            added = sum(1 for c in assignment_changes if c["type"] == "added")
            modified = sum(1 for c in assignment_changes if c["type"] == "modified")
            deleted = sum(1 for c in assignment_changes if c["type"] == "deleted")

            classes = {}
            for slug, cls_meta in metadata.get("classes", {}).items():
                classes[slug] = {
                    "course": cls_meta.get("course", slug),
                    "final_grade": cls_meta.get("final_grade"),
                    "final_percent": cls_meta.get("final_percent"),
                    "assignment_count": cls_meta.get("assignment_count", 0),
                }

            snapshots_list.append({
                "date": date,
                "time": time,
                "scrape_timestamp": metadata.get("scrape_timestamp"),
                "previous_snapshot": f"{previous[0]}/{previous[1]}" if previous else None,
                "changes": {
                    "class_level": len(class_changes),
                    "added": added,
                    "modified": modified,
                    "deleted": deleted,
                    "total": len(assignment_changes),
                },
                "classes": classes,
            })

        index = {"snapshots": snapshots_list}
        await self.write_rolling_index(index)
        return index


def _diff_assignments(
    slug: str, current: list[dict], previous: list[dict]
) -> list[dict]:
    """Diff two assignment lists for a single class.

    Called by compute_changelog during rolling index rebuild.
    """
    prev_by_key = {(a["name"], a["due_date"]): a for a in previous}
    cur_by_key = {(a["name"], a["due_date"]): a for a in current}

    changes = []

    # Added assignments
    for key in cur_by_key.keys() - prev_by_key.keys():
        a = cur_by_key[key]
        changes.append({
            "class": slug,
            "assignment": a["name"],
            "due_date": a["due_date"],
            "type": "added",
        })

    # Deleted assignments
    for key in prev_by_key.keys() - cur_by_key.keys():
        a = prev_by_key[key]
        changes.append({
            "class": slug,
            "assignment": a["name"],
            "due_date": a["due_date"],
            "type": "deleted",
        })

    # Modified assignments
    for key in cur_by_key.keys() & prev_by_key.keys():
        cur_a = cur_by_key[key]
        prev_a = prev_by_key[key]

        field_changes = []
        for field_name in ("score_raw", "percent", "grade", "category"):
            if cur_a.get(field_name) != prev_a.get(field_name):
                field_changes.append({
                    "field": field_name,
                    "old": prev_a.get(field_name),
                    "new": cur_a.get(field_name),
                })

        # Check flags changes
        cur_flags = cur_a.get("flags", {})
        prev_flags = prev_a.get("flags", {})
        if cur_flags != prev_flags:
            field_changes.append({
                "field": "flags",
                "old": prev_flags,
                "new": cur_flags,
            })

        if field_changes:
            changes.append({
                "class": slug,
                "assignment": cur_a["name"],
                "due_date": cur_a["due_date"],
                "type": "modified",
                "changes": field_changes,
            })

    return changes
