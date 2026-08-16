# ============================================================
# File: src/app/components/urgency_badge.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Urgency badge HTML component — no Streamlit import required
# ============================================================

from __future__ import annotations

from src.models.grant import DeadlineUrgency


_BADGE_CLASSES: dict[str, str] = {
    "RED":    "badge-red",
    "YELLOW": "badge-yellow",
    "GREEN":  "badge-green",
    "GRAY":   "badge-gray",
}

_LABELS: dict[str, str] = {
    "RED":    "🔴 Urgent (< 30d)",
    "YELLOW": "🟡 Soon (30–60d)",
    "GREEN":  "🟢 On Track (60–90d)",
    "GRAY":   "⚫ No Deadline",
}


def urgency_badge_html(urgency: DeadlineUrgency | str | None) -> str:
    """Return an HTML badge string for the given urgency level."""
    if urgency is None:
        key = "GRAY"
    elif isinstance(urgency, DeadlineUrgency):
        key = urgency.value
    else:
        key = str(urgency).upper()

    css_class = _BADGE_CLASSES.get(key, "badge-gray")
    label = _LABELS.get(key, key)
    return f'<span class="{css_class}">{label}</span>'


def urgency_label(urgency: DeadlineUrgency | str | None) -> str:
    """Return a plain-text label for the urgency (useful for dataframe display)."""
    if urgency is None:
        return "No Deadline"
    key = urgency.value if isinstance(urgency, DeadlineUrgency) else str(urgency).upper()
    return _LABELS.get(key, key).split(" ", 1)[-1].strip()
