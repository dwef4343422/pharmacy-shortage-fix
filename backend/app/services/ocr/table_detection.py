"""
Inventory Table Detection — locate and crop the medicine table region.

Instead of OCR-ing the entire screenshot (toolbar, side menu, status bar, ...),
we isolate the tabular grid first. Screenshots from pharmacy systems are mostly
chrome + one large data grid; cropping to that grid both speeds up OCR and
removes the UI text that requirement #11 asks us to reject.

Returns ``(x, y, w, h)`` in pixels of the detected table, or ``None`` when no
clear grid is found (the caller then falls back to the full image).
"""

from __future__ import annotations

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# A detected region must cover at least this fraction of the image to count as
# "the table" — otherwise we treat the whole image as the table.
_MIN_TABLE_FRACTION = 0.15


def detect_table_region(gray: np.ndarray) -> tuple[int, int, int, int] | None:
    """Detect the bounding box of the dominant table grid in a grayscale image."""
    if gray is None or gray.size == 0:
        return None

    h, w = gray.shape
    total = h * w

    # Ink = white.
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Horizontal line emphasis.
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(40, w // 40), 1))
    h_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel)

    # Vertical line emphasis.
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(40, h // 40)))
    v_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel)

    # Combine into a grid mask and thicken so broken lines reconnect.
    grid = cv2.add(h_lines, v_lines)
    grid = cv2.dilate(grid, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=1)

    contours, _ = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        logger.debug("No table grid contours found")
        return None

    # Pick the largest connected grid region.
    best = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(best)
    if area < _MIN_TABLE_FRACTION * total:
        logger.debug("Largest grid region too small (%.1f%%); skipping crop", 100 * area / total)
        return None

    x, y, bw, bh = cv2.boundingRect(best)
    pad = int(min(w, h) * 0.02)
    x = max(0, x - pad)
    y = max(0, y - pad)
    bw = min(w - x, bw + 2 * pad)
    bh = min(h - y, bh + 2 * pad)

    logger.info("Detected table region at (%d,%d) size %dx%d", x, y, bw, bh)
    return (x, y, bw, bh)


def crop_region(image: np.ndarray, region: tuple[int, int, int, int] | None) -> np.ndarray:
    """Return the cropped sub-image, or the image itself when region is None."""
    if region is None:
        return image
    x, y, w, h = region
    return image[y : y + h, x : x + w]
