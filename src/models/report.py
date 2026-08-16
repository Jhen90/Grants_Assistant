# ============================================================
# File: src/models/report.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: WeeklyReport ORM model — generated Jinja2 narrative reports
# ============================================================

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())

    # Snapshot counters (avoid re-querying when viewing old reports)
    grants_evaluated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    grants_recommended: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    grants_in_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    grants_submitted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", back_populates="reports")

    def __repr__(self) -> str:
        return (
            f"<WeeklyReport id={self.id!r} week={self.week_start} → {self.week_end}>"
        )


from src.models.organization import Organization  # noqa: E402, F401
