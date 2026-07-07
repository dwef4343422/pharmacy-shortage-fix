"""
Report Model — Stores shortage report metadata and aggregates.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, Integer, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SourceType(str, PyEnum):
    SCREENSHOT = "screenshot"
    EXCEL = "excel"
    CSV = "csv"
    PDF = "pdf"


class ReportStatus(str, PyEnum):
    PROCESSING = "processing"
    DRAFT = "draft"
    FINALIZED = "finalized"
    EXPORTED = "exported"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(
        String(255), default="Shortage Report"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    source_type: Mapped[str] = mapped_column(
        Enum(SourceType, name="source_type_enum", create_constraint=True),
        default=SourceType.SCREENSHOT,
    )
    status: Mapped[str] = mapped_column(
        Enum(ReportStatus, name="report_status_enum", create_constraint=True),
        default=ReportStatus.PROCESSING,
    )
    total_medicines: Mapped[int] = mapped_column(Integer, default=0)
    below_minimum_count: Mapped[int] = mapped_column(Integer, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    total_required: Mapped[int] = mapped_column(Integer, default=0)
    default_min_stock: Mapped[int] = mapped_column(Integer, default=10)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    medicines: Mapped[list["Medicine"]] = relationship(
        "Medicine", back_populates="report", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Report {self.id} — {self.title} ({self.status})>"
