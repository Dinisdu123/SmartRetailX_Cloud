import json
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.config.settings import settings
from app.database import Base, engine, get_db
from app.routes.users import router as users_router


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(
    "user-management-service"
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    contact={
        "name": "SmartRetailX Support",
        "email": "support@smartretailx.com"
    },
    license_info={
        "name": "MIT License"
    },
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST LOGGING
# ============================================================

@app.middleware("http")
async def logging_middleware(
    request: Request,
    call_next
):
    request_id = str(uuid.uuid4())[:8]

    start_time = time.time()

    client_ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    log_entry = {
        "request_id": request_id,
        "trace_id": request.headers.get(
            "X-Request-ID",
            request_id
        ),
        "service": "user-management-service",
        "method": request.method,
        "path": request.url.path,
        "client_ip": client_ip
    }

    logger.info(
        "INCOMING REQUEST: %s",
        json.dumps(log_entry)
    )

    try:
        response = await call_next(request)

    except Exception:
        logger.exception(
            "REQUEST FAILED: %s",
            json.dumps(log_entry)
        )
        raise

    duration_ms = round(
        (time.time() - start_time) * 1000,
        2
    )

    log_entry.update({
        "status_code": response.status_code,
        "duration_ms": duration_ms
    })

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "COMPLETED REQUEST: %s",
        json.dumps(log_entry)
    )

    return response


# ============================================================
# PROMETHEUS METRICS
# ============================================================

Instrumentator().instrument(app).expose(
    app,
    endpoint="/api/v1/metrics"
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(users_router)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/api/v1/health",
    tags=["System"],
    summary="Service health check"
)
def health_check():

    db_status = "disconnected"

    db = next(get_db())

    try:
        db.execute(text("SELECT 1"))

        db_status = "connected"

    except Exception as error:

        logger.error(
            "Database health check failed: %s",
            error
        )

    finally:
        db.close()

    is_healthy = db_status == "connected"

    return {
        "status": (
            "healthy"
            if is_healthy
            else "unhealthy"
        ),
        "service": "user-management-service",
        "database": db_status,
        "version": settings.APP_VERSION
    }


# ============================================================
# ROOT
# ============================================================

@app.get(
    "/",
    tags=["System"],
    summary="Service information"
)
def root():

    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "documentation": "/api/v1/docs",
        "health": "/api/v1/health",
        "metrics": "/api/v1/metrics"
    }