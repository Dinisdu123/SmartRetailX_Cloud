from datetime import datetime, timezone
import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Integer,
    String
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class RoleEnum(str, enum.Enum):
    customer = "customer"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    # ============================================================
    # PRIMARY INFORMATION
    # ============================================================

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    role = Column(
        Enum(RoleEnum),
        default=RoleEnum.customer,
        nullable=False
    )

    # ============================================================
    # TIMESTAMPS
    # ============================================================

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ============================================================
    # SOFT DELETE
    # ============================================================

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # ============================================================
    # LOGIN SECURITY
    # ============================================================

    last_login_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    login_count = Column(
        Integer,
        default=0,
        nullable=False
    )

    failed_login_attempts = Column(
        Integer,
        default=0,
        nullable=False
    )

    locked_until = Column(
        DateTime(timezone=True),
        nullable=True
    )

    def __repr__(self):
        return f"<User {self.email}>"