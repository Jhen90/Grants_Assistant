# ============================================================
# File: src/services/manifest_service.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: ManifestService — append-only audit log per application
# ============================================================

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from src.models.manifest import Manifest
from src.utils.logger import get_logger

log = get_logger(__name__)


class ManifestService:
    def create_manifest(self, db: Session, application_id: str) -> Manifest:
        """Create a new manifest for an application with the APPLICATION_CREATED event."""
        manifest = Manifest(application_id=application_id, events_json="[]")
        db.add(manifest)
        db.flush()
        self.append_event(db, application_id, "APPLICATION_CREATED", {})
        return manifest

    def append_event(
        self, db: Session, application_id: str, event_type: str, details: dict
    ) -> None:
        """Append one event to the manifest's events_json array. Never overwrites."""
        manifest = db.query(Manifest).filter_by(application_id=application_id).first()
        if manifest is None:
            log.warning("No manifest found for application %s — creating one.", application_id)
            manifest = self.create_manifest(db, application_id)

        try:
            events: list[dict] = json.loads(manifest.events_json or "[]")
        except json.JSONDecodeError:
            events = []

        events.append(
            {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "details": details,
            }
        )
        manifest.events_json = json.dumps(events, ensure_ascii=False)
        db.flush()
        log.debug("Manifest event %s appended for application %s.", event_type, application_id)

    def export_markdown(self, db: Session, application_id: str) -> str:
        """Export the manifest as a Markdown table."""
        manifest = db.query(Manifest).filter_by(application_id=application_id).first()
        if manifest is None:
            return "*(No manifest found)*"

        try:
            events: list[dict] = json.loads(manifest.events_json or "[]")
        except json.JSONDecodeError:
            events = []

        if not events:
            return "*(No events recorded)*"

        lines = [
            "| # | Event | Timestamp | Details |",
            "|---|-------|-----------|---------|",
        ]
        for i, evt in enumerate(events, 1):
            details_str = json.dumps(evt.get("details", {}))
            lines.append(
                f"| {i} | {evt.get('event_type', '?')} "
                f"| {evt.get('timestamp', '?')} "
                f"| {details_str} |"
            )
        return "\n".join(lines)
