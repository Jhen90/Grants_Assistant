# ============================================================
# File: src/services/report_service.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: ReportService — weekly snapshot generation, Jinja2 rendering, PDF export
# ============================================================

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from src.models.application import Application, ApplicationStatus
from src.models.grant import Grant, GrantStatus
from src.models.organization import Organization
from src.models.report import WeeklyReport
from src.utils.logger import get_logger

log = get_logger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "reports"


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


class ReportService:
    def generate_weekly_report(
        self, db: Session, week_start: date | None = None
    ) -> WeeklyReport:
        """
        Generate a WeeklyReport for the given week_start date (defaults to last Monday).
        If a report for that week already exists, it is overwritten with fresh data.
        """
        if week_start is None:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())  # Monday
        week_end = week_start + timedelta(days=6)

        org = db.query(Organization).filter_by(is_deleted=False).first()
        if org is None:
            raise ValueError("No organization found — run seed_data.py first.")

        snapshot = self._build_snapshot(db, org, week_start, week_end)
        markdown_content = self._render_markdown(snapshot)

        # Upsert by week_start + org_id
        existing = (
            db.query(WeeklyReport)
            .filter_by(org_id=org.id, week_start=week_start)
            .first()
        )
        if existing:
            existing.week_end = week_end
            existing.content_markdown = markdown_content
            existing.grants_evaluated = snapshot["grants_evaluated"]
            existing.grants_recommended = snapshot["grants_recommended"]
            existing.grants_in_progress = snapshot["grants_in_progress"]
            existing.grants_submitted = snapshot["grants_submitted"]
            report = existing
        else:
            report = WeeklyReport(
                org_id=org.id,
                week_start=week_start,
                week_end=week_end,
                content_markdown=markdown_content,
                grants_evaluated=snapshot["grants_evaluated"],
                grants_recommended=snapshot["grants_recommended"],
                grants_in_progress=snapshot["grants_in_progress"],
                grants_submitted=snapshot["grants_submitted"],
            )
            db.add(report)

        db.commit()
        db.refresh(report)
        log.info("Weekly report generated for week of %s.", week_start.isoformat())
        return report

    def export_markdown(self, db: Session, report_id: str) -> str:
        report = db.query(WeeklyReport).filter_by(id=report_id).first()
        if report is None:
            raise ValueError(f"Report {report_id!r} not found.")
        return report.content_markdown

    def export_pdf(self, db: Session, report_id: str, output_path: Path) -> Path:
        """Convert the report's Markdown to PDF via HTML using weasyprint."""
        try:
            from weasyprint import HTML
        except ImportError:
            raise ImportError(
                "weasyprint is not installed or its native dependencies are missing. "
                "Install via: conda install -c conda-forge weasyprint"
            )

        report = db.query(WeeklyReport).filter_by(id=report_id).first()
        if report is None:
            raise ValueError(f"Report {report_id!r} not found.")

        html_content = self._markdown_to_html(
            report.content_markdown,
            title=f"GrantNova Weekly Report — {report.week_start}",
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        HTML(string=html_content).write_pdf(str(output_path))
        log.info("PDF exported: %s", output_path)
        return output_path

    def get_all(self, db: Session, limit: int = 52) -> list[WeeklyReport]:
        return (
            db.query(WeeklyReport)
            .order_by(WeeklyReport.week_start.desc())
            .limit(limit)
            .all()
        )

    def get_by_id(self, db: Session, report_id: str) -> WeeklyReport | None:
        return db.query(WeeklyReport).filter_by(id=report_id).first()

    # ─── private helpers ───────────────────────────────────────────────────────

    def _build_snapshot(
        self, db: Session, org: Organization, week_start: date, week_end: date
    ) -> dict:
        """Collect all metrics for the report period."""
        all_grants = db.query(Grant).filter(Grant.is_deleted.is_(False)).all()
        all_apps = db.query(Application).filter(Application.is_deleted.is_(False)).all()

        # Status breakdowns
        status_counts: dict[str, int] = {}
        for grant in all_grants:
            key = grant.status.value
            status_counts[key] = status_counts.get(key, 0) + 1

        # Top scoring recommended grants (not yet applied)
        recommended = [
            g for g in all_grants if g.status == GrantStatus.RECOMMENDED
        ]
        recommended.sort(key=lambda g: g.fit_score or 0, reverse=True)
        top_recommended = recommended[:5]

        # Recent grant additions (created this week)
        new_grants = [
            g for g in all_grants
            if g.created_at and week_start <= g.created_at.date() <= week_end
        ]

        # Applications this week
        in_progress_apps = [
            a for a in all_apps
            if a.status not in (ApplicationStatus.AWARDED, ApplicationStatus.DECLINED,
                                ApplicationStatus.WITHDRAWN)
        ]

        submitted_this_week = [
            a for a in all_apps
            if a.submitted_at and week_start <= a.submitted_at.date() <= week_end
        ]

        awarded_total = [a for a in all_apps if a.status == ApplicationStatus.AWARDED]
        total_awarded_amount = sum(a.award_amount or 0 for a in awarded_total)

        # Deadline alerts (RED urgency only)
        urgent_grants = [
            g for g in all_grants
            if g.deadline_urgency and g.deadline_urgency.value == "RED"
            and g.status not in (GrantStatus.ARCHIVED, GrantStatus.SUBMITTED,
                                 GrantStatus.AWARDED, GrantStatus.DECLINED,
                                 GrantStatus.WITHDRAWN)
        ]

        try:
            programs_json = json.loads(org.programs_json or "[]")
        except json.JSONDecodeError:
            programs_json = []

        return {
            "org_name": org.name,
            "org_city": org.city,
            "org_state": org.state,
            "week_start": week_start.strftime("%B %d, %Y"),
            "week_end": week_end.strftime("%B %d, %Y"),
            "status_counts": status_counts,
            "grants_evaluated": status_counts.get("EVALUATED", 0),
            "grants_recommended": status_counts.get("RECOMMENDED", 0),
            "grants_in_progress": len(in_progress_apps),
            "grants_submitted": status_counts.get("SUBMITTED", 0),
            "total_grants": len(all_grants),
            "top_recommended": [
                {
                    "title": g.title,
                    "funder_name": g.funder_name or "Unknown",
                    "fit_score": round(g.fit_score or 0, 2),
                    "deadline": g.deadline.strftime("%Y-%m-%d") if g.deadline else "None",
                    "amount_max": g.amount_max,
                }
                for g in top_recommended
            ],
            "new_grants_this_week": [
                {"title": g.title, "funder_name": g.funder_name or "Unknown"}
                for g in new_grants
            ],
            "submitted_this_week": [
                {
                    "grant_title": a.grant.title if a.grant else "Unknown",
                    "submitted_at": a.submitted_at.strftime("%Y-%m-%d") if a.submitted_at else "?",
                }
                for a in submitted_this_week
            ],
            "urgent_grants": [
                {
                    "title": g.title,
                    "funder_name": g.funder_name or "Unknown",
                    "deadline": g.deadline.strftime("%Y-%m-%d") if g.deadline else "None",
                }
                for g in urgent_grants
            ],
            "total_awarded_amount": total_awarded_amount,
            "programs": programs_json,
        }

    def _render_markdown(self, snapshot: dict) -> str:
        """Render the weekly report Markdown using the Jinja2 template."""
        template_file = _TEMPLATES_DIR / "weekly_report.md.j2"
        if not template_file.exists():
            log.warning("Weekly report template not found — returning plain text fallback.")
            return self._plain_text_fallback(snapshot)

        env = _get_jinja_env()
        template = env.get_template("weekly_report.md.j2")
        return template.render(**snapshot)

    @staticmethod
    def _plain_text_fallback(snapshot: dict) -> str:
        lines = [
            f"# GrantNova Weekly Report",
            f"**Organization:** {snapshot['org_name']}",
            f"**Period:** {snapshot['week_start']} – {snapshot['week_end']}",
            "",
            "## Grant Pipeline",
            f"- Total grants tracked: {snapshot['total_grants']}",
            f"- Evaluated: {snapshot['grants_evaluated']}",
            f"- Recommended: {snapshot['grants_recommended']}",
            f"- In progress: {snapshot['grants_in_progress']}",
            f"- Submitted: {snapshot['grants_submitted']}",
            "",
            "## Urgent Deadlines (< 30 days)",
        ]
        for ug in snapshot.get("urgent_grants", []):
            lines.append(f"- {ug['title']} ({ug['funder_name']}) — {ug['deadline']}")
        if not snapshot.get("urgent_grants"):
            lines.append("- None")
        lines.append("")
        lines.append(f"## Total Awarded (all time): ${snapshot.get('total_awarded_amount', 0):,.0f}")
        return "\n".join(lines)

    @staticmethod
    def _markdown_to_html(markdown_text: str, title: str = "GrantNova Report") -> str:
        """Wrap Markdown in a minimal HTML page for weasyprint rendering."""
        try:
            import markdown as md_lib
            body = md_lib.markdown(markdown_text, extensions=["tables", "toc"])
        except ImportError:
            body = f"<pre>{markdown_text}</pre>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; font-size: 12pt; margin: 1.5in; }}
    h1 {{ font-size: 18pt; border-bottom: 2px solid #333; padding-bottom: 6px; }}
    h2 {{ font-size: 14pt; color: #444; margin-top: 18pt; }}
    table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
    th, td {{ border: 1px solid #bbb; padding: 6px 10px; text-align: left; }}
    th {{ background: #f0f0f0; }}
    @page {{ size: letter; margin: 1in; }}
  </style>
</head>
<body>
{body}
</body>
</html>"""
