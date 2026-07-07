"""
Pharmacy Smart Shortage Manager — Application Configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Pharmacy Smart Shortage Manager"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://pharmacy_admin:pharmacy_secure_2024@localhost:5432/pharmacy_shortage"
    DATABASE_ECHO: bool = False

    # Security
    SECRET_KEY: str = "change-this-to-a-secure-random-string-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Upload
    UPLOAD_MAX_SIZE_MB: int = 10
    UPLOAD_DIR: str = "./uploads"
    ALLOWED_EXTENSIONS: str = ".png,.jpg,.jpeg,.bmp,.tiff,.xlsx,.xls,.csv,.pdf"

    # OCR
    OCR_ENGINE: str = "tesseract"  # paddleocr | tesseract
    OCR_LANGUAGE: str = "en,ar"
    OCR_CONFIDENCE_THRESHOLD: float = 0.6
    TESSERACT_PATH: Optional[str] = None

    # Shortage Defaults
    DEFAULT_MIN_STOCK: int = 10

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins list with production-friendly defaults."""
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

        # In debug mode, allow all localhost variations
        if self.DEBUG:
            dev_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
            ]
            for origin in dev_origins:
                if origin not in origins:
                    origins.append(origin)

        return origins

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()
