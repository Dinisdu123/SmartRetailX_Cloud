variable "aws_region" {
  description = "Primary AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  type    = string
  default = "smartretailx"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "az_count" {
  type    = number
  default = 2
}

variable "db_username" {
  type    = string
  default = "smartretailx_admin"
}

variable "db_password" {
  description = "Master password for RDS. Pass via -var or TF_VAR_db_password, never commit."
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT signing secret shared by services."
  type        = string
  sensitive   = true
}



# name -> {port, path_prefix, health_check_path}
variable "services" {
  description = "Microservices to deploy on ECS Fargate"
  type = map(object({
    port              = number
    path_prefix       = string
    health_check_path = string
    cpu               = number
    memory            = number
    desired_count     = number
    min_count         = number
    max_count         = number
  }))
  default = {
    "user-management-service" = {
      port = 8001
      path_prefix = "/api/v1/users*"
      health_check_path = "/api/v1/health"
      cpu = 256
      memory = 512
      desired_count = 2
      min_count = 2
      max_count = 6
    }
    "product-catalogue-service" = {
      port = 8002
      path_prefix = "/api/v1/products*"
      health_check_path = "/api/v1/health"
      cpu = 256
      memory = 512
      desired_count = 2
      min_count = 2
      max_count = 8
    }
    "order-processing-service" = {
      port = 8003
      path_prefix = "/api/v1/orders*"
      health_check_path = "/api/v1/health"
      cpu = 256
      memory = 512
      desired_count = 2
      min_count = 2
      max_count = 8
    }
    "inventory-management-service" = {
      port = 8004
      path_prefix = "/api/v1/inventory*"
      health_check_path = "/api/v1/health"
      cpu = 256
      memory = 512
      desired_count = 2
      min_count = 2
      max_count = 6
    }
    "api-gateway" = {
      port = 8000
      path_prefix = "/*"
      health_check_path = "/health"
      cpu = 256
      memory = 512
      desired_count = 2
      min_count = 2
      max_count = 6
    }
  }
}