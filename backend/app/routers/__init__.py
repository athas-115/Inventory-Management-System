"""API routers."""

from app.routers.auth import router as auth_router
from app.routers.products import router as products_router
from app.routers.locations import router as locations_router
from app.routers.inventory import router as inventory_router
from app.routers.reports import router as reports_router
from .ai import router as ai_router

__all__ = [
    "auth_router",
    "products_router",
    "locations_router",
    "inventory_router",
    "reports_router",
]
