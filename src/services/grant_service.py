# ============================================================
# File: src/services/grant_service.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: GrantService — full grant lifecycle CRUD and scoring orchestration
# ============================================================

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from src.engine.deadline_classifier import classify_urgency
from src.engine.deduplication import find_duplicates
from src.engine.state_machine import advance_grant_status
from src.models.grant import Grant, GrantStatus
from src.services.scoring_service import score_grant as _score
from src.utils.config import get_settings
from src.utils.error_handler import DuplicateGrantError
from src.utils.logger import get_logger

log = get_logger(__name__)
_settings = get_settings()


@dataclass
class Page:
    items: list[Grant]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return max(1, -(-self.total // self.page_size))  # ceiling division


class GrantService:
    def create_grant(self, db: Session, data: dict) -> Grant:
        """
        Create a grant, deduplicate, score, classify urgency, and advance to
        EVALUATED or RECOMMENDED.
        Raises DuplicateGrantError if a duplicate is detected.
        """
        # Deduplication check
        existing_raw = [
            {
                "id": g.id,
                "title": g.title,
                "source_url": g.source_url,
                "funder_id": g.funder_id,
                "is_deleted": g.is_deleted,
            }
            for g in db.query(Grant).all()
        ]
        matches = find_duplicates(
            candidate_title=data.get("title", ""),
            candidate_url=data.get("source_url"),
            candidate_funder_id=data.get("funder_id"),
            existing_grants=existing_raw,
        )
        if matches:
            m = matches[0]
            raise DuplicateGrantError(
                match_type=m.match_type,
                match_field=m.match_field,
                existing_id=m.existing_id,
            )

        # Create grant in DISCOVERED state
        focus_areas = data.get("focus_areas", [])
        grant = Grant(
            title=data["title"],
            funder_id=data.get("funder_id"),
            funder_name=data.get("funder_name"),
            fiscal_sponsor_id=data.get("fiscal_sponsor_id"),
            status=GrantStatus.DISCOVERED,
            deadline=data.get("deadline"),
            amount_min=data.get("amount_min"),
            amount_max=data.get("amount_max"),
            focus_areas_json=json.dumps(focus_areas, ensure_ascii=False),
            target_geography=data.get("target_geography"),
            eligibility_501c3_required=bool(data.get("eligibility_501c3_required", False)),
            fiscal_sponsorship_allowed=bool(data.get("fiscal_sponsorship_allowed", True)),
            source_url=data.get("source_url"),
            notes=data.get("notes"),
        )
        db.add(grant)
        db.flush()

        # Score
        _score(grant, db)

        # Classify deadline urgency
        grant.deadline_urgency = classify_urgency(grant.deadline)

        # Advance status: DISCOVERED → EVALUATED
        grant.status = advance_grant_status(grant.status, GrantStatus.EVALUATED)

        # If score meets recommendation threshold → EVALUATED → RECOMMENDED
        if (grant.fit_score or 0.0) >= _settings.recommendation_threshold:
            grant.status = advance_grant_status(grant.status, GrantStatus.RECOMMENDED)

        db.commit()
        db.refresh(grant)
        log.info(
            "Grant created: %s (id=%s, status=%s, score=%.2f)",
            grant.title, grant.id, grant.status.value, grant.fit_score or 0,
        )
        return grant

    def get_grants_paginated(
        self,
        db: Session,
        filters: dict | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> Page:
        filters = filters or {}
        q = db.query(Grant).filter(Grant.is_deleted.is_(False))

        if "status" in filters:
            q = q.filter(Grant.status == filters["status"])
        if "funder_id" in filters:
            q = q.filter(Grant.funder_id == filters["funder_id"])
        if "min_score" in filters:
            q = q.filter(Grant.fit_score >= filters["min_score"])
        if "urgency" in filters:
            q = q.filter(Grant.deadline_urgency == filters["urgency"])
        if "search" in filters and filters["search"]:
            term = f"%{filters['search']}%"
            q = q.filter(Grant.title.ilike(term))

        total = q.count()
        items = (
            q.order_by(Grant.fit_score.desc().nullslast(), Grant.deadline.asc().nullslast())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return Page(items=items, total=total, page=page, page_size=page_size)

    def get_by_id(self, db: Session, grant_id: str) -> Grant | None:
        return db.query(Grant).filter_by(id=grant_id, is_deleted=False).first()

    def update_grant(self, db: Session, grant_id: str, data: dict) -> Grant | None:
        grant = self.get_by_id(db, grant_id)
        if grant is None:
            return None
        updatable = (
            "title", "funder_id", "funder_name", "fiscal_sponsor_id",
            "deadline", "amount_min", "amount_max", "target_geography",
            "eligibility_501c3_required", "fiscal_sponsorship_allowed",
            "source_url", "notes",
        )
        for field in updatable:
            if field in data:
                setattr(grant, field, data[field])
        if "focus_areas" in data:
            grant.focus_areas_json = json.dumps(data["focus_areas"], ensure_ascii=False)
        if "deadline" in data:
            grant.deadline_urgency = classify_urgency(data["deadline"])
        db.commit()
        db.refresh(grant)
        return grant

    def advance_status(self, db: Session, grant_id: str, new_status: GrantStatus | str) -> Grant:
        grant = self.get_by_id(db, grant_id)
        if grant is None:
            raise ValueError(f"Grant {grant_id!r} not found.")
        grant.status = advance_grant_status(grant.status, new_status)
        db.commit()
        db.refresh(grant)
        return grant

    def soft_delete(self, db: Session, grant_id: str) -> None:
        grant = self.get_by_id(db, grant_id)
        if grant:
            grant.is_deleted = True
            grant.deleted_at = datetime.utcnow()
            db.commit()
            log.info("Grant soft-deleted: %s", grant_id)

    def re_score_all(self, db: Session) -> int:
        """Re-score all non-terminal, non-deleted grants. Returns count updated."""
        terminal = {
            GrantStatus.ARCHIVED, GrantStatus.AWARDED,
            GrantStatus.DECLINED, GrantStatus.WITHDRAWN,
        }
        grants = (
            db.query(Grant)
            .filter(Grant.is_deleted.is_(False), Grant.status.notin_(terminal))
            .all()
        )
        for grant in grants:
            _score(grant, db)
            grant.deadline_urgency = classify_urgency(grant.deadline)

            # Re-evaluate RECOMMENDED threshold
            if grant.status == GrantStatus.EVALUATED:
                if (grant.fit_score or 0.0) >= _settings.recommendation_threshold:
                    grant.status = GrantStatus.RECOMMENDED
            elif grant.status == GrantStatus.RECOMMENDED:
                if (grant.fit_score or 0.0) < _settings.recommendation_threshold:
                    grant.status = GrantStatus.EVALUATED

        db.commit()
        log.info("Re-scored %d grants.", len(grants))
        return len(grants)
