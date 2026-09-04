"""Location schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    """Schema for creating a location."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class LocationUpdate(BaseModel):
    """Schema for updating a location."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


class LocationResponse(BaseModel):
    """Schema for location response."""
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
