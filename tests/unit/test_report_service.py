# ============================================================
# File: tests/unit/test_report_service.py
# Version: 1.1.0
# Created: 2026-06-25
# ============================================================

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from src.models.organization import Organization
from src.models.report import WeeklyReport
from src.services.report_service import ReportService


@pytest.fixture()
def svc() -> ReportService:
    return ReportService()


class TestGenerateWeeklyReport:
    def test_generates_report(
        self, db: Session, svc: ReportService, sample_org: Organization
    ):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        report = svc.generate_weekly_report(db, week_start=week_start)
        assert report.id is not None
        assert report.org_id == sample_org.id
        assert report.week_start == week_start

    def test_report_has_markdown_content(
        self, db: Session, svc: ReportService, sample_org: Organization
    ):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        report = svc.generate_weekly_report(db, week_start=week_start)
        assert len(report.content_markdown) > 0
        assert "GMAS" in report.content_markdown or "Report" in report.content_markdown

    def test_idempotent_generation(
        self, db: Session, svc: ReportService, sample_org: Organization
    ):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        r1 = svc.generate_weekly_report(db, week_start=week_start)
        r2 = svc.generate_weekly_report(db, week_start=week_start)
        assert r1.id == r2.id  # Same record, not a duplicate

    def test_raises_without_org(self, db: Session, svc: ReportService):
        with pytest.raises(ValueError, match="No organization found"):
            svc.generate_weekly_report(db, week_start=date.today())


class TestGetAll:
    def test_returns_list(
        self, db: Session, svc: ReportService, sample_org: Organization
    ):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        svc.generate_weekly_report(db, week_start=week_start)
        reports = svc.get_all(db)
        assert len(reports) >= 1
