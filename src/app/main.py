# ============================================================
# File: src/app/main.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: GrantNova Streamlit entry point — run with: streamlit run src/app/main.py
# ============================================================

import streamlit as st

from src.db.database import init_db
from src.utils.config import get_settings
from src.utils.logger import get_logger

log = get_logger(__name__)

_CUSTOM_CSS = """
<style>
/* ── Global fonts & colors ── */
:root {
    --color-primary:   #2c5282;
    --color-accent:    #4299e1;
    --color-warn:      #dd6b20;
    --color-danger:    #c53030;
    --color-success:   #276749;
    --color-muted:     #718096;
    --color-bg-light:  #ebf8ff;
    --color-border:    #bee3f8;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #1a365d;
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 1rem;
    padding: 4px 0;
}

/* Main header */
h1 { color: var(--color-primary); border-bottom: 2px solid var(--color-accent); padding-bottom: 8px; }
h2 { color: var(--color-primary); }
h3 { color: #2d3748; }

/* Metric cards */
[data-testid="metric-container"] {
    background: var(--color-bg-light);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 12px;
}

/* Urgency badges */
.badge-red    { background:#FED7D7; color:#c53030; padding:3px 8px; border-radius:12px; font-weight:600; font-size:0.8rem; }
.badge-yellow { background:#FEFCBF; color:#744210; padding:3px 8px; border-radius:12px; font-weight:600; font-size:0.8rem; }
.badge-green  { background:#C6F6D5; color:#276749; padding:3px 8px; border-radius:12px; font-weight:600; font-size:0.8rem; }
.badge-gray   { background:#E2E8F0; color:#4A5568; padding:3px 8px; border-radius:12px; font-weight:600; font-size:0.8rem; }

/* Approval gate blocked panel */
.gate-blocked {
    background: #FFF5F5;
    border: 2px solid #FC8181;
    border-radius: 8px;
    padding: 16px;
    margin: 12px 0;
}
.gate-passed {
    background: #F0FFF4;
    border: 2px solid #68D391;
    border-radius: 8px;
    padding: 16px;
    margin: 12px 0;
}

/* Score bar */
.score-bar-wrap { background: #E2E8F0; border-radius: 6px; height: 14px; margin-top: 4px; }
.score-bar-fill { height: 14px; border-radius: 6px; }

/* Tables */
.stDataFrame { border: 1px solid var(--color-border); border-radius: 6px; }

/* Buttons */
.stButton > button {
    border-radius: 6px;
    font-weight: 600;
}

/* Warning / error boxes */
.stAlert { border-radius: 8px; }

/* Remove Streamlit default top padding in pages */
.block-container { padding-top: 1.5rem; }
</style>
"""


def _configure_page() -> None:
    st.set_page_config(
        page_title="GrantNova",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)


def _ensure_db() -> None:
    """Initialize DB on first run; idempotent thereafter."""
    if "db_initialized" not in st.session_state:
        try:
            init_db()
            st.session_state["db_initialized"] = True
        except Exception as exc:
            st.error(f"Database initialization failed: {exc}")
            st.stop()


def main() -> None:
    _configure_page()
    _ensure_db()

    settings = get_settings()

    with st.sidebar:
        st.markdown("## 📋 GrantNova")
        st.markdown(f"*v{settings.app_version}*")
        st.divider()

    st.title("Grants Management Assistant")
    st.markdown(
        "Welcome to **GrantNova**. Use the **pages** in the sidebar to navigate the system."
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info("📥 **Enter Grant** — Add a new grant opportunity")
    with col2:
        st.info("📊 **Dashboard** — Live pipeline view")
    with col3:
        st.info("📝 **Applications** — Manage active applications")
    with col4:
        st.info("📈 **Reports** — Weekly reports and analytics")

    st.divider()
    st.caption(
        "GrantNova v1.1.0 · Rules-based scoring · No AI API required · "
        f"DB: `{settings.database_url}`"
    )


if __name__ == "__main__":
    main()
