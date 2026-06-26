# ============================================================
# File: src/app/components/grant_card.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Grant summary card for dashboard and list views
# ============================================================

from __future__ import annotations

import streamlit as st

from src.app.components.urgency_badge import urgency_badge_html
from src.engine.deadline_classifier import days_until_deadline
from src.models.grant import Grant


def render_grant_card(grant: Grant, on_select: bool = True) -> bool:
    """
    Render a compact grant summary card.
    Returns True if the user clicked 'View Details'.
    """
    score = grant.fit_score or 0.0
    score_color = "#276749" if score >= 7.0 else ("#b7791f" if score >= 5.0 else "#c53030")
    days_left = days_until_deadline(grant.deadline)

    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown(f"**{grant.title}**")
            funder = grant.funder_name or "Unknown Funder"
            deadline_str = (
                grant.deadline.strftime("%Y-%m-%d") if grant.deadline else "No deadline"
            )
            st.caption(f"{funder} · Deadline: {deadline_str}")
            st.markdown(urgency_badge_html(grant.deadline_urgency), unsafe_allow_html=True)

        with col2:
            st.markdown(
                f"<span style='font-size:1.4rem; font-weight:700; color:{score_color};'>"
                f"{score:.1f}</span><span style='color:#718096;'>/10</span>",
                unsafe_allow_html=True,
            )
            st.caption("Fit Score")

        with col3:
            status_label = grant.status.value.replace("_", " ").title()
            st.markdown(f"`{status_label}`")
            if days_left is not None:
                st.caption(f"{days_left}d remaining")

        if on_select:
            return st.button("View Details", key=f"grant_card_{grant.id}")
    return False
