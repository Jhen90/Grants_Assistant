# ============================================================
# File: src/app/pages/09_discover.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: Grant Scout — hunt/gather grant opportunities, review the ranked
#   evaluated queue (green = strong eligible match), read the weekly intelligence
#   digest, and import (human-confirmed) into the grant pipeline.
# ============================================================

import json
from datetime import date

import streamlit as st

from src.db.database import get_db
from src.models.discovered_candidate import CandidateStatus, EligibilityStatus
from src.services.discovery_service import DiscoveryService
from src.services.scout_report_service import ScoutReportService
from src.utils.config import get_settings
from src.utils.error_handler import DuplicateGrantError

st.set_page_config(page_title="Grant Scout — GrantNova", page_icon="🛰️", layout="wide")

svc = DiscoveryService()
report_svc = ScoutReportService()
settings = get_settings()


def _queue_label(c) -> str:
    """One-line queue label: green flag for strong eligible matches, fit, urgency."""
    flag = "🟢" if c.is_strong_match else ("🟡" if c.eligibility_status == EligibilityStatus.ELIGIBLE else "⚪")
    fit = f"{c.fit_score:.1f}" if c.fit_score is not None else "—"
    act = " ⏰" if c.act_now else ""
    return f"{flag}{act}  {c.raw_title[:52]}  ·  fit {fit}  ·  {c.source}"


def _confidence_flag(conf: float | None) -> str:
    if conf is None:
        return "⚪"
    if conf >= 0.75:
        return "🟢"
    if conf >= 0.5:
        return "🟡"
    return "🔴"


