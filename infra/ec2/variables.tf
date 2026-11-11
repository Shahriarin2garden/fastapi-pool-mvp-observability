variable "region" {
  description = "AWS region for the EC2 demo instance."
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Short project prefix for resource naming."
  type        = string
  default     = "fastapi-pool-mvp"
}

variable "vpc_id" {
  description = "Existing VPC (the sandbox default VPC has no subnets yet)."
  type        = string
  default     = "vpc-0a48b6836ade7f854"
}

variable "subnet_cidr" {
  description = "CIDR for the demo subnet. Must not collide with existing subnets."
  type        = string
  default     = "172.31.16.0/20"
}

variable "availability_zone" {
  description = "AZ for the demo subnet."
  type        = string
  default     = "us-east-1a"
}

variable "internet_gateway_id" {
  description = "Existing IGW of the VPC. Leave empty to create one (script auto-resolves)."
  type        = string
  default     = ""
}

variable "instance_type" {
  description = "t3.small (2 GiB) fits the full 6-container stack; t3.micro (1 GiB) is too tight."
  type        = string
  default     = "t3.small"
}

variable "root_volume_gb" {
  type    = number
  default = 20
}

variable "repo_url" {
  description = "Git repo cloned on the instance by user_data. Must be publicly readable."
  type        = string
  default     = "https://github.com/Shahriarin2garden/fastapi-pool-mvp-observability.git"
}

variable "repo_branch" {
  type    = string
  default = "main"
}

variable "ssh_cidr" {
  description = "CIDR allowed to reach SSH. Restrict to your IP for tighter security."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "web_cidr" {
  description = "CIDR allowed to reach the API and Grafana ports."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "alert_recipient" {
  description = "Email written into the instance .env for Grafana alerting."
  type        = string
  default     = "you@example.com"
}
