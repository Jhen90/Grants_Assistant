# ============================================================
# File: tests/unit/test_application_service.py
# Version: 1.1.0
# Created: 2026-06-25
# ============================================================

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src.models.application import Application, ApplicationStatus, DocumentRequirement
from src.models.grant import Grant, GrantStatus
from src.models.manifest import Manifest
from src.services.application_service import ApplicationService
from src.utils.error_handler import SubmissionBlockedError


@pytest.fixture()
def svc() -> ApplicationService:
    return ApplicationService()


class TestCreateApplication:
    def test_creates_application(
        self, db: Session, svc: ApplicationService, sample_grant: Grant
    ):
        sample_grant.status = GrantStatus.RECOMMENDED
        db.commit()
        app = svc.create_application(db, sample_grant.id)
        assert app.id is not None
        assert app.status == ApplicationStatus.DRAFT

    def test_advances_grant_to_approved_to_apply(
        self, db: Session, svc: ApplicationService, sample_grant: Grant
    ):
        sample_grant.status = GrantStatus.RECOMMENDED
        db.commit()
        svc.create_application(db, sample_grant.id)
        db.refresh(sample_grant)
        assert sample_grant.status == GrantStatus.APPROVED_TO_APPLY

    def test_creates_document_requirements(
        self, db: Session, svc: ApplicationService, sample_grant: Grant
    ):
        sample_grant.status = GrantStatus.RECOMMENDED
        db.commit()
        app = svc.create_application(db, sample_grant.id)
        docs = db.query(DocumentRequirement).filter_by(application_id=app.id).all()
        assert len(docs) > 0

    def test_creates_manifest(
        self, db: Session, svc: ApplicationService, sample_grant: Grant
    ):
        sample_grant.status = GrantStatus.RECOMMENDED
        db.commit()
        app = svc.create_application(db, sample_grant.id)
        manifest = db.query(Manifest).filter_by(application_id=app.id).first()
        assert manifest is not None


class TestCreateDraftVersion:
    def test_creates_v1(
        self, db: Session, svc: ApplicationService, sample_application: Application
    ):
        sections = {"executive_summary": "We empower youth."}
        draft = svc.create_draft_version(db, sample_application.id, sections)
        assert draft.version_number == 1
        assert draft.is_current is True

    def test_second_draft_increments_version(
        self, db: Session, svc: ApplicationService, sample_application: Application
    ):
        svc.create_draft_version(db, sample_application.id, {"s": "v1"})
        draft2 = svc.create_draft_version(db, sample_application.id, {"s": "v2"})
        assert draft2.version_number == 2

    def test_only_one_current_draft(
        self, db: Session, svc: ApplicationService, sample_application: Application
    ):
        from src.models.draft import DraftVersion
        svc.create_draft_version(db, sample_application.id, {"s": "v1"})
        svc.create_draft_version(db, sample_application.id, {"s": "v2"})
        current = (
            db.query(DraftVersion)
            .filter_by(application_id=sample_application.id, is_current=True)
            .all()
        )
        assert len(current) == 1


class TestApproveApplication:
    def test_approve_blocked_when_no_draft(
        self, db: Session, svc: ApplicationService, sample_application: Application
    ):
        with pytest.raises(SubmissionBlockedError):
            svc.approve_application(db, sample_application.id, "Reviewer")

    def test_approve_blocked_when_checklists_incomplete(
        self, db: Session, svc: ApplicationService, sample_application: Application
    ):
        svc.create_draft_version(db, sample_application.id, {"s": "draft"})
        with pytest.raises(SubmissionBlockedError):
            svc.approve_application(db, sample_application.id, "Reviewer")

    def test_approve_succeeds_when_all_reviews_complete(
        self,
        db: Session,
        svc: ApplicationService,
        sample_application_fully_reviewed: Application,
    ):
        app = svc.approve_application(
            db, sample_application_fully_reviewed.id, "Test Approver"
        )
        assert app.status == ApplicationStatus.APPROVED
        assert app.approved_by == "Test Approver"
