# ============================================================
# File: src/app/components/review_status_panel.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Review status overview panel for the Applications page
# ============================================================

from __future__ import annotations

import streamlit as st

from src.models.review import ReviewChecklist, ReviewStatus, ReviewType


_STATUS_ICONS: dict[str, str] = {
    "PENDING":     "⏳",
    "IN_PROGRESS": "🔄",
    "COMPLETED":   "✅",
    "BLOCKED":     "🚫",
}


def render_review_status_panel(checklists: list[ReviewChecklist]) -> None:
    """
    Show a 4-tile summary of all review types and their completion status.
    Intended for the Applications page review tab header.
    """
    checklist_map = {c.review_type: c for c in checklists}
    all_types = list(ReviewType)

    cols = st.columns(len(all_types))
    for col, rt in zip(cols, all_types):
        checklist = checklist_map.get(rt)
        with col:
            if checklist is None:
                icon = "⬜"
                status_label = "Not Started"
                bg = "#F7FAFC"
                border = "#E2E8F0"
            else:
                icon = _STATUS_ICONS.get(checklist.status.value, "?")
                status_label = checklist.status.value.replace("_", " ").title()
                if checklist.status == ReviewStatus.COMPLETED:
                    bg, border = "#F0FFF4", "#68D391"
                elif checklist.status == ReviewStatus.BLOCKED:
                    bg, border = "#FFF5F5", "#FC8181"
                elif checklist.status == ReviewStatus.IN_PROGRESS:
                    bg, border = "#FFFBEB", "#F6E05E"
                else:
                    bg, border = "#F7FAFC", "#E2E8F0"

            st.markdown(
                f"""
<div style="background:{bg}; border:1px solid {border}; border-radius:8px;
            padding:10px 14px; text-align:center; margin-bottom:8px;">
  <div style="font-size:1.4rem;">{icon}</div>
  <div style="font-size:0.75rem; font-weight:700; color:#2c5282;">
    {rt.value.replace('_', ' ').title()}
  </div>
  <div style="font-size:0.7rem; color:#4a5568;">{status_label}</div>
</div>
""",
                unsafe_allow_html=True,
            )
