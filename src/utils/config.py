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

    # ── Grant Discovery / Scraping ───────────────────────────────────────────
    # Polite-fetch identity and cache. The user-agent identifies GMAS to sites
    # and points to a contact so site owners can reach you if needed.
    discovery_user_agent: str = (
        "GMAS-GrantBot/1.1 (+nonprofit grant research; contact: belleticreole90@gmail.com)"
    )
    discovery_cache_dir: str = "data/discovery_cache"
    discovery_respect_robots: bool = True          # honor robots.txt (keep True)
    discovery_fetch_timeout: int = 20              # seconds per HTTP request
    discovery_min_request_interval: float = 2.0    # seconds between hits to same host

    # Source toggles
    source_grants_gov_enabled: bool = True
    grants_gov_api_url: str = "https://api.grants.gov/v1/api/search2"
    source_web_search_enabled: bool = True
    source_funder_sites_enabled: bool = True

    # Aggregators — ToS-compliant only.
    # Candid (Foundation Directory) via official API key; disabled until a key is set.
    candid_api_enabled: bool = False
    candid_api_key: str = ""
    candid_api_url: str = "https://api.candid.org/grants/v1"
    # Instrumentl has no public API and its ToS forbids scraping — import via the
    # CSV/Excel export their subscribers are permitted to download.
    instrumentl_csv_import_enabled: bool = True

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
