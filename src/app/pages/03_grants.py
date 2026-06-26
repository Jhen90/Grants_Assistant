# ============================================================
# File: src/app/pages/03_grants.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Grants — searchable, filterable grant list with detail drawer
# ============================================================

import json
from datetime import date

import streamlit as st

from src.app.components.score_breakdown import render_score_breakdown
from src.app.components.urgency_badge import urgency_badge_html
from src.db.database import get_db
from src.models.grant import Grant, GrantStatus
from src.services.application_service import ApplicationService
from src.services.funder_service import FunderService
from src.services.grant_service import GrantService
from src.utils.error_handler import InvalidStatusTransitionError

st.set_page_config(page_title="Grants — GMAS", page_icon="📋", layout="wide")

grant_svc = GrantService()
funder_svc = FunderService()
app_svc = ApplicationService()


def _render_grant_detail(grant: Grant, db) -> None:
    """Right-panel detail view for a selected grant."""
    st.subheader(grant.title)
    col1, col2, col3 = st.columns(3)
    col1.markdown(urgency_badge_html(grant.deadline_urgency), unsafe_allow_html=True)
    col2.markdown(f"**Status:** `{grant.status.value}`")
    col3.markdown(
        f"**Deadline:** {grant.deadline.strftime('%Y-%m-%d') if grant.deadline else 'None'}"
    )

    render_score_breakdown(grant.fit_score, grant.score_breakdown_json)

    with st.expander("Grant Details", expanded=True):
        d1, d2 = st.columns(2)
        d1.markdown(f"**Funder:** {grant.funder_name or '—'}")
        d1.markdown(
            f"**Amount:** "
            f"${grant.amount_min or 0:,.0f} – ${grant.amount_max or 0:,.0f}"
            if (grant.amount_min or grant.amount_max)
            else "**Amount:** Not specified"
        )
        d1.markdown(f"**Geography:** {grant.target_geography or '—'}")
        d2.markdown(f"**501c3 Required:** {'Yes' if grant.eligibility_501c3_required else 'No'}")
        d2.markdown(f"**Fiscal Sponsorship OK:** {'Yes' if grant.fiscal_sponsorship_allowed else 'No'}")
        if grant.source_url:
            d2.markdown(f"**Source:** [{grant.source_url}]({grant.source_url})")

        focus_areas: list = []
        if grant.focus_areas_json:
            try:
                focus_areas = json.loads(grant.focus_areas_json)
            except json.JSONDecodeError:
                pass
        if focus_areas:
            st.markdown("**Focus Areas:** " + ", ".join(focus_areas))

        if grant.notes:
            st.markdown(f"**Notes:** {grant.notes}")

    st.divider()

    # ── Status transition controls ───────────────────────────────────────────
    from src.models.grant import VALID_TRANSITIONS
    valid_next = VALID_TRANSITIONS.get(grant.status.value, [])
    if valid_next:
        st.subheader("Advance Status")
        new_status_str = st.selectbox(
            "Move to", valid_next, key=f"status_select_{grant.id}"
        )
        if st.button("Advance Status", key=f"advance_{grant.id}"):
            try:
                updated = grant_svc.advance_status(db, grant.id, GrantStatus(new_status_str))
                st.success(f"Status advanced to **{updated.status.value}**.")
                st.rerun()
            except InvalidStatusTransitionError as e:
                st.error(str(e))

    # ── Start Application ────────────────────────────────────────────────────
    if grant.status == GrantStatus.RECOMMENDED:
        st.divider()
        if st.button("🚀 Start Application", type="primary", key=f"start_app_{grant.id}"):
            app = app_svc.create_application(db, grant.id)
            st.success(f"Application created! ID: `{app.id}`")
            st.session_state["selected_application_id"] = app.id
            st.switch_page("pages/04_applications.py")

    # ── Soft delete ──────────────────────────────────────────────────────────
    st.divider()
    with st.expander("Danger Zone"):
        if st.button("🗑️ Archive Grant (soft delete)", key=f"delete_{grant.id}"):
            grant_svc.soft_delete(db, grant.id)
            st.warning("Grant archived.")
            st.session_state.pop("selected_grant_id", None)
            st.rerun()


def main() -> None:
    st.title("📋 Grants")

    db_gen = get_db()
    db = next(db_gen)

    try:
        # ── Filters sidebar ──────────────────────────────────────────────────
        with st.sidebar:
            st.subheader("Filters")
            search_term = st.text_input("Search title", "")
            status_filter = st.multiselect(
                "Status",
                [s.value for s in GrantStatus],
                default=[],
            )
            min_score = st.slider("Min Fit Score", 0.0, 10.0, 0.0, 0.5)
            if st.button("Re-score All Grants"):
                count = grant_svc.re_score_all(db)
                st.success(f"Re-scored {count} grants.")
                st.rerun()

        # ── Build filters dict ───────────────────────────────────────────────
        filters: dict = {}
        if search_term:
            filters["search"] = search_term
        if status_filter:
            filters["status"] = GrantStatus(status_filter[0]) if len(status_filter) == 1 else None
        if min_score > 0:
            filters["min_score"] = min_score

        # ── Paginated list ───────────────────────────────────────────────────
        page_num = st.session_state.get("grants_page", 1)
        result = grant_svc.get_grants_paginated(db, filters=filters, page=page_num, page_size=20)

        list_col, detail_col = st.columns([1, 2])

        with list_col:
            st.caption(f"Showing {len(result.items)} of {result.total} grants")

            for grant in result.items:
                score = grant.fit_score or 0.0
                score_color = "#276749" if score >= 7 else ("#b7791f" if score >= 5 else "#c53030")
                selected = st.session_state.get("selected_grant_id") == grant.id

                with st.container(border=True):
                    row1, row2 = st.columns([4, 1])
                    with row1:
                        if st.button(
                            grant.title,
                            key=f"glist_{grant.id}",
                            use_container_width=True,
                        ):
                            st.session_state["selected_grant_id"] = grant.id
                    with row2:
                        st.markdown(
                            f"<span style='color:{score_color};font-weight:700'>"
                            f"{score:.1f}</span>",
                            unsafe_allow_html=True,
                        )

            # Pagination
            pcol1, pcol2, pcol3 = st.columns(3)
            if pcol1.button("← Prev", disabled=page_num <= 1):
                st.session_state["grants_page"] = page_num - 1
                st.rerun()
            pcol2.caption(f"Page {result.page} / {result.total_pages}")
            if pcol3.button("Next →", disabled=page_num >= result.total_pages):
                st.session_state["grants_page"] = page_num + 1
                st.rerun()

        with detail_col:
            selected_id = st.session_state.get("selected_grant_id")
            if selected_id:
                grant = grant_svc.get_by_id(db, selected_id)
                if grant:
                    _render_grant_detail(grant, db)
                else:
                    st.info("Select a grant from the list.")
            else:
                st.info("Select a grant from the list to view details.")

    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


main()
