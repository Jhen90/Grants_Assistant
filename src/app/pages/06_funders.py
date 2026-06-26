# ============================================================
# File: src/app/pages/06_funders.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Funders — directory, history, and CRUD management
# ============================================================

import streamlit as st

from src.db.database import get_db
from src.models.funder import Funder, FunderType
from src.services.funder_service import FunderService

st.set_page_config(page_title="Funders — GMAS", page_icon="🏛️", layout="wide")

funder_svc = FunderService()


def _render_funder_detail(funder: Funder, db) -> None:
    st.subheader(funder.name)

    info_col, history_col = st.columns(2)

    with info_col:
        st.markdown(f"**Type:** {funder.funder_type.value.replace('_', ' ').title()}")
        st.markdown(f"**Fiscal Sponsor:** {'Yes' if funder.is_fiscal_sponsor else 'No'}")
        st.markdown(f"**501(c)(3):** {'Yes' if funder.is_501c3 else 'No'}")
        if funder.website:
            st.markdown(f"**Website:** [{funder.website}]({funder.website})")
        if funder.contact_name:
            st.markdown(f"**Contact:** {funder.contact_name}")
        if funder.contact_email:
            st.markdown(f"**Email:** {funder.contact_email}")
        if funder.priority_tier is not None:
            st.markdown(f"**Priority Tier:** {funder.priority_tier}")
        if funder.relationship_notes:
            st.markdown(f"**Notes:** {funder.relationship_notes}")

    with history_col:
        st.subheader("Grant History")
        history = funder_svc.get_history(db, funder.id)
        h1, h2, h3 = st.columns(3)
        h1.metric("Grants Tracked", history["grants_count"])
        h2.metric("Awards Won", history["awarded_count"])
        h3.metric("Win Rate", f"{history['win_rate']}%")
        if history["total_awarded"] > 0:
            st.metric("Total Awarded", f"${history['total_awarded']:,.0f}")
        if history["total_requested"] > 0:
            st.metric("Total Requested", f"${history['total_requested']:,.0f}")

    st.divider()

    # Edit form
    with st.expander("Edit Funder"):
        with st.form(f"edit_funder_{funder.id}"):
            name = st.text_input("Name", value=funder.name)
            ftype = st.selectbox(
                "Type",
                [ft.value for ft in FunderType],
                index=[ft.value for ft in FunderType].index(funder.funder_type.value),
            )
            is_fs = st.checkbox("Fiscal Sponsor", value=funder.is_fiscal_sponsor)
            is_501 = st.checkbox("501(c)(3)", value=funder.is_501c3)
            website = st.text_input("Website", value=funder.website or "")
            contact_name = st.text_input("Contact Name", value=funder.contact_name or "")
            contact_email = st.text_input("Contact Email", value=funder.contact_email or "")
            priority_tier = st.number_input(
                "Priority Tier", min_value=1, max_value=5,
                value=funder.priority_tier or 3, step=1
            )
            rel_notes = st.text_area("Relationship Notes", value=funder.relationship_notes or "")
            if st.form_submit_button("Save Changes"):
                funder_svc.update(
                    db, funder.id,
                    {
                        "name": name,
                        "funder_type": ftype,
                        "is_fiscal_sponsor": is_fs,
                        "is_501c3": is_501,
                        "website": website or None,
                        "contact_name": contact_name or None,
                        "contact_email": contact_email or None,
                        "priority_tier": priority_tier,
                        "relationship_notes": rel_notes or None,
                    },
                )
                st.success("Funder updated.")
                st.rerun()

    with st.expander("Danger Zone"):
        if st.button("🗑️ Archive Funder", key=f"del_funder_{funder.id}"):
            funder_svc.soft_delete(db, funder.id)
            st.warning("Funder archived.")
            st.session_state.pop("selected_funder_id", None)
            st.rerun()


def main() -> None:
    st.title("🏛️ Funders")

    db_gen = get_db()
    db = next(db_gen)

    try:
        list_col, detail_col = st.columns([1, 2])

        with list_col:
            # Add new funder
            with st.expander("➕ Add New Funder"):
                with st.form("add_funder_form"):
                    new_name = st.text_input("Name *")
                    new_type = st.selectbox("Type", [ft.value for ft in FunderType])
                    new_is_fs = st.checkbox("Fiscal Sponsor")
                    new_is_501 = st.checkbox("501(c)(3)")
                    new_website = st.text_input("Website")
                    if st.form_submit_button("Add Funder"):
                        if new_name.strip():
                            funder_svc.create(
                                db,
                                {
                                    "name": new_name.strip(),
                                    "funder_type": new_type,
                                    "is_fiscal_sponsor": new_is_fs,
                                    "is_501c3": new_is_501,
                                    "website": new_website or None,
                                },
                            )
                            st.success(f"Funder '{new_name}' added.")
                            st.rerun()
                        else:
                            st.error("Name is required.")

            st.divider()
            funders = funder_svc.get_all(db)
            st.caption(f"{len(funders)} funders")

            search = st.text_input("Search", placeholder="Filter by name…", key="funder_search")
            if search:
                funders = [f for f in funders if search.lower() in f.name.lower()]

            for f in funders:
                tier_label = f"T{f.priority_tier}" if f.priority_tier else ""
                fs_badge = "🤝" if f.is_fiscal_sponsor else ""
                label = f"{fs_badge}{tier_label} {f.name}".strip()
                if st.button(label, key=f"flist_{f.id}", use_container_width=True):
                    st.session_state["selected_funder_id"] = f.id
                    st.rerun()

        with detail_col:
            selected_id = st.session_state.get("selected_funder_id")
            if selected_id:
                funder = funder_svc.get_by_id(db, selected_id)
                if funder:
                    _render_funder_detail(funder, db)
                else:
                    st.info("Select a funder from the list.")
            else:
                st.info("Select a funder from the list to view details.")

    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


main()
