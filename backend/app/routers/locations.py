"""Location CRUD routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate, LocationResponse
from app.middleware.auth import get_current_user_optional

router = APIRouter(prefix="/api/locations", tags=["locations"])


@router.post("", response_model=LocationResponse, status_code=201)
async def create_location(
    location: LocationCreate,
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """Create a new location."""
    # Check for duplicate name
    result = await db.execute(
        select(Location).where(Location.name == location.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Location name already exists")

    db_location = Location(**location.model_dump())
    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)
    return db_location


@router.get("", response_model=list[LocationResponse])
async def list_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """List all locations."""
    result = await db.execute(
        select(Location)
        .offset(skip)
        .limit(limit)
        .order_by(Location.name)
    )
    return result.scalars().all()


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """Get a location by ID."""
    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: int,
    location_update: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """Update a location."""
    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Check for duplicate name if updating
    if location_update.name and location_update.name != location.name:
        result = await db.execute(
            select(Location).where(Location.name == location_update.name)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Location name already exists")

    update_data = location_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(location, key, value)

    await db.commit()
    await db.refresh(location)
    return location


@router.delete("/{location_id}", status_code=204)
async def delete_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """Delete a location."""
    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    await db.delete(location)
    await db.commit()
