# ============================================================
# File: src/services/discovery_service.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: DiscoveryService — orchestrates the discovery pipeline:
#     search/fetch  →  rules-based extract  →  dedup  →  stage candidate  →
#     (human review)  →  import into a real Grant.
#
#   Nothing here auto-creates a Grant. Candidates are staged in
#   discovered_candidates and only become Grants when a human imports them,
#   preserving GMAS's human-in-the-loop guarantee.
# ============================================================

from __future__ import annotations

import json
from datetime import date, datetime

from sqlalchemy.orm import Session

from src.db.org_profile_loader import load as load_org_profile
from src.discovery.base import GrantCandidate
from src.discovery.fetcher import PoliteFetcher
from src.discovery.sources import (
    CandidApiSource,
    FunderSiteSource,
    GrantsGovSource,
    InstrumentlCsvImporter,
    WebSearchSource,
)
from src.engine.deduplication import find_duplicates
from src.models.discovered_candidate import CandidateStatus, DiscoveredCandidate
from src.models.grant import Grant
from src.services.grant_service import GrantService
from src.utils.config import get_settings
from src.utils.error_handler import DuplicateGrantError
from src.utils.logger import get_logger

log = get_logger(__name__)


class DiscoveryService:
    def __init__(self, grant_service: GrantService | None = None) -> None:
        self._settings = get_settings()
        self._grant_svc = grant_service or GrantService()

    # ── 1. SEARCH / SCRAPE ─────────────────────────────────────────────────────

    def run_search(
        self,
        db: Session,
        query: str,
        sources: list[str] | None = None,
        limit_per_source: int = 15,
        profile_path: str | None = None,
    ) -> list[DiscoveredCandidate]:
        """
        Run the discovery pipeline for a query across the selected sources,
        stage de-duplicated candidates, and return the newly staged rows.

        `sources` filters by connector name; None = all enabled.
        """
        org_profile = load_org_profile(
            profile_path or self._settings.org_profile_path
        )

        fetcher = PoliteFetcher()
        try:
            connectors = self._active_connectors(fetcher, sources)
            raw: list[GrantCandidate] = []
            for connector in connectors:
                try:
                    raw.extend(connector.search(query, org_profile, limit_per_source))
                except Exception as exc:  # noqa: BLE001 — isolate connector failures
                    log.warning("Source %s failed: %s", connector.name, exc)
        finally:
            fetcher.close()

        return self._stage_candidates(db, raw, query)

    def fetch_known_url(
        self, db: Session, url: str, profile_path: str | None = None
    ) -> DiscoveredCandidate | None:
        """On-demand scrape of a single known funder/grant URL the user pastes."""
        org_profile = load_org_profile(profile_path or self._settings.org_profile_path)
        fetcher = PoliteFetcher()
        try:
            source = FunderSiteSource(fetcher)
            candidate = source.fetch_url(url, org_profile)
        finally:
            fetcher.close()
        if candidate is None:
            return None
        staged = self._stage_candidates(db, [candidate], search_query=url)
        return staged[0] if staged else None

    def import_instrumentl_csv(self, db: Session, csv_text: str) -> list[DiscoveredCandidate]:
        """Import an Instrumentl CSV export (ToS-compliant — no scraping)."""
        candidates = InstrumentlCsvImporter().import_csv(csv_text)
        return self._stage_candidates(db, candidates, search_query="instrumentl_csv_import")

    # ── 2. REVIEW QUEUE ────────────────────────────────────────────────────────

    def list_candidates(
        self, db: Session, status: CandidateStatus | None = CandidateStatus.NEW
    ) -> list[DiscoveredCandidate]:
        q = db.query(DiscoveredCandidate).filter(DiscoveredCandidate.is_deleted.is_(False))
        if status is not None:
            q = q.filter(DiscoveredCandidate.status == status)
        return q.order_by(DiscoveredCandidate.discovered_at.desc()).all()

    def get_candidate(self, db: Session, candidate_id: str) -> DiscoveredCandidate | None:
        return db.query(DiscoveredCandidate).filter_by(id=candidate_id, is_deleted=False).first()

    def dismiss_candidate(self, db: Session, candidate_id: str) -> None:
        cand = self.get_candidate(db, candidate_id)
        if cand:
            cand.status = CandidateStatus.DISMISSED
            cand.reviewed_at = datetime.utcnow()
            db.commit()

    # ── 3. IMPORT (human-confirmed) ────────────────────────────────────────────

    def import_candidate(
        self, db: Session, candidate_id: str, overrides: dict | None = None
    ) -> Grant:
        """
        Convert a staged candidate into a real Grant via GrantService (which
        scores + classifies it). `overrides` are the human-corrected field values
        from the review form and take precedence over the extracted values.
        """
        cand = self.get_candidate(db, candidate_id)
        if cand is None:
            raise ValueError(f"Candidate {candidate_id!r} not found.")

        data = self._candidate_to_grant_data(cand)
        if overrides:
            data.update(overrides)

        try:
            grant = self._grant_svc.create_grant(db, data)
        except DuplicateGrantError as exc:
            cand.status = CandidateStatus.DUPLICATE
            cand.dedup_note = str(exc)
            cand.linked_grant_id = exc.existing_id
            cand.reviewed_at = datetime.utcnow()
            db.commit()
            raise

        cand.status = CandidateStatus.IMPORTED
        cand.linked_grant_id = grant.id
        cand.reviewed_at = datetime.utcnow()
        db.commit()
        log.info("Candidate %s imported as Grant %s.", candidate_id, grant.id)
        return grant

    # ── internals ──────────────────────────────────────────────────────────────

    def _active_connectors(self, fetcher: PoliteFetcher, sources: list[str] | None):
        all_connectors = [
            GrantsGovSource(fetcher),
            WebSearchSource(fetcher),
            CandidApiSource(fetcher),
        ]
        active = [c for c in all_connectors if c.enabled]
        if sources:
            active = [c for c in active if c.name in sources]
        return active

    def _stage_candidates(
        self, db: Session, raw: list[GrantCandidate], search_query: str
    ) -> list[DiscoveredCandidate]:
        existing_grants = self._existing_grants_for_dedup(db)
        existing_urls = {
            c.source_url
            for c in db.query(DiscoveredCandidate.source_url)
            .filter(DiscoveredCandidate.source_url.isnot(None))
            .all()
        }

        staged: list[DiscoveredCandidate] = []
        for gc in raw:
            # Skip if we've already staged this exact URL.
            if gc.source_url and gc.source_url in existing_urls:
                continue

            row = DiscoveredCandidate(
                source=gc.source,
                source_url=gc.source_url,
                raw_title=gc.raw_title[:500] if gc.raw_title else "(untitled)",
                raw_funder=gc.raw_funder,
                extracted_json=gc.to_extracted_json(),
                raw_text_excerpt=gc.raw_text,
                search_query=search_query[:500],
                status=CandidateStatus.NEW,
            )

            # Flag (don't drop) likely duplicates of existing grants for human review.
            matches = find_duplicates(
                candidate_title=gc.raw_title or "",
                candidate_url=gc.source_url,
                candidate_funder_id=None,
                existing_grants=existing_grants,
            )
            if matches:
                m = matches[0]
                row.status = CandidateStatus.DUPLICATE
                row.linked_grant_id = m.existing_id
                row.dedup_note = f"{m.match_type} match on {m.match_field} ({m.existing_title})"

            db.add(row)
            staged.append(row)
            if gc.source_url:
                existing_urls.add(gc.source_url)

        db.commit()
        for row in staged:
            db.refresh(row)
        log.info("Staged %d candidates for query %r.", len(staged), search_query)
        return staged

    @staticmethod
    def _existing_grants_for_dedup(db: Session) -> list[dict]:
        return [
            {
                "id": g.id,
                "title": g.title,
                "source_url": g.source_url,
                "funder_id": g.funder_id,
                "is_deleted": g.is_deleted,
            }
            for g in db.query(Grant).all()
        ]

    @staticmethod
    def _candidate_to_grant_data(cand: DiscoveredCandidate) -> dict:
        try:
            payload = json.loads(cand.extracted_json or "{}")
        except json.JSONDecodeError:
            payload = {}
        extracted = dict(payload.get("extracted", {}))

        # Re-hydrate ISO date strings back into date objects.
        if isinstance(extracted.get("deadline"), str):
            try:
                extracted["deadline"] = date.fromisoformat(extracted["deadline"])
            except ValueError:
                extracted["deadline"] = None

        extracted.setdefault("title", cand.raw_title)
        extracted.setdefault("funder_name", cand.raw_funder)
        extracted.setdefault("source_url", cand.source_url)
        extracted.setdefault(
            "notes",
            f"Discovered via {cand.source} on {cand.discovered_at:%Y-%m-%d}. "
            f"Review extracted fields before submitting.",
        )
        return extracted
