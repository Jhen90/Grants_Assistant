# ============================================================
# File: src/app/pages/01_dashboard.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Dashboard — live pipeline overview with key metrics and urgent alerts
# ============================================================

import plotly.graph_objects as go
import streamlit as st

from src.app.components.grant_card import render_grant_card
from src.app.components.urgency_badge import urgency_badge_html
from src.db.database import get_db
from src.engine.deadline_classifier import days_until_deadline
from src.models.grant import DeadlineUrgency, Grant, GrantStatus
from src.services.grant_service import GrantService

st.set_page_config(page_title="Dashboard — GrantNova", page_icon="📊", layout="wide")

grant_svc = GrantService()


def _pipeline_funnel(status_counts: dict[str, int]) -> go.Figure:
    statuses = [
        "DISCOVERED", "EVALUATED", "RECOMMENDED",
        "APPROVED_TO_APPLY", "SUBMITTED", "AWARDED",
    ]
    values = [status_counts.get(s, 0) for s in statuses]
    labels = [s.replace("_", " ").title() for s in statuses]
    colors = ["#4299e1", "#48bb78", "#ed8936", "#9f7aea", "#f56565", "#68d391"]

    fig = go.Figure(
        go.Funnel(
            y=labels,
            x=values,
            textinfo="value+percent initial",
            marker=dict(color=colors),
        )
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _urgency_donut(urgency_counts: dict[str, int]) -> go.Figure:
    labels = list(urgency_counts.keys())
    values = list(urgency_counts.values())
    colors = {"RED": "#FC8181", "YELLOW": "#F6E05E", "GREEN": "#68D391", "GRAY": "#CBD5E0"}

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(colors=[colors.get(l, "#CBD5E0") for l in labels]),
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def main() -> None:
    st.title("📊 Dashboard")

    db_gen = get_db()
    db = next(db_gen)

    try:
        all_grants = db.query(Grant).filter(Grant.is_deleted.is_(False)).all()

        status_counts: dict[str, int] = {}
        urgency_counts: dict[str, int] = {"RED": 0, "YELLOW": 0, "GREEN": 0, "GRAY": 0}
        for g in all_grants:
            status_counts[g.status.value] = status_counts.get(g.status.value, 0) + 1
            urg = g.deadline_urgency.value if g.deadline_urgency else "GRAY"
            urgency_counts[urg] = urgency_counts.get(urg, 0) + 1

        # ── KPI metrics ──────────────────────────────────────────────────────
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Grants", len(all_grants))
        col2.metric("Recommended", status_counts.get("RECOMMENDED", 0))
        col3.metric("In Progress", status_counts.get("APPROVED_TO_APPLY", 0))
        col4.metric("Submitted", status_counts.get("SUBMITTED", 0))
        col5.metric("🔴 Urgent", urgency_counts.get("RED", 0))

        st.divider()

        chart_col, alert_col = st.columns([2, 1])

        with chart_col:
            st.subheader("Pipeline Funnel")
            st.plotly_chart(_pipeline_funnel(status_counts), use_container_width=True)

            st.subheader("Deadline Urgency")
            st.plotly_chart(_urgency_donut(urgency_counts), use_container_width=True)

        with alert_col:
            st.subheader("⚠️ Urgent Deadlines")
            urgent = [
                g for g in all_grants
                if g.deadline_urgency == DeadlineUrgency.RED
                and g.status.value not in (
                    "ARCHIVED", "SUBMITTED", "AWARDED", "DECLINED", "WITHDRAWN"
                )
            ]
            urgent.sort(key=lambda g: g.deadline or g.created_at.date())
            if urgent:
                for g in urgent[:8]:
                    days = days_until_deadline(g.deadline)
                    with st.container(border=True):
                        st.markdown(f"**{g.title}**")
                        st.caption(g.funder_name or "Unknown Funder")
                        st.markdown(
                            urgency_badge_html(g.deadline_urgency), unsafe_allow_html=True
                        )
                        if days is not None:
                            st.caption(f"{days} days left")
            else:
                st.success("No urgent deadlines right now.")

        st.divider()
        st.subheader("🏆 Top Recommended Grants")
        recommended = [g for g in all_grants if g.status == GrantStatus.RECOMMENDED]
        recommended.sort(key=lambda g: g.fit_score or 0, reverse=True)
        for g in recommended[:5]:
            clicked = render_grant_card(g, on_select=True)
            if clicked:
                st.session_state["selected_grant_id"] = g.id
                st.switch_page("pages/03_grants.py")

    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


main()
