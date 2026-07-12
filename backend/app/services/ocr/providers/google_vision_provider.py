"""
Google Vision Provider — cloud OCR fallback.

Optional fallback used when ``GOOGLE_APPLICATION_CREDENTIALS`` (or an explicit
credentials path) is configured. Vision's ``document_text_detection`` returns
word-level bounding polygons in **normalized** (0..1) coordinates, which we
scale back to pixels using the image dimensions so the rest of the pipeline is
backend-agnostic.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

import numpy as np

from .base import BaseOCRProvider, OCRWord, OCRProviderError

logger = logging.getLogger(__name__)


class GoogleVisionProvider(BaseOCRProvider):
    name = "google_vision"

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    def is_available(self) -> bool:
        try:
            import google.cloud.vision  # noqa: F401
        except Exception as exc:  # pragma: no cover - depends on install
            logger.debug(f"Google Vision unavailable: {exc}")
            return False

        # Need either Application Default Credentials or an explicit path.
        if self.credentials_path:
            return os.path.exists(self.credentials_path)
        # ADC may be set via env without a file path (e.g. workload identity).
        return os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is not None

    def _build_client(self):
        from google.cloud import vision

        if self.credentials_path and os.path.exists(self.credentials_path):
            from google.oauth2 import service_account

            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
            return vision.ImageAnnotatorClient(credentials=creds)
        return vision.ImageAnnotatorClient()

    def extract_words(self, image: np.ndarray) -> List[OCRWord]:
        if image is None or image.size == 0:
            return []

        try:
            import google.cloud.vision  # noqa: F401
        except Exception as exc:  # pragma: no cover - depends on install
            raise OCRProviderError("google-cloud-vision is not installed") from exc

        client = self._build_client()

        ok, encoded = cv2_imencode(image)
        if not ok:
            raise OCRProviderError("Failed to encode image for Google Vision")

        from google.cloud import vision

        vision_image = vision.Image(content=encoded.tobytes())
        response = client.document_text_detection(image=vision_image)
        if response.error.message:
            raise OCRProviderError(f"Google Vision error: {response.error.message}")

        h, w = image.shape[:2]
        words: List[OCRWord] = []
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        text = "".join(s.text for s in word.symbols).strip()
                        if not text:
                            continue
                        conf = _word_confidence(word)

                        verts = word.bounding_box.vertices
                        pts = [(v.x if v.x is not None else 0, v.y if v.y is not None else 0)
                               for v in verts]
                        if not pts:
                            continue
                        xs = [p[0] for p in pts]
                        ys = [p[1] for p in pts]
                        # Vertices are normalized 0..1 — scale to pixels.
                        bbox = [[px * w, py * h] for px, py in pts]
                        cx = (sum(xs) / len(xs)) * w
                        cy = (sum(ys) / len(ys)) * h

                        words.append(
                            OCRWord(text=text, confidence=conf, x=cx, y=cy, bbox=bbox)
                        )

        return words


def _word_confidence(word) -> float:
    """Vision gives per-symbol confidences; average them into 0..1."""
    try:
        vals = [s.confidence for s in word.symbols if s.confidence]
        if not vals:
            return 0.0
        # Vision confidences are already 0..1.
        return sum(vals) / len(vals)
    except Exception:
        return 0.0


def cv2_imencode(image: np.ndarray):
    import cv2

    return cv2.imencode(".png", image)
