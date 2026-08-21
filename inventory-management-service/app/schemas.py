from pydantic import BaseModel, Field, field_validator
from typing import Optional


# ============================================================
# INVENTORY RESPONSE
# ============================================================

class InventoryCreate(BaseModel):
    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1, max_length=200)
    stock_quantity: int = Field(..., ge=0)
    reorder_threshold: int = Field(default=10, ge=0)

    
class InventoryItem(BaseModel):
    product_id: str
    product_name: str
    stock_quantity: int
    reserved_quantity: int = 0
    reorder_threshold: int = 10
    updated_at: str

    class Config:
        from_attributes = True


# ============================================================
# INVENTORY UPDATE
# ============================================================

class InventoryUpdate(BaseModel):
    stock_quantity: int = Field(
        ...,
        ge=0,
        description="New stock quantity"
    )

    @field_validator("stock_quantity")
    @classmethod
    def validate_stock_quantity(cls, value):
        if value < 0:
            raise ValueError(
                "Stock quantity cannot be negative"
            )

        return value


# ============================================================
# STOCK DEDUCTION
# ============================================================

class StockDeductRequest(BaseModel):
    product_id: str = Field(
        ...,
        min_length=1,
        description="Product ID"
    )

    quantity: int = Field(
        ...,
        gt=0,
        description="Quantity to deduct"
    )

    order_id: str = Field(
        ...,
        min_length=1,
        description="Order ID for tracking"
    )

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value):
        if value <= 0:
            raise ValueError(
                "Quantity must be greater than 0"
            )

        return value


# ============================================================
# OPTIONAL: INVENTORY CREATION
# ============================================================

class InventoryCreate(BaseModel):
    product_id: str = Field(
        ...,
        min_length=1
    )

    product_name: str = Field(
        ...,
        min_length=1
    )

    stock_quantity: int = Field(
        ...,
        ge=0
    )

    reserved_quantity: int = Field(
        default=0,
        ge=0
    )

    reorder_threshold: int = Field(
        default=10,
        ge=0
    )