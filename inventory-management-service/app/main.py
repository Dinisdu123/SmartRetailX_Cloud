from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.routes.inventory import router as inventory_router

from prometheus_fastapi_instrumentator import (
    Instrumentator
)

from app.consumer import start_consumer_thread
from app.database import check_dynamodb_connection
from app.config.settings import settings

import logging
import json
import time
import uuid


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(
    "inventory-management-service"
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://smartretailx-frontend-029223413210.s3-website.ap-south-1.amazonaws.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STARTUP: begin listening for order events
# ============================================================

@app.on_event("startup")
def startup_event():
    start_consumer_thread()


# ============================================================
# REQUEST LOGGING MIDDLEWARE
# ============================================================

@app.middleware("http")
async def logging_middleware(
    request: Request,
    call_next
):

    request_id = str(
        uuid.uuid4()
    )[:8]

    start_time = time.time()

    log_entry = {
        "request_id": request_id,
        "trace_id": request.headers.get(
            "X-Request-ID",
            request_id
        ),
        "service": "inventory-management-service",
        "method": request.method,
        "path": request.url.path,
        "client_ip": (
            request.client.host
            if request.client
            else None
        )
    }

    logger.info(
        f"INCOMING REQUEST: "
        f"{json.dumps(log_entry)}"
    )

    response = await call_next(request)

    duration_ms = round(
        (time.time() - start_time) * 1000,
        2
    )

    log_entry.update({
        "status_code": response.status_code,
        "duration_ms": duration_ms
    })

    logger.info(
        f"COMPLETED REQUEST: "
        f"{json.dumps(log_entry)}"
    )

    response.headers[
        "X-Request-ID"
    ] = request_id

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

app.include_router(
    inventory_router
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/api/v1/health",
    summary="Health check"
)
def health_check():

    db_connected = (
        check_dynamodb_connection()
    )

    health = {
        "status": (
            "healthy"
            if db_connected
            else "degraded"
        ),
        "service": (
            "inventory-management-service"
        ),
        "version": settings.APP_VERSION,
        "environment": (
            settings.APP_ENVIRONMENT
        ),
        "dynamodb": (
            "connected"
            if db_connected
            else "disconnected"
        )
    }

    logger.info(
        json.dumps({
            "service": (
                "inventory-management-service"
            ),
            "event": "health_check",
            "status": health["status"],
            "dynamodb": health["dynamodb"]
        })
    )

    return health


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "documentation": "/api/v1/docs",
        "health": "/api/v1/health",
        "metrics": "/api/v1/metrics"
    }