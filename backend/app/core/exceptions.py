"""
Pharmacy Smart Shortage Manager — Custom Exceptions
"""

from fastapi import HTTPException, status


class OCRProcessingError(HTTPException):
    """Raised when OCR processing fails."""

    def __init__(self, detail: str = "OCR processing failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class FileParseError(HTTPException):
    """Raised when file parsing fails."""

    def __init__(self, detail: str = "Failed to parse uploaded file"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class FileValidationError(HTTPException):
    """Raised when uploaded file fails validation."""

    def __init__(self, detail: str = "Invalid file"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class ReportNotFoundError(HTTPException):
    """Raised when a report is not found."""

    def __init__(self, report_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found",
        )


class ExportError(HTTPException):
    """Raised when export generation fails."""

    def __init__(self, detail: str = "Export generation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
