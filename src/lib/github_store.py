"""GitHub Contents API implementation of SnapshotStore."""

import base64
import json
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from src.lib.snapshot_store import SnapshotStore

_API_BASE = "https://api.github.com"


class GitHubStore(SnapshotStore):
    """Reads and writes snapshot data via the GitHub Contents API.

    Repo structure:
        {snapshot_prefix}/{date}/{time}/{slug}/assignments.json
        {snapshot_prefix}/{date}/{time}/metadata.json
        {index_prefix}/rolling_index.json
    """

    def __init__(
        self,
        repo: str,
        token: str,
        snapshot_prefix: str = "snapshots",
        index_prefix: str = "index",
        branch: str = "main",
    ) -> None:
        self.repo = repo
        self.token = token
        self.snapshot_prefix = snapshot_prefix.rstrip("/")
        self.index_prefix = index_prefix.rstrip("/")
        self.branch = branch

    def _headers(self, accept: str = "application/vnd.github+json") -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _contents_url(self, path: str) -> str:
        return f"{_API_BASE}/repos/{self.repo}/contents/{path}"

    async def _get_raw(self, path: str) -> str | None:
        """Fetch raw file content from the repo. Returns None on 404."""
        url = f"{self._contents_url(path)}?ref={self.branch}"
        req = Request(url, headers=self._headers("application/vnd.github.raw+json"))
        try:
            with urlopen(req) as resp:
                return resp.read().decode("utf-8")
        except HTTPError as e:
            if e.code == 404:
                return None
            raise

    async def _get_file_sha(self, path: str) -> str | None:
        """Get the SHA of an existing file (needed for updates)."""
        url = f"{self._contents_url(path)}?ref={self.branch}"
        req = Request(url, headers=self._headers())
        try:
            with urlopen(req) as resp:
                data = json.loads(resp.read())
                return data.get("sha")
        except HTTPError as e:
            if e.code == 404:
                return None
            raise

    async def _put_file(
        self, path: str, content: str, message: str
    ) -> None:
        """Create or update a file in the repo."""
        sha = await self._get_file_sha(path)
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": self.branch,
        }
        if sha:
            payload["sha"] = sha

        data = json.dumps(payload).encode("utf-8")
        req = Request(
            self._contents_url(path),
            data=data,
            headers={**self._headers(), "Content-Type": "application/json"},
            method="PUT",
        )
        with urlopen(req) as resp:
            resp.read()

    def _snapshot_path(self, date: str, time: str, *parts: str) -> str:
        segments = [self.snapshot_prefix, date, time, *parts]
        return "/".join(segments)

    # --- Write ---

    async def write_assignments(
        self, date: str, time: str, slug: str, assignments: list[dict]
    ) -> None:
        path = self._snapshot_path(date, time, slug, "assignments.json")
        content = json.dumps(assignments, indent=2) + "\n"
        await self._put_file(path, content, f"snapshot {date}/{time}: {slug} assignments")

    async def write_metadata(
        self, date: str, time: str, metadata: dict
    ) -> None:
        path = self._snapshot_path(date, time, "metadata.json")
        content = json.dumps(metadata, indent=2) + "\n"
        await self._put_file(path, content, f"snapshot {date}/{time}: metadata")

    async def write_rolling_index(self, index: dict) -> None:
        path = f"{self.index_prefix}/rolling_index.json"
        content = json.dumps(index, indent=2) + "\n"
        await self._put_file(path, content, "update rolling index")

    # --- Read ---

    async def read_assignments(
        self, date: str, time: str, slug: str
    ) -> list[dict] | None:
        path = self._snapshot_path(date, time, slug, "assignments.json")
        raw = await self._get_raw(path)
        return json.loads(raw) if raw else None

    async def read_metadata(self, date: str, time: str) -> dict | None:
        path = self._snapshot_path(date, time, "metadata.json")
        raw = await self._get_raw(path)
        return json.loads(raw) if raw else None

    async def read_rolling_index(self) -> dict | None:
        path = f"{self.index_prefix}/rolling_index.json"
        raw = await self._get_raw(path)
        return json.loads(raw) if raw else None

    # --- Discovery ---

    async def list_snapshots(self) -> list[tuple[str, str]]:
        """List snapshots by traversing the repo directory tree.

        Uses the GitHub Contents API to list date directories, then time
        directories within each. Only includes entries that have metadata.json.
        """
        results = []
        date_dirs = await self._list_dir(self.snapshot_prefix)

        for date_name in date_dirs:
            if not re.match(r"\d{4}-\d{2}-\d{2}$", date_name):
                continue
            time_dirs = await self._list_dir(f"{self.snapshot_prefix}/{date_name}")
            for time_name in time_dirs:
                if not re.match(r"\d{6}$", time_name):
                    continue
                # Check for metadata.json
                meta = await self.read_metadata(date_name, time_name)
                if meta is not None:
                    results.append((date_name, time_name))

        return sorted(results)

    async def _list_dir(self, path: str) -> list[str]:
        """List directory entries in the repo. Returns entry names."""
        url = f"{self._contents_url(path)}?ref={self.branch}"
        req = Request(url, headers=self._headers())
        try:
            with urlopen(req) as resp:
                entries = json.loads(resp.read())
                return [e["name"] for e in entries if e["type"] == "dir"]
        except HTTPError as e:
            if e.code == 404:
                return []
            raise
