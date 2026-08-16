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
#   preserving GrantNova's human-in-the-loop guarantee.
# ============================================================

from __future__ import annotations

import json
from datetime import date, datetime

from sqlalchemy.orm import Session

from src.db.org_profile_loader import load as load_org_profile
from src.discovery.base import GrantCandidate
from src.discovery.evaluator import evaluate_candidate
from src.discovery.fetcher import PoliteFetcher
from src.discovery.query_expander import expand_queries
from src.discovery.sources import (
    CandidApiSource,
    FunderSiteSource,
    GrantsGovSource,
    InstrumentlCsvImporter,
    WebSearchSource,
)
from src.discovery.sources.funder_site import PUBLIC_PORTALS
from src.engine.deduplication import find_duplicates
from src.models.discovered_candidate import CandidateStatus, DiscoveredCandidate
from src.models.funder import Funder
from src.models.grant import Grant
from src.models.organization import Organization
from src.models.selection_criteria import SelectionCriteria
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

    def run_full_sweep(
        self,
        db: Session,
        sources: list[str] | None = None,
        limit_per_source: int = 10,
        max_queries: int = 40,
        profile_path: str | None = None,
        sweep_funder_sites: bool = True,
    ) -> list[DiscoveredCandidate]:
        """
        "Search everywhere." Expands the org profile into a battery of queries,
        runs them across all enabled keyword sources, AND sweeps every known
        funder website (priority funders + community partners from the DB) plus
        the curated public grant portals. All results are staged, de-duplicated.

        This is the entry point for the Discover page's "Search Everywhere" button
        and the scheduled weekly scan (--sweep).
        """
        org_profile = load_org_profile(profile_path or self._settings.org_profile_path)
        queries = expand_queries(org_profile, max_queries=max_queries)
        log.info("Full sweep: %d expanded queries.", len(queries))

        fetcher = PoliteFetcher()
        raw: list[GrantCandidate] = []
        try:
            # 1) Keyword sources across every expanded query.
            connectors = self._active_connectors(fetcher, sources)
            for query in queries:
                for connector in connectors:
                    try:
                        raw.extend(connector.search(query, org_profile, limit_per_source))
                    except Exception as exc:  # noqa: BLE001
                        log.warning("Source %s failed on %r: %s", connector.name, query, exc)

            # 2) Sweep every funder website we know + curated public portals.
            if sweep_funder_sites and self._settings.source_funder_sites_enabled:
                urls = self._all_known_funder_urls(db) + PUBLIC_PORTALS
                site_source = FunderSiteSource(fetcher)
                try:
                    raw.extend(site_source.sweep_urls(urls, org_profile))
                except Exception as exc:  # noqa: BLE001
                    log.warning("Funder-site sweep failed: %s", exc)
        finally:
            fetcher.close()

        return self._stage_candidates(db, raw, search_query="FULL_SWEEP")

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
        # Newest first as a stable baseline; the review queue is then ranked best-first.
        rows = q.order_by(DiscoveredCandidate.discovered_at.desc()).all()
        if status == CandidateStatus.NEW:
            rows.sort(key=self._rank_key)
        return rows

    def reevaluate_candidates(
        self,
        db: Session,
        statuses: tuple[CandidateStatus, ...] = (CandidateStatus.NEW, CandidateStatus.DUPLICATE),
    ) -> int:
        """
        Re-score all candidates in the given statuses against the CURRENT active
        criteria (e.g. after the criteria set changes). Idempotent — updates rows
        in place, never creates or duplicates them. Returns the number updated.
        """
        criteria_list, org = self._load_scoring_context(db)
        rows = (
            db.query(DiscoveredCandidate)
            .filter(
                DiscoveredCandidate.is_deleted.is_(False),
                DiscoveredCandidate.status.in_(statuses),
            )
            .all()
        )
        for row in rows:
            self._apply_evaluation(row, self._extracted_of(row), criteria_list, org)
        db.commit()
        log.info("Re-evaluated %d candidate(s) against current criteria.", len(rows))
        return len(rows)

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

    # ── evaluation helpers (EVALUATE phase) ────────────────────────────────────

    @staticmethod
    def _load_scoring_context(db: Session) -> tuple[list[dict], Organization | None]:
        """Active criteria list + primary org — the inputs the evaluator needs."""
        criteria = (
            db.query(SelectionCriteria)
            .filter_by(is_active=True)
            .order_by(SelectionCriteria.created_at)
            .first()
        )
        org = (
            db.query(Organization)
            .filter_by(is_deleted=False)
            .order_by(Organization.created_at)
            .first()
        )
        try:
            criteria_list = json.loads(criteria.criteria_json or "[]") if criteria else []
        except json.JSONDecodeError:
            criteria_list = []
        return criteria_list, org

    @staticmethod
    def _apply_evaluation(
        row: DiscoveredCandidate, extracted: dict, criteria_list: list[dict], org
    ) -> None:
        ev = evaluate_candidate(extracted, criteria_list, org)
        row.fit_score = ev.fit_score
        row.eligibility_status = ev.eligibility_status
        row.is_strong_match = ev.is_strong_match
        row.deadline_urgency = ev.deadline_urgency
        row.act_now = ev.act_now
        row.why_fits = ev.why_fits

    @staticmethod
    def _extracted_of(row: DiscoveredCandidate) -> dict:
        try:
            payload = json.loads(row.extracted_json or "{}")
        except json.JSONDecodeError:
            return {}
        return dict(payload.get("extracted", {}))

    @staticmethod
    def _rank_key(row: DiscoveredCandidate) -> tuple:
        """Best-first: strong matches, then ELIGIBLE, then higher fit (FR-SCOUT-303/304)."""
        elig_order = {"ELIGIBLE": 0, "UNKNOWN": 1, "INELIGIBLE": 2}
        elig = row.eligibility_status.value if row.eligibility_status else "UNKNOWN"
        return (
            0 if row.is_strong_match else 1,
            elig_order.get(elig, 1),
            -(row.fit_score or 0.0),
        )

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
        criteria_list, org = self._load_scoring_context(db)

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

            # EVALUATE: score + eligibility + urgency BEFORE human review (FR-SCOUT-3xx).
            self._apply_evaluation(row, gc.extracted, criteria_list, org)

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
    def _all_known_funder_urls(db: Session) -> list[str]:
        """Websites of every active funder in the DB (priority + community partners)."""
        funders = (
            db.query(Funder)
            .filter(Funder.is_deleted.is_(False), Funder.website.isnot(None))
            .all()
        )
        urls: list[str] = []
        for f in funders:
            site = (f.website or "").strip()
            if site and site.startswith("http"):
                urls.append(site)
        return urls

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
