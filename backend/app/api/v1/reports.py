"""
Reports API — CRUD operations for shortage reports.
"""

import uuid
import logging

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import ReportNotFoundError
from app.schemas.report import ReportResponse, ReportUpdate, ReportSummary, ReportListResponse
from app.schemas.medicine import MedicineUpdate, MedicineResponse
from app.models.report import Report, ReportStatus
from app.models.medicine import Medicine
from app.services.priority_service import classify_priority
from app.services.shortage_engine import recalculate_report_stats

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/reports", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None, description="Search by report title"),
    db: AsyncSession = Depends(get_db),
):
    """List all reports with pagination and optional search."""
    query = select(Report).order_by(desc(Report.created_at))

    if search:
        query = query.where(Report.title.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    reports = result.scalars().all()

    return ReportListResponse(
        reports=[ReportSummary.model_validate(r) for r in reports],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single report with all its medicines."""
    query = (
        select(Report)
        .options(selectinload(Report.medicines))
        .where(Report.id == report_id)
    )
    result = await db.execute(query)
    report = result.scalar_one_or_none()

    if not report:
        raise ReportNotFoundError(str(report_id))

    return report


@router.put("/reports/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: uuid.UUID,
    update: ReportUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update report metadata (title, status, notes)."""
    query = (
        select(Report)
        .options(selectinload(Report.medicines))
        .where(Report.id == report_id)
    )
    result = await db.execute(query)
    report = result.scalar_one_or_none()

    if not report:
        raise ReportNotFoundError(str(report_id))

    # Apply updates
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            setattr(report, field, ReportStatus(value))
        elif value is not None:
            setattr(report, field, value)

    await db.flush()
    await db.refresh(report, attribute_names=["medicines"])
    return report


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a report and all its medicines."""
    query = select(Report).where(Report.id == report_id)
    result = await db.execute(query)
    report = result.scalar_one_or_none()

    if not report:
        raise ReportNotFoundError(str(report_id))

    await db.delete(report)
    return {"message": "Report deleted successfully", "id": str(report_id)}


@router.put("/reports/{report_id}/medicines/{medicine_id}", response_model=MedicineResponse)
async def update_medicine(
    report_id: uuid.UUID,
    medicine_id: uuid.UUID,
    update: MedicineUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a single medicine entry (manual edit by pharmacist).
    Recalculates priority and required quantity automatically.
    """
    query = (
        select(Medicine)
        .where(Medicine.id == medicine_id, Medicine.report_id == report_id)
    )
    result = await db.execute(query)
    medicine = result.scalar_one_or_none()

    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")

    # Apply updates
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(medicine, field, value)

    # Recalculate priority and required quantity
    medicine.priority = classify_priority(medicine.current_stock, medicine.minimum_stock)
    medicine.required_quantity = max(0, medicine.minimum_stock - medicine.current_stock)

    # Recalculate report statistics
    report_query = (
        select(Report)
        .options(selectinload(Report.medicines))
        .where(Report.id == report_id)
    )
    report_result = await db.execute(report_query)
    report = report_result.scalar_one_or_none()

    if report:
        medicines_data = [
            {"current_stock": m.current_stock, "minimum_stock": m.minimum_stock}
            for m in report.medicines
        ]
        stats = recalculate_report_stats(medicines_data, report.default_min_stock)
        report.total_medicines = stats["total_medicines"]
        report.below_minimum_count = stats["below_minimum_count"]
        report.critical_count = stats["critical_count"]
        report.total_required = stats["total_required"]

    await db.flush()
    await db.refresh(medicine)
    return medicine


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics across all reports."""
    # Latest report
    latest_query = select(Report).order_by(desc(Report.created_at)).limit(1)
    latest_result = await db.execute(latest_query)
    latest_report = latest_result.scalar_one_or_none()

    # Total reports count
    count_result = await db.execute(select(func.count(Report.id)))
    total_reports = count_result.scalar() or 0

    # Most frequently missing medicines (across all reports)
    freq_query = (
        select(
            Medicine.name,
            func.count(Medicine.id).label("frequency"),
            func.min(Medicine.current_stock).label("lowest_stock"),
        )
        .where(Medicine.priority != "safe")
        .group_by(Medicine.name)
        .order_by(desc("frequency"))
        .limit(10)
    )
    freq_result = await db.execute(freq_query)
    frequent_medicines = [
        {"name": row.name, "frequency": row.frequency, "lowest_stock": row.lowest_stock}
        for row in freq_result
    ]

    return {
        "total_reports": total_reports,
        "latest_report": {
            "id": str(latest_report.id) if latest_report else None,
            "title": latest_report.title if latest_report else None,
            "created_at": latest_report.created_at.isoformat() if latest_report else None,
            "total_medicines": latest_report.total_medicines if latest_report else 0,
            "below_minimum_count": latest_report.below_minimum_count if latest_report else 0,
            "critical_count": latest_report.critical_count if latest_report else 0,
            "total_required": latest_report.total_required if latest_report else 0,
        } if latest_report else None,
        "frequent_missing_medicines": frequent_medicines,
    }
