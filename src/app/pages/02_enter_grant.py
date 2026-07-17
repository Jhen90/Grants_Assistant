# ============================================================
# File: src/app/pages/02_enter_grant.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Enter Grant — form to add a new grant opportunity with scoring on save
# ============================================================

from datetime import date

import streamlit as st

from src.db.database import get_db
from src.models.funder import Funder, FunderType
from src.services.funder_service import FunderService
from src.services.grant_service import GrantService
from src.utils.error_handler import DuplicateGrantError

st.set_page_config(page_title="Enter Grant — GrantNova", page_icon="📥", layout="wide")

grant_svc = GrantService()
funder_svc = FunderService()


def main() -> None:
    st.title("📥 Enter New Grant Opportunity")
    st.caption(
        "Fill in the fields below and click **Save Grant**. "
        "The system will score it automatically and advance it to EVALUATED or RECOMMENDED."
    )

    db_gen = get_db()
    db = next(db_gen)

    try:
        funders = funder_svc.get_all(db)
        fiscal_sponsors = funder_svc.get_fiscal_sponsors(db)

        funder_options = {f"{f.name} ({f.funder_type.value})": f.id for f in funders}
        funder_options_with_none = {"— Select or type new funder —": None, **funder_options}

        sponsor_options = {f.name: f.id for f in fiscal_sponsors}
        sponsor_options_with_none = {"— None (direct 501c3) —": None, **sponsor_options}

        with st.form("enter_grant_form", clear_on_submit=False):
            st.subheader("Grant Information")

            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input(
                    "Grant Title *",
                    placeholder="e.g., Youth Workforce Development Initiative",
                )
                source_url = st.text_input(
                    "Grant Source URL",
                    placeholder="https://funder.org/grants/rfp-2026",
                )
                funder_selection = st.selectbox(
                    "Funder (existing)", list(funder_options_with_none.keys()), index=0
                )
                new_funder_name = st.text_input(
                    "— OR — New Funder Name",
                    placeholder="Leave blank if selecting an existing funder above",
                )
                new_funder_type = st.selectbox(
                    "New Funder Type",
                    [ft.value for ft in FunderType],
                    index=0,
                )

            with col2:
                deadline = st.date_input(
                    "Application Deadline",
                    value=None,
                    min_value=date.today(),
                )
                amount_min = st.number_input(
                    "Minimum Award ($)", min_value=0, step=1000, value=0
                )
                amount_max = st.number_input(
                    "Maximum Award ($)", min_value=0, step=1000, value=0
                )
                target_geography = st.text_input(
                    "Target Geography",
                    placeholder="e.g., Boston MA, Massachusetts, National",
                )

            st.subheader("Eligibility & Focus")
            col3, col4 = st.columns(2)
            with col3:
                eligibility_501c3_required = st.checkbox(
                    "Requires 501(c)(3) status", value=False
                )
                fiscal_sponsorship_allowed = st.checkbox(
                    "Accepts Fiscal Sponsorship", value=True
                )
                fiscal_sponsor_selection = st.selectbox(
                    "Fiscal Sponsor (if applicable)",
                    list(sponsor_options_with_none.keys()),
                    index=0,
                )

            with col4:
                focus_areas_input = st.text_area(
                    "Focus Areas (one per line)",
                    placeholder="youth development\nworkforce training\ncommunity engagement",
                    height=120,
                )

            notes = st.text_area(
                "Internal Notes",
                placeholder="Context about this grant, where you found it, etc.",
                height=80,
            )

            submitted = st.form_submit_button("💾 Save Grant", type="primary")

        if submitted:
            if not title.strip():
                st.error("Grant title is required.")
                st.stop()

            # Resolve funder
            funder_id: str | None = funder_options_with_none.get(funder_selection)
            funder_name: str | None = None

            if funder_id is None and new_funder_name.strip():
                # Create new funder on the fly
                new_f = funder_svc.create(
                    db,
                    {
                        "name": new_funder_name.strip(),
                        "funder_type": new_funder_type,
                        "is_fiscal_sponsor": False,
                        "is_501c3": False,
                    },
                )
                funder_id = new_f.id
                funder_name = new_f.name
            elif funder_id:
                chosen_funder = funder_svc.get_by_id(db, funder_id)
                funder_name = chosen_funder.name if chosen_funder else None

            focus_areas = [
                line.strip()
                for line in focus_areas_input.splitlines()
                if line.strip()
            ]

            fiscal_sponsor_id = sponsor_options_with_none.get(fiscal_sponsor_selection)

            data = {
                "title": title.strip(),
                "funder_id": funder_id,
                "funder_name": funder_name or new_funder_name.strip() or None,
                "fiscal_sponsor_id": fiscal_sponsor_id,
                "source_url": source_url.strip() or None,
                "deadline": deadline,
                "amount_min": amount_min or None,
                "amount_max": amount_max or None,
                "target_geography": target_geography.strip() or None,
                "eligibility_501c3_required": eligibility_501c3_required,
                "fiscal_sponsorship_allowed": fiscal_sponsorship_allowed,
                "focus_areas": focus_areas,
                "notes": notes.strip() or None,
            }

            try:
                grant = grant_svc.create_grant(db, data)
                st.success(
                    f"✅ **{grant.title}** saved! "
                    f"Fit Score: **{grant.fit_score:.2f}/10** · "
                    f"Status: **{grant.status.value}**"
                )
                st.balloons()
                if st.button("View Grant Details →"):
                    st.session_state["selected_grant_id"] = grant.id
                    st.switch_page("pages/03_grants.py")

            except DuplicateGrantError as e:
                st.warning(
                    f"⚠️ Possible duplicate detected! "
                    f"Match type: **{e.match_type}** on field **{e.match_field}**. "
                    f"Existing grant ID: `{e.existing_id}`. "
                    "Review the existing grant before saving again."
                )
            except Exception as e:
                st.error(f"Error saving grant: {e}")

    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


main()
