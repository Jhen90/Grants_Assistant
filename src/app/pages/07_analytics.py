# ============================================================
# File: src/app/pages/07_analytics.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Analytics — charts for score distribution, status trends, funder breakdown
# ============================================================

import json

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.db.database import get_db
from src.models.application import Application, ApplicationStatus
from src.models.grant import Grant, GrantStatus
from src.models.funder import Funder

st.set_page_config(page_title="Analytics — GrantNova", page_icon="📊", layout="wide")


def main() -> None:
    st.title("📊 Analytics")

    db_gen = get_db()
    db = next(db_gen)

    try:
        grants = db.query(Grant).filter(Grant.is_deleted.is_(False)).all()
        applications = db.query(Application).filter(Application.is_deleted.is_(False)).all()

        if not grants:
            st.info("No grant data yet. Add some grants to see analytics.")
            return

        # ── Row 1: KPIs ─────────────────────────────────────────────────────
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Grants", len(grants))
        k2.metric("Avg Fit Score", f"{sum(g.fit_score or 0 for g in grants) / len(grants):.2f}")
        k3.metric("Applications", len(applications))
        awarded = [a for a in applications if a.status == ApplicationStatus.AWARDED]
        k4.metric("Awards Won", len(awarded))
        total_awarded = sum(a.award_amount or 0 for a in awarded)
        k5.metric("Total Awarded", f"${total_awarded:,.0f}")

        st.divider()

        # ── Row 2: Score distribution + Status breakdown ─────────────────────
        row2_col1, row2_col2 = st.columns(2)

        with row2_col1:
            st.subheader("Fit Score Distribution")
            scores = [g.fit_score for g in grants if g.fit_score is not None]
            if scores:
                fig = px.histogram(
                    x=scores,
                    nbins=20,
                    labels={"x": "Fit Score", "y": "Count"},
                    color_discrete_sequence=["#4299e1"],
                )
                fig.add_vline(x=7.0, line_dash="dash", line_color="#c53030",
                              annotation_text="Threshold 7.0")
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No scored grants yet.")

        with row2_col2:
            st.subheader("Grant Status Breakdown")
            status_counts: dict[str, int] = {}
            for g in grants:
                status_counts[g.status.value] = status_counts.get(g.status.value, 0) + 1
            fig2 = px.bar(
                x=list(status_counts.keys()),
                y=list(status_counts.values()),
                labels={"x": "Status", "y": "Count"},
                color=list(status_counts.keys()),
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig2.update_layout(
                height=300,
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.divider()

        # ── Row 3: Top funders by grant count + Focus area cloud ─────────────
        row3_col1, row3_col2 = st.columns(2)

        with row3_col1:
            st.subheader("Grants by Funder (Top 10)")
            funder_counts: dict[str, int] = {}
            for g in grants:
                fname = g.funder_name or "Unknown"
                funder_counts[fname] = funder_counts.get(fname, 0) + 1
            sorted_funders = sorted(funder_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            if sorted_funders:
                names, counts = zip(*sorted_funders)
                fig3 = px.bar(
                    x=list(counts),
                    y=list(names),
                    orientation="h",
                    labels={"x": "Count", "y": "Funder"},
                    color_discrete_sequence=["#48bb78"],
                )
                fig3.update_layout(
                    height=320,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig3, use_container_width=True)

        with row3_col2:
            st.subheader("Focus Area Frequency")
            area_counts: dict[str, int] = {}
            for g in grants:
                if g.focus_areas_json:
                    try:
                        areas = json.loads(g.focus_areas_json)
                        for a in areas:
                            area_counts[a] = area_counts.get(a, 0) + 1
                    except json.JSONDecodeError:
                        pass
            if area_counts:
                sorted_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)[:15]
                area_names, area_vals = zip(*sorted_areas)
                fig4 = px.treemap(
                    names=list(area_names),
                    parents=[""] * len(area_names),
                    values=list(area_vals),
                    color=list(area_vals),
                    color_continuous_scale="Blues",
                )
                fig4.update_layout(
                    height=320,
                    margin=dict(l=10, r=10, t=20, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No focus area data yet.")

        st.divider()

        # ── Row 4: Score vs Amount scatter ───────────────────────────────────
        st.subheader("Fit Score vs Award Amount")
        scatter_data = [
            {
                "title": g.title,
                "fit_score": g.fit_score or 0,
                "amount": g.amount_max or g.amount_min or 0,
                "status": g.status.value,
                "funder": g.funder_name or "Unknown",
            }
            for g in grants
            if (g.amount_max or g.amount_min)
        ]
        if scatter_data:
            fig5 = px.scatter(
                scatter_data,
                x="fit_score",
                y="amount",
                color="status",
                hover_name="title",
                hover_data=["funder", "status"],
                labels={"fit_score": "Fit Score (0–10)", "amount": "Award Amount ($)"},
            )
            fig5.update_layout(
                height=360,
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("Add grants with award amounts to see this chart.")

    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


main()
