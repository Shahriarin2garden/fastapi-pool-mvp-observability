variable "region" {
  description = "AWS region for the ephemeral demo cluster."
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Short project prefix for resource naming."
  type        = string
  default     = "fastapi-pool-mvp"
}

variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
  default     = "fastapi-pool-mvp-demo"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version. Bump before the 14-month standard support window lapses, otherwise the control plane bills at 6x (extended support)."
  type        = string
  default     = "1.35"
}

variable "admin_cidrs" {
  description = "CIDRs allowed to reach the public EKS API endpoint."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "node_instance_types" {
  description = "Spot-friendly instance types for the managed node group."
  type        = list(string)
  default     = ["t3.medium", "t3.large"]
}

variable "node_min_size" {
  type    = number
  default = 1
}

variable "node_max_size" {
  type    = number
  default = 3
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "ecr_repo_name" {
  description = "ECR repository created by the bootstrap layer."
  type        = string
  default     = "fastapi-pool-mvp/order-api"
}

variable "grafana_admin_user" {
  description = "Grafana admin username."
  type        = string
  default     = "admin"
}

variable "grafana_admin_password" {
  description = "Grafana admin password."
  type        = string
  sensitive   = true
  default     = "ChangeMe-Demo123"
}

variable "alb_chart_version" {
  description = "aws-load-balancer-controller Helm chart version."
  type        = string
  default     = "1.8.2"
}

variable "metrics_server_chart_version" {
  description = "metrics-server Helm chart version."
  type        = string
  default     = "3.12.2"
}

variable "kube_prometheus_stack_chart_version" {
  description = "kube-prometheus-stack Helm chart version."
  type        = string
  default     = "62.7.0"
}

variable "loki_chart_version" {
  description = "loki Helm chart version."
  type        = string
  default     = "6.7.3"
}

variable "alloy_chart_version" {
  description = "alloy Helm chart version."
  type        = string
  default     = "0.12.1"
}
