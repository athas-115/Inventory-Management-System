"""Product schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    """Schema for creating a product."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(None, max_length=100)
    brand: str | None = Field(None, max_length=100)
    unit: str = Field("unit", max_length=50)
    barcode: str | None = Field(None, max_length=100)
    min_threshold: int = Field(1, ge=0)


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(None, max_length=100)
    brand: str | None = Field(None, max_length=100)
    unit: str | None = Field(None, max_length=50)
    barcode: str | None = Field(None, max_length=100)
    min_threshold: int | None = Field(None, ge=0)


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: int
    name: str
    description: str | None = None
    category: str | None = None
    brand: str | None = None
    unit: str
    barcode: str | None = None
    min_threshold: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
