# ============================================================
# File: src/app/pages/04_applications.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Applications — draft editor, document checklist, review pipeline, approval gate
# ============================================================

import json

import streamlit as st

from src.app.components.approval_gate import render_approval_gate
from src.app.components.review_status_panel import render_review_status_panel
from src.db.database import get_db
from src.models.application import Application, ApplicationStatus, DocumentRequirement
from src.models.draft import DraftVersion
from src.services.application_service import ApplicationService
from src.services.manifest_service import ManifestService
from src.services.review_service import ReviewService
from src.utils.error_handler import SubmissionBlockedError

st.set_page_config(page_title="Applications — GrantNova", page_icon="📝", layout="wide")

app_svc = ApplicationService()
review_svc = ReviewService()
manifest_svc = ManifestService()


def _render_application_list(db) -> Application | None:
    apps = (
        db.query(Application)
        .filter(Application.is_deleted.is_(False))
        .order_by(Application.created_at.desc())
        .all()
    )
    if not apps:
        st.info("No applications yet. Start one from the Grants page.")
        return None

    selected_id = st.session_state.get("selected_application_id")
    st.caption(f"{len(apps)} application(s)")

    for app in apps:
        grant_title = app.grant.title if app.grant else "Unknown Grant"
        label = f"{grant_title[:40]} — {app.status.value}"
        if st.button(label, key=f"applist_{app.id}", use_container_width=True):
            st.session_state["selected_application_id"] = app.id
            st.rerun()

    # Return selected application
    if selected_id:
        return app_svc.get_by_id(db, selected_id)
    return None


def _render_documents_tab(application: Application, db) -> None:
    st.subheader("Document Checklist")
    docs = (
        db.query(DocumentRequirement)
        .filter_by(application_id=application.id)
        .all()
    )
    if not docs:
        st.info("No document requirements defined.")
        return

    for doc in docs:
        col1, col2 = st.columns([5, 1])
        with col1:
            new_val = st.checkbox(
                doc.document_name + (" *(required)*" if doc.is_required else ""),
                value=doc.is_complete,
                key=f"doc_{doc.id}",
            )
        with col2:
            if new_val != doc.is_complete:
                doc.is_complete = new_val
                db.commit()
                st.rerun()

    complete_count = sum(1 for d in docs if d.is_complete)
    st.progress(complete_count / len(docs))
    st.caption(f"{complete_count}/{len(docs)} documents complete")

    # Add custom requirement
    with st.expander("Add Document Requirement"):
        new_doc_name = st.text_input("Document name", key="new_doc_name")
        if st.button("Add", key="add_doc_btn"):
            if new_doc_name.strip():
                db.add(DocumentRequirement(
                    application_id=application.id,
                    document_name=new_doc_name.strip(),
                    is_required=True,
                ))
                db.commit()
                st.success("Added.")
                st.rerun()


def _render_draft_editor_tab(application: Application, db) -> None:
    st.subheader("Draft Editor")

    # Current draft
    current_draft = (
        db.query(DraftVersion)
        .filter_by(application_id=application.id, is_current=True)
        .first()
    )
    existing_sections: dict = {}
    if current_draft:
        try:
            existing_sections = json.loads(current_draft.sections_json or "{}")
        except json.JSONDecodeError:
            pass
        st.caption(f"Current draft: v{current_draft.version_number} · {current_draft.word_count or 0} words")

    # Default section keys
    default_sections = [
        "executive_summary",
        "problem_statement",
        "proposed_solution",
        "program_description",
        "evaluation_plan",
        "budget_narrative",
        "organizational_capacity",
    ]

    sections: dict = {}
    for section in default_sections:
        label = section.replace("_", " ").title()
        sections[section] = st.text_area(
            label,
            value=existing_sections.get(section, ""),
            height=120,
            key=f"draft_{application.id}_{section}",
        )

    if st.button("💾 Save Draft Version", type="primary", key="save_draft_btn"):
        draft = app_svc.create_draft_version(db, application.id, sections)
        st.success(
            f"Saved as Draft v{draft.version_number} "
            f"({draft.word_count} words)"
        )
        st.rerun()

    # Version history
    all_versions = (
        db.query(DraftVersion)
        .filter_by(application_id=application.id)
        .order_by(DraftVersion.version_number.desc())
        .all()
    )
    if len(all_versions) > 1:
        with st.expander("Version History"):
            for v in all_versions:
                st.markdown(
                    f"**v{v.version_number}** — {v.word_count or 0} words "
                    f"{'✅ Current' if v.is_current else ''}"
                )


