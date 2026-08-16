# ============================================================
# File: tests/unit/test_grant_service.py
# Version: 1.1.0
# Created: 2026-06-25
# ============================================================

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from src.models.grant import Grant, GrantStatus
from src.models.funder import Funder
from src.services.grant_service import GrantService
from src.utils.error_handler import DuplicateGrantError

# Fixtures: db, sample_org, sample_funder, sample_criteria inherited from conftest.py


@pytest.fixture()
def svc() -> GrantService:
    return GrantService()


@pytest.fixture()
def grant_data(sample_funder: Funder) -> dict:
    return {
        "title": "Youth Education Fund 2026",
        "funder_id": sample_funder.id,
        "funder_name": sample_funder.name,
        "deadline": date.today() + timedelta(days=50),
        "amount_min": 10000,
        "amount_max": 30000,
        "target_geography": "Boston, MA",
        "eligibility_501c3_required": False,
        "fiscal_sponsorship_allowed": True,
        "focus_areas": ["youth development"],
        "source_url": "https://test-foundation.org/rfp/2026",
    }


class TestCreateGrant:
    def test_creates_grant_with_evaluated_status(
        self, db: Session, svc: GrantService, grant_data: dict, sample_org, sample_criteria
    ):
        grant = svc.create_grant(db, grant_data)
        assert grant.id is not None
        assert grant.status in (GrantStatus.EVALUATED, GrantStatus.RECOMMENDED)

    def test_grant_gets_fit_score(
        self, db: Session, svc: GrantService, grant_data: dict, sample_org, sample_criteria
    ):
        grant = svc.create_grant(db, grant_data)
        assert grant.fit_score is not None
        assert 0.0 <= grant.fit_score <= 10.0

    def test_grant_gets_deadline_urgency(
        self, db: Session, svc: GrantService, grant_data: dict, sample_org, sample_criteria
    ):
        grant = svc.create_grant(db, grant_data)
        assert grant.deadline_urgency is not None

    def test_duplicate_url_raises(
        self, db: Session, svc: GrantService, grant_data: dict, sample_org, sample_criteria
    ):
        svc.create_grant(db, grant_data)
        with pytest.raises(DuplicateGrantError):
            svc.create_grant(db, grant_data)


class TestGetGrantsPaginated:
    def test_returns_page_object(
        self, db: Session, svc: GrantService, grant_data: dict, sample_org, sample_criteria
    ):
        svc.create_grant(db, grant_data)
        page = svc.get_grants_paginated(db)
        assert page.total >= 1
        assert len(page.items) >= 1

    def test_search_filter(
        self, db: Session, svc: GrantService, grant_data: dict, sample_org, sample_criteria
    ):
        svc.create_grant(db, grant_data)
        page = svc.get_grants_paginated(db, filters={"search": "Youth Education"})
        assert page.total >= 1

    def test_search_no_results(
        self, db: Session, svc: GrantService, grant_data: dict, sample_org, sample_criteria
    ):
        svc.create_grant(db, grant_data)
        page = svc.get_grants_paginated(db, filters={"search": "XYZNONEXISTENT"})
        assert page.total == 0


class TestAdvanceStatus:
    def test_advance_status(
        self, db: Session, svc: GrantService, sample_grant: Grant
    ):
        sample_grant.status = GrantStatus.EVALUATED
        db.commit()
        updated = svc.advance_status(db, sample_grant.id, GrantStatus.RECOMMENDED)
        assert updated.status == GrantStatus.RECOMMENDED


class TestSoftDelete:
    def test_soft_delete_hides_grant(
        self, db: Session, svc: GrantService, sample_grant: Grant
    ):
        svc.soft_delete(db, sample_grant.id)
        result = svc.get_by_id(db, sample_grant.id)
        assert result is None

    def test_soft_delete_sets_is_deleted(
        self, db: Session, svc: GrantService, sample_grant: Grant
    ):
        svc.soft_delete(db, sample_grant.id)
        raw = db.query(Grant).filter_by(id=sample_grant.id).first()
        assert raw is not None
        assert raw.is_deleted is True
