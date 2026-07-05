"""
Duplicate Merger — Smart detection and merging of duplicate medicine entries.
"""

import logging
from collections import defaultdict

from rapidfuzz import fuzz

from app.schemas.medicine import MedicineExtracted
from app.utils.text_normalizer import normalize_medicine_name

logger = logging.getLogger(__name__)

# Similarity threshold for fuzzy matching (0-100)
SIMILARITY_THRESHOLD = 85


def merge_duplicates(
    medicines: list[MedicineExtracted],
    threshold: int = SIMILARITY_THRESHOLD,
) -> list[MedicineExtracted]:
    """
    Merge duplicate medicine entries by summing their stock quantities.
    
    Uses fuzzy string matching to catch near-duplicate names caused by:
    - OCR errors ("Panadol" vs "Panado1")
    - Spacing differences ("Augmentin 625" vs "Augmentin  625")
    - Case differences ("IBUPROFEN" vs "Ibuprofen")
    
    Example:
        Input:  Panadol (stock=2), Panadol (stock=3)
        Output: Panadol (stock=5, merge_count=2)
    """
    if not medicines:
        return []

    if len(medicines) == 1:
        return medicines

    # Group medicines by normalized name (exact matches first)
    groups: dict[str, list[MedicineExtracted]] = defaultdict(list)

    for med in medicines:
        normalized = normalize_medicine_name(med.name).lower()
        groups[normalized].append(med)

    # Fuzzy merge across groups
    merged_groups = _fuzzy_merge_groups(dict(groups), threshold)

    # Create merged results
    results = []
    for group_name, group_medicines in merged_groups.items():
        merged = _merge_group(group_medicines)
        results.append(merged)

    logger.info(
        f"Merged {len(medicines)} entries into {len(results)} unique medicines "
        f"({len(medicines) - len(results)} duplicates removed)"
    )

    return results


def _fuzzy_merge_groups(
    groups: dict[str, list[MedicineExtracted]],
    threshold: int,
) -> dict[str, list[MedicineExtracted]]:
    """
    Merge groups whose keys are fuzzy-similar above the threshold.
    """
    keys = list(groups.keys())
    merged_keys: dict[str, str] = {}  # Maps each key to its canonical form

    for i, key_a in enumerate(keys):
        if key_a in merged_keys:
            continue

        merged_keys[key_a] = key_a

        for key_b in keys[i + 1:]:
            if key_b in merged_keys:
                continue

            similarity = fuzz.ratio(key_a, key_b)

            if similarity >= threshold:
                merged_keys[key_b] = key_a
                logger.debug(
                    f"Fuzzy merged '{key_b}' into '{key_a}' "
                    f"(similarity={similarity}%)"
                )

    # Rebuild groups using canonical keys
    result: dict[str, list[MedicineExtracted]] = defaultdict(list)
    for key, medicines in groups.items():
        canonical = merged_keys.get(key, key)
        result[canonical].extend(medicines)

    return dict(result)


def _merge_group(medicines: list[MedicineExtracted]) -> MedicineExtracted:
    """
    Merge a group of duplicate medicines into a single entry.
    
    - Sum stock quantities
    - Use the name with highest OCR confidence
    - Track merge count
    """
    if len(medicines) == 1:
        return medicines[0]

    # Pick the best name (highest confidence)
    best = max(medicines, key=lambda m: m.confidence)

    # Sum stock quantities
    total_stock = sum(m.current_stock for m in medicines)

    # Average confidence
    avg_confidence = sum(m.confidence for m in medicines) / len(medicines)

    # Use Arabic name from any entry that has it
    arabic_name = best.name_arabic
    if not arabic_name:
        for m in medicines:
            if m.name_arabic:
                arabic_name = m.name_arabic
                break

    return MedicineExtracted(
        name=best.name,
        name_arabic=arabic_name,
        current_stock=total_stock,
        confidence=avg_confidence,
        is_duplicate_merged=len(medicines) > 1,
        merge_count=len(medicines),
    )
