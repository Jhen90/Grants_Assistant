# ============================================================
# File: src/models/manifest.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Manifest ORM model — append-only audit log for each application
# ============================================================

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class Manifest(Base):
    """
    One Manifest per Application. events_json is an append-only JSON array.
    Each event: { "event_type": str, "timestamp": ISO-str, "details": dict }
    Common event_types: APPLICATION_CREATED, DRAFT_SAVED, REVIEW_COMPLETED,
                        REVIEW_BLOCKED, APPROVED, SUBMITTED, OUTCOME_RECORDED
    """

    __tablename__ = "manifests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    events_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # append-only JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    application: Mapped[Application] = relationship("Application", back_populates="manifest")

    def __repr__(self) -> str:
        return f"<Manifest id={self.id!r} application_id={self.application_id!r}>"


from src.models.application import Application  # noqa: E402, F401
