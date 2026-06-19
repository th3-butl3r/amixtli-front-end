# ─────────────────────────────────────────────────────────────────
#  main.tf — Provider de AWS y backend remoto de estado
# ─────────────────────────────────────────────────────────────────
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.51.0"
    }
  }

   backend "s3" {
    bucket       = var.bucket_name
    key          = var.bucket_key
    region       = var.aws_region
    encrypt      = true
    use_lockfile = true  # S3 native locking — reemplaza DynamoDB
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project = var.project_name
      Environment = var.environment
      ManagedBy = "Terraform"
    }
  }
}
