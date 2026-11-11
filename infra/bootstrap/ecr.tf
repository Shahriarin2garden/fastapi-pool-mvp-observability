resource "aws_ecr_repository" "order_api" {
  name                 = local.ecr_repo_name
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project   = var.project
    ManagedBy = "terraform"
  }
}

resource "aws_ecr_lifecycle_policy" "order_api" {
  repository = aws_ecr_repository.order_api.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep the most recent ${var.ecr_image_tag_limit} images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.ecr_image_tag_limit
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
