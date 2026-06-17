"""Routers package."""
from .matches import router as matches_router
from .products import router as products_router
from .users import router as users_router
from .alerts import router as alerts_router

__all__ = ["matches_router", "products_router", "users_router", "alerts_router"]
