# ============================================================
# File: tests/unit/test_scout_report.py
# Version: 1.2.0
# Created: 2026-07-16
# Description: Tests for the Grant Scout REPORT phase (ScoutReportService) —
#   renders from DB state, leads with Act Now / strong matches, marks low-confidence
#   fields unverified, and never mutates candidate state (read-only, FR-SCOUT-404).
# ============================================================

from __future__ import annotations

import json
from datetime import date, timedelta

from src.discovery.base import GrantCandidate
from src.models.discovered_candidate import CandidateStatus
from src.models.organization import Organization
from src.models.selection_criteria import SelectionCriteria
from src.services.discovery_service import DiscoveryService
from src.services.scout_report_service import ScoutReportService

_CRITERIA = [
    {"name": "Eligibility", "type": "eligibility", "weight": 5, "is_hard_filter": True, "config": {}},
    {"name": "Geography", "type": "geography", "weight": 2, "config": {"target_geographies": ["boston", "ma"]}},
    {"name": "Focus", "type": "focus_area", "weight": 3, "config": {"target_focus_areas": ["youth development"]}},
    {"name": "Amount", "type": "amount_range", "weight": 1, "config": {"min_acceptable": 5000, "max_acceptable": 100000}},
]


def _seed(db):
    db.add(Organization(
        name="The Dojo", mission="Empowering underserved youth.", is_501c3=False,
        eligibility_json=json.dumps({"has_501c3": False}),
    ))
    db.add(SelectionCriteria(name="Standard", criteria_json=json.dumps(_CRITERIA), is_active=True))
    db.commit()


def _strong(url="http://good.org/strong"):
    return GrantCandidate(
        source="test", source_url=url, raw_title="Strong Youth STEM Grant", raw_funder="Test Foundation",
        extracted={
            "title": "Strong Youth STEM Grant", "funder_name": "Test Foundation",
            "target_geography": "Boston, MA", "focus_areas": ["youth development"],
            "amount_min": 10000, "amount_max": 50000, "eligibility_501c3_required": False,
            "deadline": date.today() + timedelta(days=20),
        },
        field_confidence={"deadline": 0.9},
    )


def _low_conf(url="http://good.org/lowconf"):
    return GrantCandidate(
        source="test", source_url=url, raw_title="Low Confidence Grant", raw_funder="Maybe Fund",
        extracted={
            "title": "Low Confidence Grant", "funder_name": "Maybe Fund",
            "deadline": "2026-09-17", "eligibility_501c3_required": False,
        },
        field_confidence={"deadline": 0.3},
    )


def _strong_unverified(url="http://good.org/strong-unv"):
    """A strong match (so its deadline renders) but with a low-confidence deadline."""
    return GrantCandidate(
        source="test", source_url=url, raw_title="Strong Grant Unverified Deadline", raw_funder="Test Foundation",
        extracted={
            "title": "Strong Grant Unverified Deadline", "funder_name": "Test Foundation",
            "target_geography": "Boston, MA", "focus_areas": ["youth development"],
            "amount_min": 10000, "amount_max": 50000, "eligibility_501c3_required": False,
            "deadline": date.today() + timedelta(days=20),
        },
        field_confidence={"deadline": 0.3},  # below threshold → must be flagged unverified
    )


def test_renders_header_and_candidate(db):
    _seed(db)
    DiscoveryService()._stage_candidates(db, [_strong()], "q")
    report = ScoutReportService().generate_report(db)
    assert "GRANT SCOUT INTELLIGENCE REPORT" in report.markdown
    assert "Strong Youth STEM Grant" in report.markdown
    assert report.total == 1
    assert report.act_now == 1  # eligible strong match, near deadline


def test_ordering_act_now_leads(db):
    _seed(db)
    DiscoveryService()._stage_candidates(db, [_low_conf(), _strong()], "q")
    md = ScoutReportService().generate_report(db).markdown
    # Act Now section appears before the "other candidates" section.
    assert "ACT NOW" in md
    assert md.index("Strong Youth STEM Grant") < md.index("Low Confidence Grant")


def test_low_confidence_field_marked_unverified(db):
    _seed(db)
    DiscoveryService()._stage_candidates(db, [_strong_unverified()], "q")
    md = ScoutReportService().generate_report(db).markdown
    assert "unverified" in md


def test_report_is_read_only(db):
    _seed(db)
    DiscoveryService()._stage_candidates(db, [_strong(), _low_conf()], "q")
    before = {c.id: c.status for c in DiscoveryService().list_candidates(db, status=CandidateStatus.NEW)}
    ScoutReportService().generate_report(db)
    after = {c.id: c.status for c in DiscoveryService().list_candidates(db, status=CandidateStatus.NEW)}
    assert before == after
    assert all(s == CandidateStatus.NEW for s in after.values())


def test_empty_period_renders_safely(db):
    _seed(db)
    report = ScoutReportService().generate_report(db)
    assert report.total == 0
    assert "No new opportunities" in report.markdown
