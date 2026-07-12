"""
Row Extractor — turn flat OCR tokens into structured medicine rows.

OCR returns a flat list of words with positions. Inventory screenshots are
tabular, so we:

  1. Group words into rows by vertical (Y) proximity.
  2. Within each row, separate: medicine name, stock number, unit, expiry date.
  3. Drop tokens that are clearly NOT medicine data: UI chrome, buttons, menu
     items, dates (as names), and invoice numbers (requirement #11). Pure
     random English words are filtered later by the matcher (no DB match).

The output is a list of ``CandidateRow`` objects the matcher/pipeline turn into
structured ``MedicineExtracted`` results.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.ocr.providers.base import OCRWord
from app.utils.text_normalizer import (
    extract_stock_number,
    is_medicine_name,
    split_mixed_language,
)

logger = logging.getLogger(__name__)


# --- Rejection helpers (requirement #11) ----------------------------------- #

# Buttons / menu items / UI chrome that frequently appears on pharmacy screens.
UI_KEYWORDS = {
    "file", "edit", "view", "help", "settings", "tools", "window", "exit",
    "save", "delete", "print", "cancel", "ok", "submit", "add", "new", "open",
    "close", "search", "filter", "sort", "export", "import", "upload", "download",
    "login", "logout", "username", "password", "menu", "home", "back", "next",
    "previous", "page", "refresh", "update", "report", "dashboard", "logout",
    "invoice", "bill", "customer", "supplier", "cashier", "admin", "user",
    "date", "time", "total", "subtotal", "amount", "price", "cost", "discount",
    "quantity", "qty", "balance", "settings", "profile", "language", "theme",
}

# Common date formats: 12/05/2024, 2024-05-12, 12-05-24, 5/2024, May 2024.
DATE_RE = re.compile(
    r"""
    (
        \b\d{1,4}[/-]\d{1,2}([/-]\d{1,4})?\b         # 12/05/2024 or 2024-05-12
      | \b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}\b        # 12 May 2024
      | \b[A-Za-z]{3,9}\s+\d{1,2},?\s*\d{2,4}\b      # May 12, 2024
    )
    """,
    re.VERBOSE,
)

# Invoice / reference numbers: INV-1234, #123456, فاتورة 1234, REF 99.
INVOICE_RE = re.compile(
    r"""
    (
        \b(inv|invoice|ref|bill|فاتورة|رقم)\b[-\s:#]*\d{2,}
      | \#\d{3,}
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Unit keywords that may appear next to a stock value.
UNIT_RE = re.compile(
    r"\b(units?|pcs?|pieces?|boxes?|box|tabs?|cap?su?les?|strips?|vials?|"
    r"amps?|ampoules?|packs?|bottles?|kg|g|mg|ml|l)\b",
    re.IGNORECASE,
)


def is_ui_text(text: str) -> bool:
    return text.strip().lower() in UI_KEYWORDS


def is_date(text: str) -> bool:
    return bool(DATE_RE.search(text.strip()))


def is_invoice(text: str) -> bool:
    return bool(INVOICE_RE.search(text.strip()))


def extract_unit(text: str) -> Optional[str]:
    m = UNIT_RE.search(text)
    return m.group(1).lower() if m else None


# --- Candidate row model --------------------------------------------------- #

@dataclass
class CandidateRow:
    name: str
    name_arabic: Optional[str] = None
    current_stock: int = 0
    unit: Optional[str] = None
    expiry: Optional[str] = None
    confidence: float = 1.0
    raw_tokens: List[str] = field(default_factory=list)


# --- Extraction ------------------------------------------------------------ #

_Y_ROW_THRESHOLD = 20  # px proximity to consider tokens on the same row


def _group_rows(words: List[OCRWord]) -> List[List[OCRWord]]:
    ordered = sorted(words, key=lambda w: w.y)
    rows: List[List[OCRWord]] = []
    current: List[OCRWord] = [ordered[0]]

    for item in ordered[1:]:
        if abs(item.y - current[0].y) < _Y_ROW_THRESHOLD:
            current.append(item)
        else:
            rows.append(sorted(current, key=lambda w: w.x))
            current = [item]
    if current:
        rows.append(sorted(current, key=lambda w: w.x))
    return rows


def extract_rows(words: List[OCRWord], min_confidence: float = 0.0) -> List[CandidateRow]:
    """Group OCR words into structured medicine-row candidates."""
    if not words:
        return []

    filtered = [w for w in words if w.confidence >= min_confidence and w.text.strip()]
    if not filtered:
        return []

    rows = _group_rows(filtered)
    candidates: List[CandidateRow] = []

    for row in rows:
        name_tokens: List[str] = []
        numbers: List[tuple[float, int, float]] = []  # (x, value, confidence)
        unit: Optional[str] = None
        expiry: Optional[str] = None

        for tok in row:
            text = tok.text.strip()

            # Structural rejects: dates / invoice numbers / UI chrome.
            if is_date(text):
                expiry = text
                continue
            if is_invoice(text) or is_ui_text(text):
                continue

            # Unit-only token?
            tok_unit = extract_unit(text)
            if tok_unit:
                unit = unit or tok_unit

            # Numeric stock?
            stock = extract_stock_number(text)
            if stock is not None and len(text) <= 8:
                numbers.append((tok.x, stock, tok.confidence))
                continue

            # Otherwise, is it a plausible medicine-name token?
            if is_medicine_name(text):
                name_tokens.append(text)

        if not name_tokens:
            continue

        # Medicine name: join tokens left-to-right.
        raw_name = " ".join(name_tokens)
        eng_name, ar_name = split_mixed_language(raw_name)

        # Stock: prefer the rightmost numeric token (stock column sits right).
        stock_value = 0
        if numbers:
            stock_value = max(numbers, key=lambda n: n[0])[1]

        avg_conf = sum(tok.confidence for tok in row) / len(row)

        candidates.append(
            CandidateRow(
                name=eng_name,
                name_arabic=ar_name,
                current_stock=stock_value,
                unit=unit,
                expiry=expiry,
                confidence=avg_conf,
                raw_tokens=[t.text for t in row],
            )
        )

    logger.info("Extracted %d candidate rows from OCR", len(candidates))
    return candidates
