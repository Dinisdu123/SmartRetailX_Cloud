# SmartRetailX — Distributed Cloud Commerce Platform

A cloud-native, microservices-based e-commerce platform built on AWS, developed for COMP60010 (Enterprise Cloud and Distributed Web Applications). This project re-architects a monolithic retail platform into independently deployable services running on Amazon ECS Fargate.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Services](#services)
- [Technology Stack](#technology-stack)
- [AWS Infrastructure](#aws-infrastructure)
- [Project Structure](#project-structure)
- [Local Development Setup](#local-development-setup)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Monitoring and Observability](#monitoring-and-observability)
- [Backup and Disaster Recovery](#backup-and-disaster-recovery)
- [Known Issues and Limitations](#known-issues-and-limitations)
- [Future Improvements](#future-improvements)

---

## Architecture Overview

Client traffic reaches the platform through an **Application Load Balancer (ALB)**, which performs path-based routing directly to backend microservices running on **Amazon ECS Fargate**. A dedicated **API Gateway** service also runs behind the same ALB, handling centralised JWT verification and acting as the default routing target for any path not covered by an explicit ALB rule.

```
Browser
  |
  v
S3 Static Website (React frontend)
  |
  v
Application Load Balancer (path-based routing)
  |
  |-- /api/v1/users*      -> User Management Service
  |-- /api/v1/products*   -> Product Catalogue Service
  |-- /api/v1/orders*     -> Order Processing Service
  |-- /api/v1/inventory*  -> Inventory Management Service
  \-- (default)           -> API Gateway
                                |
                                |-- RDS PostgreSQL (Multi-AZ)
                                |-- DynamoDB (products, inventory)
                                \-- SQS (order events)
```

See `/docs/architecture-diagram.png`, `/docs/data-flow-diagram.png`, and `/docs/auth-flow-diagram.png` for detailed diagrams.

---

## Services

| Service                          | Port | Responsibility                                           | Data Store     |
| -------------------------------- | ---- | -------------------------------------------------------- | -------------- |
| **user-management-service**      | 8001 | Registration, login, JWT issuance, profile, RBAC         | RDS PostgreSQL |
| **product-catalogue-service**    | 8002 | Product CRUD, search, filtering                          | DynamoDB       |
| **order-processing-service**     | 8003 | Order creation, status transitions, SQS event publishing | RDS PostgreSQL |
| **inventory-management-service** | 8004 | Stock level tracking                                     | DynamoDB       |
| **api-gateway**                  | 8000 | Request proxying, centralised auth, default routing      | -              |

Each service is independently containerised, has its own ECS task definition, and can be deployed without affecting the others.

---

## Technology Stack

- **Language/Framework:** Python 3.11/3.12, FastAPI, Uvicorn
- **Frontend:** React (Vite), Axios, React Router
- **Databases:** Amazon RDS (PostgreSQL 15, Multi-AZ), Amazon DynamoDB
- **Messaging:** Amazon SQS (with dead-letter queue)
- **Auth:** JWT (PyJWT), bcrypt password hashing
- **Container orchestration:** Amazon ECS on AWS Fargate
- **Container registry:** Amazon ECR
- **Load balancing:** Application Load Balancer
- **Secrets:** AWS Secrets Manager, SSM Parameter Store
- **Service discovery:** AWS Cloud Map
- **Monitoring:** Amazon CloudWatch (Logs, Metrics, Dashboards, Alarms)
- **Backup:** AWS Backup
- **Frontend hosting:** Amazon S3 (static website hosting)
- **Testing:** pytest, Postman, k6

---

## AWS Infrastructure

| Resource           | Name/Identifier                                                |
| ------------------ | -------------------------------------------------------------- |
| ECS Cluster        | `smartretailx-cluster`                                         |
| ALB                | `smartretailx-alb`                                             |
| RDS Instance       | `smartretailx-postgres`                                        |
| DynamoDB Tables    | `smartretailx-products`, `smartretailx-inventory`              |
| SQS Queues         | `smartretailx-orders-queue`, `smartretailx-notification-queue` |
| S3 Frontend Bucket | `smartretailx-frontend-<account-id>`                           |
| AWS Backup Vault   | `smartretailx-backup-vault`                                    |
| Region             | `ap-south-1`                                                   |

All infrastructure was provisioned and managed via the AWS CLI; no CloudFormation/Terraform/CDK templates are included in this iteration (see Future Improvements).

---

## Project Structure

```
smartretailx/
|-- user-management-service/
|   |-- app/
|   |   |-- main.py
|   |   |-- config/settings.py
|   |   |-- models.py
|   |   |-- schemas.py
|   |   |-- database.py
|   |   |-- middleware/auth.py
|   |   \-- routes/users.py
|   |-- Dockerfile
|   |-- .dockerignore
|   \-- requirements.txt
|-- product-catalogue-service/
|   \-- (same structure, routes/products.py)
|-- order-processing-service/
|   \-- (same structure, routes/orders.py)
|-- inventory-management-service/
|   \-- (same structure, routes/inventory.py)
|-- api-gateway/
|   |-- app/
|   |   |-- main.py
|   |   |-- router.py
|   |   \-- middleware/auth.py
|   |-- Dockerfile
|   \-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- pages/
|   |   |-- components/
|   |   |-- context/AuthContext.jsx
|   |   \-- services/
|   |       |-- config.js
|   |       |-- api.js
|   |       |-- productApi.js
|   |       |-- orderApi.js
|   |       \-- inventoryApi.js
|   \-- package.json
|-- smartretailx-load-test.js          # k6 load testing script
|-- test_smartretailx_integration.py   # pytest integration suite
|-- SmartRetailX-API.postman_collection.json
|-- cloudwatch-dashboard.json
|-- backup-plan-fixed.json
|-- backup-selection.json
\-- README.md
```

---

## Local Development Setup

Each service can be run locally for development. Example for `order-processing-service`:

```bash
cd order-processing-service
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Create a .env file (NEVER commit this -- see .dockerignore)
cat > .env << EOF
DATABASE_URL=postgresql://postgres:password@localhost:5432/orderdb
JWT_SECRET_KEY=<your-local-dev-secret>
SQS_ENDPOINT=http://localhost:9324
PRODUCT_SERVICE_URL=http://localhost:8002
EOF

uvicorn app.main:app --reload --port 8003
```

Repeat for each service, adjusting ports and dependencies accordingly. Local development assumes:

- A local PostgreSQL instance for `user-management-service` and `order-processing-service`
- A local DynamoDB emulator (e.g. `dynamodb-local` or an ElasticMQ-equivalent) for `product-catalogue-service` and `inventory-management-service`, or valid AWS credentials pointing at real DynamoDB

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173` by default, which must be included in each backend service's CORS `allow_origins` list.

---

## Deployment

Each service follows the same deployment pipeline:

```bash
# 1. Build the Docker image
docker build -t <service-name>-test .

# 2. Tag and push to ECR
docker tag <service-name>-test:latest \
  <account-id>.dkr.ecr.ap-south-1.amazonaws.com/smartretailx/<service-name>:<tag>

docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/smartretailx/<service-name>:<tag>

# 3. Register a new ECS task definition revision with the updated image
aws ecs register-task-definition --cli-input-json file://taskdef.json --region ap-south-1

# 4. Update the ECS service to roll onto the new revision
aws ecs update-service --cluster smartretailx-cluster \
  --service <service-name> \
  --task-definition <task-def-arn> \
  --region ap-south-1
```

ECS performs a rolling deployment with a deployment circuit breaker that automatically halts rollout if new tasks repeatedly fail health checks.

**Important:** ECR repositories in this project have **tag immutability enabled** -- an existing tag (e.g. `latest`) cannot be overwritten once pushed. Always push under a new, unique tag per deployment.

---

## Environment Variables

Sensitive values (database URLs, JWT secrets, DB credentials) are **never** stored in task definitions as plaintext. They are held in AWS Secrets Manager / SSM Parameter Store and injected at container start via the ECS task definition's `secrets` field.

| Variable                                               | Service(s)                                                                         | Source                         |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------- | ------------------------------ |
| `DATABASE_URL`                                         | order-processing, user-management (or split `DB_HOST`/`DB_USERNAME`/`DB_PASSWORD`) | SSM / Secrets Manager          |
| `JWT_SECRET_KEY`                                       | all services                                                                       | Secrets Manager                |
| `JWT_REFRESH_SECRET_KEY`                               | user-management                                                                    | Secrets Manager                |
| `SQS_QUEUE_URL`                                        | order-processing                                                                   | Plaintext env (non-sensitive)  |
| `PRODUCT_SERVICE_URL`                                  | order-processing                                                                   | Plaintext env, Cloud Map DNS   |
| `DYNAMODB_PRODUCTS_TABLE` / `DYNAMODB_INVENTORY_TABLE` | product-catalogue, inventory-management                                            | Plaintext env                  |
| `CORS_ORIGINS`                                         | user-management                                                                    | Plaintext env, comma-separated |
| `AWS_REGION`                                           | all services                                                                       | Plaintext env                  |

**Do not set `SQS_ENDPOINT` or `DYNAMODB_ENDPOINT` in production** -- these are local-development-only overrides. Leaving them unset causes services to correctly use real AWS endpoints.

---

## API Documentation

Each service auto-generates OpenAPI/Swagger documentation via FastAPI, available at:

```
http://<alb-dns-name>/api/v1/docs
```

per service when accessed directly, or via the individual service's `/api/v1/docs` path when running locally.

A Postman collection (`SmartRetailX-API.postman_collection.json`) is included, covering all endpoints across all services with automated test assertions and token-chaining (login response auto-populates the bearer token for subsequent requests).

---

## Testing

**Integration tests (pytest):**

```bash
pip install pytest requests
pytest test_smartretailx_integration.py -v
```

23 tests covering registration, login, authentication, RBAC, product browsing, order validation, and a full end-to-end customer journey -- run directly against the live deployed ALB endpoint.

**Load testing (k6):**

```bash
k6 run smartretailx-load-test.js
```

Simulates a staged load profile (ramp to 20 VUs, sustained load, spike to 50 VUs) exercising login, product browsing, and order history retrieval. See the technical report for detailed results and bottleneck analysis.

**API testing (Postman):** Import `SmartRetailX-API.postman_collection.json` and run the full collection via the Postman Runner.

---

## Monitoring and Observability

- **Logs:** Centralised in CloudWatch Logs, one log group per service (`/ecs/smartretailx/<service-name>`)
- **Dashboard:** `SmartRetailX-Platform` CloudWatch dashboard -- ECS CPU/memory per service, ALB request count/latency/errors, RDS CPU/connections
- **Alarms:** CPU thresholds per service, ALB 5xx error rate, RDS CPU, plus pre-existing auto-scaling target-tracking alarms and unhealthy-target alarms
- **Distributed tracing:** Not implemented in this iteration -- IAM permissions for AWS X-Ray exist but no service is instrumented. Request correlation is currently achieved via `X-Request-ID` header propagation and structured JSON logging instead.

---

## Backup and Disaster Recovery

- **AWS Backup** manages centralised, policy-driven backups for RDS PostgreSQL and both DynamoDB tables
- **Backup plan:** `smartretailx-backup-plan` -- daily backups at 18:00 UTC, 35-day retention
- **Backup vault:** `smartretailx-backup-vault`
- **RDS:** Multi-AZ enabled (automatic failover), storage encrypted at rest, 7-day native automated backup retention in addition to AWS Backup's 35-day retention
- **DynamoDB:** Server-side encryption enabled (AWS KMS-managed keys)

**RPO:** less than or equal to 24 hours (daily backup schedule) | **RTO:** near-zero for AZ failure (Multi-AZ failover); 10-30 minutes estimated for full restore from a recovery point (not yet drilled -- see Known Issues)

---

## Known Issues and Limitations

1. **No HTTPS/TLS** -- the platform currently runs over plain HTTP. CloudFront distribution creation is blocked pending AWS account verification (`AccessDenied: Your account must be verified before you can add new CloudFront resources`). This is the most significant outstanding gap before any production use.
2. **SQS events are published but not consumed** -- `order-processing-service` publishes `OrderPlaced`/`OrderConfirmed`/etc. events, but no service currently subscribes to them. Inventory stock is not automatically adjusted on order placement.
3. **Payment Service and Notification Service were not implemented** -- scoped in the original design, deferred due to time constraints.
4. **401/403 inconsistency** -- some endpoints return `401` for missing authentication, others return the FastAPI/Starlette `HTTPBearer` default of `403`. Found via integration testing, not yet standardised.
5. **Distributed tracing not instrumented** -- see Monitoring section above.
6. **DR restore procedure is documented but not drilled** -- backup creation has been verified, but a full restore-and-cutover exercise has not been performed.


---

## Future Improvements

In priority order:

1. Implement an SQS consumer in `inventory-management-service` to automatically adjust stock on order events (Saga pattern with compensating actions)
2. Complete AWS account verification and deploy CloudFront + ACM for end-to-end HTTPS
3. Increase `user-management-service` CPU allocation and re-tune the bcrypt thread pool based on load-test findings
4. Implement the Payment Service and a real event-driven Notification Service
5. Extend to multi-region deployment (RDS cross-region replica or Aurora Global Database, DynamoDB Global Tables, Route 53 latency-based routing)
6. Instrument AWS X-Ray distributed tracing across all services
7. Standardise authentication error codes across all services
8. Perform a full disaster recovery restore drill to empirically validate RTO estimates
9. Introduce Infrastructure as Code (CloudFormation/Terraform/CDK) to replace manual AWS CLI provisioning

---

## Author

NG Dinidu Sehara -- CB011679
COMP60010: Enterprise Cloud and Distributed Web Applications
