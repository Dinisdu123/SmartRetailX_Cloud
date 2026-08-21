import jwt
import os
from fastapi import HTTPException, Request
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "smartretailx-super-secret-jwt-key-2024"
)

ALGORITHM = "HS256"

PUBLIC_PATHS = [
    "/api/v1/users/register",
    "/api/v1/users/login",
    "/api/v1/products",
    "/api/v1/health",
    "/api/v1/metrics",
    "/docs",
    "/openapi.json",
    "/redoc"
]


def is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith("/api/v1/products/")


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="smartretailx",
            issuer="user-management-service"
        )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type"
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )

    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token audience"
        )

    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token issuer"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


def extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    parts = auth_header.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]