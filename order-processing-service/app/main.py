from fastapi import FastAPI, Request

from fastapi.middleware.cors import CORSMiddleware

from prometheus_fastapi_instrumentator import (
    Instrumentator
)

from app.routes.orders import (
    router as orders_router,
    get_sqs_client,
    sqs_circuit_breaker
)

from app.database import (
    Base,
    engine,
    SessionLocal
)

from app.config.settings import settings

from sqlalchemy import text

import logging
import json
import time
import uuid


# ============================================================
# DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(
    "order-processing-service"
)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(

    title=settings.APP_NAME,

    description=settings.APP_DESCRIPTION,

    version=settings.APP_VERSION,

    docs_url="/api/v1/docs",

    redoc_url="/api/v1/redoc",

    openapi_url="/api/v1/openapi.json"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://smartretailx-frontend-029223413210.s3-website.ap-south-1.amazonaws.com"
],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ============================================================
# REQUEST LOGGING
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

        "request_id":
            request_id,

        "trace_id":
            request.headers.get(
                "X-Request-ID",
                request_id
            ),

        "service":
            "order-processing-service",

        "method":
            request.method,

        "path":
            request.url.path,

        "client_ip":
            request.client.host
            if request.client
            else None
    }


    logger.info(
        f"INCOMING REQUEST: "
        f"{json.dumps(log_entry)}"
    )


    try:

        response = await call_next(
            request
        )

        duration_ms = round(
            (
                time.time()
                - start_time
            ) * 1000,
            2
        )


        log_entry.update({

            "status_code":
                response.status_code,

            "duration_ms":
                duration_ms
        })


        logger.info(
            f"COMPLETED REQUEST: "
            f"{json.dumps(log_entry)}"
        )


        return response


    except Exception as exc:

        logger.error(
            f"REQUEST FAILED: {exc}"
        )

        raise


# ============================================================
# PROMETHEUS
# ============================================================

Instrumentator().instrument(
    app
).expose(
    app,
    endpoint="/api/v1/metrics"
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(
    orders_router
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/api/v1/health"
)
def health_check():

    health = {

        "status":
            "healthy",

        "service":
            "order-processing-service",

        "version":
            settings.APP_VERSION,

        "environment":
            settings.APP_ENVIRONMENT,

        "database":
            "unknown",

        "sqs":
            "unknown"
    }


    # --------------------------------------------------------
    # PostgreSQL
    # --------------------------------------------------------

    try:

        db = SessionLocal()

        db.execute(
            text("SELECT 1")
        )

        db.close()

        health["database"] = (
            "connected"
        )


    except Exception as exc:

        health["database"] = (
            "disconnected"
        )

        health["status"] = (
            "degraded"
        )

        logger.error(
            f"Database health check failed: "
            f"{exc}"
        )


    # --------------------------------------------------------
    # SQS
    # --------------------------------------------------------

    try:

        sqs = get_sqs_client()

        sqs.list_queues(
            QueueNamePrefix="orders"
        )

        health["sqs"] = (
            "connected"
        )


    except Exception as exc:

        health["sqs"] = (
            "disconnected"
        )

        health["status"] = (
            "degraded"
        )

        logger.error(
            f"SQS health check failed: "
            f"{exc}"
        )


    if (
        health["database"]
        == "disconnected"
        and
        health["sqs"]
        == "disconnected"
    ):

        health["status"] = (
            "unhealthy"
        )


    return health


# ============================================================
# CIRCUIT BREAKER STATUS
# ============================================================

@app.get(
    "/api/v1/circuit-breaker/status"
)
def circuit_breaker_status():

    return {

        "service":
            "order-processing-service",

        "circuit_breaker": {

            "state":
                sqs_circuit_breaker.state,

            "failure_count":
                sqs_circuit_breaker.failure_count,

            "failure_threshold":
                sqs_circuit_breaker.failure_threshold,

            "recovery_timeout_seconds":
                sqs_circuit_breaker.recovery_timeout,

            "last_failure_time":
                sqs_circuit_breaker.last_failure_time
        }
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {

        "service":
            settings.APP_NAME,

        "version":
            settings.APP_VERSION,

        "documentation":
            "/api/v1/docs",

        "health":
            "/api/v1/health",

        "metrics":
            "/api/v1/metrics"
    }