# ============================================================
# File: src/discovery/sources/aggregator.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: ToS-COMPLIANT aggregator connectors.
#
#   We deliberately DO NOT scrape Instrumentl or Candid — their Terms of Service
#   prohibit automated extraction. Instead:
#     • CandidApiSource   → uses Candid's official paid API (key-gated, OFF by
#                           default; turns on only when CANDID_API_KEY is set).
#     • InstrumentlCsvImporter → imports the CSV/Excel export that Instrumentl
#                           subscribers are permitted to download from their
#                           own account. No scraping involved.
# ============================================================

from __future__ import annotations

import csv
import io
from datetime import datetime

from src.discovery.base import GrantCandidate, GrantSource
from src.discovery.fetcher import PoliteFetcher
from src.utils.config import get_settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class CandidApiSource(GrantSource):
    """Candid (Foundation Directory) via official API. Disabled until a key is set."""

    name = "candid_api"

    def __init__(self, fetcher: PoliteFetcher | None = None) -> None:
        self._settings = get_settings()
        self._fetcher = fetcher or PoliteFetcher()

    @property
    def enabled(self) -> bool:
        return bool(self._settings.candid_api_enabled and self._settings.candid_api_key)

    def search(self, query: str, org_profile: dict, limit: int = 25) -> list[GrantCandidate]:
        if not self.enabled:
            log.info("Candid API disabled (set candid_api_enabled + candid_api_key to use).")
            return []

        headers = {"Subscription-Key": self._settings.candid_api_key}
        # Candid's API shape varies by product/tier; this is intentionally
        # defensive and maps common fields. Adjust to your subscribed endpoint.
        try:
            resp = self._fetcher._client.get(  # reuse the polite client
                self._settings.candid_api_url,
                params={"query": query, "size": limit},
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            log.warning("Candid API request failed: %s", exc)
            return []

        rows = data.get("data") or data.get("results") or []
        candidates: list[GrantCandidate] = []
        for row in rows:
            candidates.append(
                GrantCandidate(
                    source=self.name,
                    source_url=row.get("url"),
                    raw_title=row.get("title") or row.get("name") or "",
                    raw_funder=row.get("funder_name") or row.get("funder"),
                    extracted={
                        "title": row.get("title") or row.get("name") or "",
                        "funder_name": row.get("funder_name") or row.get("funder"),
                        "source_url": row.get("url"),
                    },
                    field_confidence={"title": 0.9, "funder_name": 0.9},
                )
            )
        return candidates


class InstrumentlCsvImporter:
    """
    Imports an Instrumentl CSV/Excel export. NOT a GrantSource (no live query) —
    it parses a file the subscriber downloaded themselves. ToS-compliant.
    """

    name = "instrumentl_csv"

    # Map of likely Instrumentl column headers -> our extracted keys.
    _COLUMN_MAP = {
        "name": "title",
        "opportunity": "title",
        "title": "title",
        "funder": "funder_name",
        "funder name": "funder_name",
        "deadline": "deadline",
        "next deadline": "deadline",
        "amount": "amount_max",
        "max award": "amount_max",
        "min award": "amount_min",
        "url": "source_url",
        "link": "source_url",
        "website": "source_url",
        "geography": "target_geography",
        "location": "target_geography",
    }

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def enabled(self) -> bool:
        return self._settings.instrumentl_csv_import_enabled

    def import_csv(self, csv_text: str) -> list[GrantCandidate]:
        if not self.enabled:
            return []

        reader = csv.DictReader(io.StringIO(csv_text))
        candidates: list[GrantCandidate] = []
        for row in reader:
            extracted: dict = {}
            for raw_col, value in row.items():
                if raw_col is None or value is None or not str(value).strip():
                    continue
                key = self._COLUMN_MAP.get(raw_col.strip().lower())
                if not key:
                    continue
                extracted[key] = self._coerce(key, str(value).strip())

            if not extracted.get("title"):
                continue
            candidates.append(
                GrantCandidate(
                    source=self.name,
                    source_url=extracted.get("source_url"),
                    raw_title=extracted["title"],
                    raw_funder=extracted.get("funder_name"),
                    extracted=extracted,
                    field_confidence={k: 0.85 for k in extracted},
                )
            )
        log.info("Instrumentl CSV: imported %d candidates.", len(candidates))
        return candidates

    @staticmethod
    def _coerce(key: str, value: str):
        if key == "deadline":
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y"):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            return None
        if key in ("amount_min", "amount_max"):
            cleaned = value.replace("$", "").replace(",", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return None
        return value
