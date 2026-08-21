terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  # Recommended: remote state so your team / CI doesn't fight over local state.
  # Create the bucket + DynamoDB lock table once by hand (or in a bootstrap
  # workspace) BEFORE pointing this block at them, then uncomment:
  #
  # backend "s3" {
  #   bucket         = "smartretailx-tfstate-<your-unique-suffix>"
  #   key            = "smartretailx/dev/terraform.tfstate"
  #   region         = "eu-west-1"
  #   dynamodb_table = "smartretailx-tf-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}
