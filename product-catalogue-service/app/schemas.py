from pydantic import BaseModel, Field, validator
from typing import Optional
import re


class ProductCreate(BaseModel):

    name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    description: str = Field(
        ...,
        max_length=1000
    )

    price: float = Field(
        ...,
        gt=0
    )

    category: str = Field(
        ...,
        min_length=1,
        max_length=50
    )

    stock_quantity: int = Field(
        ...,
        ge=0
    )

    image_url: Optional[str] = None

    @validator("name")
    def validate_name(cls, value):

        value = value.strip()

        if not value:
            raise ValueError(
                "Product name cannot be empty"
            )

        return value

    @validator("category")
    def validate_category(cls, value):

        value = value.strip()

        if not value:
            raise ValueError(
                "Category cannot be empty"
            )

        return value

    @validator("image_url")
    def validate_image_url(cls, value):

        if value is None or not value.strip():
            return None

        pattern = re.compile(
            r"^https?://",
            re.IGNORECASE
        )

        if not pattern.match(value):

            raise ValueError(
                "Image URL must start with http:// or https://"
            )

        return value.strip()


class ProductUpdate(BaseModel):

    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100
    )

    description: Optional[str] = Field(
        None,
        max_length=1000
    )

    price: Optional[float] = Field(
        None,
        gt=0
    )

    category: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50
    )

    stock_quantity: Optional[int] = Field(
        None,
        ge=0
    )

    image_url: Optional[str] = None

    @validator("name")
    def validate_name(cls, value):

        if value is not None:

            value = value.strip()

            if not value:
                raise ValueError(
                    "Product name cannot be empty"
                )

        return value

    @validator("category")
    def validate_category(cls, value):

        if value is not None:

            value = value.strip()

            if not value:
                raise ValueError(
                    "Category cannot be empty"
                )

        return value

    @validator("image_url")
    def validate_image_url(cls, value):

        if value is None or not value.strip():
            return None

        if not re.match(
            r"^https?://",
            value,
            re.IGNORECASE
        ):

            raise ValueError(
                "Image URL must start with http:// or https://"
            )

        return value.strip()


class ProductResponse(BaseModel):

    id: str

    name: str

    description: str

    price: float

    category: str

    stock_quantity: int

    image_url: Optional[str] = None

    created_at: str

    updated_at: str

    class Config:
        from_attributes = True