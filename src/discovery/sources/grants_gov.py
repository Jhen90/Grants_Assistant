# ============================================================
# File: src/discovery/sources/grants_gov.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: grants.gov Search2 API connector. Official, free, public REST
#   endpoint — no key required, no scraping. Returns federal opportunities.
#   API: POST https://api.grants.gov/v1/api/search2
# ============================================================

from __future__ import annotations

from datetime import date, datetime

from src.discovery.base import GrantCandidate, GrantSource
from src.discovery.fetcher import PoliteFetcher
from src.utils.config import get_settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class GrantsGovSource(GrantSource):
    name = "grants.gov"

    def __init__(self, fetcher: PoliteFetcher | None = None) -> None:
        self._settings = get_settings()
        self._fetcher = fetcher or PoliteFetcher()

    @property
    def enabled(self) -> bool:
        return self._settings.source_grants_gov_enabled

    def search(self, query: str, org_profile: dict, limit: int = 25) -> list[GrantCandidate]:
        if not self.enabled:
            return []

        payload = {
            "keyword": query,
            "oppStatuses": "forecasted|posted",  # only currently-open/forecast
            "rows": limit,
            "startRecordNum": 0,
        }
        data = self._fetcher.post_json(self._settings.grants_gov_api_url, payload)
        if not isinstance(data, dict):
            log.info("grants.gov returned no usable data for %r.", query)
            return []

        hits = (data.get("data") or {}).get("oppHits") or []
        candidates: list[GrantCandidate] = []
        for hit in hits:
            candidates.append(self._to_candidate(hit))
        log.info("grants.gov: %d candidates for %r.", len(candidates), query)
        return candidates

    def _to_candidate(self, hit: dict) -> GrantCandidate:
        opp_id = hit.get("id") or hit.get("number")
        url = (
            f"https://www.grants.gov/search-results-detail/{opp_id}" if opp_id else None
        )
        deadline = self._parse_close_date(hit.get("closeDate"))

        extracted: dict = {
            "title": hit.get("title", "").strip(),
            "funder_name": hit.get("agencyName") or hit.get("agency") or "Federal Agency",
            "source_url": url,
            "eligibility_501c3_required": False,  # federal varies; human verifies
            "fiscal_sponsorship_allowed": True,
        }
        confidence = {"title": 0.95, "funder_name": 0.9}
        evidence = {"funder_name": hit.get("agencyName", "")}

        if deadline:
            extracted["deadline"] = deadline
            confidence["deadline"] = 0.95
            evidence["deadline"] = f"closeDate={hit.get('closeDate')}"

        return GrantCandidate(
            source=self.name,
            source_url=url,
            raw_title=extracted["title"],
            raw_funder=extracted["funder_name"],
            extracted=extracted,
            field_confidence=confidence,
            evidence=evidence,
        )

    @staticmethod
    def _parse_close_date(value: str | None) -> date | None:
        if not value:
            return None
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None
