data "aws_iam_policy_document" "github_oidc_assume" {
  count = var.enable_github_oidc ? 1 : 0

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github[0].arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["https://token.actions.githubusercontent.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:*"]
    }
  }
}

resource "aws_iam_openid_connect_provider" "github" {
  count = var.enable_github_oidc ? 1 : 0

  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["https://token.actions.githubusercontent.com"]
  thumbprint_list = ["6938fd4d98bab03faadb56920e2d5c9c3d44cba5"]

  tags = { Project = var.project }
}

resource "aws_iam_role" "github_deploy" {
  count = var.enable_github_oidc ? 1 : 0

  name               = "${var.project}-github-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_oidc_assume[0].json

  tags = { Project = var.project }
}

resource "aws_iam_role_policy" "github_deploy" {
  count = var.enable_github_oidc ? 1 : 0

  name = "deploy-actions"
  role = aws_iam_role.github_deploy[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [
        {
          Effect = "Allow"
          Action = [
            "ecr:GetAuthorizationToken",
            "ecr:BatchCheckLayerAvailability",
            "ecr:BatchGetImage",
            "ecr:CompleteLayerUpload",
            "ecr:GetDownloadUrlForLayer",
            "ecr:InitiateLayerUpload",
            "ecr:PutImage",
            "ecr:UploadLayerPart"
          ]
          Resource = "*"
        },
        {
          Effect   = "Allow"
          Action   = ["eks:DescribeCluster", "eks:ListClusters"]
          Resource = "*"
        },
        {
          Effect   = "Allow"
          Action   = ["iam:CreateServiceLinkedRole"]
          Resource = "*"
        }
      ],
      [
        {
          Effect = "Allow"
          Action = [
            "elasticloadbalancing:*",
            "ec2:CreateSecurityGroup",
            "ec2:CreateTags",
            "ec2:DeleteSecurityGroup",
            "ec2:Describe*",
            "ec2:RevokeSecurityGroupIngress",
            "ec2:AuthorizeSecurityGroupIngress"
          ]
          Resource = "*"
        }
      ]
    )
  })
}
