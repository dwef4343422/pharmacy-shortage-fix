"""
OCR Provider Interface — Abstract base for pluggable OCR engines.

Each provider wraps a concrete OCR backend (PaddleOCR, Google Vision,
Tesseract) and exposes a single normalized method: ``extract_words``.

The provider is responsible for loading its model **once** (singleton) and
returning lightweight ``OCRWord`` objects with pixel-space positions so the
downstream pipeline can reconstruct table rows without re-running OCR.

The heavy model import / initialization happens lazily inside the provider so
that a missing optional dependency (e.g. paddleocr on a constrained deploy)
does not crash application startup.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


@dataclass
class OCRWord:
    """A single recognized text token with position + confidence.

    Coordinates are in **pixel space** of the image passed to ``extract_words``.
    ``x`` / ``y`` are the center of the token; ``bbox`` is the polygon as a list
    of ``[x, y]`` points (used for debugging / future geomety tricks).
    """

    text: str
    confidence: float  # normalized 0..1
    x: float  # center x (px)
    y: float  # center y (px)
    bbox: Optional[List[List[float]]] = None

    def as_dict(self) -> dict:
        return {
            "text": self.text,
            "confidence": round(self.confidence, 4),
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "bbox": self.bbox,
        }


class OCRProviderError(RuntimeError):
    """Raised when a provider cannot initialize or run OCR."""


class BaseOCRProvider(ABC):
    """Contract every OCR backend must satisfy."""

    #: Stable identifier used for config switching and logging.
    name: str = "base"

    def __init__(self, **kwargs) -> None:
        self._config = kwargs

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the underlying engine/library can be used.

        Must be cheap and must NOT load the model — only probe for the
        dependency/credentials. Model loading is deferred to ``extract_words``.
        """
        raise NotImplementedError

    @abstractmethod
    def extract_words(self, image: np.ndarray) -> List[OCRWord]:
        """Run OCR on a single BGR/grayscale image and return text tokens.

        Implementations must load (and cache) their model on first call so the
        model is **not** reloaded per image.
        """
        raise NotImplementedError

    def close(self) -> None:
        """Release any held resources (models, clients). Default: no-op."""
        return None

    def warm_up(self) -> None:
        """Eagerly load the model at startup. Default: no-op.

        Providers with heavy models override this so the app loads the engine
        exactly once on boot (fast first request, stable memory footprint).
        """
        return None

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<{type(self).__name__} name={self.name!r}>"
