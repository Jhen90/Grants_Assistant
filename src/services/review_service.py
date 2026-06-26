# ============================================================
# File: src/services/review_service.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: ReviewService — 4-category human review pipeline
# ============================================================

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from src.models.review import (
    AmbiguityRecord,
    AssumptionRecord,
    ChecklistItem,
    ReviewChecklist,
    ReviewStatus,
    ReviewType,
)
from src.templates.checklists.default_checklist_items import DEFAULT_CHECKLIST_ITEMS
from src.utils.logger import get_logger

log = get_logger(__name__)


class ReviewService:
    def initialize_checklists(
        self, db: Session, application_id: str, draft_version_id: str
    ) -> list[ReviewChecklist]:
        """
        Create 4 ReviewChecklists (one per ReviewType) with default items.
        Idempotent — skips checklist types that already exist for this draft version.
        """
        checklists: list[ReviewChecklist] = []

        for review_type in ReviewType:
            existing = (
                db.query(ReviewChecklist)
                .filter_by(
                    application_id=application_id,
                    draft_version_id=draft_version_id,
                    review_type=review_type,
                )
                .first()
            )
            if existing:
                checklists.append(existing)
                continue

            checklist = ReviewChecklist(
                application_id=application_id,
                draft_version_id=draft_version_id,
                review_type=review_type,
                status=ReviewStatus.PENDING,
                has_blocking_items=False,
            )
            db.add(checklist)
            db.flush()

            # Seed default items
            for item_def in DEFAULT_CHECKLIST_ITEMS.get(review_type, []):
                item = ChecklistItem(
                    checklist_id=checklist.id,
                    text=item_def["text"],
                    is_critical=item_def.get("is_critical", False),
                )
                db.add(item)

            db.flush()
            checklists.append(checklist)
            log.info("Review checklist created: %s for app %s.", review_type.value, application_id)

        return checklists

    def update_checklist_item(
        self, db: Session, item_id: str, is_checked: bool, finding_notes: str | None = None
    ) -> ChecklistItem:
        """
        Update a checklist item's checked state and notes.
        Re-evaluates the parent checklist's blocking status.
        """
        item = db.query(ChecklistItem).filter_by(id=item_id).first()
        if item is None:
            raise ValueError(f"ChecklistItem {item_id!r} not found.")

        item.is_checked = is_checked
        if finding_notes is not None:
            item.finding_notes = finding_notes
        db.flush()

        # Update parent checklist blocking status
        self._refresh_blocking_status(db, item.checklist_id)
        return item

    def add_assumption(
        self,
        db: Session,
        checklist_id: str,
        description: str,
        basis: str,
        is_documented: bool = False,
    ) -> AssumptionRecord:
        record = AssumptionRecord(
            checklist_id=checklist_id,
            description=description,
            basis=basis,
            is_documented=is_documented,
        )
        db.add(record)
        db.flush()
        # Mark checklist IN_PROGRESS if PENDING
        self._ensure_in_progress(db, checklist_id)
        return record

    def add_ambiguity(
        self,
        db: Session,
        checklist_id: str,
        description: str,
        resolution: str,
        decision: str,
    ) -> AmbiguityRecord:
        record = AmbiguityRecord(
            checklist_id=checklist_id,
            description=description,
            resolution=resolution,
            decision=decision,
        )
        db.add(record)
        db.flush()
        self._ensure_in_progress(db, checklist_id)
        return record

    def complete_checklist(
        self, db: Session, checklist_id: str, reviewer_name: str
    ) -> ReviewChecklist:
        """
        Attempt to mark a checklist as COMPLETED. Sets BLOCKED if any critical
        item is unchecked; COMPLETED otherwise.
        """
        checklist = db.query(ReviewChecklist).filter_by(id=checklist_id).first()
        if checklist is None:
            raise ValueError(f"ReviewChecklist {checklist_id!r} not found.")

        self._refresh_blocking_status(db, checklist_id)
        db.refresh(checklist)

        if checklist.has_blocking_items:
            checklist.status = ReviewStatus.BLOCKED
        else:
            checklist.status = ReviewStatus.COMPLETED
            checklist.completed_at = datetime.utcnow()

        checklist.reviewer_name = reviewer_name
        db.flush()
        log.info(
            "Checklist %s marked %s by %s.",
            checklist_id, checklist.status.value, reviewer_name,
        )
        return checklist

    def get_checklists_for_application(
        self, db: Session, application_id: str, draft_version_id: str | None = None
    ) -> list[ReviewChecklist]:
        q = db.query(ReviewChecklist).filter_by(application_id=application_id)
        if draft_version_id:
            q = q.filter_by(draft_version_id=draft_version_id)
        return q.order_by(ReviewChecklist.review_type).all()

    # ─── private helpers ───────────────────────────────────────────────────────

    def _refresh_blocking_status(self, db: Session, checklist_id: str) -> None:
        """Set has_blocking_items=True if any critical item is unchecked."""
        items = db.query(ChecklistItem).filter_by(checklist_id=checklist_id).all()
        has_blocker = any(i.is_critical and not i.is_checked for i in items)
        checklist = db.query(ReviewChecklist).filter_by(id=checklist_id).first()
        if checklist:
            checklist.has_blocking_items = has_blocker
            if has_blocker and checklist.status == ReviewStatus.COMPLETED:
                checklist.status = ReviewStatus.BLOCKED
            db.flush()

    def _ensure_in_progress(self, db: Session, checklist_id: str) -> None:
        checklist = db.query(ReviewChecklist).filter_by(id=checklist_id).first()
        if checklist and checklist.status == ReviewStatus.PENDING:
            checklist.status = ReviewStatus.IN_PROGRESS
            db.flush()
