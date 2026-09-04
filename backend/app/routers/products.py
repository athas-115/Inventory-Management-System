"""Product CRUD routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.middleware.auth import get_current_user_optional

router = APIRouter(prefix="/api/products", tags=["products"])


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """Create a new product."""
    # Check for duplicate barcode
    if product.barcode:
        result = await db.execute(
            select(Product).where(Product.barcode == product.barcode)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Barcode already exists")

    db_product = Product(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.get("", response_model=list[ProductResponse])
async def list_products(
    search: str | None = Query(None, description="Search by name or barcode"),
    category: str | None = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """List all products with optional filters."""
    query = select(Product)

    if search:
        query = query.where(
            (Product.name.ilike(f"%{search}%")) |
            (Product.barcode.ilike(f"%{search}%"))
        )
    if category:
        query = query.where(Product.category == category)

    query = query.offset(skip).limit(limit).order_by(Product.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/categories", response_model=list[str])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """List all unique categories."""
    result = await db.execute(
        select(Product.category)
        .where(Product.category.isnot(None))
        .distinct()
        .order_by(Product.category)
    )
    return [r for r in result.scalars().all() if r]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """Get a product by ID."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """Update a product."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check for duplicate barcode if updating
    if product_update.barcode and product_update.barcode != product.barcode:
        result = await db.execute(
            select(Product).where(Product.barcode == product_update.barcode)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Barcode already exists")

    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_current_user_optional),
):
    """Delete a product."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(product)
    await db.commit()
