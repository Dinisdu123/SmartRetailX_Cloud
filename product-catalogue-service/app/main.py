from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.routes.products import router as products_router
from app.database import check_dynamodb_connection
from app.config.settings import settings
import logging
import json
import time
import uuid
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("product-catalogue-service")

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    contact={
        "name": "SmartRetailX Support",
        "email": "support@smartretailx.com",
    },
    license_info={
        "name": "MIT License",
    },
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

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    log_entry = {
        "request_id": request_id,
        "trace_id": request.headers.get("X-Request-ID", request_id),
        "service": "product-catalogue-service",
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host
    }
    logger.info(f"INCOMING REQUEST: {json.dumps(log_entry)}")

    response = await call_next(request)

    duration_ms = round((time.time() - start_time) * 1000, 2)
    log_entry.update({
        "status_code": response.status_code,
        "duration_ms": duration_ms
    })
    logger.info(f"COMPLETED REQUEST: {json.dumps(log_entry)}")

    return response

Instrumentator().instrument(app).expose(app, endpoint="/api/v1/metrics")
app.include_router(products_router)

@app.get("/api/v1/health")
def health_check():
    """
    Health check endpoint that verifies DynamoDB connectivity
    
    Returns:
        - status: healthy/unhealthy
        - service: service name
        - database: connected/disconnected
        - version: service version
    """
    # Check DynamoDB connectivity
    db_connected = check_dynamodb_connection()
    is_healthy = db_connected
    
    logger.info(json.dumps({
        "service": "product-catalogue-service",
        "event": "health_check",
        "status": "healthy" if is_healthy else "unhealthy",
        "database": "connected" if db_connected else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }))
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "service": "product-catalogue-service",
        "database": "connected" if db_connected else "disconnected",
        "version": settings.APP_VERSION
    }

@app.get("/")
def root():
    """Root endpoint with service information"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "documentation": "/api/v1/docs",
        "health": "/api/v1/health",
        "metrics": "/api/v1/metrics"
    }