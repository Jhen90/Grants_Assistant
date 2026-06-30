# ============================================================
# File: tests/unit/test_scoring_engine.py
# Version: 1.1.1
# Created: 2026-06-25
# Modified: 2026-06-30
# Description: Tests for the deterministic ScoringEngine. The engine is a pure,
#   duck-typed function (reads grant/org via getattr), so we use SimpleNamespace
#   stand-ins rather than ORM instances. Criteria use the real `config` schema and
#   `is_hard_filter` flag the engine actually reads.
# ============================================================

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.engine.scoring_engine import ScoringEngine


@pytest.fixture()
def engine() -> ScoringEngine:
    return ScoringEngine()


@pytest.fixture()
def org() -> SimpleNamespace:
    return SimpleNamespace(
        city="Boston",
        state="MA",
        eligibility_json=json.dumps({"target_population": "youth aged 10-18"}),
        programs_json=json.dumps([{"name": "Youth Martial Arts"}]),
    )


@pytest.fixture()
def criteria() -> list[dict]:
    return [
        {
            "name": "Geography",
            "type": "geography",
            "weight": 2,
            "config": {"target_geographies": ["Boston", "MA"]},
        },
        {
            "name": "Focus Area",
            "type": "focus_area",
            "weight": 3,
            "config": {"target_focus_areas": ["youth development", "martial arts"]},
        },
        {
            "name": "Eligibility",
            "type": "eligibility",
            "weight": 5,
            "is_hard_filter": True,
            "config": {},
        },
        {
            "name": "Amount",
            "type": "amount_range",
            "weight": 1,
            "config": {"min_acceptable": 5000, "max_acceptable": 100000},
        },
    ]


def _make_grant(**kwargs) -> SimpleNamespace:
    return SimpleNamespace(
        id="test-grant-id",
        title="Test Grant",
        target_geography=kwargs.get("target_geography", "Boston, MA"),
        focus_areas_json=json.dumps(kwargs.get("focus_areas", ["youth development"])),
        eligibility_501c3_required=kwargs.get("eligibility_501c3_required", False),
        fiscal_sponsorship_allowed=kwargs.get("fiscal_sponsorship_allowed", True),
        amount_min=kwargs.get("amount_min", 10000),
        amount_max=kwargs.get("amount_max", 50000),
        fiscal_sponsor_id=kwargs.get("fiscal_sponsor_id", "sponsor-id"),
    )


class TestScoringEngineDeterminism:
    def test_same_inputs_same_score(self, engine, org, criteria):
        grant = _make_grant()
        r1 = engine.score_grant(grant, criteria, org)
        r2 = engine.score_grant(grant, criteria, org)
        assert r1.fit_score == r2.fit_score

    def test_score_in_range(self, engine, org, criteria):
        result = engine.score_grant(_make_grant(), criteria, org)
        assert 0.0 <= result.fit_score <= 10.0


class TestHardFilter:
    def test_hard_filter_triggers_when_501c3_required_no_sponsor(self, engine, org, criteria):
        grant = _make_grant(
            eligibility_501c3_required=True,
            fiscal_sponsorship_allowed=False,
            fiscal_sponsor_id=None,
        )
        result = engine.score_grant(grant, criteria, org)
        assert result.hard_filter_failed is True
        assert result.fit_score == 0.0

    def test_hard_filter_passes_with_fiscal_sponsor(self, engine, org, criteria):
        grant = _make_grant(
            eligibility_501c3_required=True,
            fiscal_sponsorship_allowed=True,
            fiscal_sponsor_id="some-sponsor",
        )
        result = engine.score_grant(grant, criteria, org)
        assert result.hard_filter_failed is False


class TestGeographyEvaluator:
    def _geo(self, result):
        return next(cr for cr in result.criterion_results if "Geography" in cr.name)

    def test_exact_city_state_match(self, engine, org, criteria):
        result = engine.score_grant(_make_grant(target_geography="Boston, MA"), criteria, org)
        assert self._geo(result).raw_score == 1.0

    def test_national_grants_get_partial(self, engine, org, criteria):
        result = engine.score_grant(_make_grant(target_geography="National"), criteria, org)
        assert self._geo(result).raw_score == 0.5

    def test_wrong_geography_scores_zero(self, engine, org, criteria):
        result = engine.score_grant(_make_grant(target_geography="Los Angeles, CA"), criteria, org)
        assert self._geo(result).raw_score == 0.0


class TestFocusAreaEvaluator:
    def _fa(self, result):
        return next(cr for cr in result.criterion_results if "Focus" in cr.name)

    def test_matching_focus_area_scores_full(self, engine, org, criteria):
        result = engine.score_grant(_make_grant(focus_areas=["youth development"]), criteria, org)
        assert self._fa(result).raw_score == 1.0

    def test_no_matching_focus_area_scores_zero(self, engine, org, criteria):
        result = engine.score_grant(_make_grant(focus_areas=["elderly care", "housing"]), criteria, org)
        assert self._fa(result).raw_score == 0.0


class TestNormalization:
    def test_score_breakdown_serializable(self, engine, org, criteria):
        result = engine.score_grant(_make_grant(), criteria, org)
        parsed = json.loads(result.to_json())
        assert "fit_score" in parsed
        assert "criteria" in parsed  # engine emits 'criteria', one entry per rule
        assert len(parsed["criteria"]) == len(criteria)
