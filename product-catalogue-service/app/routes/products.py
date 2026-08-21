from fastapi import APIRouter, HTTPException, Depends, Query, status

from app.database import get_table
from app.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse
)
from app.middleware.auth import require_admin

from typing import Optional, List
from decimal import Decimal
import uuid
from datetime import datetime, timezone


router = APIRouter(
    prefix="/api/v1/products",
    tags=["Products"]
)


def to_float(value):
    """
    Convert DynamoDB Decimal values to float.
    """

    if isinstance(value, Decimal):
        return float(value)

    return value


def format_product(item: dict) -> dict:
    """
    Format DynamoDB product data for API response.
    """

    product = dict(item)

    product["price"] = to_float(
        product.get("price", 0)
    )

    product["stock_quantity"] = int(
        product.get("stock_quantity", 0)
    )

    return product


# ============================================================
# GET ALL PRODUCTS
# ============================================================

@router.get(
    "",
    response_model=List[ProductResponse],
    summary="Get all products",
    description="Retrieve products with optional filtering"
)
def get_products(
    category: Optional[str] = Query(
        None,
        description="Filter by category"
    ),

    search: Optional[str] = Query(
        None,
        description="Search product name"
    ),

    minPrice: Optional[float] = Query(
        None,
        description="Minimum price",
        gt=0
    ),

    maxPrice: Optional[float] = Query(
        None,
        description="Maximum price",
        gt=0
    )
):

    table = get_table()

    response = table.scan()

    items = response.get("Items", [])

    # --------------------------------------------
    # Category filter
    # --------------------------------------------

    if category:

        items = [
            item
            for item in items
            if item.get("category", "").lower()
            == category.lower()
        ]

    # --------------------------------------------
    # Search filter
    # --------------------------------------------

    if search:

        search_lower = search.lower()

        items = [
            item
            for item in items
            if search_lower
            in item.get("name", "").lower()
        ]

    # --------------------------------------------
    # Minimum price
    # --------------------------------------------

    if minPrice is not None:

        items = [
            item
            for item in items
            if to_float(
                item.get("price", 0)
            ) >= minPrice
        ]

    # --------------------------------------------
    # Maximum price
    # --------------------------------------------

    if maxPrice is not None:

        items = [
            item
            for item in items
            if to_float(
                item.get("price", 0)
            ) <= maxPrice
        ]

    return [
        format_product(item)
        for item in items
    ]


# ============================================================
# GET PRODUCT BY ID
# ============================================================

@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID"
)
def get_product(product_id: str):

    table = get_table()

    response = table.get_item(
        Key={
            "id": product_id
        }
    )

    item = response.get("Item")

    if not item:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return format_product(item)


# ============================================================
# CREATE PRODUCT
# ============================================================

@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    description="Create a new product. Admin only."
)
def create_product(
    product: ProductCreate,
    token: dict = Depends(require_admin)
):

    table = get_table()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    new_product = {
        "id": str(uuid.uuid4()),

        "name": product.name,

        "description": product.description,

        "price": Decimal(
            str(product.price)
        ),

        "category": product.category,

        "stock_quantity": product.stock_quantity,

        "image_url": product.image_url or "",

        "created_at": now,

        "updated_at": now
    }

    table.put_item(
        Item=new_product
    )

    return format_product(
        new_product
    )


# ============================================================
# UPDATE PRODUCT
# ============================================================

@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product",
    description="Update a product. Admin only."
)
def update_product(
    product_id: str,
    updates: ProductUpdate,
    token: dict = Depends(require_admin)
):

    table = get_table()

    response = table.get_item(
        Key={
            "id": product_id
        }
    )

    item = response.get("Item")

    if not item:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    update_data = updates.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():

        if key == "price" and value is not None:

            item[key] = Decimal(
                str(value)
            )

        elif key == "image_url":

            item[key] = value or ""

        elif value is not None:

            item[key] = value

    item["updated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    table.put_item(
        Item=item
    )

    return format_product(item)


# ============================================================
# DELETE PRODUCT
# ============================================================

@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
    description="Delete a product. Admin only."
)
def delete_product(
    product_id: str,
    token: dict = Depends(require_admin)
):

    table = get_table()

    response = table.get_item(
        Key={
            "id": product_id
        }
    )

    if not response.get("Item"):

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    table.delete_item(
        Key={
            "id": product_id
        }
    )

    return None