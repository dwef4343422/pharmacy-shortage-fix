"""
Medicine Matcher — verify OCR'd names against the medicine database.

Uses RapidFuzz with a ``WRatio`` scorer (good for mixed Arabic/English and
spacing/case differences) and a configurable similarity cutoff (default 90).

A name that matches a known medicine at >= cutoff is accepted and marked
``verified=True`` with its canonical ``matched_name``. A name with no match is
treated as a *random English word / OCR noise* and rejected by the caller
(requirement #11).
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from rapidfuzz import fuzz, process

from app.utils.text_normalizer import normalize_medicine_name

logger = logging.getLogger(__name__)


def _prepare(candidates: List[str]) -> List[str]:
    """Normalize candidate names once for consistent comparison."""
    seen = {}
    for c in candidates:
        if not c:
            continue
        norm = normalize_medicine_name(c)
        if norm:
            seen.setdefault(norm.lower(), norm)
    return list(seen.values())


def match_medicine(
    name: str,
    candidates: List[str],
    threshold: float = 90.0,
) -> Tuple[Optional[str], float]:
    """Return ``(matched_canonical_name, score)`` or ``(None, 0.0)``.

    ``score`` is on the RapidFuzz 0..100 scale. A ``None`` result means the name
    did not meet the similarity threshold (i.e. it is not a known medicine).
    """
    if not name or not candidates:
        return None, 0.0

    query = normalize_medicine_name(name)
    if not query:
        return None, 0.0

    prepared = _prepare(candidates)
    if not prepared:
        return None, 0.0

    best = process.extractOne(
        query,
        prepared,
        scorer=fuzz.WRatio,
        score_cutoff=threshold,
    )
    if best is None:
        return None, 0.0

    matched, score, _idx = best
    return matched, float(score)
