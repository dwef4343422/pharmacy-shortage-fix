"""
OCR Provider Factory — config-driven selection + singleton caching.

Selection rules
---------------
1. Honour ``settings.OCR_ENGINE`` (``paddleocr`` | ``google_vision`` |
   ``tesseract``).
2. The chosen provider is only used if its dependency/credentials are present
   (``is_available()``). Otherwise we fall back through the priority chain
   ``paddleocr -> google_vision -> tesseract`` so the app never hard-fails just
   because the preferred engine isn't installed.
3. Each provider instance is cached process-wide. Because providers load their
   models lazily and cache them internally, calling ``get_provider()`` again
   returns the exact same (already-warm) engine — the model is never reloaded
   per request.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from app.core.config import settings
from app.services.ocr.providers.base import BaseOCRProvider
from app.services.ocr.providers.paddleocr_provider import PaddleOCRProvider
from app.services.ocr.providers.tesseract_provider import TesseractProvider
from app.services.ocr.providers.google_vision_provider import GoogleVisionProvider

logger = logging.getLogger(__name__)

# Process-wide cache keyed by requested engine name.
_PROVIDERS: Dict[str, BaseOCRProvider] = {}

# Fallback priority when the configured engine is unavailable.
_FALLBACK_ORDER = ("paddleocr", "google_vision", "tesseract")


def _make(engine: str) -> BaseOCRProvider:
    """Instantiate a provider for a given engine id (no availability check)."""
    engine = (engine or "tesseract").lower()
    if engine == "paddleocr":
        lang = _primary_lang()
        return PaddleOCRProvider(lang=lang)
    if engine == "google_vision":
        return GoogleVisionProvider(
            credentials_path=getattr(settings, "GOOGLE_VISION_CREDENTIALS", None)
        )
    # default / tesseract
    return TesseractProvider(
        lang=settings.OCR_LANGUAGE or "eng+ara",
        tesseract_cmd=getattr(settings, "TESSERACT_PATH", None),
    )


def _primary_lang() -> str:
    """PaddleOCR uses a single primary lang id (e.g. 'en', 'ar', 'ch')."""
    langs = (settings.OCR_LANGUAGE or "en").split(",")
    return langs[0].strip() or "en"


def get_provider(engine: Optional[str] = None) -> BaseOCRProvider:
    """Return the (cached) OCR provider to use, honoring config + fallbacks."""
    requested = (engine or settings.OCR_ENGINE or "paddleocr").lower()

    # Fast path: already cached for this request key.
    if requested in _PROVIDERS:
        return _PROVIDERS[requested]

    order = [requested] + [e for e in _FALLBACK_ORDER if e != requested]
    last_error: Optional[Exception] = None

    for candidate in order:
        try:
            provider = _make(candidate)
            if provider.is_available():
                logger.info("OCR provider selected: %s", provider.name)
                _PROVIDERS[requested] = provider
                return provider
            logger.warning("OCR provider '%s' reported unavailable", candidate)
        except Exception as exc:  # pragma: no cover - defensive
            last_error = exc
            logger.warning("OCR provider '%s' failed to build: %s", candidate, exc)

    # Last resort: return the configured provider even if not available so the
    # caller can surface a clear runtime error instead of crashing startup.
    logger.error(
        "No available OCR provider found (last_error=%s). "
        "Falling back to '%s' which may fail at runtime.",
        last_error,
        requested,
    )
    provider = _make(requested)
    _PROVIDERS[requested] = provider
    return provider


def reset_providers() -> None:
    """Clear the cache (used by tests / config reloads)."""
    _PROVIDERS.clear()
