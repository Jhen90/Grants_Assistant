# ============================================================
# File: tests/integration/test_report_generation.py
# Version: 1.1.0
# Created: 2026-06-25
# Description: Integration test — report generation with real grant pipeline data
# ============================================================

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from src.models.grant import Grant, GrantStatus
from src.models.organization import Organization
from src.models.report import WeeklyReport
from src.services.grant_service import GrantService
from src.services.report_service import ReportService


@pytest.fixture()
def grant_svc() -> GrantService:
    return GrantService()


@pytest.fixture()
def report_svc() -> ReportService:
    return ReportService()


def test_report_reflects_pipeline_data(
    db: Session,
    grant_svc: GrantService,
    report_svc: ReportService,
    sample_org: Organization,
    sample_funder,
    sample_fiscal_sponsor,
    sample_criteria,
):
    """Report should capture current pipeline counts correctly."""
    # Add 2 grants
    grant_svc.create_grant(
        db,
        {
            # Distinct titles — near-identical titles from the same funder are
            # (correctly) flagged as duplicates by the dedup engine.
            "title": "Youth Mentorship Program Fund",
            "funder_id": sample_funder.id,
            "funder_name": sample_funder.name,
            "deadline": date.today() + timedelta(days=50),
            "eligibility_501c3_required": False,
            "fiscal_sponsorship_allowed": True,
            "focus_areas": ["youth development"],
        },
    )
    grant_svc.create_grant(
        db,
        {
            "title": "Affordable Housing Capital Initiative",
            "funder_id": sample_funder.id,
            "funder_name": sample_funder.name,
            "source_url": "http://unique-url-for-b.org/rfp",
            "deadline": date.today() + timedelta(days=20),
            "eligibility_501c3_required": False,
            "fiscal_sponsorship_allowed": True,
            "focus_areas": ["housing"],
        },
    )

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    report = report_svc.generate_weekly_report(db, week_start=week_start)

    assert report.org_id == sample_org.id
    assert report.grants_evaluated + report.grants_recommended >= 2
    assert "GrantNova" in report.content_markdown or "Report" in report.content_markdown


def test_markdown_export_contains_org_name(
    db: Session,
    report_svc: ReportService,
    sample_org: Organization,
):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    report = report_svc.generate_weekly_report(db, week_start=week_start)
    md = report_svc.export_markdown(db, report.id)
    assert sample_org.name in md
