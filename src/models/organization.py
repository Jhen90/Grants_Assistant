# ============================================================
# File: src/models/organization.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Organization ORM model — the grant-seeking entity profile
# ============================================================

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    mission: Mapped[str] = mapped_column(Text, nullable=False)
    values_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    programs_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    eligibility_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON dict
    website: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ein: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_501c3: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    documents: Mapped[list[OrgDocument]] = relationship(
        "OrgDocument", back_populates="organization", cascade="all, delete-orphan"
    )
    reports: Mapped[list[WeeklyReport]] = relationship("WeeklyReport", back_populates="organization")

    def __repr__(self) -> str:
        return f"<Organization id={self.id!r} name={self.name!r}>"


class OrgDocument(Base):
    __tablename__ = "org_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(100), nullable=False)  # "990", "letter_of_support", etc.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", back_populates="documents")

    def __repr__(self) -> str:
        return f"<OrgDocument id={self.id!r} filename={self.filename!r}>"


# Avoid circular import: WeeklyReport imported via string reference in relationship
from src.models.report import WeeklyReport  # noqa: E402, F401
