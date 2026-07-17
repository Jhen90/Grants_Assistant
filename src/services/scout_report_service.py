# ============================================================
# File: src/services/scout_report_service.py
# Version: 1.2.0
# Created: 2026-07-16
# Modified: 2026-07-16
# Description: Grant Scout REPORT phase — generates the weekly "intelligence report"
#   digest of newly discovered candidates, led by Act Now items then strong matches
#   (FR-SCOUT-4xx). Rendered from DB state via Jinja2 (no AI). READ-ONLY: it never
#   mutates candidate state. Low-confidence extracted fields are marked unverified.
# ============================================================

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from src.models.discovered_candidate import CandidateStatus, DiscoveredCandidate
from src.services.discovery_service import DiscoveryService
from src.utils.logger import get_logger

log = get_logger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "reports"
_LOW_CONFIDENCE = 0.5

_ELIGIBILITY_LABEL = {
    "ELIGIBLE": "✅ Yes",
    "INELIGIBLE": "❌ No",
    "UNKNOWN": "⚠️ Unknown",
}


@dataclass
class ScoutReport:
    markdown: str
    total: int
    strong: int
    act_now: int
    generated_at: datetime


def _jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=False,  # Markdown output, not HTML
        trim_blocks=True,
        lstrip_blocks=True,
    )


class ScoutReportService:
    def generate_report(self, db: Session, since: date | None = None) -> ScoutReport:
        """
        Build the Scout intelligence digest from candidates awaiting review.
        `since` (defaults to none = all NEW) filters by discovery date. Read-only.
        """
        q = db.query(DiscoveredCandidate).filter(
            DiscoveredCandidate.is_deleted.is_(False),
            DiscoveredCandidate.status == CandidateStatus.NEW,
        )
        if since is not None:
            q = q.filter(DiscoveredCandidate.discovered_at >= datetime(since.year, since.month, since.day))
        rows = q.all()
        rows.sort(key=DiscoveryService._rank_key)  # best-first, shared with the queue

        act_now = [r for r in rows if r.act_now]
        strong = [r for r in rows if r.is_strong_match and not r.act_now]
        others = [r for r in rows if not r.is_strong_match and not r.act_now]

        generated_at = datetime.utcnow()
        ctx = {
            "date": date.today().isoformat(),
            "generated_at": generated_at.strftime("%Y-%m-%d %H:%M UTC"),
            "total": len(rows),
            "strong": sum(1 for r in rows if r.is_strong_match),
            "act_now": len(act_now),
            "act_now_items": [self._view(r) for r in act_now],
            "strong_items": [self._view(r) for r in strong],
            "other_items": [self._view(r) for r in others],
        }
        markdown = _jinja_env().get_template("scout_digest.md.j2").render(**ctx)
        return ScoutReport(
            markdown=markdown,
            total=len(rows),
            strong=ctx["strong"],
            act_now=len(act_now),
            generated_at=generated_at,
        )

    # ── view-model builder ─────────────────────────────────────────────────────

    @staticmethod
    def _view(row: DiscoveredCandidate) -> dict:
        try:
            payload = json.loads(row.extracted_json or "{}")
        except json.JSONDecodeError:
            payload = {}
        extracted = payload.get("extracted", {})
        conf = payload.get("field_confidence", {})

        def unverified(field: str) -> bool:
            return conf.get(field, 1.0) < _LOW_CONFIDENCE

        # Amount range
        amt_min = extracted.get("amount_min")
        amt_max = extracted.get("amount_max")
        if amt_min or amt_max:
            amount = f"${(amt_min or amt_max):,.0f}–${(amt_max or amt_min):,.0f}"
            if unverified("amount_min") or unverified("amount_max"):
                amount += " (unverified)"
        else:
            amount = "Not specified"

        # Deadline
        deadline = extracted.get("deadline") or "Not specified"
        if deadline != "Not specified" and unverified("deadline"):
            deadline = f"{deadline} (unverified — confirm on funder site)"

        elig = row.eligibility_status.value if row.eligibility_status else "UNKNOWN"

        return {
            "title": row.raw_title,
            "funder": extracted.get("funder_name") or row.raw_funder or "Unknown funder",
            "amount": amount,
            "deadline": deadline,
            "urgency": row.deadline_urgency or "GRAY",
            "eligibility": _ELIGIBILITY_LABEL.get(elig, elig),
            "fit": f"{row.fit_score:.1f}" if row.fit_score is not None else "—",
            "why_fits": row.why_fits or "",
            "url": row.source_url or "(no link)",
        }
