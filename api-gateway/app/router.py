import os
from dotenv import load_dotenv

load_dotenv()

SERVICES = {
    "users": os.getenv("USER_SERVICE_URL", "http://localhost:8001"),
    "products": os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8002"),
    "orders": os.getenv("ORDER_SERVICE_URL", "http://localhost:8003"),
    "inventory": os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8004"),
    "notifications": os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8005"),
}

def resolve_service(path: str) -> str | None:
    parts = path.strip("/").split("/")
    if len(parts) < 3:
        return None

    resource = parts[2]

    if resource in SERVICES:
        return SERVICES[resource]

    return None