from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status
)

from app.database import get_inventory_table
from app.schemas import (
    InventoryItem,
    InventoryUpdate,
    StockDeductRequest
)
from app.middleware.auth import require_admin

from typing import List
from datetime import datetime, timezone

import logging
import json


logger = logging.getLogger(
    "inventory-management-service"
)

router = APIRouter(
    prefix="/api/v1/inventory",
    tags=["Inventory"]
)

from app.schemas import (
    InventoryItem,
    InventoryUpdate,
    InventoryCreate,
    StockDeductRequest
)

# ============================================================
# CREATE INVENTORY RECORD
# ============================================================

@router.post(
    "",
    response_model=InventoryItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create inventory record",
    description="Create a new inventory record for a product. Admin only."
)
def create_inventory_item(
    item: InventoryCreate,
    token: dict = Depends(require_admin)
):
    """
    Create a new inventory record.
    """

    table = get_inventory_table()

    existing = table.get_item(
        Key={
            "product_id": item.product_id
        }
    )

    if existing.get("Item"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inventory record already exists for this product"
        )

    now = datetime.now(timezone.utc).isoformat()

    new_item = {
        "product_id": item.product_id,
        "product_name": item.product_name,
        "stock_quantity": item.stock_quantity,
        "reserved_quantity": 0,
        "reorder_threshold": item.reorder_threshold,
        "created_at": now,
        "updated_at": now
    }

    table.put_item(
        Item=new_item
    )

    logger.info(
        json.dumps({
            "service": "inventory-management-service",
            "event": "inventory_created",
            "product_id": item.product_id,
            "stock_quantity": item.stock_quantity
        })
    )

    return format_item(new_item)

# ============================================================
# HELPER
# ============================================================

def format_item(item: dict) -> dict:
    """
    Convert DynamoDB numeric values into Python integers
    for API responses.
    """

    item["stock_quantity"] = int(
        item.get("stock_quantity", 0)
    )

    item["reserved_quantity"] = int(
        item.get("reserved_quantity", 0)
    )

    item["reorder_threshold"] = int(
        item.get("reorder_threshold", 10)
    )

    return item


# ============================================================
# GET ALL INVENTORY
# ============================================================

@router.get(
    "",
    response_model=List[InventoryItem],
    summary="Get all inventory items",
    description="Retrieve all inventory items. Admin only."
)
def get_all_inventory(
    token: dict = Depends(require_admin)
):
    """
    Get all inventory items.
    """

    table = get_inventory_table()

    response = table.scan()

    items = response.get(
        "Items",
        []
    )

    return [
        format_item(item)
        for item in items
    ]


# ============================================================
# GET INVENTORY BY PRODUCT
# ============================================================

@router.get(
    "/{product_id}",
    response_model=InventoryItem,
    summary="Get inventory by product ID",
    description="Retrieve inventory for a specific product. Admin only."
)
def get_inventory_item(
    product_id: str,
    token: dict = Depends(require_admin)
):
    """
    Get inventory for a specific product.
    """

    table = get_inventory_table()

    response = table.get_item(
        Key={
            "product_id": product_id
        }
    )

    item = response.get("Item")

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )

    return format_item(item)


# ============================================================
# UPDATE INVENTORY
# ============================================================

@router.put(
    "/{product_id}",
    response_model=InventoryItem,
    summary="Update inventory",
    description="Update stock quantity. Admin only."
)
def update_inventory(
    product_id: str,
    update: InventoryUpdate,
    token: dict = Depends(require_admin)
):
    """
    Update stock quantity for a product.
    """

    table = get_inventory_table()

    response = table.get_item(
        Key={
            "product_id": product_id
        }
    )

    item = response.get("Item")

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )

    item["stock_quantity"] = update.stock_quantity

    item["updated_at"] = (
        datetime.now(timezone.utc).isoformat()
    )

    table.put_item(
        Item=item
    )

    logger.info(
        json.dumps({
            "service": "inventory-management-service",
            "event": "inventory_updated",
            "product_id": product_id,
            "new_quantity": update.stock_quantity
        })
    )

    return format_item(item)


# ============================================================
# DEDUCT STOCK
# ============================================================

@router.post(
    "/deduct",
    response_model=InventoryItem,
    summary="Deduct stock",
    description="Deduct stock quantity for an order. Admin only."
)
def deduct_stock(
    request: StockDeductRequest,
    token: dict = Depends(require_admin)
):
    """
    Deduct stock for an order.

    Prevents stock from becoming negative.
    """

    table = get_inventory_table()

    response = table.get_item(
        Key={
            "product_id": request.product_id
        }
    )

    item = response.get("Item")

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )

    current_stock = int(
        item.get("stock_quantity", 0)
    )

    # Prevent negative stock
    if current_stock < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient stock. "
                f"Available: {current_stock}, "
                f"Requested: {request.quantity}"
            )
        )

    new_stock = current_stock - request.quantity

    item["stock_quantity"] = new_stock

    item["updated_at"] = (
        datetime.now(timezone.utc).isoformat()
    )

    table.put_item(
        Item=item
    )

    logger.info(
        json.dumps({
            "service": "inventory-management-service",
            "event": "stock_deducted",
            "product_id": request.product_id,
            "quantity_deducted": request.quantity,
            "remaining_stock": new_stock,
            "order_id": request.order_id
        })
    )

    return format_item(item)