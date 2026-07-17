# ============================================================
# File: tests/unit/test_discovery_service.py
# Version: 1.2.0
# Created: 2026-07-16
# Description: Tests for DiscoveryService — staging, URL de-dup, duplicate flagging
#   against existing grants, human-confirmed import, dismissal, and queue listing.
#   Candidates are hand-built (no network); import exercises the real GrantService.
# ============================================================

from __future__ import annotations

import json

from src.discovery.base import GrantCandidate
from src.models.discovered_candidate import CandidateStatus, DiscoveredCandidate
from src.models.grant import Grant, GrantStatus
from src.services.discovery_service import DiscoveryService


def _candidate(url="http://funder.org/rfp", title="STEM Youth Grant", funder="Test Foundation"):
    return GrantCandidate(
        source="test",
        source_url=url,
        raw_title=title,
        raw_funder=funder,
        extracted={
            "title": title,
            "funder_name": funder,
            "source_url": url,
            "focus_areas": ["youth development"],
            "target_geography": "Boston, MA",
        },
        field_confidence={"title": 0.9, "funder_name": 0.8},
    )


class TestStaging:
    def test_stage_new_candidate(self, db):
        svc = DiscoveryService()
        staged = svc._stage_candidates(db, [_candidate()], search_query="q")
        assert len(staged) == 1
        assert staged[0].status == CandidateStatus.NEW
        assert staged[0].raw_title == "STEM Youth Grant"
        assert db.query(DiscoveredCandidate).count() == 1

    def test_skips_already_staged_url(self, db):
        svc = DiscoveryService()
        svc._stage_candidates(db, [_candidate(url="http://dup.org/1")], search_query="q1")
        again = svc._stage_candidates(db, [_candidate(url="http://dup.org/1")], search_query="q2")
        assert again == []  # same URL not staged twice
        assert db.query(DiscoveredCandidate).count() == 1

    def test_extracted_json_roundtrips(self, db):
        svc = DiscoveryService()
        staged = svc._stage_candidates(db, [_candidate()], search_query="q")
        payload = json.loads(staged[0].extracted_json)
        assert payload["extracted"]["funder_name"] == "Test Foundation"
        assert "field_confidence" in payload


class TestDuplicateFlagging:
    def test_flags_url_duplicate_of_existing_grant(self, db, sample_funder):
        existing = Grant(
            title="Existing Grant",
            funder_id=sample_funder.id,
            funder_name=sample_funder.name,
            status=GrantStatus.DISCOVERED,
            source_url="http://collide.org/1",
        )
        db.add(existing)
        db.commit()

        svc = DiscoveryService()
        staged = svc._stage_candidates(
            db, [_candidate(url="http://collide.org/1", title="Totally Different Title")], "q"
        )
        assert len(staged) == 1
        assert staged[0].status == CandidateStatus.DUPLICATE
        assert staged[0].linked_grant_id == existing.id
        assert staged[0].dedup_note


class TestImport:
    def test_import_candidate_creates_grant(self, db, sample_funder, sample_org, sample_criteria):
        svc = DiscoveryService()
        staged = svc._stage_candidates(db, [_candidate(url="http://import.org/1")], "q")
        cid = staged[0].id

        grant = svc.import_candidate(db, cid)
        assert isinstance(grant, Grant)
        assert grant.title == "STEM Youth Grant"

        cand = svc.get_candidate(db, cid)
        assert cand.status == CandidateStatus.IMPORTED
        assert cand.linked_grant_id == grant.id

    def test_dismiss_candidate(self, db):
        svc = DiscoveryService()
        staged = svc._stage_candidates(db, [_candidate()], "q")
        svc.dismiss_candidate(db, staged[0].id)
        assert svc.get_candidate(db, staged[0].id).status == CandidateStatus.DISMISSED


class TestListing:
    def test_list_filters_by_status(self, db):
        svc = DiscoveryService()
        svc._stage_candidates(db, [_candidate(url="http://a.org/1")], "q")
        new_list = svc.list_candidates(db, status=CandidateStatus.NEW)
        assert len(new_list) == 1
        assert svc.list_candidates(db, status=CandidateStatus.DISMISSED) == []
