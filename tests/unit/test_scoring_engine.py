# ============================================================
# File: tests/unit/test_scoring_engine.py
# Version: 1.1.0
# Created: 2026-06-25
# ============================================================

from __future__ import annotations

import json
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from src.engine.scoring_engine import ScoringEngine
from src.models.grant import Grant, GrantStatus
from src.models.organization import Organization


@pytest.fixture()
def engine() -> ScoringEngine:
    return ScoringEngine()


@pytest.fixture()
def org() -> Organization:
    org = Organization.__new__(Organization)
    org.city = "Boston"
    org.state = "MA"
    org.is_501c3 = False
    org.programs_json = json.dumps([{"name": "Youth Martial Arts", "focus_areas": ["youth development"]}])
    org.eligibility_json = json.dumps({"target_population": "youth aged 10-18"})
    return org


@pytest.fixture()
def criteria() -> list[dict]:
    return [
        {
            "name": "Geography",
            "type": "geography",
            "weight": 2,
            "org_geography": "Boston, MA",
        },
        {
            "name": "Focus Area",
            "type": "focus_area",
            "weight": 3,
            "org_focus_areas": ["youth development", "martial arts"],
        },
        {
            "name": "Eligibility",
            "type": "eligibility",
            "weight": 5,
        },
        {
            "name": "Amount",
            "type": "amount_range",
            "weight": 1,
            "org_typical_ask": 25000,
        },
    ]


def _make_grant(**kwargs) -> Grant:
    g = Grant.__new__(Grant)
    g.id = "test-grant-id"
    g.status = GrantStatus.DISCOVERED
    g.target_geography = kwargs.get("target_geography", "Boston, MA")
    g.focus_areas_json = json.dumps(kwargs.get("focus_areas", ["youth development"]))
    g.eligibility_501c3_required = kwargs.get("eligibility_501c3_required", False)
    g.fiscal_sponsorship_allowed = kwargs.get("fiscal_sponsorship_allowed", True)
    g.amount_min = kwargs.get("amount_min", 10000)
    g.amount_max = kwargs.get("amount_max", 50000)
    g.fiscal_sponsor_id = kwargs.get("fiscal_sponsor_id", "sponsor-id")
    return g


class TestScoringEngineDeterminism:
    def test_same_inputs_same_score(self, engine, org, criteria):
        grant = _make_grant()
        r1 = engine.score_grant(grant, criteria, org)
        r2 = engine.score_grant(grant, criteria, org)
        assert r1.fit_score == r2.fit_score

    def test_score_in_range(self, engine, org, criteria):
        grant = _make_grant()
        result = engine.score_grant(grant, criteria, org)
        assert 0.0 <= result.fit_score <= 10.0


class TestHardFilter:
    def test_hard_filter_triggers_when_501c3_required_no_sponsor(
        self, engine, org, criteria
    ):
        grant = _make_grant(
            eligibility_501c3_required=True,
            fiscal_sponsorship_allowed=False,
            fiscal_sponsor_id=None,
        )
        result = engine.score_grant(grant, criteria, org)
        assert result.hard_filter_failed is True

    def test_hard_filter_passes_with_fiscal_sponsor(self, engine, org, criteria):
        grant = _make_grant(
            eligibility_501c3_required=True,
            fiscal_sponsorship_allowed=True,
            fiscal_sponsor_id="some-sponsor",
        )
        result = engine.score_grant(grant, criteria, org)
        assert result.hard_filter_failed is False


class TestGeographyEvaluator:
    def test_exact_city_state_match(self, engine, org, criteria):
        grant = _make_grant(target_geography="Boston, MA")
        result = engine.score_grant(grant, criteria, org)
        geo_cr = next(cr for cr in result.criterion_results if "Geography" in cr.name)
        assert geo_cr.raw_score == 1.0

    def test_national_grants_get_partial(self, engine, org, criteria):
        grant = _make_grant(target_geography="National")
        result = engine.score_grant(grant, criteria, org)
        geo_cr = next(cr for cr in result.criterion_results if "Geography" in cr.name)
        assert geo_cr.raw_score == 0.5

    def test_wrong_geography_scores_zero(self, engine, org, criteria):
        grant = _make_grant(target_geography="Los Angeles, CA")
        result = engine.score_grant(grant, criteria, org)
        geo_cr = next(cr for cr in result.criterion_results if "Geography" in cr.name)
        assert geo_cr.raw_score == 0.0


class TestFocusAreaEvaluator:
    def test_matching_focus_area_scores_full(self, engine, org, criteria):
        grant = _make_grant(focus_areas=["youth development"])
        result = engine.score_grant(grant, criteria, org)
        fa_cr = next(cr for cr in result.criterion_results if "Focus" in cr.name)
        assert fa_cr.raw_score == 1.0

    def test_no_matching_focus_area_scores_zero(self, engine, org, criteria):
        grant = _make_grant(focus_areas=["elderly care", "housing"])
        result = engine.score_grant(grant, criteria, org)
        fa_cr = next(cr for cr in result.criterion_results if "Focus" in cr.name)
        assert fa_cr.raw_score == 0.0


class TestNormalization:
    def test_score_breakdown_serializable(self, engine, org, criteria):
        grant = _make_grant()
        result = engine.score_grant(grant, criteria, org)
        json_str = result.to_json()
        parsed = json.loads(json_str)
        assert "fit_score" in parsed
        assert "criteria_results" in parsed
