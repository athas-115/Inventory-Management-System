"""Usage log schemas."""

from datetime import datetime
from pydantic import BaseModel

from app.models.usage_log import UsageAction


class UsageLogResponse(BaseModel):
    """Schema for usage log response."""
    id: int
    batch_id: int
    user_id: int | None = None
    action: UsageAction
    quantity_change: int
    from_location_id: int | None = None
    to_location_id: int | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
