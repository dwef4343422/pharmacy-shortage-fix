"""
Shortage Engine — Core business logic for shortage calculation.
"""

import logging
import uuid
from datetime import datetime, timezone

from app.schemas.medicine import MedicineExtracted, MedicineCreate
from app.schemas.report import ReportCreate
from app.services.priority_service import classify_priority
from app.services.duplicate_merger import merge_duplicates
from app.models.medicine import Priority

logger = logging.getLogger(__name__)


def calculate_shortage(
    extracted_medicines: list[MedicineExtracted],
    default_min_stock: int = 10,
    merge_duplicates_flag: bool = True,
) -> ReportCreate:
    """
    Full shortage calculation pipeline.
    
    Steps:
    1. Merge duplicates
    2. For each medicine, calculate required quantity
    3. Classify priority
    4. Filter out medicines at or above minimum stock
    5. Generate report with statistics
    """
    # Step 1: Merge duplicates
    if merge_duplicates_flag and len(extracted_medicines) > 1:
        medicines = merge_duplicates(extracted_medicines)
    else:
        medicines = extracted_medicines

    # Step 2-4: Process each medicine
    shortage_medicines: list[MedicineCreate] = []
    total_required = 0
    critical_count = 0
    below_minimum_count = 0

    for med in medicines:
        min_stock = default_min_stock
        priority = classify_priority(med.current_stock, min_stock)

        # Calculate required quantity
        if med.current_stock < min_stock:
            required_qty = min_stock - med.current_stock
        else:
            required_qty = 0

        # Create medicine entry
        medicine_entry = MedicineCreate(
            name=med.name,
            name_arabic=med.name_arabic,
            current_stock=med.current_stock,
            minimum_stock=min_stock,
            ocr_confidence=med.confidence,
            is_duplicate_merged=med.is_duplicate_merged,
            merge_count=med.merge_count,
            notes=med.notes,
        )

        shortage_medicines.append(medicine_entry)

        # Update statistics
        if priority != Priority.SAFE:
            below_minimum_count += 1
            total_required += required_qty
        if priority == Priority.CRITICAL:
            critical_count += 1

    # Step 5: Generate report
    now = datetime.now(timezone.utc)
    report = ReportCreate(
        title=f"Shortage Report — {now.strftime('%Y-%m-%d %H:%M')}",
        source_type="screenshot",
        default_min_stock=default_min_stock,
        medicines=shortage_medicines,
    )

    logger.info(
        f"Shortage report generated: {len(shortage_medicines)} medicines, "
        f"{below_minimum_count} below minimum, {critical_count} critical, "
        f"{total_required} total required"
    )

    return report


def recalculate_report_stats(
    medicines: list[dict], default_min_stock: int = 10
) -> dict:
    """
    Recalculate report statistics after manual edits.
    Returns updated totals for the report.
    """
    total_medicines = len(medicines)
    below_minimum_count = 0
    critical_count = 0
    total_required = 0

    for med in medicines:
        current = med.get("current_stock", 0)
        min_stock = med.get("minimum_stock", default_min_stock)
        priority = classify_priority(current, min_stock)

        if priority != Priority.SAFE:
            below_minimum_count += 1
            total_required += max(0, min_stock - current)
        if priority == Priority.CRITICAL:
            critical_count += 1

    return {
        "total_medicines": total_medicines,
        "below_minimum_count": below_minimum_count,
        "critical_count": critical_count,
        "total_required": total_required,
    }
