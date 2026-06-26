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

    return {
        "org_name": getattr(org, "name", ""),
        "mission": getattr(org, "mission", ""),
        "values": getattr(org, "values_text", ""),
        "city": getattr(org, "city", "") or elig.get("city", ""),
        "state": getattr(org, "state", "") or elig.get("state", ""),
        "target_population": elig.get("target_population", "youth ages 13–18"),
        "org_type": elig.get("org_type", ""),
        "partner_names": partner_names,
        "website": getattr(org, "website", "") or "",
    }


def extract_variables(body: str) -> list[str]:
    """Return list of unique variable names found in a template body."""
    return list(dict.fromkeys(_VAR_PATTERN.findall(body)))
