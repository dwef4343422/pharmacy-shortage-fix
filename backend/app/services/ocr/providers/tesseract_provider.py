"""
Tesseract Provider — lightweight CPU fallback OCR engine.

Used when PaddleOCR (or Google Vision) is unavailable. Tesseract is slower and
less accurate on dense inventory tables, but it has no heavy model download and
is almost always present on a server image, making it a safe fallback.
"""

from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np

from .base import BaseOCRProvider, OCRWord, OCRProviderError

logger = logging.getLogger(__name__)


class TesseractProvider(BaseOCRProvider):
    name = "tesseract"

    def __init__(self, lang: str = "eng+ara", tesseract_cmd: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        # Accept either "en,ar" (our config format) or "eng+ara" (tesseract).
        self.lang = lang.replace(",", "+")
        self.tesseract_cmd = tesseract_cmd

    def is_available(self) -> bool:
        try:
            import pytesseract  # noqa: F401

            # Cheap sanity check that the binary exists.
            import shutil

            return shutil.which("tesseract") is not None or self.tesseract_cmd is not None
        except Exception as exc:  # pragma: no cover - depends on install
            logger.debug(f"Tesseract unavailable: {exc}")
            return False

    def extract_words(self, image: np.ndarray) -> List[OCRWord]:
        if image is None or image.size == 0:
            return []

        try:
            import pytesseract
        except Exception as exc:  # pragma: no cover - depends on install
            raise OCRProviderError("pytesseract is not installed") from exc

        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            lang=self.lang,
        )

        words: List[OCRWord] = []
        n = len(data.get("text", []))
        for i in range(n):
            text = (data["text"][i] or "").strip()
            if not text:
                continue

            raw_conf = data["conf"][i]
            conf = int(raw_conf) if isinstance(raw_conf, (int, float)) else 0
            # Tesseract reports -1 for word groups it skipped; treat as 0.
            conf = max(0, conf) / 100.0

            left = data["left"][i]
            top = data["top"][i]
            w = data["width"][i]
            h = data["height"][i]
            x = left + w / 2
            y = top + h / 2

            words.append(
                OCRWord(
                    text=text,
                    confidence=conf,
                    x=x,
                    y=y,
                    bbox=[[left, top], [left + w, top], [left + w, top + h], [left, top + h]],
                )
            )

        return words
