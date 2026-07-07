"""
Image Preprocessing — Prepares images for optimal OCR accuracy.
"""

import cv2
import numpy as np
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Apply a full preprocessing pipeline to maximize OCR accuracy.
    
    Steps:
    1. Decode image from bytes
    2. Resize if too small
    3. Convert to grayscale
    4. Apply CLAHE contrast enhancement
    5. Denoise
    6. Apply adaptive thresholding for table detection
    7. Deskew if rotated
    
    Returns an optimized numpy array ready for OCR.
    """
    # Decode from bytes
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode image")

    logger.info(f"Original image size: {img.shape}")

    # Step 1: Resize if too small (upscale for better OCR)
    height, width = img.shape[:2]
    if width < 1000:
        scale_factor = 1000 / width
        img = cv2.resize(
            img, None, fx=scale_factor, fy=scale_factor,
            interpolation=cv2.INTER_CUBIC
        )
        logger.info(f"Upscaled to: {img.shape}")

    # Step 2: Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 3: CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Step 4: Denoise
    denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

    # Step 5: Deskew
    deskewed = _deskew(denoised)

    # Convert back to 3-channel for PaddleOCR compatibility
    result = cv2.cvtColor(deskewed, cv2.COLOR_GRAY2BGR)

    logger.info(f"Preprocessed image size: {result.shape}")
    return result


def preprocess_for_table_detection(image_bytes: bytes) -> np.ndarray:
    """
    Specialized preprocessing for table structure detection.
    Enhances horizontal and vertical lines.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise ValueError("Could not decode image")

    # Binary threshold
    _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Detect horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)

    # Detect vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)

    # Combine
    table_mask = cv2.add(horizontal_lines, vertical_lines)

    return table_mask


def _deskew(image: np.ndarray) -> np.ndarray:
    """Correct image rotation/skew using Hough transform."""
    try:
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=100,
            minLineLength=100, maxLineGap=10
        )

        if lines is None:
            return image

        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            if abs(angle) < 15:  # Only consider near-horizontal lines
                angles.append(angle)

        if not angles:
            return image

        median_angle = np.median(angles)

        if abs(median_angle) < 0.5:  # Skip if nearly straight
            return image

        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            image, rotation_matrix, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        logger.info(f"Deskewed by {median_angle:.2f} degrees")
        return rotated

    except Exception as e:
        logger.warning(f"Deskew failed: {e}")
        return image


def bytes_to_pil_image(image_bytes: bytes) -> Image.Image:
    """Convert raw bytes to a PIL Image."""
    return Image.open(io.BytesIO(image_bytes))


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """Convert PIL Image to OpenCV numpy array."""
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
