variable "region" {
  description = "AWS region for always-on resources."
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Short project prefix used to name global resources."
  type        = string
  default     = "fastapi-pool-mvp"
}

variable "billing_alarm_usd" {
  description = "CloudWatch billing alarm threshold in USD."
  type        = number
  default     = 15
}

variable "budget_monthly_usd" {
  description = "Monthly cost budget limit in USD."
  type        = number
  default     = 15
}

variable "budget_email" {
  description = "Email address for budget and billing alarm notifications."
  type        = string
}

variable "enable_github_oidc" {
  description = "Create an OIDC trust role so GitHub Actions can deploy without stored AWS keys."
  type        = bool
  default     = true
}

variable "github_repo" {
  description = "GitHub repository allowed to assume the deploy role (org/repo)."
  type        = string
  default     = "CANDIDATE_NAME/fastapi-pool-mvp-observability"
}

variable "ecr_image_tag_limit" {
  description = "Number of images the ECR lifecycle policy keeps."
  type        = number
  default     = 10
}
