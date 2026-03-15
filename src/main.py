"""Scrape all classes, return structured result with full data payload."""

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import datetime

from playwright.async_api import async_playwright

from src.config import load_config
from src.scraper.base import ClassSnapshot
from src.scraper.sis import SISSource


@dataclass
class ClassResult:
    """Per-class scrape result with assignments and metadata."""

    slug: str
    assignments: list[dict]
    metadata: dict


@dataclass
class ScrapeResult:
    """Full scrape result. Contains everything n8n needs to commit to GitHub."""

    date: str
    time: str
    scrape_timestamp: str
    classes: list[ClassResult] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "time": self.time,
            "scrape_timestamp": self.scrape_timestamp,
            "classes": [
                {
                    "slug": c.slug,
                    "assignments": c.assignments,
                    "metadata": c.metadata,
                }
                for c in self.classes
            ],
            "metadata": self.metadata,
        }


def _snapshot_to_class_result(snap: ClassSnapshot) -> ClassResult:
    """Convert a ClassSnapshot to a ClassResult with serializable data."""
    return ClassResult(
        slug=snap.slug,
        assignments=[asdict(a) for a in snap.assignments],
        metadata=asdict(snap.metadata),
    )


async def run_scrape() -> ScrapeResult:
    config = load_config()
    source_config = config.sources["sis"]
    scraper = SISSource()
    timestamp = datetime.now().astimezone()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        # Login
        print("Logging in...")
        await page.goto(source_config.login_url, wait_until="networkidle")
        await scraper.login(page, config.username, config.password)

        # Verify authentication succeeded by checking for the SIS auth cookie.
        cookies = await context.cookies()
        if not any(c["name"] == "psaid" for c in cookies):
            raise RuntimeError(
                "Authentication failed: Auth cookie not found after login. "
                "Credentials may be invalid. "
                f"Current URL: {page.url}"
            )
        print(f"  Logged in. URL: {page.url}")

        # Scrape each class
        snapshots = []

        for i, cls in enumerate(source_config.classes):
            if i > 0:
                await scraper.throttle()

            print(f"\nScraping class {i+1}/{len(source_config.classes)}...")
            snapshot = await scraper.scrape_class(page, source_config, cls)

            meta = snapshot.metadata
            print(f"  {meta.course} | {meta.teacher}")
            print(f"  Grade: {meta.final_grade} {meta.final_percent}%")
            print(f"  Assignments: {meta.assignment_count} | Last updated: {meta.last_updated}")

            snapshots.append(snapshot)

        await browser.close()

    # Build class results
    date_str = timestamp.strftime("%Y-%m-%d")
    time_str = timestamp.strftime("%H%M%S")
    class_results = [_snapshot_to_class_result(snap) for snap in snapshots]

    # Build metadata (same structure as metadata.json in data repo)
    metadata = {
        "scrape_timestamp": timestamp.isoformat(),
        "source": "sis",
        "classes": {cr.slug: cr.metadata for cr in class_results},
    }

    result = ScrapeResult(
        date=date_str,
        time=time_str,
        scrape_timestamp=timestamp.isoformat(),
        classes=class_results,
        metadata=metadata,
    )

    print(f"\nDone! {result.date}/{result.time} - {len(result.classes)} classes")
    return result
