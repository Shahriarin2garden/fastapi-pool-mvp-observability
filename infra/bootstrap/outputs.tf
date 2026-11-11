output "state_bucket" {
  value       = aws_s3_bucket.terraform_state.id
  description = "S3 bucket for the cluster layer remote state."
}

output "lock_table" {
  value       = aws_dynamodb_table.terraform_lock.name
  description = "DynamoDB table for Terraform state locking."
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.order_api.repository_url
  description = "ECR registry URL for the order API image."
}

output "github_deploy_role_arn" {
  value       = var.enable_github_oidc ? aws_iam_role.github_deploy[0].arn : null
  description = "Role ARN to put in AWS_DEPLOY_ROLE_ARN for GitHub Actions OIDC."
}
