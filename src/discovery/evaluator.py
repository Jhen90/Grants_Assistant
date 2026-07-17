# ============================================================
# File: src/discovery/evaluator.py
# Version: 1.2.0
# Created: 2026-07-16
# Modified: 2026-07-16
# Description: Grant Scout EVALUATE phase. Scores a discovered candidate BEFORE a
#   human reviews it, so the review queue can be ranked best-first and eligible
#   strong matches highlighted (green). Pure + deterministic: it reuses the existing
#   ScoringEngine (no new scoring math) and the deadline classifier. No DB access —
#   the caller passes the active criteria list and the organization.
#
#   Eligibility follows the engine's fiscal-sponsorship rule (FR-SCOUT-302): a grant
#   that requires 501(c)(3) but allows a fiscal sponsor the org can use is ELIGIBLE.
# ============================================================

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from types import SimpleNamespace

from src.engine.deadline_classifier import classify_urgency
from src.engine.scoring_engine import ScoringEngine
from src.models.discovered_candidate import EligibilityStatus
from src.utils.config import get_settings

_engine = ScoringEngine()


@dataclass
class CandidateEvaluation:
    """Result of evaluating one discovered candidate (pre-import)."""

    fit_score: float
    eligibility_status: EligibilityStatus
    is_strong_match: bool
    deadline_urgency: str            # DeadlineUrgency value: RED/YELLOW/GREEN/GRAY
    act_now: bool
    why_fits: str
    reasons: list[str] = field(default_factory=list)


def _grant_like(extracted: dict) -> SimpleNamespace:
    """Adapt an extracted-field dict to the attribute shape ScoringEngine expects."""
    return SimpleNamespace(
        title=extracted.get("title", ""),
        target_geography=extracted.get("target_geography"),
        focus_areas_json=json.dumps(extracted.get("focus_areas", []) or []),
        eligibility_501c3_required=bool(extracted.get("eligibility_501c3_required", False)),
        fiscal_sponsorship_allowed=bool(extracted.get("fiscal_sponsorship_allowed", True)),
        fiscal_sponsor_id=extracted.get("fiscal_sponsor_id"),
        amount_min=extracted.get("amount_min"),
        amount_max=extracted.get("amount_max"),
    )


def _coerce_deadline(value) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def evaluate_candidate(
    extracted: dict,
    criteria_list: list[dict] | None,
    org: object | None,
) -> CandidateEvaluation:
    """
    Score + assess a candidate's extracted fields against the active criteria.

    When there is no active criteria set or no organization, returns a neutral
    UNKNOWN evaluation with fit 0.0 (never raises) — FR-SCOUT-302.
    """
    settings = get_settings()
    urgency = classify_urgency(_coerce_deadline(extracted.get("deadline"))).value

    if not criteria_list or org is None:
        return CandidateEvaluation(
            fit_score=0.0,
            eligibility_status=EligibilityStatus.UNKNOWN,
            is_strong_match=False,
            deadline_urgency=urgency,
            act_now=False,
            why_fits="",
            reasons=["No active selection criteria or organization to evaluate against."],
        )

    result = _engine.score_grant(_grant_like(extracted), criteria_list, org)

    eligibility = _derive_eligibility(result)
    is_strong = (
        result.fit_score >= settings.recommendation_threshold
        and eligibility == EligibilityStatus.ELIGIBLE
    )
    act_now = is_strong and urgency in ("RED", "YELLOW")

    return CandidateEvaluation(
        fit_score=result.fit_score,
        eligibility_status=eligibility,
        is_strong_match=is_strong,
        deadline_urgency=urgency,
        act_now=act_now,
        why_fits=_why_fits(result, extracted),
        reasons=[c.notes for c in result.criterion_results if c.notes],
    )


def _derive_eligibility(result) -> EligibilityStatus:
    if result.hard_filter_failed:
        return EligibilityStatus.INELIGIBLE
    elig = next(
        (c for c in result.criterion_results if c.evaluator_type == "eligibility"), None
    )
    if elig is None:
        return EligibilityStatus.ELIGIBLE  # nothing disqualifies
    if elig.raw_score >= 1.0:
        return EligibilityStatus.ELIGIBLE
    if elig.raw_score >= 0.5:
        return EligibilityStatus.UNKNOWN   # e.g. fiscal sponsor allowed but none assigned yet
    return EligibilityStatus.INELIGIBLE


def _why_fits(result, extracted: dict) -> str:
    """Deterministic, specific one-liner naming the matched focus area(s) + geography."""
    bits: list[str] = []
    geo_hit = next(
        (c for c in result.criterion_results
         if c.evaluator_type == "geography" and c.raw_score > 0), None
    )
    focus_hit = next(
        (c for c in result.criterion_results
         if c.evaluator_type == "focus_area" and c.raw_score > 0), None
    )
    focus_areas = extracted.get("focus_areas") or []
    if focus_hit and focus_areas:
        bits.append("focus on " + ", ".join(focus_areas[:3]))
    geo = extracted.get("target_geography")
    if geo_hit and geo:
        bits.append(f"serves {geo}")
    if not bits:
        return f"Fit {result.fit_score:.1f}/10 against current criteria."
    return f"{'; '.join(bits)} — fit {result.fit_score:.1f}/10."