def _render_import_form(cand, db) -> None:
    """Pre-filled, human-editable form. Nothing saves until the user confirms."""
    try:
        payload = json.loads(cand.extracted_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    extracted = payload.get("extracted", {})
    conf = payload.get("field_confidence", {})
    evidence = payload.get("evidence", {})

    st.markdown(f"#### Review & Import — {cand.raw_title}")
    st.caption(f"Source: **{cand.source}** · {cand.source_url or 'no URL'}")

    if cand.status == CandidateStatus.DUPLICATE:
        st.warning(f"⚠️ Possible duplicate — {cand.dedup_note}")

    with st.form(f"import_{cand.id}"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input(
                f"{_confidence_flag(conf.get('title'))} Title",
                value=extracted.get("title", cand.raw_title) or "",
            )
            funder_name = st.text_input(
                f"{_confidence_flag(conf.get('funder_name'))} Funder",
                value=extracted.get("funder_name", cand.raw_funder) or "",
            )
            deadline_str = extracted.get("deadline") or ""
            deadline_val = None
            if isinstance(deadline_str, str) and deadline_str:
                try:
                    deadline_val = date.fromisoformat(deadline_str)
                except ValueError:
                    deadline_val = None
            deadline = st.date_input(
                f"{_confidence_flag(conf.get('deadline'))} Deadline",
                value=deadline_val,
            )
            target_geography = st.text_input(
                f"{_confidence_flag(conf.get('target_geography'))} Target Geography",
                value=extracted.get("target_geography", "") or "",
            )
        with col2:
            amount_min = st.number_input(
                f"{_confidence_flag(conf.get('amount_min'))} Amount Min ($)",
                min_value=0.0,
                value=float(extracted.get("amount_min") or 0),
                step=1000.0,
            )
            amount_max = st.number_input(
                f"{_confidence_flag(conf.get('amount_max'))} Amount Max ($)",
                min_value=0.0,
                value=float(extracted.get("amount_max") or 0),
                step=1000.0,
            )
            req_501c3 = st.checkbox(
                f"{_confidence_flag(conf.get('eligibility_501c3_required'))} Requires 501(c)(3)",
                value=bool(extracted.get("eligibility_501c3_required", False)),
            )
            fs_allowed = st.checkbox(
                f"{_confidence_flag(conf.get('fiscal_sponsorship_allowed'))} Fiscal Sponsorship Allowed",
                value=bool(extracted.get("fiscal_sponsorship_allowed", True)),
            )

        focus_default = "\n".join(extracted.get("focus_areas", []) or [])
        focus_text = st.text_area(
            f"{_confidence_flag(conf.get('focus_areas'))} Focus Areas (one per line)",
            value=focus_default,
            height=90,
        )

        c1, c2 = st.columns(2)
        do_import = c1.form_submit_button("✅ Import as Grant", type="primary")
        do_dismiss = c2.form_submit_button("🗑️ Dismiss")

    if evidence:
        with st.expander("Extraction evidence (where each value came from)"):
            for field_name, snippet in evidence.items():
                st.markdown(f"**{field_name}:** {snippet}")

    if cand.raw_text_excerpt:
        with st.expander("Raw page excerpt"):
            st.text(cand.raw_text_excerpt)

    if do_dismiss:
        svc.dismiss_candidate(db, cand.id)
        st.success("Candidate dismissed.")
        st.rerun()

    if do_import:
        overrides = {
            "title": title.strip(),
            "funder_name": funder_name.strip() or None,
            "deadline": deadline,
            "amount_min": amount_min or None,
            "amount_max": amount_max or None,
            "target_geography": target_geography.strip() or None,
            "eligibility_501c3_required": req_501c3,
            "fiscal_sponsorship_allowed": fs_allowed,
            "focus_areas": [ln.strip() for ln in focus_text.splitlines() if ln.strip()],
            "source_url": cand.source_url,
        }
        try:
            grant = svc.import_candidate(db, cand.id, overrides=overrides)
            st.success(
                f"✅ Imported **{grant.title}** — scored {grant.fit_score:.1f}/10, "
                f"status {grant.status.value}."
            )
            st.balloons()
            st.rerun()
        except DuplicateGrantError as e:
            st.error(
                f"Not imported — duplicate ({e.match_type} on {e.match_field}). "
                f"Existing grant: {e.existing_id}"
            )
            st.rerun()


def main() -> None:
    st.title("🛰️ Grant Scout")
    st.caption(
        "Hunt, gather, evaluate, and report on grant opportunities. Every result is "
        "scored and staged for your review — nothing becomes a tracked grant until you "
        "confirm it. 🟢 = strong eligible match, ⏰ = act now (closing soon)."
    )

    db_gen = get_db()
    db = next(db_gen)

    try:
        search_tab, review_tab, report_tab, url_tab, csv_tab = st.tabs(
            ["🔍 Search", "📋 Review Queue", "📊 Report", "🔗 Scrape URL", "📄 Instrumentl CSV"]
        )

        # ── Search tab ───────────────────────────────────────────────────────
        with search_tab:
            st.subheader("Run a Search")
            default_q = "youth development STEM grant Massachusetts 2026"
            query = st.text_input("Search query", value=default_q)

            source_labels = {
                "grants.gov": "grants.gov (federal API)",
                "web_search": "Web search",
                "candid_api": "Candid API (if enabled)",
            }
            chosen = st.multiselect(
                "Sources",
                options=list(source_labels.keys()),
                default=["grants.gov", "web_search"],
                format_func=lambda s: source_labels[s],
            )
            col_a, col_b = st.columns([1, 1])
            with col_a:
                if st.button("🔍 Search this query", type="primary"):
                    with st.spinner("Searching and extracting… (polite rate-limiting may take a moment)"):
                        staged = svc.run_search(db, query, sources=chosen or None)
                    st.success(f"Staged {len(staged)} candidate(s). See the Review Queue tab.")
            with col_b:
                if st.button("🌐 Search Everywhere"):
                    st.caption(
                        "Expands your org profile into many queries and sweeps all "
                        "known funders + public portals. This can take a few minutes."
                    )
                    with st.spinner("Running full sweep across all sources…"):
                        staged = svc.run_full_sweep(db, sources=chosen or None)
                    st.success(
                        f"Full sweep complete — staged {len(staged)} candidate(s). "
                        "See the Review Queue tab."
                    )

        # ── Review queue tab ─────────────────────────────────────────────────
        with review_tab:
            st.subheader("Ranked Review Queue")
            st.caption("Best-first: strong eligible matches (🟢) rise to the top.")
            top_row = st.columns([2, 1])
            with top_row[0]:
                status_filter = st.radio(
                    "Show",
                    [CandidateStatus.NEW, CandidateStatus.DUPLICATE, CandidateStatus.IMPORTED,
                     CandidateStatus.DISMISSED],
                    format_func=lambda s: s.value.title(),
                    horizontal=True,
                )
            with top_row[1]:
                hide_ineligible = st.toggle("Hide ineligible", value=False)

            candidates = svc.list_candidates(db, status=status_filter)
            if hide_ineligible:
                candidates = [
                    c for c in candidates if c.eligibility_status != EligibilityStatus.INELIGIBLE
                ]
            if not candidates:
                st.info("No candidates with this status.")
            else:
                strong_n = sum(1 for c in candidates if c.is_strong_match)
                act_n = sum(1 for c in candidates if c.act_now)
                st.write(f"**{len(candidates)}** shown · 🟢 **{strong_n}** strong · ⏰ **{act_n}** act now")
                labels = {_queue_label(c): c.id for c in candidates}
                selected_label = st.selectbox("Select a candidate", list(labels.keys()))
                selected_id = labels[selected_label]
                cand = svc.get_candidate(db, selected_id)
                if cand:
                    if cand.is_strong_match:
                        st.success(f"🟢 Strong eligible match · fit {cand.fit_score:.1f}/10 · {cand.why_fits}")
                    elif cand.eligibility_status == EligibilityStatus.INELIGIBLE:
                        st.caption(f"Not currently eligible · fit {cand.fit_score:.1f}/10")
                    st.divider()
                    _render_import_form(cand, db)

        # ── Report tab ───────────────────────────────────────────────────────
        with report_tab:
            st.subheader("Grant Scout Intelligence Report")
            st.caption("A weekly digest of candidates awaiting review — Act Now first.")
            if st.button("📊 Generate digest", type="primary"):
                report = report_svc.generate_report(db)
                st.write(
                    f"**{report.total}** new · 🟢 **{report.strong}** strong · ⏰ **{report.act_now}** act now"
                )
                st.code(report.markdown, language="markdown")
                st.download_button(
                    "⬇️ Download digest (Markdown)",
                    data=report.markdown,
                    file_name=f"scout_digest_{date.today().isoformat()}.md",
                    mime="text/markdown",
                )

        # ── Scrape URL tab ───────────────────────────────────────────────────
        with url_tab:
            st.subheader("Scrape a Specific Grant URL")
            st.caption(
                "Paste a funder's public grant/RFP page. GrantNova fetches it (honoring "
                "robots.txt) and extracts fields for your review."
            )
            url = st.text_input("Grant page URL", placeholder="https://funder.org/grants/rfp-2026")
            if st.button("🔗 Fetch & Extract"):
                if url.strip():
                    with st.spinner("Fetching…"):
                        cand = svc.fetch_known_url(db, url.strip())
                    if cand:
                        st.success("Extracted. Review it below.")
                        st.divider()
                        _render_import_form(cand, db)
                    else:
                        st.error("Could not fetch or parse that URL (blocked by robots.txt or unreachable).")
                else:
                    st.warning("Enter a URL.")

        # ── Instrumentl CSV tab ──────────────────────────────────────────────
        with csv_tab:
            st.subheader("Import Instrumentl CSV Export")
            st.caption(
                "Instrumentl's ToS prohibits scraping, but subscribers may export "
                "their matches to CSV. Upload that export here."
            )
            uploaded = st.file_uploader("Instrumentl CSV export", type=["csv"])
            if uploaded is not None and st.button("📄 Import CSV"):
                csv_text = uploaded.getvalue().decode("utf-8", errors="replace")
                staged = svc.import_instrumentl_csv(db, csv_text)
                st.success(f"Staged {len(staged)} candidate(s) from CSV. See the Review Queue tab.")

    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


main()
