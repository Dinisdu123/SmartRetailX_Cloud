from datetime import datetime, timedelta, timezone
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor
import asyncio

_bcrypt_executor = ThreadPoolExecutor(max_workers=4)

import bcrypt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database import get_db
from app.middleware.auth import (
    create_access_token,
    create_refresh_token,
    require_admin,
    verify_refresh_token,
    verify_token
)
from app.models import RoleEnum, User
from app.schemas import (
    RefreshTokenRequest,
    TokenPairResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate
)


router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)


# ============================================================
# REGISTER
# ============================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new customer account."
)
async def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    existing = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    loop = asyncio.get_event_loop()
    hashed_password = await loop.run_in_executor(
        _bcrypt_executor,
        bcrypt.hashpw,
        user.password.encode("utf-8"),
        bcrypt.gensalt()
    )

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hashed_password.decode("utf-8"),
        role=RoleEnum.customer
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenPairResponse,
    summary="User login",
    description="Authenticate a user and return JWT access and refresh tokens."
)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.email == credentials.email)
        .first()
    )

    # --------------------------------------------------------
    # Do not reveal whether the email exists
    # --------------------------------------------------------

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # --------------------------------------------------------
    # Check account status
    # --------------------------------------------------------

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been deactivated"
        )

    # --------------------------------------------------------
    # Check temporary account lock
    # --------------------------------------------------------

    now = datetime.now(timezone.utc)

    if user.locked_until:

        locked_until = user.locked_until

        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(
                tzinfo=timezone.utc
            )

        if locked_until > now:
            remaining_seconds = int(
                (locked_until - now).total_seconds()
            )

            remaining_minutes = max(
                1,
                (remaining_seconds + 59) // 60
            )

            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=(
                    f"Account temporarily locked. "
                    f"Try again in approximately "
                    f"{remaining_minutes} minute(s)."
                )
            )

        # Lock period has expired
        user.locked_until = None
        user.failed_login_attempts = 0

    # --------------------------------------------------------
    # Verify password
    # --------------------------------------------------------

    loop = asyncio.get_event_loop()
    password_valid = await loop.run_in_executor(
        _bcrypt_executor,
        bcrypt.checkpw,
        credentials.password.encode("utf-8"),
        user.password_hash.encode("utf-8")
    )

    if not password_valid:

        user.failed_login_attempts += 1

        if (
            user.failed_login_attempts
            >= settings.MAX_FAILED_LOGIN_ATTEMPTS
        ):
            user.locked_until = (
                now
                + timedelta(
                    minutes=settings.ACCOUNT_LOCK_MINUTES
                )
            )

            db.commit()

            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=(
                    "Too many failed login attempts. "
                    "Account temporarily locked."
                )
            )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # --------------------------------------------------------
    # Successful login
    # --------------------------------------------------------

    user.failed_login_attempts = 0
    user.locked_until = None
    user.login_count += 1
    user.last_login_at = now

    db.commit()

    # --------------------------------------------------------
    # Generate tokens
    # --------------------------------------------------------

    access_token = create_access_token(
        str(user.id),
        user.role.value
    )

    refresh_token = create_refresh_token(
        str(user.id),
        user.role.value
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


# ============================================================
# REFRESH TOKEN
# ============================================================

@router.post(
    "/refresh",
    response_model=TokenPairResponse,
    summary="Refresh access token",
    description="Generate a new access and refresh token pair."
)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    payload = verify_refresh_token(
        request.refresh_token
    )

    user = (
        db.query(User)
        .filter(
            User.id == payload["sub"],
            User.is_active == True
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated"
        )

    access_token = create_access_token(
        str(user.id),
        user.role.value
    )

    new_refresh_token = create_refresh_token(
        str(user.id),
        user.role.value
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token
    }


# ============================================================
# LOGOUT
# ============================================================

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Logout by instructing the client to discard its JWT tokens."
)
def logout():
    return {
        "message": (
            "Successfully logged out. "
            "Please discard the access and refresh tokens."
        )
    }


# ============================================================
# GET PROFILE
# ============================================================

@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Return the profile of the authenticated user."
)
def get_profile(
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token)
):
    user = (
        db.query(User)
        .filter(
            User.id == token["sub"],
            User.is_active == True
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


# ============================================================
# GET ALL USERS - ADMIN
# ============================================================

@router.get(
    "",
    response_model=list[UserResponse],
    summary="Get all users",
    description="Return all active users. Admin only."
)
def get_all_users(
    db: Session = Depends(get_db),
    token: dict = Depends(require_admin)
):
    users = (
        db.query(User)
        .filter(User.is_active == True)
        .order_by(User.created_at.desc())
        .all()
    )

    return users


# ============================================================
# GET USER BY ID - ADMIN
# ============================================================

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Return a user by ID. Admin only."
)
def get_user_by_id(
    user_id: UUID,
    db: Session = Depends(get_db),
    token: dict = Depends(require_admin)
):
    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.is_active == True
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


# ============================================================
# UPDATE PROFILE
# ============================================================

@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Update user profile",
    description="Update the authenticated user's profile."
)
def update_profile(
    updates: UserUpdate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token)
):
    user = (
        db.query(User)
        .filter(
            User.id == token["sub"],
            User.is_active == True
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # --------------------------------------------------------
    # Email update
    # --------------------------------------------------------

    if updates.email and updates.email != user.email:

        existing = (
            db.query(User)
            .filter(User.email == updates.email)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use by another account"
            )

        user.email = updates.email

    # --------------------------------------------------------
    # Name update
    # --------------------------------------------------------

    if updates.name is not None:
        user.name = updates.name

    db.commit()
    db.refresh(user)

    return user


# ============================================================
# DELETE USER - ADMIN
# ============================================================

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Soft-delete a user account. Admin only."
)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    token: dict = Depends(require_admin)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already deleted"
        )

    user.is_active = False
    user.deleted_at = datetime.now(timezone.utc)

    db.commit()

    return None