"""
Medicine Model — Individual medicine entries within a shortage report.
"""

import uuid
from enum import Enum as PyEnum

from sqlalchemy import String, Integer, Enum, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Priority(str, PyEnum):
    CRITICAL = "critical"   # Stock = 0
    HIGH = "high"           # Stock 1-5
    MEDIUM = "medium"       # Stock 6-9
    SAFE = "safe"           # Stock >= minimum


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    name_arabic: Mapped[str | None] = mapped_column(String(500), nullable=True)
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    minimum_stock: Mapped[int] = mapped_column(Integer, default=10)
    required_quantity: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[str] = mapped_column(
        Enum(Priority, name="priority_enum", create_constraint=True),
        default=Priority.SAFE,
    )
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_duplicate_merged: Mapped[bool] = mapped_column(default=False)
    merge_count: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Foreign Key
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )

    # Relationship
    report: Mapped["Report"] = relationship("Report", back_populates="medicines")

    def __repr__(self) -> str:
        return f"<Medicine {self.name} stock={self.current_stock} priority={self.priority}>"
