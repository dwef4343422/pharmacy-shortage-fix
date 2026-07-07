"""
File Parser — Excel, CSV, and PDF parsing for medicine extraction.
"""

import io
import logging
from typing import Optional

import pandas as pd

from app.schemas.medicine import MedicineExtracted
from app.utils.text_normalizer import (
    normalize_medicine_name,
    extract_stock_number,
    is_medicine_name,
    split_mixed_language,
)

logger = logging.getLogger(__name__)

# Common column name patterns for medicine name and stock
MEDICINE_NAME_PATTERNS = [
    "medicine", "drug", "item", "product", "name", "description",
    "اسم", "دواء", "صنف", "منتج", "الصنف", "اسم الدواء", "اسم الصنف",
    "medicine name", "drug name", "item name", "product name",
]

STOCK_PATTERNS = [
    "stock", "quantity", "qty", "remaining", "balance", "available", "on hand",
    "count", "inventory", "الكمية", "الرصيد", "المتبقي", "المخزون",
    "current stock", "stock qty", "remaining qty", "available qty",
]


async def parse_excel(file_bytes: bytes, filename: str = "") -> list[MedicineExtracted]:
    """
    Parse an Excel file (.xlsx/.xls) and extract medicine + stock data.
    Uses smart column detection to find relevant columns regardless of header language.
    """
    try:
        df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
        return _extract_from_dataframe(df)
    except Exception as e:
        logger.error(f"Excel parsing failed: {e}")
        # Try older format
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), engine="xlrd")
            return _extract_from_dataframe(df)
        except Exception as e2:
            logger.error(f"Excel parsing (xlrd) also failed: {e2}")
            raise ValueError(f"Could not parse Excel file: {e}")


async def parse_csv(file_bytes: bytes, filename: str = "") -> list[MedicineExtracted]:
    """Parse a CSV file and extract medicine + stock data."""
    try:
        # Try UTF-8 first, then fallback encodings
        for encoding in ["utf-8", "utf-8-sig", "cp1256", "latin-1"]:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
                if len(df.columns) > 1:  # Valid parse
                    return _extract_from_dataframe(df)
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue

        raise ValueError("Could not parse CSV with any supported encoding")

    except Exception as e:
        logger.error(f"CSV parsing failed: {e}")
        raise ValueError(f"Could not parse CSV file: {e}")


async def parse_pdf(file_bytes: bytes, filename: str = "") -> list[MedicineExtracted]:
    """Parse a PDF file by extracting tables."""
    try:
        import pdfplumber

        medicines = []

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()

                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    # Convert table to DataFrame
                    try:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        page_medicines = _extract_from_dataframe(df)
                        medicines.extend(page_medicines)
                    except Exception as e:
                        logger.warning(f"Failed to parse table on page {page_num + 1}: {e}")
                        continue

        if not medicines:
            # Fallback: extract text and try to parse
            logger.warning("No tables found in PDF, attempting text extraction")
            medicines = _extract_from_pdf_text(file_bytes)

        return medicines

    except Exception as e:
        logger.error(f"PDF parsing failed: {e}")
        raise ValueError(f"Could not parse PDF file: {e}")


def _extract_from_dataframe(df: pd.DataFrame) -> list[MedicineExtracted]:
    """
    Extract medicine entries from a pandas DataFrame.
    Automatically detects which columns contain medicine names and stock quantities.
    """
    if df.empty:
        return []

    # Clean column names
    df.columns = [str(col).strip().lower() for col in df.columns]

    # Detect medicine name column
    name_col = _find_column(df, MEDICINE_NAME_PATTERNS)
    stock_col = _find_column(df, STOCK_PATTERNS)

    if name_col is None:
        # Fallback: assume first text column is medicine name
        for col in df.columns:
            if df[col].dtype == object:
                name_col = col
                break

    if name_col is None:
        logger.warning("Could not identify medicine name column")
        return []

    if stock_col is None:
        # Fallback: find first numeric column after the name column
        cols = list(df.columns)
        name_idx = cols.index(name_col) if name_col in cols else 0
        for col in cols[name_idx + 1:]:
            try:
                pd.to_numeric(df[col], errors="coerce")
                if df[col].notna().sum() > 0:
                    stock_col = col
                    break
            except Exception:
                continue

    logger.info(f"Detected columns — Name: '{name_col}', Stock: '{stock_col}'")

    medicines = []
    for _, row in df.iterrows():
        name = str(row.get(name_col, "")).strip()

        if not name or not is_medicine_name(name):
            continue

        stock = 0
        if stock_col:
            stock_val = row.get(stock_col)
            if pd.notna(stock_val):
                extracted = extract_stock_number(str(stock_val))
                stock = extracted if extracted is not None else 0

        normalized_name = normalize_medicine_name(name)
        if not normalized_name:
            continue

        eng_name, ar_name = split_mixed_language(normalized_name)

        medicines.append(
            MedicineExtracted(
                name=eng_name,
                name_arabic=ar_name,
                current_stock=stock,
                confidence=1.0,  # File-based extraction is deterministic
            )
        )

    logger.info(f"Extracted {len(medicines)} medicines from DataFrame")
    return medicines


def _find_column(df: pd.DataFrame, patterns: list[str]) -> Optional[str]:
    """Find the best matching column name from a list of patterns."""
    for pattern in patterns:
        for col in df.columns:
            if pattern in col.lower():
                return col
    return None


def _extract_from_pdf_text(file_bytes: bytes) -> list[MedicineExtracted]:
    """Fallback: extract medicines from PDF text content (no tables)."""
    try:
        import pdfplumber

        medicines = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.strip().split("\n")
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) < 2:
                        continue

                    # Try to find a number at the end of the line (stock)
                    stock = extract_stock_number(parts[-1])
                    if stock is not None:
                        name_parts = parts[:-1]
                        name = " ".join(name_parts)
                        if is_medicine_name(name):
                            eng_name, ar_name = split_mixed_language(
                                normalize_medicine_name(name)
                            )
                            medicines.append(
                                MedicineExtracted(
                                    name=eng_name,
                                    name_arabic=ar_name,
                                    current_stock=stock,
                                    confidence=0.7,
                                )
                            )

        return medicines

    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        return []
