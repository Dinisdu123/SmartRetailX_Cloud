from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from app.middleware.auth import (
    is_public_path,
    extract_token,
    verify_token
)

from app.router import resolve_service

import httpx
import uuid
import logging
import json
import time

from dotenv import load_dotenv


load_dotenv()


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("api-gateway")


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="SmartRetailX — API Gateway",
    description="Single entry point for all SmartRetailX microservices",
    version="1.0.0"
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
# OPENAPI
# ============================================================

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="SmartRetailX — API Gateway",
        version="1.0.0",
        description="Single entry point for all SmartRetailX microservices",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    openapi_schema["security"] = [
        {
            "BearerAuth": []
        }
    ]

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/v1/health")
def health_check():

    return {
        "status": "healthy",
        "service": "api-gateway",
        "routes": [
            "/api/v1/users → User Management Service (port 8001)",
            "/api/v1/products → Product Catalogue Service (port 8002)",
            "/api/v1/orders → Order Processing Service (port 8003)",
            "/api/v1/inventory → Inventory Management Service (port 8004)"
        ]
    }


# ============================================================
# DISTRIBUTED TRACE TEST
# ============================================================

@app.get("/api/v1/trace-test")
async def trace_test(request: Request):

    trace_id = str(uuid.uuid4())[:8]

    results = {}

    headers = {
        "X-Request-ID": trace_id,
        "X-Gateway": "smartretailx-api-gateway"
    }

    logger.info(json.dumps({
        "trace_id": trace_id,
        "service": "api-gateway",
        "event": "trace_test_started"
    }))

    services = {
        "user-management": "http://localhost:8001/api/v1/health",
        "product-catalogue": "http://localhost:8002/api/v1/health",
        "order-processing": "http://localhost:8003/api/v1/health",
        "inventory-management": "http://localhost:8004/api/v1/health"
    }

    async with httpx.AsyncClient(timeout=5.0) as client:

        for service_name, url in services.items():

            try:

                response = await client.get(
                    url,
                    headers=headers
                )

                results[service_name] = {
                    "status": response.json().get(
                        "status",
                        "unknown"
                    ),
                    "status_code": response.status_code,
                    "trace_id_forwarded": trace_id
                }

            except Exception as e:

                results[service_name] = {
                    "status": "unavailable",
                    "error": str(e),
                    "trace_id_forwarded": trace_id
                }

    logger.info(json.dumps({
        "trace_id": trace_id,
        "service": "api-gateway",
        "event": "trace_test_complete",
        "services_checked": len(results)
    }))

    return {
        "trace_id": trace_id,
        "message": (
            "Distributed trace completed — "
            "check service logs for the trace_id"
        ),
        "results": results
    }


# ============================================================
# API GATEWAY
# ============================================================

@app.api_route(
    "/api/v1/{path:path}",
    methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH"
    ]
)
async def gateway(
    request: Request,
    path: str
):

    request_id = str(uuid.uuid4())[:8]

    start_time = time.time()

    full_path = f"/api/v1/{path}"

    logger.info(json.dumps({
        "request_id": request_id,
        "service": "api-gateway",
        "method": request.method,
        "path": full_path,
        "client_ip": request.client.host
        if request.client else None
    }))


    # ========================================================
    # AUTHENTICATION
    # ========================================================

    if not is_public_path(full_path):

        token = extract_token(request)

        if not token:

            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )

        verify_token(token)


    # ========================================================
    # RESOLVE TARGET SERVICE
    # ========================================================

    target_base = resolve_service(full_path)

    if not target_base:

        raise HTTPException(
            status_code=404,
            detail=f"No service found for path: {full_path}"
        )


    # ========================================================
    # BUILD TARGET URL
    # ========================================================

    target_url = f"{target_base}{full_path}"

    if request.url.query:
        target_url += f"?{request.url.query}"


    # ========================================================
    # FORWARD HEADERS
    # ========================================================

    headers = dict(request.headers)

    headers["X-Request-ID"] = request_id
    headers["X-Gateway"] = "smartretailx-api-gateway"

    headers.pop("host", None)


    # ========================================================
    # FORWARD REQUEST
    # ========================================================

    try:

        body = await request.body()

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body
            )


        duration_ms = round(
            (time.time() - start_time) * 1000,
            2
        )


        logger.info(json.dumps({
            "request_id": request_id,
            "service": "api-gateway",
            "method": request.method,
            "path": full_path,
            "target": target_url,
            "status_code": response.status_code,
            "duration_ms": duration_ms
        }))


        # ====================================================
        # RESPONSE
        # ====================================================

        content_type = response.headers.get(
            "content-type",
            ""
        )

        if "application/json" in content_type:

            content = response.json()

        else:

            content = response.text


        return JSONResponse(
            content=content,
            status_code=response.status_code,
            headers={
                "X-Request-ID": request_id
            }
        )


    # ========================================================
    # CONNECTION ERROR
    # ========================================================

    except httpx.ConnectError:

        logger.error(json.dumps({
            "request_id": request_id,
            "service": "api-gateway",
            "event": "service_unavailable",
            "target": target_url
        }))

        raise HTTPException(
            status_code=503,
            detail="Service unavailable. Please try again later."
        )


    # ========================================================
    # TIMEOUT
    # ========================================================

    except httpx.TimeoutException:

        logger.error(json.dumps({
            "request_id": request_id,
            "service": "api-gateway",
            "event": "service_timeout",
            "target": target_url
        }))

        raise HTTPException(
            status_code=504,
            detail="Service timeout. Please try again later."
        )