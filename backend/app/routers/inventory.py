"""Inventory operations routes."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.inventory import InventoryBatch, BatchStatus
from app.models.usage_log import UsageLog, UsageAction
from app.models.product import Product
from app.models.location import Location
from app.schemas.inventory import (
    InventoryBatchCreate,
    InventoryBatchUpdate,
    InventoryBatchResponse,
    ConsumeRequest,
    MoveRequest,
)
from app.middleware.auth import get_current_user_optional

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.post("", response_model=InventoryBatchResponse, status_code=201)
async def add_inventory(
    batch: InventoryBatchCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user_optional),
):
    """Add a new inventory batch."""
    # Verify product exists
    result = await db.execute(
        select(Product).where(Product.id == batch.product_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found")

    # Verify location exists
    result = await db.execute(
        select(Location).where(Location.id == batch.location_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Location not found")

    db_batch = InventoryBatch(
        **batch.model_dump(),
        original_quantity=batch.quantity,
        status=BatchStatus.SEALED,
    )
    db.add(db_batch)
    await db.flush()

    # Log the addition
    log = UsageLog(
        batch_id=db_batch.id,
        user_id=user.id if user else None,
        action=UsageAction.ADDED,
        quantity_change=batch.quantity,
    )
    db.add(log)

    await db.commit()
    await db.refresh(db_batch)

    # Load relationships
    result = await db.execute(
        select(InventoryBatch)
        .options(selectinload(InventoryBatch.product), selectinload(InventoryBatch.location))
        .where(InventoryBatch.id == db_batch.id)
    )
    return result.scalar_one()


@router.get("", response_model=list[InventoryBatchResponse])
async def list_inventory(
    product_id: int | None = Query(None, description="Filter by product"),
    location_id: int | None = Query(None, description="Filter by location"),
    status: BatchStatus | None = Query(None, description="Filter by status"),
    include_depleted: bool = Query(False, description="Include depleted batches"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """List inventory batches with optional filters."""
    query = select(InventoryBatch).options(
        selectinload(InventoryBatch.product),
        selectinload(InventoryBatch.location),
    )

    if product_id:
        query = query.where(InventoryBatch.product_id == product_id)
    if location_id:
        query = query.where(InventoryBatch.location_id == location_id)
    if status:
        query = query.where(InventoryBatch.status == status)
    elif not include_depleted:
        query = query.where(InventoryBatch.status != BatchStatus.DEPLETED)

    query = query.offset(skip).limit(limit).order_by(
        InventoryBatch.expiry_date.asc().nullslast(),
        InventoryBatch.created_at.desc(),
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{batch_id}", response_model=InventoryBatchResponse)
async def get_inventory_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """Get an inventory batch by ID."""
    result = await db.execute(
        select(InventoryBatch)
        .options(selectinload(InventoryBatch.product), selectinload(InventoryBatch.location))
        .where(InventoryBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Inventory batch not found")
    return batch


@router.post("/consume", response_model=InventoryBatchResponse)
async def consume_inventory(
    request: ConsumeRequest,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user_optional),
):
    """Consume/open inventory items.

    Actions:
    - DEPLETE: Decrement quantity, mark as DEPLETED when zero
    - OPEN: Decrement from storage batch, create new ACTIVE batch at target location
    """
    result = await db.execute(
        select(InventoryBatch)
        .options(selectinload(InventoryBatch.product), selectinload(InventoryBatch.location))
        .where(InventoryBatch.id == request.batch_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Inventory batch not found")

    if batch.status == BatchStatus.DEPLETED:
        raise HTTPException(status_code=400, detail="Batch is already depleted")

    if request.quantity > batch.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Requested quantity ({request.quantity}) exceeds available ({batch.quantity})"
        )

    if request.action == "DEPLETE":
        # Simple consumption: decrement quantity
        batch.quantity -= request.quantity
        if batch.quantity == 0:
            batch.status = BatchStatus.DEPLETED

        log = UsageLog(
            batch_id=batch.id,
            user_id=user.id if user else None,
            action=UsageAction.DEPLETED,
            quantity_change=-request.quantity,
            notes=request.notes,
        )
        db.add(log)
        await db.commit()
        await db.refresh(batch)
        return batch

    elif request.action == "OPEN":
        # Open action: create active batch at target location
        target_location_id = request.target_location_id or batch.location_id

        # Verify target location exists
        result = await db.execute(
            select(Location).where(Location.id == target_location_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Target location not found")

        # Decrement source batch
        batch.quantity -= request.quantity
        if batch.quantity == 0:
            batch.status = BatchStatus.DEPLETED

        # Create new active batch
        new_batch = InventoryBatch(
            product_id=batch.product_id,
            location_id=target_location_id,
            quantity=request.quantity,
            original_quantity=request.quantity,
            status=BatchStatus.ACTIVE,
            expiry_date=batch.expiry_date,
            purchase_date=batch.purchase_date,
            opened_date=datetime.utcnow(),
            notes=request.notes,
        )
        db.add(new_batch)
        await db.flush()

        # Log the open action
        log = UsageLog(
            batch_id=batch.id,
            user_id=user.id if user else None,
            action=UsageAction.OPENED,
            quantity_change=-request.quantity,
            notes=request.notes,
        )
        db.add(log)

        await db.commit()

        # Return the new active batch
        result = await db.execute(
            select(InventoryBatch)
            .options(selectinload(InventoryBatch.product), selectinload(InventoryBatch.location))
            .where(InventoryBatch.id == new_batch.id)
        )
        return result.scalar_one()

    raise HTTPException(status_code=400, detail="Invalid action")


@router.post("/move", response_model=InventoryBatchResponse)
async def move_inventory(
    request: MoveRequest,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user_optional),
):
    """Move inventory between locations."""
    result = await db.execute(
        select(InventoryBatch)
        .options(selectinload(InventoryBatch.product), selectinload(InventoryBatch.location))
        .where(InventoryBatch.id == request.batch_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Inventory batch not found")

    if batch.status == BatchStatus.DEPLETED:
        raise HTTPException(status_code=400, detail="Cannot move depleted batch")

    # Verify target location exists
    result = await db.execute(
        select(Location).where(Location.id == request.to_location_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Target location not found")

    if batch.location_id == request.to_location_id:
        raise HTTPException(status_code=400, detail="Source and target locations are the same")

    from_location_id = batch.location_id
    quantity_to_move = request.quantity or batch.quantity

    if request.quantity and request.quantity > batch.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Requested quantity ({request.quantity}) exceeds available ({batch.quantity})"
        )

    if request.quantity and request.quantity < batch.quantity:
        # Partial move: split the batch
        batch.quantity -= request.quantity

        new_batch = InventoryBatch(
            product_id=batch.product_id,
            location_id=request.to_location_id,
            quantity=request.quantity,
            original_quantity=request.quantity,
            status=batch.status,
            expiry_date=batch.expiry_date,
            purchase_date=batch.purchase_date,
            opened_date=batch.opened_date,
            notes=request.notes or batch.notes,
        )
        db.add(new_batch)
        await db.flush()

        # Log the move
        log = UsageLog(
            batch_id=new_batch.id,
            user_id=user.id if user else None,
            action=UsageAction.MOVED,
            quantity_change=request.quantity,
            from_location_id=from_location_id,
            to_location_id=request.to_location_id,
            notes=request.notes,
        )
        db.add(log)

        await db.commit()

        result = await db.execute(
            select(InventoryBatch)
            .options(selectinload(InventoryBatch.product), selectinload(InventoryBatch.location))
            .where(InventoryBatch.id == new_batch.id)
        )
        return result.scalar_one()
    else:
        # Full move: update location
        batch.location_id = request.to_location_id
        if request.notes:
            batch.notes = request.notes

        # Log the move
        log = UsageLog(
            batch_id=batch.id,
            user_id=user.id if user else None,
            action=UsageAction.MOVED,
            quantity_change=quantity_to_move,
            from_location_id=from_location_id,
            to_location_id=request.to_location_id,
            notes=request.notes,
        )
        db.add(log)

        await db.commit()
        await db.refresh(batch)
        return batch


@router.put("/{batch_id}", response_model=InventoryBatchResponse)
async def update_inventory_batch(
    batch_id: int,
    batch_update: InventoryBatchUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user_optional),
):
    """Update an inventory batch (manual adjustment)."""
    result = await db.execute(
        select(InventoryBatch)
        .options(selectinload(InventoryBatch.product), selectinload(InventoryBatch.location))
        .where(InventoryBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Inventory batch not found")

    old_quantity = batch.quantity
    update_data = batch_update.model_dump(exclude_unset=True)

    # Verify new location if provided
    if "location_id" in update_data:
        result = await db.execute(
            select(Location).where(Location.id == update_data["location_id"])
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Location not found")

    for key, value in update_data.items():
        setattr(batch, key, value)

    # Log quantity adjustment if changed
    if "quantity" in update_data and update_data["quantity"] != old_quantity:
        log = UsageLog(
            batch_id=batch.id,
            user_id=user.id if user else None,
            action=UsageAction.ADJUSTED,
            quantity_change=update_data["quantity"] - old_quantity,
        )
        db.add(log)

    await db.commit()
    await db.refresh(batch)
    return batch


@router.delete("/{batch_id}", status_code=204)
async def delete_inventory_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """Delete an inventory batch."""
    result = await db.execute(
        select(InventoryBatch).where(InventoryBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Inventory batch not found")

    await db.delete(batch)
    await db.commit()
