# ============================================================
# File: src/models/draft.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: DraftVersion ORM model — versioned application narrative drafts
# ============================================================

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class DraftVersion(Base):
    """
    Stores a numbered snapshot of an application's narrative sections.
    sections_json is a dict: { "section_name": "content text", ... }
    Only one version per application has is_current=True.
    """

    __tablename__ = "draft_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sections_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # JSON dict
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    application: Mapped[Application] = relationship("Application", back_populates="draft_versions")

    def __repr__(self) -> str:
        return (
            f"<DraftVersion id={self.id!r} app_id={self.application_id!r} "
            f"v={self.version_number} current={self.is_current}>"
        )


from src.models.application import Application  # noqa: E402, F401
