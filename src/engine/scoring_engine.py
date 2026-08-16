# ============================================================
# File: src/engine/scoring_engine.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Deterministic rules-based scoring engine — pure functions, no randomness
# ============================================================

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from src.utils.logger import get_logger

log = get_logger(__name__)

# Broader geographies that give a partial geography score
_BROADER_GEOS = frozenset(
    [
        "national", "nationwide", "united states", "usa", "us",
        "northeast", "new england", "east coast",
    ]
)


# ─── Result dataclasses ────────────────────────────────────────────────────────

@dataclass
class CriterionResult:
    name: str
    evaluator_type: str
    raw_score: float       # 0.0 – 1.0
    weight: int
    weighted_score: float  # raw_score * weight
    passed: bool           # False = hard filter failed
    notes: str = ""


@dataclass
class ScoreResult:
    fit_score: float                              # 0.0 – 10.0 (normalised)
    hard_filter_failed: bool
    criterion_results: list[CriterionResult] = field(default_factory=list)
    score_breakdown_json: dict = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize score_breakdown_json for storage in the DB."""
        return json.dumps(self.score_breakdown_json, ensure_ascii=False)


# ─── ScoringEngine ─────────────────────────────────────────────────────────────

class ScoringEngine:
    """
    Pure, deterministic scoring engine. Same inputs always produce the same output.
    No DB access — all data passed in as plain objects/dicts.
    """

    def score_grant(
        self,
        grant: object,
        criteria_list: list[dict],
        org: object,
    ) -> ScoreResult:
        """
        Score a grant against the active selection criteria for an organization.

        Args:
            grant: A Grant ORM instance (or duck-typed dict with same attributes).
            criteria_list: Parsed criteria_json from SelectionCriteria.criteria_json.
            org: An Organization ORM instance.

        Returns:
            ScoreResult with fit_score, hard_filter_failed flag, and criterion breakdown.
        """
        criterion_results: list[CriterionResult] = []
        hard_filter_failed = False

        for rule in criteria_list:
            result = self._evaluate_criterion(rule, grant, org)
            criterion_results.append(result)

            if rule.get("is_hard_filter") and not result.passed:
                hard_filter_failed = True
                log.debug(
                    "Hard filter FAILED on criterion '%s' for grant '%s'",
                    rule.get("name"), getattr(grant, "title", "?"),
                )
                break  # Short-circuit — no need to score further

        if hard_filter_failed:
            fit_score = 0.0
        else:
            fit_score = self._normalize(criterion_results)

        breakdown = {
            "fit_score": fit_score,
            "hard_filter_failed": hard_filter_failed,
            "criteria": [asdict(r) for r in criterion_results],
        }

        return ScoreResult(
            fit_score=round(fit_score, 2),
            hard_filter_failed=hard_filter_failed,
            criterion_results=criterion_results,
            score_breakdown_json=breakdown,
        )

    # ─── per-criterion dispatch ────────────────────────────────────────────────

    def _evaluate_criterion(
        self, rule: dict, grant: object, org: object
    ) -> CriterionResult:
        evaluator_type = rule.get("type", "unknown")
        name = rule.get("name", evaluator_type)
        weight = int(rule.get("weight", 1))
        config = rule.get("config", {})

        dispatch = {
            "geography":   self._eval_geography,
            "focus_area":  self._eval_focus_area,
            "eligibility": self._eval_eligibility,
            "amount_range": self._eval_amount_range,
        }

        evaluator = dispatch.get(evaluator_type)
        if evaluator is None:
            log.warning("Unknown evaluator type '%s' — skipping with raw_score=0.0.", evaluator_type)
            return CriterionResult(
                name=name, evaluator_type=evaluator_type,
                raw_score=0.0, weight=weight, weighted_score=0.0,
                passed=True, notes=f"Unknown evaluator type: {evaluator_type}",
            )

        raw_score, notes = evaluator(rule, grant, org, config)
        is_hard_filter = bool(rule.get("is_hard_filter"))
        passed = not (is_hard_filter and raw_score == 0.0)

        return CriterionResult(
            name=name,
            evaluator_type=evaluator_type,
            raw_score=raw_score,
            weight=weight,
            weighted_score=round(raw_score * weight, 4),
            passed=passed,
            notes=notes,
        )

    # ─── individual evaluators ─────────────────────────────────────────────────

    def _eval_geography(
        self, rule: dict, grant: object, org: object, config: dict
    ) -> tuple[float, str]:
        """
        Scores geographic fit.
        - Any target geo found in grant.target_geography → 1.0
        - Broader regional term found (national, northeast, etc.) → 0.5
        - No match → 0.0
        """
        target_geos = [g.lower() for g in config.get("target_geographies", [])]
        grant_geo = (getattr(grant, "target_geography", "") or "").lower()

        if not grant_geo:
            return 0.5, "No geography specified on grant — assuming partial match."

        # Check for direct match
        for geo in target_geos:
            if geo in grant_geo:
                return 1.0, f"Exact geography match: '{geo}' found in '{grant_geo}'."

        # Check for broader regional terms
        for broader in _BROADER_GEOS:
            if broader in grant_geo:
                return 0.5, f"Broader geography match: '{broader}' found — partial credit."

        return 0.0, f"No geography match. Grant geo: '{grant_geo}'. Target: {target_geos}."

    def _eval_focus_area(
        self, rule: dict, grant: object, org: object, config: dict
    ) -> tuple[float, str]:
        """
        Scores focus area alignment.
        - Any target focus area matches a grant focus area → 1.0
        - No match → 0.0
        """
        target_areas = [a.lower() for a in config.get("target_focus_areas", [])]

        raw_focus_json = getattr(grant, "focus_areas_json", None) or "[]"
        try:
            grant_areas_raw = json.loads(raw_focus_json) if isinstance(raw_focus_json, str) else raw_focus_json
        except (json.JSONDecodeError, TypeError):
            grant_areas_raw = []

        grant_areas = [str(a).lower() for a in grant_areas_raw]

        if not grant_areas:
            return 0.0, "Grant has no focus areas specified."

        matched = [a for a in grant_areas if any(t in a or a in t for t in target_areas)]
        if matched:
            return 1.0, f"Focus area match: {matched}."

        return 0.0, f"No focus area match. Grant areas: {grant_areas}. Target: {target_areas}."

    def _eval_eligibility(
        self, rule: dict, grant: object, org: object, config: dict
    ) -> tuple[float, str]:
        """
        Eligibility evaluator — PASS (1.0), PARTIAL (0.5), or FAIL (0.0, hard filter).

        Logic per Implementation Plan Section C-P2-04:
        - No 501c3 required → PASS
        - Org has own 501c3 → PASS
        - Requires 501c3 + allows fiscal + sponsor available → PASS
        - Requires 501c3 + allows fiscal + NO sponsor → PARTIAL (0.5)
        - Requires 501c3 + NO fiscal allowed + no own 501c3 → FAIL (hard filter)
        """
        eligibility_json = getattr(org, "eligibility_json", None) or "{}"
        if isinstance(eligibility_json, str):
            try:
                elig = json.loads(eligibility_json)
            except json.JSONDecodeError:
                elig = {}
        else:
            elig = eligibility_json

        has_own_501c3 = bool(elig.get("has_501c3", False))
        grant_requires_501c3 = bool(getattr(grant, "eligibility_501c3_required", False))
        grant_allows_fiscal = bool(getattr(grant, "fiscal_sponsorship_allowed", True))

        # Determine if a fiscal sponsor is configured for this grant
        grant_has_fiscal_sponsor = bool(getattr(grant, "fiscal_sponsor_id", None))
        org_has_default_sponsor = bool(elig.get("default_fiscal_sponsor"))
        fiscal_sponsor_available = grant_has_fiscal_sponsor or org_has_default_sponsor

        if not grant_requires_501c3:
            return 1.0, "No 501(c)(3) required — open eligibility."

        if has_own_501c3:
            return 1.0, "Organization holds its own 501(c)(3)."

        if grant_allows_fiscal and fiscal_sponsor_available:
            sponsor = getattr(grant, "fiscal_sponsor_id", None) or elig.get("default_fiscal_sponsor")
            return 1.0, f"Fiscal sponsor available: {sponsor}."

        if grant_allows_fiscal and not fiscal_sponsor_available:
            return 0.5, (
                "Fiscal sponsorship allowed but no sponsor configured for this grant. "
                "Assign a fiscal sponsor to qualify."
            )

        # Grant requires 501c3, does not allow fiscal sponsorship, org has no 501c3
        return 0.0, (
            "HARD FILTER: Grant requires 501(c)(3) and does not accept fiscal sponsorship. "
            "Organization does not hold 501(c)(3). Cannot apply."
        )

    def _eval_amount_range(
        self, rule: dict, grant: object, org: object, config: dict
    ) -> tuple[float, str]:
        """
        Scores whether the grant amount falls within acceptable range.
        - Full overlap → 1.0
        - Partial overlap → 0.5
        - No overlap → 0.0
        - No amount specified on grant → 0.5 (unknown, assume partial)
        """
        min_acceptable = float(config.get("min_acceptable", 0))
        max_acceptable = float(config.get("max_acceptable", float("inf")))

        grant_min = getattr(grant, "amount_min", None)
        grant_max = getattr(grant, "amount_max", None)

        if grant_min is None and grant_max is None:
            return 0.5, "Grant amount not specified — assuming partial fit."

        g_min = float(grant_min) if grant_min is not None else 0.0
        g_max = float(grant_max) if grant_max is not None else g_min

        # No overlap
        if g_max < min_acceptable or g_min > max_acceptable:
            return 0.0, (
                f"Amount range ${g_min:,.0f}–${g_max:,.0f} is outside "
                f"acceptable range ${min_acceptable:,.0f}–${max_acceptable:,.0f}."
            )

        # Full overlap (grant range is within acceptable range)
        if g_min >= min_acceptable and g_max <= max_acceptable:
            return 1.0, f"Grant amount ${g_min:,.0f}–${g_max:,.0f} within acceptable range."

        # Partial overlap
        return 0.5, (
            f"Partial amount overlap: grant ${g_min:,.0f}–${g_max:,.0f} vs "
            f"acceptable ${min_acceptable:,.0f}–${max_acceptable:,.0f}."
        )

    # ─── normalization ─────────────────────────────────────────────────────────

    @staticmethod
    def _normalize(criterion_results: list[CriterionResult]) -> float:
        """Convert weighted scores to a 0–10 scale."""
        if not criterion_results:
            return 0.0
        total_weighted = sum(r.weighted_score for r in criterion_results)
        max_possible = sum(r.weight for r in criterion_results)
        if max_possible == 0:
            return 0.0
        return (total_weighted / max_possible) * 10.0
