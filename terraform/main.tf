provider "aws" {
  region = var.aws_region
}

resource "aws_ecr_repository" "app_repo" {
  name                 = var.repo_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "repo_policy" {
  repository = aws_ecr_repository.app_repo.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last ${var.image_count} images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = var.image_count
      }
      action = {
        type = "expire"
      }
    }]
  })
}

data "aws_iam_role" "ec2_role" {
  name = "notary-ec2-iam-role"
}

resource "aws_iam_policy" "ecr_access" {
  name        = "ECR_Read_Access_Policy"
  description = "Allow EC2 instance to pull images from ECR"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:DescribeRepositories"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_ecr_policy" {
  role       = data.aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.ecr_access.arn
}

output "repository_url" {
  value = aws_ecr_repository.app_repo.repository_url
}