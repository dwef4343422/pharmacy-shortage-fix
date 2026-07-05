"""
Text Normalizer — Arabic and English text normalization for medicine names.
"""

import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

# Arabic normalization maps
ARABIC_NORMALIZATION = {
    "\u0622": "\u0627",  # آ -> ا (alef madda -> alef)
    "\u0623": "\u0627",  # أ -> ا (alef hamza above -> alef)
    "\u0625": "\u0627",  # إ -> ا (alef hamza below -> alef)
    "\u0649": "\u064a",  # ى -> ي (alef maksura -> ya)
    "\u0629": "\u0647",  # ة -> ه (ta marbuta -> ha)
}

# Arabic diacritics pattern (tashkeel)
ARABIC_DIACRITICS = re.compile(
    "[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]"
)

# Common OCR misreads for medicine names
OCR_CORRECTIONS = {
    "panad0l": "panadol",
    "augment1n": "augmentin",
    "am0xil": "amoxil",
    "0meprazole": "omeprazole",
    "ibupr0fen": "ibuprofen",
    "metf0rmin": "metformin",
}


def normalize_medicine_name(name: str) -> str:
    """
    Normalize a medicine name for consistent matching.
    Handles Arabic, English, and mixed-language names.
    """
    if not name or not name.strip():
        return ""

    normalized = name.strip()

    # Remove extra whitespace
    normalized = re.sub(r"\s+", " ", normalized)

    # Detect if Arabic
    if _contains_arabic(normalized):
        normalized = normalize_arabic(normalized)
    else:
        normalized = normalize_english(normalized)

    return normalized


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text by removing diacritics and normalizing letters."""
    # Remove diacritics (tashkeel)
    result = ARABIC_DIACRITICS.sub("", text)

    # Apply letter normalization
    for original, replacement in ARABIC_NORMALIZATION.items():
        result = result.replace(original, replacement)

    # Remove tatweel (kashida)
    result = result.replace("\u0640", "")

    return result.strip()


def normalize_english(text: str) -> str:
    """Normalize English text for consistent matching."""
    result = text.lower().strip()

    # Apply known OCR correction patterns
    for misread, correct in OCR_CORRECTIONS.items():
        result = result.replace(misread, correct)

    # Remove non-alphanumeric characters except spaces and hyphens
    result = re.sub(r"[^\w\s\-]", "", result)

    # Normalize Unicode characters
    result = unicodedata.normalize("NFKD", result)

    return result


def _contains_arabic(text: str) -> bool:
    """Check if text contains Arabic characters."""
    return bool(re.search(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]", text))


def extract_stock_number(text: str) -> int | None:
    """
    Extract a numeric stock value from text.
    Handles various formats: '5', '05', '5 units', etc.
    """
    # Remove common non-numeric suffixes
    cleaned = re.sub(r"(units?|pcs?|boxes?|tabs?|caps?|pieces?)", "", text, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    # Try to find a number
    match = re.search(r"(\d+)", cleaned)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def is_medicine_name(text: str) -> bool:
    """
    Heuristic check if a text string is likely a medicine name.
    Filters out UI elements, buttons, headers, etc.
    """
    if not text or len(text.strip()) < 2:
        return False

    text_lower = text.lower().strip()

    # Common non-medicine patterns to exclude
    exclude_patterns = [
        r"^(total|sum|count|page|print|save|delete|edit|cancel|ok|yes|no)$",
        r"^(price|cost|discount|supplier|barcode|category|date|time)$",
        r"^(search|filter|sort|export|import|upload|download)$",
        r"^\d+\.\d+$",  # Pure decimal numbers (likely prices)
        r"^[\d\s\.\,]+$",  # Pure numbers
        r"^.{1}$",  # Single characters
    ]

    for pattern in exclude_patterns:
        if re.match(pattern, text_lower):
            return False

    return True


def split_mixed_language(text: str) -> tuple[str, str | None]:
    """
    Split mixed Arabic+English medicine name into separate components.
    Returns (english_name, arabic_name) or (name, None).
    """
    arabic_parts = []
    english_parts = []

    for word in text.split():
        if _contains_arabic(word):
            arabic_parts.append(word)
        else:
            english_parts.append(word)

    english_name = " ".join(english_parts) if english_parts else text
    arabic_name = " ".join(arabic_parts) if arabic_parts else None

    return english_name, arabic_name
