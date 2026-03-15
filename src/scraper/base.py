"""Abstract base class for table data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from playwright.async_api import Page

from src.config import ClassConfig, SourceConfig


@dataclass
class Assignment:
    due_date: str  # ISO format YYYY-MM-DD
    category: str
    name: str
    flags: dict[str, bool]
    score_raw: str
    points_earned: float | None
    points_possible: float | None
    percent: float | None
    grade: str | None
    has_comments: bool

    @property
    def identity_key(self) -> tuple[str, str]:
        """Composite key for matching assignments across snapshots."""
        return (self.name, self.due_date)


@dataclass
class ClassMetadata:
    course: str
    teacher: str
    expression: str
    term: str
    final_grade: str | None
    final_percent: float | None
    assignment_count: int
    last_updated: str | None


@dataclass
class ClassSnapshot:
    slug: str
    metadata: ClassMetadata
    assignments: list[Assignment]


class TableSource(ABC):
    """Abstract base for scraping assignment data from a portal."""

    @abstractmethod
    async def login(self, page: Page, username: str, password: str) -> None:
        """Authenticate with the portal."""
        ...

    @abstractmethod
    async def scrape_class(
        self, page: Page, source_config: SourceConfig, class_config: ClassConfig
    ) -> ClassSnapshot:
        """Scrape a single class page and return normalized data."""
        ...
