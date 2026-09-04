"""Report schemas."""

from datetime import date
from pydantic import BaseModel

from app.models.inventory import BatchStatus


class StockReportItem(BaseModel):
    """Single item in stock report."""
    product_id: int
    product_name: str
    category: str | None = None
    location_id: int
    location_name: str
    total_quantity: int
    sealed_quantity: int
    active_quantity: int
    earliest_expiry: date | None = None
    batch_count: int


class StockReportResponse(BaseModel):
    """Stock report response."""
    items: list[StockReportItem]
    total_products: int
    total_items: int
    low_stock_count: int


class LowStockItem(BaseModel):
    """Low stock alert item."""
    product_id: int
    product_name: str
    current_quantity: int
    min_threshold: int
    deficit: int
