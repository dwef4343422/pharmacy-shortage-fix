"""
Export API — Generate and download shortage reports in various formats.
"""

import uuid
import logging

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import ReportNotFoundError, ExportError
from app.models.report import Report
from app.services.export_service import export_to_excel, export_to_csv, export_to_pdf

import io

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/reports/{report_id}/export")
async def export_report(
    report_id: uuid.UUID,
    format: str = Query("excel", description="Export format: excel, csv, pdf"),
    db: AsyncSession = Depends(get_db),
):
    """
    Export a shortage report in the specified format.
    
    Supported formats:
    - excel: .xlsx file with colored priority rows
    - csv: .csv file (UTF-8 with BOM)
    - pdf: .pdf with professional table layout
    """
    # Fetch report with medicines
    query = (
        select(Report)
        .options(selectinload(Report.medicines))
        .where(Report.id == report_id)
    )
    result = await db.execute(query)
    report = result.scalar_one_or_none()

    if not report:
        raise ReportNotFoundError(str(report_id))

    # Prepare data dict for export services
    report_data = {
        "title": report.title,
        "created_at": report.created_at.isoformat(),
        "total_medicines": report.total_medicines,
        "below_minimum_count": report.below_minimum_count,
        "critical_count": report.critical_count,
        "total_required": report.total_required,
        "medicines": [
            {
                "name": m.name,
                "name_arabic": m.name_arabic,
                "current_stock": m.current_stock,
                "minimum_stock": m.minimum_stock,
                "required_quantity": m.required_quantity,
                "priority": m.priority.value if hasattr(m.priority, "value") else m.priority,
                "notes": m.notes,
            }
            for m in report.medicines
        ],
    }

    # Sort by priority (critical first)
    priority_order = {"critical": 0, "high": 1, "medium": 2, "safe": 3}
    report_data["medicines"].sort(
        key=lambda m: priority_order.get(m["priority"], 4)
    )

    try:
        if format == "excel":
            file_bytes = export_to_excel(report_data)
            return StreamingResponse(
                io.BytesIO(file_bytes),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=shortage_report_{report_id}.xlsx"
                },
            )

        elif format == "csv":
            file_bytes = export_to_csv(report_data)
            return StreamingResponse(
                io.BytesIO(file_bytes),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=shortage_report_{report_id}.csv"
                },
            )

        elif format == "pdf":
            file_bytes = export_to_pdf(report_data)
            return StreamingResponse(
                io.BytesIO(file_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=shortage_report_{report_id}.pdf"
                },
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported export format: '{format}'. Use: excel, csv, pdf",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise ExportError(f"Failed to generate {format} export: {str(e)}")
