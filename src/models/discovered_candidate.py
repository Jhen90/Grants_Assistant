# ============================================================
# File: src/models/discovered_candidate.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: DiscoveredCandidate ORM model — a grant opportunity found by the
#   discovery subsystem, staged for human review BEFORE it becomes a Grant.
#   This keeps the human-in-the-loop guarantee: nothing auto-creates a Grant.
# ============================================================

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class CandidateStatus(str, enum.Enum):
    NEW = "NEW"              # awaiting human review
    IMPORTED = "IMPORTED"    # converted into a Grant record
    DISMISSED = "DISMISSED"  # human rejected it
    DUPLICATE = "DUPLICATE"  # matched an existing grant during dedup


class DiscoveredCandidate(Base):
    __tablename__ = "discovered_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # connector name
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True, index=True)
    raw_title: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_funder: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Full rules-based extraction payload: {extracted, field_confidence, evidence}
    extracted_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    raw_text_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus, name="candidate_status_enum"),
        nullable=False,
        default=CandidateStatus.NEW,
        index=True,
    )
    # If imported, the Grant it became; if duplicate, the existing Grant it matched.
    linked_grant_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    dedup_note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    search_query: Mapped[str | None] = mapped_column(String(500), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<DiscoveredCandidate id={self.id!r} source={self.source!r} "
            f"status={self.status.value!r} title={self.raw_title!r}>"
        )
