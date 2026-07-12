"""
Pydantic Schemas — Medicine request/response models.
"""

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class MedicineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    name_arabic: Optional[str] = Field(None, max_length=500)
    current_stock: int = Field(0, ge=0)
    minimum_stock: int = Field(10, ge=0)
    notes: Optional[str] = None


class MedicineCreate(MedicineBase):
    """Used when creating a medicine entry from OCR/parsing results."""
    ocr_confidence: Optional[float] = None
    is_duplicate_merged: bool = False
    merge_count: int = 1


class MedicineUpdate(BaseModel):
    """Used when pharmacist manually edits a medicine entry."""
    name: Optional[str] = None
    name_arabic: Optional[str] = None
    current_stock: Optional[int] = Field(None, ge=0)
    minimum_stock: Optional[int] = Field(None, ge=0)
    required_quantity: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class MedicineResponse(MedicineBase):
    id: uuid.UUID
    required_quantity: int = 0
    priority: str = "safe"
    ocr_confidence: Optional[float] = None
    is_duplicate_merged: bool = False
    merge_count: int = 1

    class Config:
        from_attributes = True


class MedicineExtracted(BaseModel):
    """Raw medicine data extracted from OCR or file parsing."""
    name: str
    matched_name: Optional[str] = None  # canonical DB match (verification)
    name_arabic: Optional[str] = None
    current_stock: int = 0
    unit: Optional[str] = None
    expiry: Optional[str] = None
    confidence: float = 1.0
    verified: bool = False  # matched a known medicine in the DB (>= threshold)
    is_duplicate_merged: bool = False
    merge_count: int = 1
    notes: Optional[str] = None

    def to_structured_json(self) -> dict:
        """Requirement #12 structured JSON shape."""
        return {
            "medicine_name": self.name,
            "matched_name": self.matched_name,
            "current_stock": self.current_stock,
            "unit": self.unit,
            "expiry": self.expiry,
            "confidence": round(self.confidence, 3),
            "verified": self.verified,
        }
