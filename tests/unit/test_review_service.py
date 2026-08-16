# ============================================================
# File: tests/unit/test_review_service.py
# Version: 1.1.0
# Created: 2026-06-25
# ============================================================

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src.models.application import Application
from src.models.draft import DraftVersion
from src.models.review import ChecklistItem, ReviewChecklist, ReviewStatus, ReviewType
from src.services.application_service import ApplicationService
from src.services.review_service import ReviewService


@pytest.fixture()
def svc() -> ReviewService:
    return ReviewService()


@pytest.fixture()
def draft_with_app(db: Session, sample_application: Application) -> tuple[Application, DraftVersion]:
    draft = DraftVersion(
        application_id=sample_application.id,
        version_number=1,
        sections_json="{}",
        is_current=True,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return sample_application, draft


class TestInitializeChecklists:
    def test_creates_4_checklists(
        self, db: Session, svc: ReviewService, draft_with_app
    ):
        app, draft = draft_with_app
        checklists = svc.initialize_checklists(db, app.id, draft.id)
        assert len(checklists) == 4

    def test_all_review_types_present(
        self, db: Session, svc: ReviewService, draft_with_app
    ):
        app, draft = draft_with_app
        checklists = svc.initialize_checklists(db, app.id, draft.id)
        types = {c.review_type for c in checklists}
        assert types == set(ReviewType)

    def test_idempotent_initialization(
        self, db: Session, svc: ReviewService, draft_with_app
    ):
        app, draft = draft_with_app
        svc.initialize_checklists(db, app.id, draft.id)
        checklists2 = svc.initialize_checklists(db, app.id, draft.id)
        assert len(checklists2) == 4  # No duplicates

    def test_default_items_seeded(
        self, db: Session, svc: ReviewService, draft_with_app
    ):
        app, draft = draft_with_app
        checklists = svc.initialize_checklists(db, app.id, draft.id)
        for cl in checklists:
            items = db.query(ChecklistItem).filter_by(checklist_id=cl.id).all()
            assert len(items) > 0


class TestUpdateChecklistItem:
    def test_mark_item_checked(
        self, db: Session, svc: ReviewService, draft_with_app
    ):
        app, draft = draft_with_app
        checklists = svc.initialize_checklists(db, app.id, draft.id)
        items = db.query(ChecklistItem).filter_by(checklist_id=checklists[0].id).all()
        item = items[0]
        result = svc.update_checklist_item(db, item.id, is_checked=True)
        assert result.is_checked is True


class TestCompleteChecklist:
    def test_complete_fails_when_critical_unchecked(
        self, db: Session, svc: ReviewService, draft_with_app
    ):
        app, draft = draft_with_app
        checklists = svc.initialize_checklists(db, app.id, draft.id)
        # Leave all items unchecked
        cl = svc.complete_checklist(db, checklists[0].id, "Reviewer")
        assert cl.status == ReviewStatus.BLOCKED

    def test_complete_succeeds_when_all_critical_checked(
        self, db: Session, svc: ReviewService, draft_with_app
    ):
        app, draft = draft_with_app
        checklists = svc.initialize_checklists(db, app.id, draft.id)
        cl = checklists[0]
        items = db.query(ChecklistItem).filter_by(checklist_id=cl.id, is_critical=True).all()
        for item in items:
            svc.update_checklist_item(db, item.id, is_checked=True)
        result = svc.complete_checklist(db, cl.id, "Reviewer")
        assert result.status == ReviewStatus.COMPLETED
        assert result.reviewer_name == "Reviewer"
