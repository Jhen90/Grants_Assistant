# ============================================================
# File: src/app/pages/08_settings.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Settings — org profile, DB info, re-seed, re-score controls
# ============================================================

from pathlib import Path

import streamlit as st

from src.db.database import backup_db, get_db, init_db
from src.models.organization import Organization
from src.models.selection_criteria import SelectionCriteria
from src.services.grant_service import GrantService
from src.utils.config import get_settings

st.set_page_config(page_title="Settings — GrantNova", page_icon="⚙️", layout="wide")

settings = get_settings()
grant_svc = GrantService()


def main() -> None:
    st.title("⚙️ Settings")

    db_gen = get_db()
    db = next(db_gen)

    try:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Organization Profile")
            org = db.query(Organization).filter_by(is_deleted=False).first()
            if org:
                st.markdown(f"**Name:** {org.name}")
                st.markdown(f"**Mission:** {org.mission or '—'}")
                st.markdown(f"**City, State:** {org.city}, {org.state}")
                st.markdown(f"**EIN:** {org.ein or '—'}")
                st.markdown(f"**501(c)(3):** {'Yes' if org.is_501c3 else 'No'}")
                st.caption(f"Org ID: `{org.id}`")
            else:
                st.warning("No organization found. Run `python -m src.db.seed_data` to seed.")

            st.divider()
            st.subheader("Active Selection Criteria")
            criteria = db.query(SelectionCriteria).filter_by(is_active=True).first()
            if criteria:
                st.markdown(f"**Name:** {criteria.name}")
                import json
                try:
                    clist = json.loads(criteria.criteria_json or "[]")
                    st.caption(f"{len(clist)} criteria rules active")
                    with st.expander("View Criteria"):
                        for c in clist:
                            st.markdown(
                                f"- **{c.get('name', '?')}** "
                                f"(weight={c.get('weight', 1)}, "
                                f"type={c.get('type', '?')})"
                            )
                except json.JSONDecodeError:
                    st.error("Could not parse criteria JSON.")
            else:
                st.warning("No active selection criteria. Run seed_data.py.")

        with col2:
            st.subheader("Application Settings")
            st.markdown(f"**App Version:** `{settings.app_version}`")
            st.markdown(f"**Recommendation Threshold:** `{settings.recommendation_threshold}`")
            st.markdown(f"**Dedup Fuzzy Threshold:** `{settings.dedup_fuzzy_threshold}`")
            st.markdown(f"**Database URL:** `{settings.database_url}`")
            st.markdown(f"**Log Level:** `{settings.log_level}`")
            st.markdown(f"**Export Directory:** `{settings.export_dir}`")

            st.divider()
            st.subheader("Database Operations")

            if st.button("🔄 Re-score All Grants"):
                with st.spinner("Re-scoring..."):
                    count = grant_svc.re_score_all(db)
                st.success(f"Re-scored {count} grants.")

            if st.button("💾 Backup Database"):
                try:
                    path = backup_db()
                    if path:
                        st.success(f"Backup saved to: `{path}`")
                    else:
                        st.info("Backup skipped (non-SQLite database).")
                except Exception as e:
                    st.error(f"Backup failed: {e}")

            st.divider()
            st.subheader("Seed Data")
            st.caption(
                "Run from the terminal to seed the database with org profile, "
                "funders, and templates:\n\n"
                "```bash\nconda activate gmas\npython -m src.db.seed_data\n```"
            )
            st.markdown(
                "To use a custom org profile:\n\n"
                "```bash\npython -m src.db.seed_data --profile path/to/profile.md\n```"
            )

            st.divider()
            st.subheader("Environment Info")
            st.markdown(
                f"- Ollama integration: "
                f"{'**Enabled**' if settings.ollama_enabled else 'Disabled'}\n"
                f"- Google Docs integration: "
                f"{'**Enabled**' if settings.google_docs_enabled else 'Disabled'}"
            )

    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


main()
