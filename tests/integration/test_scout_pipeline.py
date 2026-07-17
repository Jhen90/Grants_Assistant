# ============================================================
# File: tests/integration/test_scout_pipeline.py
# Version: 1.2.0
# Created: 2026-07-16
# Description: End-to-end Grant Scout pipeline — stage -> evaluate -> ranked queue,
#   with the human-in-the-loop guarantee (nothing auto-imports). Re-evaluation is
#   idempotent. All in-memory; no network.
# ============================================================

from __future__ import annotations

import json
from datetime import date, timedelta

from src.discovery.base import GrantCandidate
from src.models.discovered_candidate import CandidateStatus, EligibilityStatus
from src.models.grant import Grant
from src.models.organization import Organization
from src.models.selection_criteria import SelectionCriteria
from src.services.discovery_service import DiscoveryService

_CRITERIA = [
    {"name": "Eligibility", "type": "eligibility", "weight": 5, "is_hard_filter": True, "config": {}},
    {"name": "Geography", "type": "geography", "weight": 2, "config": {"target_geographies": ["boston", "ma"]}},
    {"name": "Focus", "type": "focus_area", "weight": 3, "config": {"target_focus_areas": ["youth development", "stem"]}},
    {"name": "Amount", "type": "amount_range", "weight": 1, "config": {"min_acceptable": 5000, "max_acceptable": 100000}},
]


def _seed_context(db):
    db.add(Organization(
        name="The Dojo", mission="Empowering underserved youth.", is_501c3=False,
        eligibility_json=json.dumps({"has_501c3": False}),
    ))
    db.add(SelectionCriteria(name="Standard", criteria_json=json.dumps(_CRITERIA), is_active=True))
    db.commit()


def _strong():
    return GrantCandidate(
        source="test", source_url="http://good.org/strong", raw_title="Strong Youth STEM Grant",
        extracted={
            "title": "Strong Youth STEM Grant", "target_geography": "Boston, MA",
            "focus_areas": ["youth development"], "amount_min": 10000, "amount_max": 50000,
            "eligibility_501c3_required": False, "deadline": date.today() + timedelta(days=20),
        },
    )


def _weak():
    return GrantCandidate(
        source="test", source_url="http://good.org/weak", raw_title="Unrelated Healthcare Grant",
        extracted={
            "title": "Unrelated Healthcare Grant", "target_geography": "California",
            "focus_areas": ["healthcare"], "eligibility_501c3_required": False,
        },
    )


def test_pipeline_stages_evaluates_and_ranks(db):
    _seed_context(db)
    svc = DiscoveryService()
    staged = svc._stage_candidates(db, [_weak(), _strong()], search_query="q")

    # Every staged candidate is evaluated (fit + eligibility populated).
    assert all(c.fit_score is not None for c in staged)
    assert all(c.eligibility_status is not None for c in staged)

    # Ranked queue puts the strong eligible match first (FR-SCOUT-303/304).
    queue = svc.list_candidates(db, status=CandidateStatus.NEW)
    assert queue[0].raw_title == "Strong Youth STEM Grant"
    assert queue[0].is_strong_match is True
    assert queue[0].eligibility_status == EligibilityStatus.ELIGIBLE
    assert queue[0].act_now is True  # eligible strong match with a near deadline

    # Human-in-the-loop: evaluation NEVER auto-creates a Grant (NFR-SCOUT-003).
    assert db.query(Grant).count() == 0


def test_reevaluation_is_idempotent(db):
    _seed_context(db)
    svc = DiscoveryService()
    svc._stage_candidates(db, [_strong(), _weak()], search_query="q")
    before = svc.list_candidates(db, status=CandidateStatus.NEW)
    before_scores = {c.id: c.fit_score for c in before}

    updated = svc.reevaluate_candidates(db)
    after = svc.list_candidates(db, status=CandidateStatus.NEW)

    assert updated == len(before)              # each row updated
    assert len(after) == len(before)           # no rows created/duplicated
    assert {c.id: c.fit_score for c in after} == before_scores  # stable scores
