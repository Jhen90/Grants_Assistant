# ============================================================
# File: src/discovery/__init__.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: Grant discovery subsystem — search, fetch, rules-based extract.
#   NO paid AI API. Extraction is deterministic; all candidates require human
#   confirmation before becoming Grant records (human-in-the-loop).
# ============================================================

from src.discovery.base import GrantCandidate, GrantSource

__all__ = ["GrantCandidate", "GrantSource"]
