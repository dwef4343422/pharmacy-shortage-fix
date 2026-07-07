"""
Pydantic Schemas — Report request/response models.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.medicine import MedicineResponse, MedicineCreate


class ReportCreate(BaseModel):
    title: str = Field("Shortage Report", max_length=255)
    source_type: str = "screenshot"
    default_min_stock: int = Field(10, ge=1)
    medicines: list[MedicineCreate] = []
    notes: Optional[str] = None


class ReportUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    default_min_stock: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = None


class ReportResponse(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    source_type: str
    status: str
    total_medicines: int = 0
    below_minimum_count: int = 0
    critical_count: int = 0
    total_required: int = 0
    default_min_stock: int = 10
    notes: Optional[str] = None
    medicines: list[MedicineResponse] = []

    class Config:
        from_attributes = True


class ReportSummary(BaseModel):
    """Lightweight report for list views."""
    id: uuid.UUID
    title: str
    created_at: datetime
    source_type: str
    status: str
    total_medicines: int = 0
    below_minimum_count: int = 0
    critical_count: int = 0
    total_required: int = 0

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    reports: list[ReportSummary]
    total: int
    page: int
    page_size: int
