"""
API package for BioMLStudio

Contains all API routes, dependencies, and middleware.
"""

from fastapi import APIRouter

# Create main API router
api_router = APIRouter()

__all__ = ["api_router"]