def _render_reviews_tab(application: Application, db) -> None:
    st.subheader("Review Checklists")

    current_draft = (
        db.query(DraftVersion)
        .filter_by(application_id=application.id, is_current=True)
        .first()
    )
    if current_draft is None:
        st.warning("Save a draft before starting reviews.")
        return

    checklists = review_svc.get_checklists_for_application(
        db, application.id, current_draft.id
    )

    if not checklists:
        if st.button("🚀 Initialize Review Checklists", type="primary"):
            review_svc.initialize_checklists(db, application.id, current_draft.id)
            db.commit()
            st.success("Review checklists created.")
            st.rerun()
        return

    render_review_status_panel(checklists)
    st.divider()

    from src.models.review import ChecklistItem, ReviewType, AssumptionRecord, AmbiguityRecord

    checklist_tabs = st.tabs([c.review_type.value.replace("_", " ").title() for c in checklists])
    for tab, checklist in zip(checklist_tabs, checklists):
        with tab:
            items = (
                db.query(ChecklistItem).filter_by(checklist_id=checklist.id).all()
            )
            for item in items:
                new_val = st.checkbox(
                    ("🔴 " if item.is_critical else "") + item.text,
                    value=item.is_checked,
                    key=f"ci_{item.id}",
                )
                if new_val != item.is_checked:
                    review_svc.update_checklist_item(db, item.id, new_val)
                    db.commit()
                    st.rerun()

            reviewer = st.text_input(
                "Reviewer name", key=f"reviewer_{checklist.id}"
            )
            if st.button("Mark Complete", key=f"complete_{checklist.id}"):
                if not reviewer.strip():
                    st.warning("Enter reviewer name.")
                else:
                    updated = review_svc.complete_checklist(db, checklist.id, reviewer.strip())
                    db.commit()
                    if updated.has_blocking_items:
                        st.error("Checklist is BLOCKED — resolve critical items first.")
                    else:
                        st.success("Checklist marked COMPLETED.")
                    st.rerun()

            # Assumption log (only for ASSUMPTION_LOG type)
            if checklist.review_type == ReviewType.ASSUMPTION_LOG:
                with st.expander("Log an Assumption"):
                    desc = st.text_input("Description", key=f"ass_desc_{checklist.id}")
                    basis = st.text_input("Basis / Source", key=f"ass_basis_{checklist.id}")
                    if st.button("Add Assumption", key=f"ass_add_{checklist.id}"):
                        review_svc.add_assumption(db, checklist.id, desc, basis)
                        db.commit()
                        st.success("Assumption logged.")
                        st.rerun()

            # Ambiguity log
            if checklist.review_type == ReviewType.AMBIGUITY_RESOLUTION:
                with st.expander("Log an Ambiguity"):
                    amb_desc = st.text_input("Ambiguity", key=f"amb_desc_{checklist.id}")
                    amb_res = st.text_input("Resolution", key=f"amb_res_{checklist.id}")
                    amb_dec = st.text_input("Decision made", key=f"amb_dec_{checklist.id}")
                    if st.button("Add Ambiguity", key=f"amb_add_{checklist.id}"):
                        review_svc.add_ambiguity(db, checklist.id, amb_desc, amb_res, amb_dec)
                        db.commit()
                        st.success("Ambiguity logged.")
                        st.rerun()


def _render_manifest_tab(application: Application, db) -> None:
    st.subheader("Application Manifest (Audit Log)")
    md = manifest_svc.export_markdown(db, application.id)
    st.markdown(md)


def _render_approval_tab(application: Application, db) -> None:
    st.subheader("Approval Gate")
    current_draft = (
        db.query(DraftVersion)
        .filter_by(application_id=application.id, is_current=True)
        .first()
    )
    checklists = review_svc.get_checklists_for_application(
        db, application.id, current_draft.id if current_draft else None
    )

    def handle_approve(approver_name: str) -> None:
        try:
            app_svc.approve_application(db, application.id, approver_name)
            st.success("✅ Application APPROVED and ready for submission!")
            st.rerun()
        except SubmissionBlockedError as e:
            st.error(f"Approval blocked: {e.reason}")
            for b in e.blockers:
                st.markdown(f"- {b}")

    render_approval_gate(checklists, has_draft=current_draft is not None, on_approve=handle_approve)

    if application.status == ApplicationStatus.APPROVED:
        st.divider()
        st.subheader("Record Submission")
        with st.form("record_submission_form"):
            method = st.selectbox(
                "Submission Method", ["Online Portal", "Email", "Mail", "Other"]
            )
            confirmation = st.text_input("Confirmation / Tracking Number")
            submitter = st.text_input("Submitted By")
            if st.form_submit_button("📤 Record Submission"):
                app_svc.record_submission(db, application.id, method, confirmation, submitter)
                st.success("Submission recorded!")
                st.rerun()

    if application.status == ApplicationStatus.SUBMITTED:
        st.divider()
        st.subheader("Record Outcome")
        with st.form("record_outcome_form"):
            outcome = st.selectbox("Outcome", ["AWARDED", "DECLINED", "WITHDRAWN"])
            award_amt = st.number_input("Award Amount ($)", min_value=0, step=1000, value=0)
            if st.form_submit_button("Record Outcome"):
                app_svc.record_outcome(
                    db, application.id, outcome, float(award_amt) if award_amt else None
                )
                st.success(f"Outcome recorded: {outcome}")
                st.rerun()


def main() -> None:
    st.title("📝 Applications")

    db_gen = get_db()
    db = next(db_gen)

    try:
        list_col, main_col = st.columns([1, 3])

        with list_col:
            application = _render_application_list(db)

        with main_col:
            if application is None:
                st.info("Select an application from the list.")
                return

            grant_title = application.grant.title if application.grant else "Unknown Grant"
            st.subheader(f"{grant_title}")
            st.caption(f"Status: **{application.status.value}** · ID: `{application.id}`")

            tab_names = ["Overview", "Documents", "Draft Editor", "Reviews", "Approval / Outcome", "Manifest"]
            overview_t, docs_t, draft_t, reviews_t, approval_t, manifest_t = st.tabs(tab_names)

            with overview_t:
                st.markdown(f"**Grant:** {grant_title}")
                st.markdown(f"**Status:** `{application.status.value}`")
                if application.submitted_at:
                    st.markdown(f"**Submitted:** {application.submitted_at.strftime('%Y-%m-%d')}")
                if application.award_amount:
                    st.markdown(f"**Award Amount:** ${application.award_amount:,.0f}")
                if application.approved_by:
                    st.markdown(f"**Approved by:** {application.approved_by}")

            with docs_t:
                _render_documents_tab(application, db)

            with draft_t:
                _render_draft_editor_tab(application, db)

            with reviews_t:
                _render_reviews_tab(application, db)

            with approval_t:
                _render_approval_tab(application, db)

            with manifest_t:
                _render_manifest_tab(application, db)

    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


main()
