"""
User Model — User accounts and preferences (Phase 2 auth).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    settings: Mapped[dict | None] = mapped_column(
        JSON,
        default=lambda: {
            "default_min_stock": 10,
            "language": "en",
            "theme": "light",
            "export_format": "excel",
            "ocr_sensitivity": "medium",
        },
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"
