"""
PaddleOCR Provider — primary, high-accuracy OCR engine.

The PaddleOCR model is large and slow to initialize, so it is loaded **once**
and cached on the class. Every image after the first reuses the same in-memory
engine, which is what keeps per-image processing well under the 10s budget.

PaddleOCR 2.x and 3.x have different APIs:
  * 2.x: ``PaddleOCR(use_angle_cls=, lang=, show_log=, use_gpu=,
    enable_mkldnn=)`` and ``ocr(img, cls=)`` returning
    ``[[ [bbox], (text, conf) ], ...]``.
  * 3.x: ``PaddleOCR(lang=, use_textline_orientation=)`` and ``ocr(img)``
    returning ``[ {rec_texts, rec_scores, rec_polys, ...} ]`` (one dict per
    image, via the paddlex backend).

This provider detects the major version and adapts both construction and result
parsing, so the rest of the pipeline is unaffected by which release is installed.
"""

from __future__ import annotations

import logging
import os

# PaddlePaddle 3.x on CPU uses a oneDNN/PIR path that raises
# "ConvertPirAttribute2RuntimeAttribute ... not support" on Windows. Disable the
# oneDNN backend before paddle is first imported so CPU inference works.
os.environ.setdefault("FLAGS_use_mkldnn", "0")

from typing import List, Optional

import numpy as np

from .base import BaseOCRProvider, OCRWord, OCRProviderError

logger = logging.getLogger(__name__)


class PaddleOCRProvider(BaseOCRProvider):
    name = "paddleocr"

    # Class-level singleton: the model is loaded once for the whole process.
    _engine = None

    def __init__(
        self,
        lang: str = "en",
        use_gpu: bool = False,
        use_angle_cls: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.lang = lang
        self.use_gpu = use_gpu
        self.use_angle_cls = use_angle_cls
        self._version = self._detect_major_version()

    # ------------------------------------------------------------------ #
    @staticmethod
    def _detect_major_version() -> int:
        try:
            import paddleocr

            v = getattr(paddleocr, "__version__", "0")
            return int(v.split(".")[0])
        except Exception:
            return 0

    # ------------------------------------------------------------------ #
    # Availability probe — only checks the dependency is importable.
    # ------------------------------------------------------------------ #
    def is_available(self) -> bool:
        try:
            import paddleocr  # noqa: F401

            # 3.x requires paddlepaddle (the paddlex backend) to actually run.
            if self._detect_major_version() >= 3:
                try:
                    import paddle  # noqa: F401

                    return True
                except Exception:
                    return False
            return True
        except Exception as exc:  # pragma: no cover - depends on install
            logger.debug(f"PaddleOCR unavailable: {exc}")
            return False

    # ------------------------------------------------------------------ #
    # Lazy, cached model construction.
    # ------------------------------------------------------------------ #
    def warm_up(self) -> None:
        """Load (and cache) the PaddleOCR model at startup — once, per process."""
        self._ensure_engine()

    def _ensure_engine(self):
        if PaddleOCRProvider._engine is None:
            try:
                from paddleocr import PaddleOCR
            except Exception as exc:
                raise OCRProviderError(f"paddleocr is not installed: {exc}") from exc

            logger.info(
                "Loading PaddleOCR model (lang=%s, version=%s) — one-time init",
                self.lang,
                self._version,
            )
            if self._version >= 3:
                # PaddleOCR 3.x API (paddlex backend). No show_log/use_gpu kwargs.
                # Disable the doc-orientation + unwarping sub-models to keep the
                # pipeline fast (they are unnecessary for upright screenshots).
                try:
                    import paddle

                    paddle.set_flags({"FLAGS_use_mkldnn": False})
                except Exception:  # pragma: no cover - paddle import guarded above
                    pass
                # Use the lighter "mobile" detection/recognition models instead of
                # the default "medium" ones: on CPU (MKLDNN disabled to avoid a
                # paddle 3.x oneDNN/PIR crash) the mobile models are several times
                # faster while still very accurate on printed pharmacy text.
                kwargs_3x = dict(
                    lang=self.lang,
                    use_textline_orientation=self.use_angle_cls,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    enable_mkldnn=False,
                )
                if (self.lang or "en").lower().startswith("en"):
                    kwargs_3x["text_detection_model_name"] = "PP-OCRv4_mobile_det"
                    kwargs_3x["text_recognition_model_name"] = "en_PP-OCRv4_mobile_rec"
                PaddleOCRProvider._engine = PaddleOCR(**kwargs_3x)
            else:
                # PaddleOCR 2.x API.
                PaddleOCRProvider._engine = PaddleOCR(
                    use_angle_cls=self.use_angle_cls,
                    lang=self.lang,
                    show_log=False,
                    use_gpu=self.use_gpu,
                    enable_mkldnn=True,
                )
            logger.info("PaddleOCR model loaded and cached")
        return PaddleOCRProvider._engine

    # ------------------------------------------------------------------ #
    # OCR pass.
    # ------------------------------------------------------------------ #
    def extract_words(self, image: np.ndarray) -> List[OCRWord]:
        if image is None or image.size == 0:
            return []

        engine = self._ensure_engine()
        if self._version >= 3:
            results = engine.ocr(image)  # 3.x: no `cls` parameter
        else:
            results = engine.ocr(image, cls=self.use_angle_cls)  # 2.x

        return self._parse(results)

    # ------------------------------------------------------------------ #
    # Result parsing (handles both 2.x and 3.x shapes).
    # ------------------------------------------------------------------ #
    def _parse(self, results) -> List[OCRWord]:
        words: List[OCRWord] = []

        if not results:
            return words

        # PaddleOCR 3.x: list of per-image dicts.
        if isinstance(results, list) and results and isinstance(results[0], dict):
            for res in results:
                if not res:
                    continue
                texts = res.get("rec_texts") or []
                scores = res.get("rec_scores") or []
                polys = res.get("rec_polys") or res.get("dt_polys") or []
                for text, score, poly in zip(texts, scores, polys):
                    word = self._make_word(text, score, poly)
                    if word is not None:
                        words.append(word)
            return words

        # PaddleOCR 2.x: list of per-image lists of [bbox, (text, conf)].
        for img_res in results:
            if not img_res:
                continue
            for line in img_res:
                try:
                    bbox_raw, (text, conf) = line
                except (ValueError, TypeError):
                    continue
                word = self._make_word(text, conf, bbox_raw)
                if word is not None:
                    words.append(word)
        return words

    @staticmethod
    def _make_word(text, conf, poly) -> Optional[OCRWord]:
        text = (text or "").strip()
        if not text:
            return None

        try:
            conf = float(conf) if conf is not None else 0.0
        except (ValueError, TypeError):
            conf = 0.0

        if poly is None:
            return OCRWord(text=text, confidence=conf, x=0.0, y=0.0)

        try:
            pts = [[float(p[0]), float(p[1])] for p in poly]
        except (ValueError, TypeError, IndexError):
            return OCRWord(text=text, confidence=conf, x=0.0, y=0.0)

        if not pts:
            return OCRWord(text=text, confidence=conf, x=0.0, y=0.0)

        x = sum(p[0] for p in pts) / len(pts)
        y = sum(p[1] for p in pts) / len(pts)
        return OCRWord(text=text, confidence=conf, x=x, y=y, bbox=pts)
