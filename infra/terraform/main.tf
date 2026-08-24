# Provider aimed at LocalStack by default so `terraform apply` costs nothing and
# needs no AWS account. Point it at real AWS by setting `use_localstack = false`
# and supplying real credentials — the resource definitions are identical.

provider "aws" {
  region                      = var.region
  access_key                  = var.use_localstack ? "test" : null
  secret_key                  = var.use_localstack ? "test" : null
  s3_use_path_style           = var.use_localstack
  skip_credentials_validation = var.use_localstack
  skip_metadata_api_check     = var.use_localstack
  skip_requesting_account_id  = var.use_localstack

  dynamic "endpoints" {
    for_each = var.use_localstack ? [1] : []
    content {
      dynamodb   = var.localstack_endpoint
      cloudwatch = var.localstack_endpoint
      iam        = var.localstack_endpoint
      sts        = var.localstack_endpoint
    }
  }
}

locals {
  tags = {
    Project   = "db-sentinel"
    ManagedBy = "terraform"
    Env       = var.environment
  }
}
