import requests
import time
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger("smartretailx-alerting")

SERVICES = {
    "api-gateway": "http://localhost:8000/api/v1/health",
    "user-management": "http://localhost:8001/api/v1/health",
    "product-catalogue": "http://localhost:8002/api/v1/health",
    "order-processing": "http://localhost:8003/api/v1/health",
    "inventory-management": "http://localhost:8004/api/v1/health",
}

INVENTORY_URL = "http://localhost:8004/api/v1/inventory"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))
CRITICAL_STOCK_THRESHOLD = int(os.getenv("CRITICAL_STOCK_THRESHOLD", "5"))

alerts_history = []

def create_alert(alert_type: str, severity: str, service: str, message: str, details: dict = {}):
    alert = {
        "id": len(alerts_history) + 1,
        "timestamp": datetime.utcnow().isoformat(),
        "alert_type": alert_type,
        "severity": severity,
        "service": service,
        "message": message,
        "details": details
    }
    alerts_history.append(alert)

    if severity == "CRITICAL":
        logger.error(json.dumps({
            "event": "ALERT",
            "severity": severity,
            "alert_type": alert_type,
            "service": service,
            "message": message,
            "details": details
        }))
    elif severity == "WARNING":
        logger.warning(json.dumps({
            "event": "ALERT",
            "severity": severity,
            "alert_type": alert_type,
            "service": service,
            "message": message,
            "details": details
        }))
    else:
        logger.info(json.dumps({
            "event": "ALERT",
            "severity": severity,
            "alert_type": alert_type,
            "service": service,
            "message": message,
            "details": details
        }))

    return alert

def check_service_health():
    logger.info("Running service health checks...")
    for service_name, health_url in SERVICES.items():
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                if status == "degraded":
                    create_alert(
                        alert_type="SERVICE_DEGRADED",
                        severity="WARNING",
                        service=service_name,
                        message=f"{service_name} is reporting degraded status",
                        details=data
                    )
                    logger.warning(f"⚠️  WARNING: {service_name} is DEGRADED")
                else:
                    logger.info(f"✅ {service_name} is healthy")
            else:
                create_alert(
                    alert_type="SERVICE_UNHEALTHY",
                    severity="CRITICAL",
                    service=service_name,
                    message=f"{service_name} returned status code {response.status_code}",
                    details={"status_code": response.status_code}
                )
                logger.error(f"🚨 CRITICAL: {service_name} returned {response.status_code}")

        except requests.exceptions.ConnectionError:
            create_alert(
                alert_type="SERVICE_UNAVAILABLE",
                severity="CRITICAL",
                service=service_name,
                message=f"{service_name} is unreachable — connection refused",
                details={"url": health_url}
            )
            logger.error(f" CRITICAL: {service_name} is UNAVAILABLE")

        except requests.exceptions.Timeout:
            create_alert(
                alert_type="SERVICE_TIMEOUT",
                severity="WARNING",
                service=service_name,
                message=f"{service_name} health check timed out",
                details={"url": health_url, "timeout": 5}
            )
            logger.warning(f"  WARNING: {service_name} health check TIMED OUT")

def check_inventory_levels():
    if not ADMIN_TOKEN:
        logger.info("No admin token configured — skipping inventory check")
        return

    try:
        response = requests.get(
            INVENTORY_URL,
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            timeout=5
        )
        if response.status_code == 200:
            items = response.json()
            for item in items:
                stock = item.get("stock_quantity", 0)
                product_name = item.get("product_name", "Unknown")
                product_id = item.get("product_id", "Unknown")

                if stock == 0:
                    create_alert(
                        alert_type="OUT_OF_STOCK",
                        severity="CRITICAL",
                        service="inventory-management",
                        message=f"{product_name} is OUT OF STOCK",
                        details={
                            "product_id": product_id,
                            "product_name": product_name,
                            "stock_quantity": stock
                        }
                    )
                    logger.error(f" CRITICAL: {product_name} is OUT OF STOCK")

                elif stock <= CRITICAL_STOCK_THRESHOLD:
                    create_alert(
                        alert_type="CRITICAL_LOW_STOCK",
                        severity="CRITICAL",
                        service="inventory-management",
                        message=f"{product_name} has critically low stock: {stock} units remaining",
                        details={
                            "product_id": product_id,
                            "product_name": product_name,
                            "stock_quantity": stock,
                            "threshold": CRITICAL_STOCK_THRESHOLD
                        }
                    )
                    logger.error(f" CRITICAL: {product_name} has only {stock} units left")

    except Exception as e:
        logger.error(f"Failed to check inventory levels: {e}")

def print_alert_summary():
    if not alerts_history:
        logger.info("No alerts fired — all systems operational")
        return

    logger.info(f" Alert Summary: {len(alerts_history)} total alerts")
    critical = [a for a in alerts_history if a["severity"] == "CRITICAL"]
    warnings = [a for a in alerts_history if a["severity"] == "WARNING"]
    logger.info(f"    Critical: {len(critical)}")
    logger.info(f"    Warnings: {len(warnings)}")

def run_monitoring():
    logger.info("=" * 60)
    logger.info("SmartRetailX Alerting System Started")
    logger.info(f"Monitoring {len(SERVICES)} services")
    logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
    logger.info(f"Critical stock threshold: {CRITICAL_STOCK_THRESHOLD} units")
    logger.info("=" * 60)

    cycle = 0
    while True:
        cycle += 1
        logger.info(f"\n--- Monitoring Cycle {cycle} ---")
        check_service_health()
        check_inventory_levels()
        print_alert_summary()
        logger.info(f"Next check in {CHECK_INTERVAL} seconds...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_monitoring()