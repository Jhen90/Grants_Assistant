# ============================================================
# File: src/app/components/score_breakdown.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Score breakdown display component (bar chart + detail table)
# ============================================================

from __future__ import annotations

import json

import streamlit as st


def render_score_breakdown(
    fit_score: float | None,
    score_breakdown_json: str | None,
) -> None:
    """
    Render a fit score progress bar and a per-criterion detail table.
    score_breakdown_json is the JSON string stored in Grant.score_breakdown_json.
    """
    score = fit_score or 0.0
    score_pct = int(score / 10 * 100)

    # Color the bar by threshold
    if score >= 7.0:
        bar_color = "#276749"
    elif score >= 5.0:
        bar_color = "#b7791f"
    else:
        bar_color = "#c53030"

    st.markdown(
        f"""
<div>
  <span style="font-size:1.6rem; font-weight:700; color:{bar_color};">{score:.2f}</span>
  <span style="color:#718096;"> / 10.0 fit score</span>
  <div class="score-bar-wrap">
    <div class="score-bar-fill" style="width:{score_pct}%; background:{bar_color};"></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if not score_breakdown_json:
        st.caption("No score breakdown available.")
        return

    try:
        breakdown = json.loads(score_breakdown_json)
    except (json.JSONDecodeError, TypeError):
        st.caption("Score breakdown could not be parsed.")
        return

    criteria_results = breakdown.get("criteria_results", [])
    if not criteria_results:
        st.caption("No criterion details available.")
        return

    with st.expander("Score Breakdown by Criterion", expanded=False):
        rows = []
        for cr in criteria_results:
            rows.append(
                {
                    "Criterion": cr.get("name", "?"),
                    "Type": cr.get("evaluator_type", "?"),
                    "Raw": f"{cr.get('raw_score', 0):.2f}",
                    "Weight": cr.get("weight", 1),
                    "Weighted": f"{cr.get('weighted_score', 0):.2f}",
                    "Passed": "✅" if cr.get("passed") else "❌",
                    "Notes": cr.get("notes", ""),
                }
            )
        st.table(rows)

        hard_failed = breakdown.get("hard_filter_failed", False)
        if hard_failed:
            st.error("⛔ Hard filter FAILED — this grant is not eligible.")
