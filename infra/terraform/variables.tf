variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment tag"
  type        = string
  default     = "local"
}

variable "use_localstack" {
  description = "Target LocalStack instead of real AWS (free, no account needed)"
  type        = bool
  default     = true
}

variable "localstack_endpoint" {
  description = "LocalStack edge endpoint"
  type        = string
  default     = "http://localhost:4566"
}

variable "slo_availability_target" {
  description = "Availability SLO target as a fraction (e.g. 0.999 = 99.9%)"
  type        = number
  default     = 0.999
}

variable "latency_slo_ms" {
  description = "Latency SLO threshold in milliseconds (p99 query duration)"
  type        = number
  default     = 100
}
