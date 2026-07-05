"""
API v1 Router Package
"""

from fastapi import APIRouter
from app.api.v1 import upload, reports, export, settings

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(upload.router, tags=["Upload"])
api_router.include_router(reports.router, tags=["Reports"])
api_router.include_router(export.router, tags=["Export"])
api_router.include_router(settings.router, tags=["Settings"])
