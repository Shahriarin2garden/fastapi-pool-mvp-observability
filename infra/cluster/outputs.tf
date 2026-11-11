output "cluster_name" {
  value       = module.eks.cluster_name
  description = "EKS cluster name for kubeconfig and CI."
}

output "region" {
  value = var.region
}

output "ecr_repository_url" {
  value       = data.aws_ecr_repository.order_api.repository_url
  description = "ECR repository URL for the order API image."
}

output "node_group_autoscaling" {
  value = "spot: min=${var.node_min_size} max=${var.node_max_size} desired=${var.node_desired_size} (${join(", ", var.node_instance_types)})"
}
