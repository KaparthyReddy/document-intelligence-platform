"""
Routes package for Document Intelligence Platform API
"""

from fastapi import APIRouter
from .upload import upload_router
from .analysis import analysis_router
from .insights import insights_router

def register_routes(app):
    """Register all API routes"""
    
    # Create main API router
    api_router = APIRouter(prefix="/api")
    
    # Include sub-routers
    api_router.include_router(upload_router, tags=["Upload"])
    api_router.include_router(analysis_router, tags=["Analysis"])
    api_router.include_router(insights_router, tags=["Insights"])
    
    # Register with app
    app.include_router(api_router)
    
    print("✅ All API routes registered")

__all__ = ['register_routes']