"""
Settings API — User preferences management.
"""

import logging

from fastapi import APIRouter

from app.schemas.upload import SettingsRequest, SettingsResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory settings store (Phase 2: replace with DB-backed user settings)
_current_settings = SettingsResponse(
    default_min_stock=10,
    language="en",
    theme="light",
    export_format="excel",
    ocr_sensitivity="medium",
)


@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """Get current user settings."""
    return _current_settings


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(settings_update: SettingsRequest):
    """Update user settings."""
    global _current_settings

    update_data = settings_update.model_dump(exclude_unset=True)

    current_dict = _current_settings.model_dump()
    current_dict.update({k: v for k, v in update_data.items() if v is not None})

    _current_settings = SettingsResponse(**current_dict)

    logger.info(f"Settings updated: {update_data}")
    return _current_settings
