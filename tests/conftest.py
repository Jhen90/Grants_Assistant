# ============================================================
# File: tests/conftest.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Pytest fixtures — in-memory SQLite DB and core domain objects
# ============================================================

from __future__ import annotations

import json
from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.db.database import Base
from src.models import (
    Application,
    ApplicationStatus,
    DraftVersion,
    Funder,
    FunderType,
    Grant,
    GrantStatus,
    Organization,
    ReviewChecklist,
    ReviewStatus,
    ReviewType,
    SelectionCriteria,
)
from src.models.review import ChecklistItem  # noqa: F401 — ensures model is registered


@pytest.fixture(scope="function")
def db() -> Session:
    """
    Create an isolated in-memory SQLite session for each test.
    WAL mode not applicable for :memory:, but FK enforcement is turned on.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def _set_fk(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture()
def sample_org(db: Session) -> Organization:
    org = Organization(
        name="The Dojo",
        mission="Empowering underserved youth through martial arts and mentorship.",
        city="Boston",
        state="MA",
        is_501c3=False,
        programs_json=json.dumps([{"name": "Youth Martial Arts"}]),
        eligibility_json=json.dumps({"target_population": "youth aged 10–18"}),
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.fixture()
def sample_funder(db: Session) -> Funder:
    funder = Funder(
        name="Test Foundation",
        funder_type=FunderType.FOUNDATION,
        is_fiscal_sponsor=False,
        is_501c3=True,
    )
    db.add(funder)
    db.commit()
    db.refresh(funder)
    return funder


@pytest.fixture()
def sample_fiscal_sponsor(db: Session) -> Funder:
    sponsor = Funder(
        name="Teen Empowerment",
        funder_type=FunderType.OTHER,
        is_fiscal_sponsor=True,
        is_501c3=True,
    )
    db.add(sponsor)
    db.commit()
    db.refresh(sponsor)
    return sponsor


@pytest.fixture()
def sample_criteria(db: Session) -> SelectionCriteria:
    criteria_rules = [
        {
            "name": "Geography Match",
            "type": "geography",
            "weight": 2,
            "org_geography": "Boston, MA",
        },
        {
            "name": "Focus Area Match",
            "type": "focus_area",
            "weight": 3,
            "org_focus_areas": ["youth development", "martial arts"],
        },
        {
            "name": "Eligibility Check",
            "type": "eligibility",
            "weight": 5,
        },
        {
            "name": "Amount Range",
            "type": "amount_range",
            "weight": 1,
            "org_typical_ask": 25000,
        },
    ]
    criteria = SelectionCriteria(
        name="Standard",
        criteria_json=json.dumps(criteria_rules),
        is_active=True,
    )
    db.add(criteria)
    db.commit()
    db.refresh(criteria)
    return criteria


@pytest.fixture()
def sample_grant(db: Session, sample_funder: Funder, sample_fiscal_sponsor: Funder) -> Grant:
    grant = Grant(
        title="Youth Workforce Initiative",
        funder_id=sample_funder.id,
        funder_name=sample_funder.name,
        fiscal_sponsor_id=sample_fiscal_sponsor.id,
        status=GrantStatus.DISCOVERED,
        deadline=date.today() + timedelta(days=45),
        amount_min=10000,
        amount_max=50000,
        focus_areas_json=json.dumps(["youth development", "workforce training"]),
        target_geography="Boston, MA",
        eligibility_501c3_required=False,
        fiscal_sponsorship_allowed=True,
    )
    db.add(grant)
    db.commit()
    db.refresh(grant)
    return grant


@pytest.fixture()
def sample_application(db: Session, sample_grant: Grant) -> Application:
    sample_grant.status = GrantStatus.APPROVED_TO_APPLY
    db.commit()
    application = Application(
        grant_id=sample_grant.id,
        status=ApplicationStatus.DRAFT,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@pytest.fixture()
def sample_application_fully_reviewed(
    db: Session, sample_application: Application
) -> Application:
    """
    Application with a current draft and all 4 review checklists in COMPLETED status
    with no blocking items. Ready for approve_application() to succeed.
    """
    # Create a draft
    draft = DraftVersion(
        application_id=sample_application.id,
        version_number=1,
        sections_json=json.dumps({"executive_summary": "We empower youth."}),
        word_count=5,
        is_current=True,
    )
    db.add(draft)
    db.flush()

    # Create 4 completed checklists with no critical items unchecked
    for rt in ReviewType:
        checklist = ReviewChecklist(
            application_id=sample_application.id,
            draft_version_id=draft.id,
            review_type=rt,
            status=ReviewStatus.COMPLETED,
            has_blocking_items=False,
            reviewer_name="Test Reviewer",
        )
        db.add(checklist)

    db.commit()
    db.refresh(sample_application)
    return sample_application
