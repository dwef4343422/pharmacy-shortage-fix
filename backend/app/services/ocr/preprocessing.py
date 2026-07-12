"""
Image Preprocessing — prepares a screenshot region for fast, accurate OCR.

This module replaces the previous two separate preprocessors (which each
re-decoded the image) with a single, stage-ordered pipeline:

    1. Decode (done once by the caller / orchestrator)
    2. Resize to a bounded working resolution (keeps <10s budget)
    3. Grayscale
    4. CLAHE contrast enhancement
    5. Denoise
    6. Adaptive threshold  -> isolates ink, suppresses background UI noise
    7. Deskew (rotation correction via Hough lines)
    8. Sharpen text (unsharp mask)

The result is a 3-channel BGR image ready for any OCR provider. The adaptive
threshold map is also exposed (``adaptive_threshold``) so the table detector
can reuse the same ink mask without re-computing it.
"""

from __future__ import annotations

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Keep the longest side bounded so per-image cost stays predictable.
_MAX_DIM = 1600
_MIN_WIDTH = 800


def decode_image(image_bytes: bytes) -> np.ndarray:
    """Decode raw bytes into a BGR ``numpy.ndarray``. Called once per image."""
    if not image_bytes:
        raise ValueError("Empty image bytes")
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image bytes")
    return img


def _resize_to_working(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    longest = max(h, w)

    if longest > _MAX_DIM:
        scale = _MAX_DIM / float(longest)
        return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    if w < _MIN_WIDTH:
        scale = _MIN_WIDTH / float(w)
        # Don't blow past the max bound when upscaling.
        if max(h * scale, w * scale) > _MAX_DIM:
            scale = _MAX_DIM / float(max(h, w))
        return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    return img


def adaptive_threshold(gray: np.ndarray) -> np.ndarray:
    """Adaptive Gaussian threshold -> binary image (ink = white)."""
    return cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=15,
    )


def _deskew(gray: np.ndarray) -> np.ndarray:
    """Correct small rotations using Hough-detected near-horizontal lines."""
    try:
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=100,
            minLineLength=100, maxLineGap=10,
        )
        if lines is None:
            return gray

        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if abs(angle) < 15:  # only near-horizontal structure
                angles.append(angle)

        if not angles:
            return gray

        median_angle = float(np.median(angles))
        if abs(median_angle) < 0.5:
            return gray

        h, w = gray.shape[:2]
        center = (w // 2, h // 2)
        rot = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            gray, rot, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        logger.info("Deskewed by %.2f degrees", median_angle)
        return rotated
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Deskew failed: %s", exc)
        return gray


def _sharpen(gray: np.ndarray) -> np.ndarray:
    """Unsharp-mask style sharpening to crisp up text strokes."""
    blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=3)
    sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def preprocess(image: np.ndarray) -> np.ndarray:
    """Run the full preprocessing pipeline; returns a 3-channel BGR image."""
    if image is None or image.size == 0:
        raise ValueError("Empty image for preprocessing")

    working = _resize_to_working(image)
    logger.debug("Preprocess working size: %s", working.shape)

    gray = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY)

    # 4. Contrast enhancement.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 5. Denoise.
    denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

    # 6. Adaptive threshold isolates ink and removes background UI noise.
    binary = adaptive_threshold(denoised)
    # ink_mask: text pixels = white (255), background = black (0).
    ink_mask = cv2.bitwise_not(binary)

    # Clean background to white while keeping the (dark) text untouched. This
    # suppresses faint UI chrome / grid lines that aren't real ink.
    cleaned = denoised.copy()
    cleaned[ink_mask == 0] = 255

    # 7. Deskew + 8. Sharpen on the cleaned image.
    deskewed = _deskew(cleaned)
    sharpened = _sharpen(deskewed)

    # Back to 3 channels for provider compatibility.
    return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
