from pydantic import BaseModel, Field, field_validator
from enum import Enum
from uuid import UUID
from datetime import datetime


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class OrderCreate(BaseModel):
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)
    total_price: float = Field(..., gt=0)
    shipping_address: str = Field(..., min_length=5, max_length=500)

    @field_validator("product_id")
    @classmethod
    def validate_product_id(cls, v):
        if not v.strip():
            raise ValueError("Product ID cannot be empty")
        return v.strip()

    @field_validator("shipping_address")
    @classmethod
    def validate_shipping_address(cls, v):
        if not v or not v.strip():
            raise ValueError("Shipping address cannot be empty")

        return v.strip()


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    product_id: str
    quantity: int
    total_price: float
    status: OrderStatus
    shipping_address: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True