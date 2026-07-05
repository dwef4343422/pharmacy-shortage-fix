"""
Pydantic Schemas — Upload request/response models.
"""

from typing import Optional

from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Response after successful file upload and initial processing."""
    report_id: str
    message: str = "File uploaded and processing started"
    source_type: str
    file_name: str
    file_size_kb: float


class ProcessingStatus(BaseModel):
    """Status of OCR/parsing processing."""
    report_id: str
    status: str  # processing, completed, failed
    progress: int = 0  # 0-100
    step: str = ""  # Current processing step description
    message: Optional[str] = None


class SettingsRequest(BaseModel):
    """User settings update request."""
    default_min_stock: Optional[int] = None
    language: Optional[str] = None
    theme: Optional[str] = None
    export_format: Optional[str] = None
    ocr_sensitivity: Optional[str] = None


class SettingsResponse(BaseModel):
    """User settings response."""
    default_min_stock: int = 10
    language: str = "en"
    theme: str = "light"
    export_format: str = "excel"
    ocr_sensitivity: str = "medium"
