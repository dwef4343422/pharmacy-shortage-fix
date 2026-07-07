"""
OCR Service — PaddleOCR and Tesseract integration for medicine extraction.
"""

import logging
import re
from typing import Optional

import numpy as np

from app.core.config import settings
from app.schemas.medicine import MedicineExtracted
from app.utils.image_preprocessing import preprocess_image
from app.utils.text_normalizer import (
    normalize_medicine_name,
    extract_stock_number,
    is_medicine_name,
    split_mixed_language,
)

logger = logging.getLogger(__name__)

# Global OCR engine instance (singleton)
_ocr_engine = None


def get_ocr_engine():
    """Get or initialize the PaddleOCR engine (singleton pattern)."""
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from paddleocr import PaddleOCR

            _ocr_engine = PaddleOCR(
                use_angle_cls=True,
                lang="en",  # Use English model (handles numbers well)
                show_log=False,
                use_gpu=False,
                enable_mkldnn=True,
            )
            logger.info("PaddleOCR engine initialized successfully")
        except ImportError:
            logger.warning("PaddleOCR not available, falling back to Tesseract")
            _ocr_engine = "tesseract"
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            _ocr_engine = "tesseract"

    return _ocr_engine


async def process_screenshot(image_bytes: bytes, min_confidence: float = None) -> list[MedicineExtracted]:
    """
    Process a screenshot image and extract medicine names + stock quantities.
    
    Pipeline:
    1. Preprocess image for optimal OCR
    2. Run OCR to get all text blocks with positions
    3. Detect table structure from text positions
    4. Extract medicine name + stock pairs
    5. Normalize and validate results
    """
    if min_confidence is None:
        min_confidence = settings.OCR_CONFIDENCE_THRESHOLD

    # Step 1: Preprocess
    preprocessed = preprocess_image(image_bytes)

    # Step 2: Run OCR
    ocr_results = _run_ocr(preprocessed)

    if not ocr_results:
        logger.warning("OCR produced no results")
        return []

    # Step 3: Parse table structure and extract medicines
    medicines = _extract_medicines_from_ocr(ocr_results, min_confidence)

    logger.info(f"Extracted {len(medicines)} medicines from screenshot")
    return medicines


def _run_ocr(image: np.ndarray) -> list[dict]:
    """Run OCR engine on preprocessed image."""
    engine = get_ocr_engine()

    if engine == "tesseract":
        return _run_tesseract(image)

    try:
        results = engine.ocr(image, cls=True)

        if not results or not results[0]:
            return []

        parsed = []
        for line in results[0]:
            bbox = line[0]
            text = line[1][0]
            confidence = line[1][1]

            # Calculate center position for table structure detection
            x_center = sum(p[0] for p in bbox) / 4
            y_center = sum(p[1] for p in bbox) / 4

            parsed.append({
                "text": text.strip(),
                "confidence": confidence,
                "x": x_center,
                "y": y_center,
                "bbox": bbox,
            })

        return parsed

    except Exception as e:
        logger.error(f"PaddleOCR failed: {e}, falling back to Tesseract")
        return _run_tesseract(image)


def _run_tesseract(image: np.ndarray) -> list[dict]:
    """Fallback OCR using Tesseract."""
    try:
        import pytesseract

        if settings.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH

        # Get detailed data with positions
        data = pytesseract.image_to_data(
            image, output_type=pytesseract.Output.DICT, lang="eng+ara"
        )

        parsed = []
        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            conf = int(data["conf"][i]) if data["conf"][i] != "-1" else 0

            if not text or conf < 20:
                continue

            parsed.append({
                "text": text,
                "confidence": conf / 100.0,
                "x": data["left"][i] + data["width"][i] / 2,
                "y": data["top"][i] + data["height"][i] / 2,
                "bbox": None,
            })

        return parsed

    except Exception as e:
        logger.error(f"Tesseract OCR failed: {e}")
        return []


def _extract_medicines_from_ocr(
    ocr_results: list[dict], min_confidence: float
) -> list[MedicineExtracted]:
    """
    Extract medicine-stock pairs from OCR results by detecting table structure.
    
    Strategy:
    1. Sort results by Y position (top to bottom = rows)
    2. Group into rows by Y proximity
    3. Within each row, find medicine name (text) and stock (number)
    """
    if not ocr_results:
        return []

    # Filter by confidence
    results = [r for r in ocr_results if r["confidence"] >= min_confidence]

    if not results:
        return []

    # Sort by Y position (top to bottom)
    results.sort(key=lambda r: r["y"])

    # Group into rows (items within Y_THRESHOLD pixels are same row)
    Y_THRESHOLD = 20
    rows: list[list[dict]] = []
    current_row: list[dict] = [results[0]]

    for item in results[1:]:
        if abs(item["y"] - current_row[0]["y"]) < Y_THRESHOLD:
            current_row.append(item)
        else:
            rows.append(sorted(current_row, key=lambda r: r["x"]))
            current_row = [item]

    if current_row:
        rows.append(sorted(current_row, key=lambda r: r["x"]))

    # Extract medicines from rows
    medicines = []
    for row in rows:
        medicine = _parse_row(row)
        if medicine:
            medicines.append(medicine)

    return medicines


def _parse_row(row_items: list[dict]) -> Optional[MedicineExtracted]:
    """
    Parse a single table row to extract medicine name and stock.
    
    Heuristics:
    - Text items that pass is_medicine_name check -> medicine name
    - Numeric items -> potential stock value
    - Prioritize the first text and first number found
    """
    texts = []
    numbers = []

    for item in row_items:
        text = item["text"].strip()

        # Try to extract number
        stock = extract_stock_number(text)
        if stock is not None and len(text) <= 6:  # Short numeric strings = stock
            numbers.append({
                "value": stock,
                "confidence": item["confidence"],
                "x": item["x"],
            })
        elif is_medicine_name(text):
            texts.append({
                "text": text,
                "confidence": item["confidence"],
                "x": item["x"],
            })

    if not texts:
        return None

    # Use the leftmost text as medicine name (typically first column)
    name_item = min(texts, key=lambda t: t["x"])
    medicine_name = normalize_medicine_name(name_item["text"])

    if not medicine_name or len(medicine_name) < 2:
        return None

    # Find stock: use the rightmost number (stock column is usually right)
    stock_value = 0
    if numbers:
        stock_item = max(numbers, key=lambda n: n["x"])
        stock_value = stock_item["value"]

    # Split mixed language names
    eng_name, ar_name = split_mixed_language(medicine_name)

    avg_confidence = sum(item["confidence"] for item in row_items) / len(row_items)

    return MedicineExtracted(
        name=eng_name,
        name_arabic=ar_name,
        current_stock=stock_value,
        confidence=avg_confidence,
    )
