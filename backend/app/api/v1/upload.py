"""
Upload API — File upload and OCR processing endpoints.
"""

import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import FileValidationError, OCRProcessingError
from app.schemas.upload import UploadResponse
from app.schemas.report import ReportResponse
from app.services.ocr_service import process_screenshot
from app.services.file_parser import parse_excel, parse_csv, parse_pdf
from app.services.shortage_engine import calculate_shortage
from app.services.priority_service import classify_priority
from app.models.report import Report, SourceType, ReportStatus
from app.models.medicine import Medicine

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/bmp", "image/tiff"}
ALLOWED_FILE_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv",
    "application/pdf",
}


def _detect_source_type(content_type: str, filename: str) -> str:
    """Detect the source type from file content type and name."""
    if content_type in ALLOWED_IMAGE_TYPES:
        return "screenshot"
    
    ext = Path(filename).suffix.lower() if filename else ""
    if ext in (".xlsx", ".xls") or "spreadsheet" in content_type or "excel" in content_type:
        return "excel"
    elif ext == ".csv" or content_type == "text/csv":
        return "csv"
    elif ext == ".pdf" or content_type == "application/pdf":
        return "pdf"
    elif content_type in ALLOWED_IMAGE_TYPES or ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff"):
        return "screenshot"
    
    return "screenshot"  # Default fallback


@router.post("/upload", response_model=ReportResponse)
async def upload_file(
    file: UploadFile = File(...),
    min_stock: int = Query(default=10, ge=1, description="Default minimum stock level"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a file (screenshot, Excel, CSV, or PDF) and process it into a shortage report.
    
    The endpoint:
    1. Validates the file type and size
    2. Routes to the appropriate parser (OCR for images, parsers for files)
    3. Merges duplicates and calculates shortages
    4. Saves the report to the database
    5. Returns the complete report
    """
    # Validate file size
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)

    if file_size_mb > settings.UPLOAD_MAX_SIZE_MB:
        raise FileValidationError(
            f"File too large ({file_size_mb:.1f} MB). "
            f"Maximum allowed: {settings.UPLOAD_MAX_SIZE_MB} MB."
        )

    if not file.filename:
        raise FileValidationError("No filename provided")

    # Detect source type
    source_type = _detect_source_type(file.content_type or "", file.filename)
    logger.info(f"Upload received: {file.filename} ({file_size_mb:.2f} MB, type: {source_type})")

    # Process file based on type
    try:
        if source_type == "screenshot":
            extracted = await process_screenshot(content)
        elif source_type == "excel":
            extracted = await parse_excel(content, file.filename)
        elif source_type == "csv":
            extracted = await parse_csv(content, file.filename)
        elif source_type == "pdf":
            extracted = await parse_pdf(content, file.filename)
        else:
            raise FileValidationError(f"Unsupported file type: {source_type}")
    except FileValidationError:
        raise
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise OCRProcessingError(f"Failed to process file: {str(e)}")

    if not extracted:
        raise OCRProcessingError(
            "No medicine data could be extracted from the file. "
            "Please ensure the file contains a table with medicine names and stock quantities."
        )

    # Calculate shortage report
    report_data = calculate_shortage(extracted, default_min_stock=min_stock)
    report_data.source_type = source_type

    # Save to database
    db_report = Report(
        title=report_data.title,
        source_type=SourceType(source_type),
        status=ReportStatus.DRAFT,
        default_min_stock=min_stock,
        total_medicines=len(report_data.medicines),
        notes=report_data.notes,
    )

    # Process and save medicines
    below_minimum = 0
    critical = 0
    total_required = 0

    for med_data in report_data.medicines:
        priority = classify_priority(med_data.current_stock, med_data.minimum_stock)
        required_qty = max(0, med_data.minimum_stock - med_data.current_stock)

        db_medicine = Medicine(
            name=med_data.name,
            name_arabic=med_data.name_arabic,
            current_stock=med_data.current_stock,
            minimum_stock=med_data.minimum_stock,
            required_quantity=required_qty,
            priority=priority,
            ocr_confidence=med_data.ocr_confidence,
            is_duplicate_merged=med_data.is_duplicate_merged,
            merge_count=med_data.merge_count,
            notes=med_data.notes,
            report_id=db_report.id,
        )
        db_report.medicines.append(db_medicine)

        if priority.value != "safe":
            below_minimum += 1
            total_required += required_qty
        if priority.value == "critical":
            critical += 1

    db_report.below_minimum_count = below_minimum
    db_report.critical_count = critical
    db_report.total_required = total_required

    db.add(db_report)
    await db.flush()
    await db.refresh(db_report, attribute_names=["medicines"])

    logger.info(
        f"Report created: {db_report.id} — "
        f"{len(db_report.medicines)} medicines, {critical} critical"
    )

    return db_report
