"""Inventory service for complex business logic."""

from datetime import datetime, date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.inventory import InventoryBatch, BatchStatus
from app.models.product import Product
from app.models.usage_log import UsageLog, UsageAction


class InventoryService:
    """Service for inventory business logic."""

    @staticmethod
    async def get_total_quantity_for_product(
        db: AsyncSession,
        product_id: int,
        location_id: int | None = None,
    ) -> int:
        """Get total quantity for a product across all locations or a specific location."""
        query = (
            select(func.coalesce(func.sum(InventoryBatch.quantity), 0))
            .where(
                (InventoryBatch.product_id == product_id) &
                (InventoryBatch.status != BatchStatus.DEPLETED)
            )
        )
        if location_id:
            query = query.where(InventoryBatch.location_id == location_id)

        result = await db.execute(query)
        return result.scalar() or 0

    @staticmethod
    async def get_expiring_batches(
        db: AsyncSession,
        days: int = 7,
        product_id: int | None = None,
    ) -> list[InventoryBatch]:
        """Get batches expiring within specified days."""
        from datetime import timedelta

        cutoff = datetime.utcnow().date() + timedelta(days=days)

        query = (
            select(InventoryBatch)
            .options(
                selectinload(InventoryBatch.product),
                selectinload(InventoryBatch.location),
            )
            .where(
                (InventoryBatch.status != BatchStatus.DEPLETED) &
                (InventoryBatch.expiry_date.isnot(None)) &
                (InventoryBatch.expiry_date <= cutoff)
            )
            .order_by(InventoryBatch.expiry_date.asc())
        )

        if product_id:
            query = query.where(InventoryBatch.product_id == product_id)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_fifo_batch(
        db: AsyncSession,
        product_id: int,
        location_id: int | None = None,
        prefer_active: bool = True,
    ) -> InventoryBatch | None:
        """Get the oldest batch for FIFO consumption.

        Args:
            db: Database session
            product_id: Product to look for
            location_id: Optional specific location
            prefer_active: If True, prefer ACTIVE batches over SEALED

        Returns:
            The batch to consume first based on expiry (then created date)
        """
        query = (
            select(InventoryBatch)
            .options(
                selectinload(InventoryBatch.product),
                selectinload(InventoryBatch.location),
            )
            .where(
                (InventoryBatch.product_id == product_id) &
                (InventoryBatch.status != BatchStatus.DEPLETED) &
                (InventoryBatch.quantity > 0)
            )
        )

        if location_id:
            query = query.where(InventoryBatch.location_id == location_id)

        if prefer_active:
            # Order by: ACTIVE first, then by expiry, then by created date
            query = query.order_by(
                InventoryBatch.status.desc(),  # ACTIVE before SEALED
                InventoryBatch.expiry_date.asc().nullslast(),
                InventoryBatch.created_at.asc(),
            )
        else:
            query = query.order_by(
                InventoryBatch.expiry_date.asc().nullslast(),
                InventoryBatch.created_at.asc(),
            )

        result = await db.execute(query.limit(1))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_usage_history(
        db: AsyncSession,
        product_id: int | None = None,
        batch_id: int | None = None,
        action: UsageAction | None = None,
        limit: int = 100,
    ) -> list[UsageLog]:
        """Get usage history with optional filters."""
        query = select(UsageLog).order_by(UsageLog.created_at.desc()).limit(limit)

        if batch_id:
            query = query.where(UsageLog.batch_id == batch_id)
        elif product_id:
            # Join through batch to filter by product
            query = (
                query
                .join(InventoryBatch)
                .where(InventoryBatch.product_id == product_id)
            )

        if action:
            query = query.where(UsageLog.action == action)

        result = await db.execute(query)
        return list(result.scalars().all())
