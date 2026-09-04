"""Stock reports routes."""

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.inventory import InventoryBatch, BatchStatus
from app.models.product import Product
from app.models.location import Location
from app.schemas.reports import StockReportItem, StockReportResponse, LowStockItem
from app.middleware.auth import get_current_user_optional

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/stock", response_model=StockReportResponse)
async def get_stock_report(
    product_id: int | None = Query(None, description="Filter by product"),
    location_id: int | None = Query(None, description="Filter by location"),
    category: str | None = Query(None, description="Filter by category"),
    expiring_before: date | None = Query(None, description="Filter by expiry date"),
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """Generate a stock report with optional filters."""
    # Build query for aggregated stock by product and location
    query = (
        select(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Product.category,
            Location.id.label("location_id"),
            Location.name.label("location_name"),
            func.sum(InventoryBatch.quantity).label("total_quantity"),
            func.sum(
                case(
                    (InventoryBatch.status == BatchStatus.SEALED, InventoryBatch.quantity),
                    else_=0
                )
            ).label("sealed_quantity"),
            func.sum(
                case(
                    (InventoryBatch.status == BatchStatus.ACTIVE, InventoryBatch.quantity),
                    else_=0
                )
            ).label("active_quantity"),
            func.min(InventoryBatch.expiry_date).label("earliest_expiry"),
            func.count(InventoryBatch.id).label("batch_count"),
        )
        .join(Product, InventoryBatch.product_id == Product.id)
        .join(Location, InventoryBatch.location_id == Location.id)
        .where(InventoryBatch.status != BatchStatus.DEPLETED)
        .group_by(Product.id, Product.name, Product.category, Location.id, Location.name)
    )

    if product_id:
        query = query.where(Product.id == product_id)
    if location_id:
        query = query.where(Location.id == location_id)
    if category:
        query = query.where(Product.category == category)
    if expiring_before:
        query = query.where(InventoryBatch.expiry_date <= expiring_before)

    result = await db.execute(query)
    rows = result.all()

    items = [
        StockReportItem(
            product_id=row.product_id,
            product_name=row.product_name,
            category=row.category,
            location_id=row.location_id,
            location_name=row.location_name,
            total_quantity=row.total_quantity or 0,
            sealed_quantity=row.sealed_quantity or 0,
            active_quantity=row.active_quantity or 0,
            earliest_expiry=row.earliest_expiry,
            batch_count=row.batch_count,
        )
        for row in rows
    ]

    # Calculate totals
    total_products = len(set(item.product_id for item in items))
    total_items = sum(item.total_quantity for item in items)

    # Get low stock count
    low_stock_result = await db.execute(
        select(func.count(func.distinct(Product.id)))
        .select_from(Product)
        .outerjoin(
            InventoryBatch,
            (InventoryBatch.product_id == Product.id) &
            (InventoryBatch.status != BatchStatus.DEPLETED)
        )
        .group_by(Product.id, Product.min_threshold)
        .having(
            func.coalesce(func.sum(InventoryBatch.quantity), 0) < Product.min_threshold
        )
    )
    low_stock_count = len(low_stock_result.all())

    return StockReportResponse(
        items=items,
        total_products=total_products,
        total_items=total_items,
        low_stock_count=low_stock_count,
    )


@router.get("/low-stock", response_model=list[LowStockItem])
async def get_low_stock(
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """Get products below their minimum threshold."""
    # Subquery for total quantity per product
    quantity_subquery = (
        select(
            InventoryBatch.product_id,
            func.coalesce(func.sum(InventoryBatch.quantity), 0).label("total_qty")
        )
        .where(InventoryBatch.status != BatchStatus.DEPLETED)
        .group_by(InventoryBatch.product_id)
        .subquery()
    )

    query = (
        select(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            func.coalesce(quantity_subquery.c.total_qty, 0).label("current_quantity"),
            Product.min_threshold,
        )
        .outerjoin(quantity_subquery, Product.id == quantity_subquery.c.product_id)
        .where(
            func.coalesce(quantity_subquery.c.total_qty, 0) < Product.min_threshold
        )
        .order_by(Product.name)
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        LowStockItem(
            product_id=row.product_id,
            product_name=row.product_name,
            current_quantity=row.current_quantity,
            min_threshold=row.min_threshold,
            deficit=row.min_threshold - row.current_quantity,
        )
        for row in rows
    ]


@router.get("/expiring", response_model=list[dict])
async def get_expiring_items(
    days: int = Query(7, ge=1, le=365, description="Days until expiry"),
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """Get items expiring within specified days."""
    from datetime import datetime, timedelta

    cutoff_date = datetime.utcnow().date() + timedelta(days=days)

    query = (
        select(
            InventoryBatch.id,
            InventoryBatch.quantity,
            InventoryBatch.expiry_date,
            InventoryBatch.status,
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Location.id.label("location_id"),
            Location.name.label("location_name"),
        )
        .join(Product, InventoryBatch.product_id == Product.id)
        .join(Location, InventoryBatch.location_id == Location.id)
        .where(
            (InventoryBatch.status != BatchStatus.DEPLETED) &
            (InventoryBatch.expiry_date.isnot(None)) &
            (InventoryBatch.expiry_date <= cutoff_date)
        )
        .order_by(InventoryBatch.expiry_date.asc())
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "batch_id": row.id,
            "product_id": row.product_id,
            "product_name": row.product_name,
            "location_id": row.location_id,
            "location_name": row.location_name,
            "quantity": row.quantity,
            "expiry_date": row.expiry_date.isoformat() if row.expiry_date else None,
            "status": row.status.value,
            "days_until_expiry": (row.expiry_date - datetime.utcnow().date()).days if row.expiry_date else None,
        }
        for row in rows
    ]
