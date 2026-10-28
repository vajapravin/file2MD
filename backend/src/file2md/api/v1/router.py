"""API v1 master router."""

from fastapi import APIRouter

from file2md.api.v1.endpoints import convert, health

api_v1_router = APIRouter()

# Register endpoint routers
api_v1_router.include_router(health.router)
api_v1_router.include_router(convert.router)
