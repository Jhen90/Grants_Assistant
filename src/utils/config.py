# ============================================================
# File: src/utils/config.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Application settings via pydantic-settings; loaded once at startup
# ============================================================

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "GMAS"
    app_version: str = "1.1.0"
    log_level: str = "INFO"
    log_file: str = "logs/gmas.log"

    # Database
    database_url: str = "sqlite:///data/gmas.db"

    # Org profile
    org_profile_path: str = "data/org_profile/org_profile_seed_data.md"

    # Scoring thresholds
    recommendation_threshold: float = 7.0  # fit_score >= this → RECOMMENDED
    dedup_fuzzy_threshold: float = 0.85     # similarity >= this → fuzzy duplicate

    # Export
    export_dir: str = "data/exports"

    # Phase 7 — Ollama (deferred)
    ollama_enabled: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Phase 8 — Google Docs (deferred)
    google_docs_enabled: bool = False
    google_docs_credentials_path: str = ""

    @property
    def db_path(self) -> Path:
        """Resolve the SQLite file path from the DATABASE_URL."""
        url = self.database_url
        if url.startswith("sqlite:///"):
            return Path(url.replace("sqlite:///", ""))
        return Path("data/gmas.db")

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
