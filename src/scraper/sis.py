"""SIS (Student Information System) portal scraper implementation."""

import asyncio
import random
import re

from bs4 import BeautifulSoup
from playwright.async_api import Page

from src.config import ClassConfig, SourceConfig
from src.scraper.base import Assignment, ClassMetadata, ClassSnapshot, TableSource
from src.scraper.normalize import (
    FLAG_NAMES,
    normalize_date,
    parse_final_grade,
    parse_percent,
    parse_score,
)


class SISSource(TableSource):
    """Scraper for SIS (Student Information System) portal."""

    async def login(self, page: Page, username: str, password: str) -> None:
        try:
            await page.wait_for_selector("#fieldAccount", state="visible", timeout=10000)
        except Exception:
            content = (await page.content())[:1500]
            print(f"  LOGIN FORM NOT FOUND. Page content: {content}")
            raise
        # Human-like delays between form interactions
        await asyncio.sleep(random.uniform(0.5, 1.5))
        await page.locator("#fieldAccount").click()
        await page.locator("#fieldAccount").type(username, delay=random.uniform(40, 120))
        await asyncio.sleep(random.uniform(0.3, 0.8))
        await page.locator("#fieldPassword").click()
        await page.locator("#fieldPassword").type(password, delay=random.uniform(40, 120))
        await asyncio.sleep(random.uniform(0.5, 1.5))
        await page.click("#btn-enter-sign-in")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(random.uniform(3, 6))

    async def scrape_class(
        self, page: Page, source_config: SourceConfig, class_config: ClassConfig
    ) -> ClassSnapshot:
        url = source_config.class_url(class_config)
        await page.goto(url, wait_until="networkidle")

        # Wait for the score table to render (JS-injected after page load).
        # Wait for a td, not just the table element -- the table shell appears
        # in the DOM before rows are populated, causing page.content() to
        # capture an empty table if we stop waiting too early.
        try:
            await page.wait_for_selector("#scoreTable td", timeout=15000)
        except Exception:
            pass  # Table may legitimately not exist (empty term)

        html = await page.content()
        soup = BeautifulSoup(html, "lxml")

        metadata = self._extract_metadata(soup)
        assignments = self._extract_assignments(soup)
        last_updated = self._extract_last_updated(soup)

        if last_updated:
            metadata.last_updated = last_updated

        # Sort: due_date DESC, then name ASC
        assignments.sort(key=lambda a: (-_date_sort_key(a.due_date), a.name))

        metadata.assignment_count = len(assignments)

        return ClassSnapshot(
            slug=class_config.slug,
            metadata=metadata,
            assignments=assignments,
        )

    @staticmethod
    async def throttle() -> None:
        delay = random.uniform(4, 10)
        await asyncio.sleep(delay)

    def _extract_metadata(self, soup: BeautifulSoup) -> ClassMetadata:
        # The metadata table lost its linkDescList class; locate it by position
        # under #content-main (3rd div child contains the summary table).
        content_main = soup.find(id="content-main")
        meta_table = None
        if content_main:
            divs = content_main.find_all("div", recursive=False)
            if len(divs) >= 3:
                meta_table = divs[2].find("table")
        if not meta_table:
            meta_table = soup.find("table", class_="linkDescList")  # fallback
        cells = []
        if meta_table:
            cells = [td.get_text(strip=True) for td in meta_table.find_all("td")]

        # Cells: [course, teacher, expression, term, final_grade_raw]
        course = cells[0] if len(cells) > 0 else ""
        teacher = cells[1] if len(cells) > 1 else ""
        expression = cells[2] if len(cells) > 2 else ""
        term = cells[3] if len(cells) > 3 else ""
        final_grade_raw = cells[4] if len(cells) > 4 else ""

        final_grade, final_percent = parse_final_grade(final_grade_raw)

        return ClassMetadata(
            course=course,
            teacher=teacher,
            expression=expression,
            term=term,
            final_grade=final_grade,
            final_percent=final_percent,
            assignment_count=0,
            last_updated=None,
        )

    def _extract_assignments(self, soup: BeautifulSoup) -> list[Assignment]:
        score_table = soup.find("table", id="scoreTable")
        if not score_table:
            return []

        rows = score_table.find_all("tr")
        assignments = []

        for row in rows[1:]:  # skip header
            cells = row.find_all("td")
            if not cells or len(cells) < 14:
                continue

            first_text = cells[0].get_text(strip=True)
            if "Last Updated" in first_text:
                continue

            # Parse flags (cells 3-9): flag is active if <img> is present
            flags = {}
            for fi, flag_name in enumerate(FLAG_NAMES):
                cell = cells[3 + fi]
                flags[flag_name] = cell.find("img") is not None

            score_text = cells[10].get_text(strip=True)
            points_earned, points_possible = parse_score(score_text)
            percent = parse_percent(cells[11].get_text(strip=True))
            grade_text = cells[12].get_text(strip=True)

            assignments.append(
                Assignment(
                    due_date=normalize_date(cells[0].get_text(strip=True)),
                    category=cells[1].get_text(strip=True),
                    name=cells[2].get_text(strip=True),
                    flags=flags,
                    score_raw=score_text,
                    points_earned=points_earned,
                    points_possible=points_possible,
                    percent=percent,
                    grade=grade_text or None,
                    has_comments=cells[13].get_text(strip=True) == "View" if len(cells) > 13 else False,
                )
            )

        return assignments

    def _extract_last_updated(self, soup: BeautifulSoup) -> str | None:
        score_table = soup.find("table", id="scoreTable")
        if not score_table:
            return None

        rows = score_table.find_all("tr")
        for row in rows:
            text = row.get_text(strip=True)
            match = re.search(r"Last Updated:\s*(.+)", text)
            if match:
                return match.group(1).strip()
        return None


def _date_sort_key(iso_date: str) -> int:
    """Convert ISO date string to integer for sorting. Returns 0 for unparseable dates."""
    try:
        return int(iso_date.replace("-", ""))
    except (ValueError, AttributeError):
        return 0
