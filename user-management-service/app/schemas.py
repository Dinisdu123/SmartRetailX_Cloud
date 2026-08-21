from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
import re
from pydantic import BaseModel, Field, EmailStr, field_validator

class RoleEnum(str, Enum):
    customer = "customer"
    admin = "admin"


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()

        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")

        if len(v) > 100:
            raise ValueError("Name cannot exceed 100 characters")

        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not any(c.isupper() for c in v):
            raise ValueError(
                "Password must contain at least one uppercase letter"
            )

        if not any(c.islower() for c in v):
            raise ValueError(
                "Password must contain at least one lowercase letter"
            )

        if not any(c.isdigit() for c in v):
            raise ValueError(
                "Password must contain at least one number"
            )

        return v


# ============================================================
# LOGIN
# ============================================================

class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ============================================================
# USER RESPONSE
# ============================================================

class UserResponse(BaseModel):

    id: UUID
    name: str
    email: str
    role: RoleEnum
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# UPDATE PROFILE
# ============================================================

class UserUpdate(BaseModel):

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100
    )

    email: Optional[EmailStr] = None

    @field_validator("name")
    def validate_name(cls, value):
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty")

        return value


# ============================================================
# TOKEN RESPONSE
# ============================================================

class TokenResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"


# ============================================================
# REFRESH TOKEN
# ============================================================

class RefreshTokenRequest(BaseModel):

    refresh_token: str


# ============================================================
# TOKEN PAIR
# ============================================================

class TokenPairResponse(BaseModel):

    access_token: str

    refresh_token: str

    token_type: str = "bearer"