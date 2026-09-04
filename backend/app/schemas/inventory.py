"""Inventory batch schemas."""

from datetime import datetime, date
from pydantic import BaseModel, Field

from app.models.inventory import BatchStatus
from app.schemas.product import ProductResponse
from app.schemas.location import LocationResponse


class InventoryBatchCreate(BaseModel):
    """Schema for creating an inventory batch."""
    product_id: int
    location_id: int
    quantity: int = Field(1, ge=1)
    expiry_date: date | None = None
    purchase_date: date | None = None
    notes: str | None = Field(None, max_length=500)
    purchase_price: float | None = Field(None, ge=0)


class InventoryBatchUpdate(BaseModel):
    """Schema for updating an inventory batch."""
    quantity: int | None = Field(None, ge=0)
    location_id: int | None = None
    expiry_date: date | None = None
    notes: str | None = Field(None, max_length=500)
    status: BatchStatus | None = None


class InventoryBatchResponse(BaseModel):
    """Schema for inventory batch response."""
    id: int
    product_id: int
    location_id: int
    quantity: int
    original_quantity: int
    status: BatchStatus
    expiry_date: date | None = None
    purchase_date: date | None = None
    opened_date: datetime | None = None
    notes: str | None = None
    purchase_price: float | None = None
    created_at: datetime
    updated_at: datetime

    # Nested relations (optional)
    product: ProductResponse | None = None
    location: LocationResponse | None = None

    class Config:
        from_attributes = True


class ConsumeRequest(BaseModel):
    """Schema for consuming/opening inventory."""
    batch_id: int
    quantity: int = Field(1, ge=1)
    action: str = Field("DEPLETE", pattern="^(DEPLETE|OPEN)$")
    # For OPEN action: where is the item being used
    target_location_id: int | None = None
    notes: str | None = Field(None, max_length=500)


class MoveRequest(BaseModel):
    """Schema for moving inventory between locations."""
    batch_id: int
    to_location_id: int
    quantity: int | None = None  # None = move entire batch
    notes: str | None = Field(None, max_length=500)
