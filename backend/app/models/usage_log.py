"""Usage log model for tracking inventory actions."""

from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UsageAction(str, Enum):
    """Type of usage action."""
    ADDED = "ADDED"        # Inventory added
    OPENED = "OPENED"      # Item opened/activated
    DEPLETED = "DEPLETED"  # Item fully consumed
    MOVED = "MOVED"        # Item moved between locations
    ADJUSTED = "ADJUSTED"  # Manual adjustment


class UsageLog(Base):
    """Log of inventory usage actions."""

    __tablename__ = "usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("inventory_batches.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Action details
    action: Mapped[UsageAction] = mapped_column(
        SQLEnum(UsageAction), index=True
    )
    quantity_change: Mapped[int] = mapped_column(Integer, default=0)

    # For MOVED actions
    from_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    to_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )

    # Optional notes
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    # Relationships
    batch: Mapped["InventoryBatch"] = relationship("InventoryBatch", back_populates="usage_logs")
    user: Mapped["User"] = relationship("User")
    from_location: Mapped["Location"] = relationship("Location", foreign_keys=[from_location_id])
    to_location: Mapped["Location"] = relationship("Location", foreign_keys=[to_location_id])

    def __repr__(self) -> str:
        return f"<UsageLog {self.action}: batch={self.batch_id}, qty={self.quantity_change}>"
