# ============================================================
# File: src/app/pages/05_reports.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Reports — generate, view, and export weekly grant management reports
# ============================================================

from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from src.db.database import get_db
from src.services.report_service import ReportService
from src.utils.config import get_settings

st.set_page_config(page_title="Reports — GMAS", page_icon="📈", layout="wide")

report_svc = ReportService()
settings = get_settings()


def main() -> None:
    st.title("📈 Reports")

    db_gen = get_db()
    db = next(db_gen)

    try:
        col_list, col_view = st.columns([1, 3])

        with col_list:
            st.subheader("Generate Report")
            # Default to current week's Monday
            today = date.today()
            default_monday = today - timedelta(days=today.weekday())
            week_start = st.date_input(
                "Week Start (Monday)",
                value=default_monday,
                key="report_week_start",
            )
            if st.button("Generate Weekly Report", type="primary"):
                with st.spinner("Generating..."):
                    try:
                        report = report_svc.generate_weekly_report(db, week_start=week_start)
                        st.success(f"Report generated for week of {week_start}.")
                        st.session_state["selected_report_id"] = report.id
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

            st.divider()
            st.subheader("Past Reports")
            past_reports = report_svc.get_all(db, limit=52)
            for r in past_reports:
                label = f"{r.week_start} → {r.week_end}"
                if st.button(label, key=f"rlist_{r.id}", use_container_width=True):
                    st.session_state["selected_report_id"] = r.id
                    st.rerun()

        with col_view:
            selected_id = st.session_state.get("selected_report_id")
            if not selected_id:
                st.info("Generate or select a report to view it.")
                return

            report = report_svc.get_by_id(db, selected_id)
            if report is None:
                st.error("Report not found.")
                return

            st.subheader(f"Weekly Report — {report.week_start} to {report.week_end}")
            st.caption(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M')}")

            # ── Export buttons ───────────────────────────────────────────────
            export_col1, export_col2 = st.columns(2)
            with export_col1:
                md_content = report_svc.export_markdown(db, report.id)
                st.download_button(
                    label="📄 Download Markdown",
                    data=md_content,
                    file_name=f"gmas_report_{report.week_start}.md",
                    mime="text/markdown",
                    key="dl_md",
                )
            with export_col2:
                if st.button("🖨️ Export PDF", key="export_pdf_btn"):
                    pdf_path = (
                        Path(settings.export_dir)
                        / f"gmas_report_{report.week_start}.pdf"
                    )
                    try:
                        report_svc.export_pdf(db, report.id, pdf_path)
                        st.success(f"PDF saved to: `{pdf_path}`")
                    except ImportError as e:
                        st.warning(str(e))
                    except Exception as e:
                        st.error(f"PDF export failed: {e}")

            st.divider()

            # ── KPI summary ──────────────────────────────────────────────────
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Evaluated", report.grants_evaluated)
            k2.metric("Recommended", report.grants_recommended)
            k3.metric("In Progress", report.grants_in_progress)
            k4.metric("Submitted", report.grants_submitted)

            st.divider()

            # ── Rendered Markdown ────────────────────────────────────────────
            st.markdown(report.content_markdown)

    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


main()
