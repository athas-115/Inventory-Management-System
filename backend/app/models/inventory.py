"""Inventory batch model."""

from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, Integer, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BatchStatus(str, Enum):
    """Status of an inventory batch."""
    SEALED = "SEALED"      # Unopened/stored
    ACTIVE = "ACTIVE"      # Currently in use (opened)
    DEPLETED = "DEPLETED"  # Fully consumed


class InventoryBatch(Base):
    """A batch of inventory items."""

    __tablename__ = "inventory_batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )

    # Quantity tracking
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    original_quantity: Mapped[int] = mapped_column(Integer, default=1)

    # Status
    status: Mapped[BatchStatus] = mapped_column(
        SQLEnum(BatchStatus), default=BatchStatus.SEALED, index=True
    )

    # Dates
    expiry_date: Mapped[datetime | None] = mapped_column(Date, nullable=True, index=True)
    purchase_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    opened_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Optional metadata
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    purchase_price: Mapped[float | None] = mapped_column(nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="inventory_batches")
    location: Mapped["Location"] = relationship("Location", back_populates="inventory_batches")
    usage_logs: Mapped[list["UsageLog"]] = relationship(
        "UsageLog", back_populates="batch", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<InventoryBatch {self.id}: {self.quantity}x {self.product_id} @ {self.location_id}>"
