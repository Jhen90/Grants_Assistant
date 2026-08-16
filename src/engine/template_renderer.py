# ============================================================
# File: src/engine/template_renderer.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Renders paragraph templates with {{variable}} substitution
# ============================================================

from __future__ import annotations

import json
import re

from src.utils.logger import get_logger

log = get_logger(__name__)

_VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")
_FILL_IN_PLACEHOLDER = "[FILL IN: {var}]"


def render_template(body: str, context: dict[str, str]) -> str:
    """
    Substitute {{variable}} placeholders in body using context dict.
    Unknown variables become '[FILL IN: variable_name]' — never raise on missing keys.

    Returns the rendered string.
    """
    def replacer(match: re.Match) -> str:  # type: ignore[type-arg]
        var = match.group(1)
        value = context.get(var)
        if value is None:
            log.debug("Template variable '%s' not found in context — using placeholder.", var)
            return _FILL_IN_PLACEHOLDER.format(var=var)
        return str(value)

    rendered = _VAR_PATTERN.sub(replacer, body)
    return rendered


def build_org_context(org: object) -> dict[str, str]:
    """
    Build a template context dict from an Organization ORM instance.
    Returns a flat dict of all variables available for template substitution.
    """
    eligibility_json = getattr(org, "eligibility_json", None) or "{}"
    if isinstance(eligibility_json, str):
        try:
            elig = json.loads(eligibility_json)
        except json.JSONDecodeError:
            elig = {}
    else:
        elig = eligibility_json

    programs_json = getattr(org, "programs_json", None) or "[]"
    if isinstance(programs_json, str):
        try:
            programs = json.loads(programs_json)
        except json.JSONDecodeError:
            programs = []
    else:
        programs = programs_json

    partner_names = ", ".join(
        p.get("name", "") for p in programs if p.get("name")
    ) if programs else ""

    # Coerce every value to a string — nullable ORM columns read as None, which
    # would otherwise render the literal text "None" in a template.
    return {
        "org_name": getattr(org, "name", "") or "",
        "mission": getattr(org, "mission", "") or "",
        "values": getattr(org, "values_text", "") or "",
        "city": getattr(org, "city", "") or elig.get("city", "") or "",
        "state": getattr(org, "state", "") or elig.get("state", "") or "",
        "target_population": elig.get("target_population", "youth ages 13–18") or "",
        "org_type": elig.get("org_type", "") or "",
        "partner_names": partner_names or "",
        "website": getattr(org, "website", "") or "",
    }


def extract_variables(body: str) -> list[str]:
    """Return list of unique variable names found in a template body."""
    return list(dict.fromkeys(_VAR_PATTERN.findall(body)))
