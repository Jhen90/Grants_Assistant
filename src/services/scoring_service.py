# ============================================================
# File: src/services/scoring_service.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: ScoringService — thin wrapper around ScoringEngine; persists score to DB
# ============================================================

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from src.engine.scoring_engine import ScoringEngine
from src.models.grant import Grant
from src.models.organization import Organization
from src.models.selection_criteria import SelectionCriteria
from src.utils.logger import get_logger

log = get_logger(__name__)

_engine = ScoringEngine()


def score_grant(grant: Grant, db: Session) -> Grant:
    """
    Score a grant against the active SelectionCriteria for the first Organization.
    Persists fit_score, score_breakdown_json to the grant record (caller must commit).
    Returns the mutated grant.
    """
    criteria = (
        db.query(SelectionCriteria).filter_by(is_active=True).order_by(
            SelectionCriteria.created_at
        ).first()
    )
    if criteria is None:
        log.warning("No active SelectionCriteria found — grant %s scored 0.0.", grant.id)
        grant.fit_score = 0.0
        grant.score_breakdown_json = json.dumps({"error": "No active criteria found"})
        return grant

    org = db.query(Organization).filter_by(is_deleted=False).order_by(
        Organization.created_at
    ).first()
    if org is None:
        log.warning("No Organization found — grant %s scored 0.0.", grant.id)
        grant.fit_score = 0.0
        grant.score_breakdown_json = json.dumps({"error": "No organization found"})
        return grant

    try:
        criteria_list = json.loads(criteria.criteria_json or "[]")
    except json.JSONDecodeError:
        criteria_list = []

    result = _engine.score_grant(grant, criteria_list, org)
    grant.fit_score = result.fit_score
    grant.score_breakdown_json = result.to_json()
    log.info(
        "Grant %s scored %.2f (hard_filter=%s)",
        grant.id, result.fit_score, result.hard_filter_failed,
    )
    return grant
