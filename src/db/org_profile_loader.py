# ============================================================
# File: src/db/org_profile_loader.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Parses org_profile_seed_data.md into typed Python dicts for seed_data.py
# ============================================================

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from src.utils.error_handler import ConfigurationError
from src.utils.logger import get_logger

log = get_logger(__name__)

REQUIRED_SCALAR_FIELDS = ["name", "mission", "city", "state"]
REQUIRED_SECTION_KEYS = ["eligibility"]


def load(profile_path: str = "data/org_profile/org_profile_seed_data.md") -> dict[str, Any]:
    """
    Parse the org profile Markdown file and return a merged dict.

    The Markdown file embeds data in ```yaml ... ``` fenced code blocks.
    All yaml blocks are merged into a single dict. Repeated keys are overwritten
    in document order (later blocks win).

    Returns a dict with keys:
        name, mission, values_text, city, state, website,
        programs (list), eligibility (dict),
        priority_funders (list), community_partners (list)

    Raises ConfigurationError if required fields are missing.
    """
    path = Path(profile_path)
    if not path.exists():
        raise ConfigurationError(
            f"Org profile file not found: {path.resolve()}. "
            "Create the file or pass --profile with the correct path."
        )

    content = path.read_text(encoding="utf-8")
    log.info("Loading org profile from %s", path)

    # Extract all ```yaml ... ``` blocks
    yaml_blocks = re.findall(r"```yaml\n(.*?)```", content, re.DOTALL)

    if not yaml_blocks:
        raise ConfigurationError(
            f"No YAML blocks found in {profile_path}. "
            "The org profile must contain at least one ```yaml ... ``` block."
        )

    merged: dict[str, Any] = {}
    for i, block in enumerate(yaml_blocks):
        try:
            parsed = yaml.safe_load(block)
        except yaml.YAMLError as exc:
            raise ConfigurationError(
                f"YAML parse error in block {i + 1} of {profile_path}: {exc}"
            ) from exc

        if isinstance(parsed, dict):
            merged.update(parsed)

    # Validate required scalar fields
    missing_scalars = [f for f in REQUIRED_SCALAR_FIELDS if not merged.get(f)]
    if missing_scalars:
        raise ConfigurationError(
            f"Org profile is missing required fields: {missing_scalars}. "
            f"Add these to a ```yaml block in {profile_path}."
        )

    # Validate required section keys
    missing_sections = [k for k in REQUIRED_SECTION_KEYS if k not in merged]
    if missing_sections:
        raise ConfigurationError(
            f"Org profile is missing required sections: {missing_sections}. "
            f"Add an 'eligibility:' block in {profile_path}."
        )

    # Normalize optional lists to empty lists if absent
    merged.setdefault("programs", [])
    merged.setdefault("priority_funders", [])
    merged.setdefault("community_partners", [])
    merged.setdefault("values_text", "")
    merged.setdefault("website", "")

    # Strip trailing whitespace from multiline scalar strings
    for key in ("mission", "values_text"):
        if isinstance(merged.get(key), str):
            merged[key] = merged[key].strip()

    log.info(
        "Org profile loaded: %s | programs=%d | priority_funders=%d | community_partners=%d",
        merged["name"],
        len(merged["programs"]),
        len(merged["priority_funders"]),
        len(merged["community_partners"]),
    )

    return merged
