"""
OCR Service — orchestrator for the provider-based OCR pipeline.

This module is the public entry point used by the rest of the app
(``app.api.v1.upload`` and ``app.main`` import from here), so its public names
(``process_screenshot``, ``get_ocr_engine``) are preserved for backward
compatibility. Internally it now delegates to a small, focused pipeline:

    decode image
      -> detect + crop the inventory table      (table_detection)
      -> preprocess (gray / denoise / adaptive   (preprocessing)
                     threshold / deskew / sharpen)
      -> OCR via a singleton provider            (provider_factory)
      -> group tokens into structured rows        (row_extractor)
      -> verify each name against the medicine    (matcher)
         database with RapidFuzz (>= threshold)
      -> structured MedicineExtracted results

Per-image cost is kept under the 10s budget by cropping to the table, bounding
the working resolution, and loading each OCR model exactly once.
"""

import logging
import time
from typing import List, Optional

import cv2
import numpy as np

from app.core.config import settings
from app.schemas.medicine import MedicineExtracted
from app.services.ocr.preprocessing import decode_image, preprocess
from app.services.ocr.table_detection import detect_table_region, crop_region
from app.services.ocr.provider_factory import get_provider
from app.services.ocr.row_extractor import extract_rows
from app.services.ocr.matcher import match_medicine
from app.services.ocr.medicine_reference import get_reference_medicines

logger = logging.getLogger(__name__)

# Last-run timing snapshot (handy for health/debug endpoints).
_LAST_TIMING: dict = {}


async def process_screenshot(
    image_bytes: bytes,
    min_confidence: float = None,
    candidate_names: Optional[List[str]] = None,
) -> List[MedicineExtracted]:
    """
    Extract verified medicines from a pharmacy screenshot.

    Args:
        image_bytes: raw image bytes.
        min_confidence: minimum per-token OCR confidence (defaults to config).
        candidate_names: optional list of canonical medicine names to match
            against (e.g. from the DB). Falls back to the built-in reference DB.

    Returns:
        A list of structured ``MedicineExtracted`` results (only names that
        matched a known medicine at >= threshold are kept).
    """
    if min_confidence is None:
        min_confidence = settings.OCR_CONFIDENCE_THRESHOLD

    t_total = time.perf_counter()

    # 1. Decode once (no duplicate decode anywhere in the pipeline).
    img = decode_image(image_bytes)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Detect + crop the inventory table (skip full-screen OCR).
    t_pre = time.perf_counter()
    region = detect_table_region(gray)
    roi = crop_region(img, region)
    # 3. Preprocess the cropped region.
    preprocessed = preprocess(roi)
    pre_time = time.perf_counter() - t_pre

    # 4. OCR via the (singleton) provider — model loaded once, then reused.
    t_ocr = time.perf_counter()
    provider = get_provider()
    words = provider.extract_words(preprocessed)
    ocr_time = time.perf_counter() - t_ocr

    if not words:
        logger.warning("OCR produced no results")
        _record_timing(pre_time, ocr_time, 0.0, time.perf_counter() - t_total, 0)
        return []

    # 5. Group tokens into structured rows; reject UI/date/invoice tokens.
    rows = extract_rows(words, min_confidence)

    # 6. Verify each name against the medicine database (RapidFuzz >= threshold).
    t_match = time.perf_counter()
    candidates = candidate_names or get_reference_medicines()
    threshold = settings.OCR_MATCH_THRESHOLD

    results: List[MedicineExtracted] = []
    for row in rows:
        matched_name, score = match_medicine(row.name, candidates, threshold)
        if matched_name is None:
            logger.debug(
                "Rejected (no medicine DB match >= %.0f): %r", threshold, row.name
            )
            continue

        results.append(
            MedicineExtracted(
                name=row.name,            # medicine_name (as printed)
                matched_name=matched_name,  # canonical DB name
                name_arabic=row.name_arabic,
                current_stock=row.current_stock,
                unit=row.unit,
                expiry=row.expiry,
                confidence=row.confidence,
                verified=True,
            )
        )
    match_time = time.perf_counter() - t_match

    total_time = time.perf_counter() - t_total
    _record_timing(pre_time, ocr_time, match_time, total_time, len(results))

    logger.info(
        "Extracted %d verified medicines from %d candidate rows",
        len(results),
        len(rows),
    )
    return results


def _record_timing(pre: float, ocr: float, match: float, total: float, count: int) -> None:
    """Log detailed per-stage timings (requirement #13)."""
    logger.info(
        "OCR PIPELINE TIMING — preprocessing=%.3fs, ocr=%.3fs, matching=%.3fs, "
        "total=%.3fs, medicines=%d, engine cached",
        pre,
        ocr,
        match,
        total,
        count,
    )
    _LAST_TIMING.update(
        {
            "preprocessing_s": round(pre, 4),
            "ocr_s": round(ocr, 4),
            "matching_s": round(match, 4),
            "total_s": round(total, 4),
            "medicines": count,
        }
    )


def get_last_timing() -> dict:
    """Return the most recent pipeline timing snapshot."""
    return dict(_LAST_TIMING)


# --------------------------------------------------------------------------- #
# Backward-compatible aliases
# --------------------------------------------------------------------------- #
def get_ocr_engine():
    """Alias preserved for ``app.main`` / older callers. Returns the provider."""
    return get_provider()


def warm_up_ocr() -> None:
    """Load the active OCR model once at application startup (singleton)."""
    try:
        get_provider().warm_up()
        logger.info("OCR engine warmed up")
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("OCR warm-up failed (will load on first use): %s", exc)
