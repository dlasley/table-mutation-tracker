"""Configuration loader for the scraper."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the same directory as this file (src/.env).
# In production the file is copied into the Docker image by the Dockerfile.
# Cloud Run env vars take precedence since load_dotenv doesn't override existing vars.
load_dotenv(Path(__file__).parent / ".env")


@dataclass
class ClassConfig:
    slug: str
    url: str
    gpa_weight: str = "regular"       # "regular", "honors", "ap", "excluded"
    gpa_override_grade: str | None = None  # fallback when final_grade is null


@dataclass
class SourceConfig:
    base_url: str
    login_path: str
    classes: list[ClassConfig]

    @property
    def login_url(self) -> str:
        return self.base_url + self.login_path

    def class_url(self, cls: ClassConfig) -> str:
        return self.base_url + cls.url


@dataclass
class AppConfig:
    sources: dict[str, SourceConfig] = field(default_factory=dict)
    username: str = ""
    password: str = ""


def load_config(
    config_path: str | Path = "config/sources.json",
) -> AppConfig:
    """Load config from sources.json and environment variables."""
    config_path = Path(config_path)
    with open(config_path) as f:
        raw = json.load(f)

    sources = {}
    for source_name, source_data in raw.items():
        classes = [
            ClassConfig(
                slug=c["slug"],
                url=c["url"],
                gpa_weight=c.get("gpa_weight", "regular"),
                gpa_override_grade=c.get("gpa_override_grade"),
            )
            for c in source_data["classes"]
        ]
        sources[source_name] = SourceConfig(
            base_url=source_data["base_url"],
            login_path=source_data["login_path"],
            classes=classes,
        )

    return AppConfig(
        sources=sources,
        username=os.environ.get("SIS_USERNAME", ""),
        password=os.environ.get("SIS_PASSWORD", ""),
    )
