# ============================================================
# File: src/discovery/base.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: Core types for the discovery subsystem — GrantCandidate (the
#   normalized, pre-import representation of a discovered grant) and the
#   GrantSource abstract base class all connectors implement.
# ============================================================

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass
class GrantCandidate:
    """
    A discovered grant opportunity prior to human review and import.

    `extracted` holds rules-based field guesses keyed exactly like the dict
    GrantService.create_grant() expects (title, funder_name, deadline,
    amount_min, amount_max, focus_areas, target_geography,
    eligibility_501c3_required, fiscal_sponsorship_allowed, source_url, notes).

    `field_confidence` maps each extracted field to a 0.0–1.0 confidence so the
    UI can flag low-confidence values for the human to verify. `evidence` keeps
    the raw text snippet each value came from, for auditability.
    """

    source: str                      # connector name, e.g. "grants.gov"
    source_url: str | None
    raw_title: str
    raw_funder: str | None = None
    extracted: dict = field(default_factory=dict)
    field_confidence: dict = field(default_factory=dict)
    evidence: dict = field(default_factory=dict)
    raw_text: str | None = None      # truncated page text kept for human review

    def to_extracted_json(self) -> str:
        payload = {
            "extracted": self._json_safe(self.extracted),
            "field_confidence": self.field_confidence,
            "evidence": self.evidence,
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _json_safe(d: dict) -> dict:
        out: dict = {}
        for k, v in d.items():
            out[k] = v.isoformat() if isinstance(v, date) else v
        return out


class GrantSource(ABC):
    """
    Abstract base for all discovery connectors. A source knows how to turn a
    query (and/or the org profile) into a list of GrantCandidate objects.

    Implementations MUST be safe to call with the source disabled — return [].
    """

    name: str = "base"

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Whether this source is turned on in settings."""

    @abstractmethod
    def search(self, query: str, org_profile: dict, limit: int = 25) -> list[GrantCandidate]:
        """Return candidate opportunities for the query. Never raise on no results."""
