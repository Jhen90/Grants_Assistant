# ============================================================
# File: tests/unit/test_candidate_evaluator.py
# Version: 1.2.0
# Created: 2026-07-16
# Description: Tests for the Grant Scout EVALUATE phase (evaluate_candidate) —
#   pre-review fit scoring, eligibility (incl. the fiscal-sponsorship rule),
#   strong-match + Act Now flags, determinism, and the no-criteria fallback.
# ============================================================

from __future__ import annotations

import json
from datetime import date, timedelta
from types import SimpleNamespace

from src.discovery.evaluator import evaluate_candidate
from src.models.discovered_candidate import EligibilityStatus

# Criteria in the ScoringEngine's `config` format, with a hard-filter eligibility rule.
CRITERIA = [
    {"name": "Eligibility", "type": "eligibility", "weight": 5, "is_hard_filter": True, "config": {}},
    {"name": "Geography", "type": "geography", "weight": 2, "config": {"target_geographies": ["boston", "ma"]}},
    {"name": "Focus", "type": "focus_area", "weight": 3, "config": {"target_focus_areas": ["youth development", "stem"]}},
    {"name": "Amount", "type": "amount_range", "weight": 1, "config": {"min_acceptable": 5000, "max_acceptable": 100000}},
]


def _org(has_501c3=False, default_sponsor=None):
    elig = {"has_501c3": has_501c3}
    if default_sponsor:
        elig["default_fiscal_sponsor"] = default_sponsor
    return SimpleNamespace(eligibility_json=json.dumps(elig))


def _strong_extracted(**over):
    base = {
        "title": "Youth STEM Grant",
        "target_geography": "Boston, MA",
        "focus_areas": ["youth development"],
        "amount_min": 10000,
        "amount_max": 50000,
        "eligibility_501c3_required": False,
        "deadline": date.today() + timedelta(days=20),  # RED urgency
    }
    base.update(over)
    return base


class TestScoring:
    def test_strong_match_scores_high_and_flags(self):
        ev = evaluate_candidate(_strong_extracted(), CRITERIA, _org())
        assert ev.fit_score == 10.0
        assert ev.eligibility_status == EligibilityStatus.ELIGIBLE
        assert ev.is_strong_match is True

    def test_weak_match_not_strong(self):
        weak = _strong_extracted(target_geography="California", focus_areas=["healthcare"], amount_min=None, amount_max=None)
        ev = evaluate_candidate(weak, CRITERIA, _org())
        assert ev.fit_score < 7.0
        assert ev.is_strong_match is False


class TestEligibility:
    def test_hard_filter_makes_ineligible(self):
        extracted = _strong_extracted(
            eligibility_501c3_required=True, fiscal_sponsorship_allowed=False
        )
        ev = evaluate_candidate(extracted, CRITERIA, _org(has_501c3=False))
        assert ev.eligibility_status == EligibilityStatus.INELIGIBLE
        assert ev.fit_score == 0.0
        assert ev.is_strong_match is False

    def test_fiscal_sponsorship_keeps_eligible(self):
        # Requires 501(c)(3) BUT allows a fiscal sponsor the org has → ELIGIBLE (FR-SCOUT-302).
        extracted = _strong_extracted(
            eligibility_501c3_required=True, fiscal_sponsorship_allowed=True
        )
        ev = evaluate_candidate(
            extracted, CRITERIA, _org(has_501c3=False, default_sponsor="Teen Empowerment")
        )
        assert ev.eligibility_status == EligibilityStatus.ELIGIBLE


class TestActNow:
    def test_act_now_when_strong_and_urgent(self):
        ev = evaluate_candidate(_strong_extracted(), CRITERIA, _org())
        assert ev.deadline_urgency == "RED"
        assert ev.act_now is True

    def test_no_act_now_when_deadline_far(self):
        ev = evaluate_candidate(
            _strong_extracted(deadline=date.today() + timedelta(days=200)), CRITERIA, _org()
        )
        assert ev.deadline_urgency == "GRAY"
        assert ev.act_now is False


class TestFallbackAndDeterminism:
    def test_no_criteria_returns_unknown(self):
        for crit in ([], None):
            ev = evaluate_candidate(_strong_extracted(), crit, _org())
            assert ev.eligibility_status == EligibilityStatus.UNKNOWN
            assert ev.fit_score == 0.0
            assert ev.is_strong_match is False

    def test_deterministic(self):
        a = evaluate_candidate(_strong_extracted(), CRITERIA, _org())
        b = evaluate_candidate(_strong_extracted(), CRITERIA, _org())
        assert (a.fit_score, a.eligibility_status, a.act_now) == (b.fit_score, b.eligibility_status, b.act_now)

    def test_why_fits_names_focus_and_geography(self):
        ev = evaluate_candidate(_strong_extracted(), CRITERIA, _org())
        assert "youth development" in ev.why_fits
        assert "Boston" in ev.why_fits
