# ============================================================
# File: src/app/components/approval_gate.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Approval gate UI panel — shows pass/block status before approve button
# ============================================================

from __future__ import annotations

import streamlit as st

from src.models.review import ReviewChecklist, ReviewStatus, ReviewType
from src.utils.error_handler import SubmissionBlockedError


def render_approval_gate(
    checklists: list[ReviewChecklist],
    has_draft: bool,
    on_approve: "callable[[str], None]",
) -> None:
    """
    Render the approval gate panel.
    - Shows a green "Ready to Approve" section if all checks pass.
    - Shows a red "Blocked" section with specific blockers otherwise.
    - If ready, renders an approver name input and "Approve Application" button.
    - on_approve(approver_name) is called when the button is clicked.
    """
    blockers: list[str] = []

    if not has_draft:
        blockers.append("No draft version saved yet.")

    checklist_map = {c.review_type: c for c in checklists}
    for rt in ReviewType:
        checklist = checklist_map.get(rt)
        if checklist is None:
            blockers.append(f"{rt.value.replace('_', ' ').title()} review not started.")
            continue
        if checklist.status != ReviewStatus.COMPLETED:
            blockers.append(
                f"{rt.value.replace('_', ' ').title()} review "
                f"is {checklist.status.value.replace('_', ' ').lower()} — must be COMPLETED."
            )
        if checklist.has_blocking_items:
            blockers.append(
                f"{rt.value.replace('_', ' ').title()} review has unchecked critical items."
            )

    if blockers:
        st.markdown(
            '<div class="gate-blocked"><strong>⛔ Approval Blocked</strong></div>',
            unsafe_allow_html=True,
        )
        st.error("The following items must be resolved before this application can be approved:")
        for b in blockers:
            st.markdown(f"- {b}")
    else:
        st.markdown(
            '<div class="gate-passed"><strong>✅ All Reviews Complete — Ready to Approve</strong></div>',
            unsafe_allow_html=True,
        )
        approver_name = st.text_input(
            "Approver name",
            placeholder="Your name",
            key="approval_gate_approver_name",
        )
        if st.button("✅ Approve Application", type="primary", key="approval_gate_btn"):
            if not approver_name.strip():
                st.warning("Please enter your name before approving.")
            else:
                on_approve(approver_name.strip())
