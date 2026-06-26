# ============================================================
# File: tests/integration/test_full_grant_lifecycle.py
# Version: 1.1.0
# Created: 2026-06-25
# Description: End-to-end lifecycle: discovery → evaluation → approval → submission → outcome
# ============================================================

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from src.models.application import ApplicationStatus
from src.models.grant import GrantStatus
from src.models.organization import Organization
from src.models.review import ReviewType
from src.services.application_service import ApplicationService
from src.services.grant_service import GrantService
from src.services.review_service import ReviewService
from src.utils.error_handler import SubmissionBlockedError


@pytest.fixture()
def grant_svc() -> GrantService:
    return GrantService()


@pytest.fixture()
def app_svc() -> ApplicationService:
    return ApplicationService()


@pytest.fixture()
def review_svc() -> ReviewService:
    return ReviewService()


def test_full_lifecycle_happy_path(
    db: Session,
    grant_svc: GrantService,
    app_svc: ApplicationService,
    review_svc: ReviewService,
    sample_org: Organization,
    sample_funder,
    sample_fiscal_sponsor,
    sample_criteria,
):
    """
    Tests the full flow:
    DISCOVERED → EVALUATED/RECOMMENDED → start application →
    create draft → initialize reviews → complete all reviews →
    approve application → record submission → record outcome (AWARDED).
    """
    # 1. Create grant
    grant = grant_svc.create_grant(
        db,
        {
            "title": "Full Lifecycle Test Grant",
            "funder_id": sample_funder.id,
            "funder_name": sample_funder.name,
            "fiscal_sponsor_id": sample_fiscal_sponsor.id,
            "deadline": date.today() + timedelta(days=45),
            "amount_min": 15000,
            "amount_max": 40000,
            "target_geography": "Boston, MA",
            "eligibility_501c3_required": False,
            "fiscal_sponsorship_allowed": True,
            "focus_areas": ["youth development", "martial arts"],
        },
    )
    assert grant.status in (GrantStatus.EVALUATED, GrantStatus.RECOMMENDED)
    assert grant.fit_score is not None

    # Force to RECOMMENDED so we can start an application
    grant_svc.advance_status(db, grant.id, GrantStatus.RECOMMENDED)
    db.refresh(grant)
    assert grant.status == GrantStatus.RECOMMENDED

    # 2. Start application
    application = app_svc.create_application(db, grant.id)
    assert application.status == ApplicationStatus.DRAFT
    db.refresh(grant)
    assert grant.status == GrantStatus.APPROVED_TO_APPLY

    # 3. Save a draft
    draft = app_svc.create_draft_version(
        db,
        application.id,
        {
            "executive_summary": "The Dojo empowers underserved youth.",
            "problem_statement": "Youth in Boston lack structured programming.",
            "proposed_solution": "Weekly martial arts and mentorship sessions.",
        },
    )
    assert draft.version_number == 1
    assert draft.is_current is True

    # 4. Initialize reviews
    checklists = review_svc.initialize_checklists(db, application.id, draft.id)
    assert len(checklists) == 4

    # 5. Complete all reviews (check all critical items)
    from src.models.review import ChecklistItem, ReviewStatus
    for cl in checklists:
        items = db.query(ChecklistItem).filter_by(checklist_id=cl.id, is_critical=True).all()
        for item in items:
            review_svc.update_checklist_item(db, item.id, is_checked=True)
        result = review_svc.complete_checklist(db, cl.id, "Integration Test Reviewer")
        assert result.status == ReviewStatus.COMPLETED

    # 6. Approve application — hard gate should pass
    approved_app = app_svc.approve_application(db, application.id, "Director Jones")
    assert approved_app.status == ApplicationStatus.APPROVED
    assert approved_app.approved_by == "Director Jones"

    # 7. Record submission
    submitted_app = app_svc.record_submission(
        db,
        application.id,
        method="Online Portal",
        confirmation="CONF-2026-001",
        submitter="Jane Smith",
    )
    assert submitted_app.status == ApplicationStatus.SUBMITTED
    db.refresh(grant)
    assert grant.status == GrantStatus.SUBMITTED

    # 8. Record outcome — AWARDED
    awarded_app = app_svc.record_outcome(db, application.id, "AWARDED", award_amount=35000.0)
    assert awarded_app.status == ApplicationStatus.AWARDED
    assert awarded_app.award_amount == 35000.0
    db.refresh(grant)
    assert grant.status == GrantStatus.AWARDED


def test_approve_blocked_without_reviews(
    db: Session,
    grant_svc: GrantService,
    app_svc: ApplicationService,
    sample_org,
    sample_funder,
    sample_fiscal_sponsor,
    sample_criteria,
):
    """Attempt to approve without completing reviews — must raise SubmissionBlockedError."""
    grant = grant_svc.create_grant(
        db,
        {
            "title": "Blocked Gate Test",
            "funder_id": sample_funder.id,
            "funder_name": sample_funder.name,
            "deadline": date.today() + timedelta(days=60),
            "eligibility_501c3_required": False,
            "fiscal_sponsorship_allowed": True,
        },
    )
    grant_svc.advance_status(db, grant.id, GrantStatus.RECOMMENDED)
    application = app_svc.create_application(db, grant.id)
    app_svc.create_draft_version(db, application.id, {"s": "draft content"})

    with pytest.raises(SubmissionBlockedError) as exc_info:
        app_svc.approve_application(db, application.id, "Reviewer")
    assert len(exc_info.value.blockers) > 0
