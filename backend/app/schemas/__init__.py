"""Pydantic schemas for API request/response."""

from app.schemas.user import UserCreate, UserResponse, UserUpdate, TokenResponse
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.location import LocationCreate, LocationUpdate, LocationResponse
from app.schemas.inventory import (
    InventoryBatchCreate,
    InventoryBatchUpdate,
    InventoryBatchResponse,
    ConsumeRequest,
    MoveRequest,
)
from app.schemas.usage_log import UsageLogResponse
from app.schemas.reports import StockReportItem, StockReportResponse, LowStockItem

__all__ = [
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "TokenResponse",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "LocationCreate",
    "LocationUpdate",
    "LocationResponse",
    "InventoryBatchCreate",
    "InventoryBatchUpdate",
    "InventoryBatchResponse",
    "ConsumeRequest",
    "MoveRequest",
    "UsageLogResponse",
    "StockReportItem",
    "StockReportResponse",
    "LowStockItem",
]
