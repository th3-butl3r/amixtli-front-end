# ── 1. Execution Role — ECS lo usa para descargar la imagen de ECR ──
# Equivale al antiguo "apprunner-ecr-role" pero para ECS.
# ─────────────────────────────────────────────────────────────────
# iam.tf — Rol para que ECS descargue imágenes de ECR
# ─────────────────────────────────────────────────────────────────
resource "aws_iam_role" "ecs_execution_nuestroentorno" {
  name = "${var.project_name}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_nuestroentorno" {
  role       = aws_iam_role.ecs_execution_nuestroentorno.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ── 2. Task Role — lo usa el contenedor en runtime ────────────────
# Vacío por ahora. Se amplía si la app necesita acceder a S3, SQS, etc.

resource "aws_iam_role" "ecs_task_nuestroentorno" {
  name = "${var.project_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

# ── 3. OIDC + Rol para GitHub Actions ────────────────────────────

resource "aws_iam_openid_connect_provider" "github_nuestroentorno" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_actions_nuestroentorno" {
  name = "${var.project_name}-github-actions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRoleWithWebIdentity"
      Principal = { Federated = aws_iam_openid_connect_provider.github_nuestroentorno.arn }
      Condition = {
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:th3-butl3r/${var.github_repository}:*"
        }
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}

resource "aws_iam_policy" "github_actions_nuestroentorno" {
  name = "${var.project_name}-github-actions-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Push de imágenes a ECR
      {
        Effect   = "Allow"
        Action   = "ecr:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ]
        Resource = aws_ecr_repository.page_nuestroentorno.arn
      },
      # Desplegar nueva versión en ECS
      {
        Effect = "Allow"
        Action = [
          "ecs:RegisterTaskDefinition",
          "ecs:DescribeTaskDefinition",
          "ecs:UpdateService",
          "ecs:DescribeServices",
        ]
        Resource = "*"
      },
      # Necesario para que ECS pueda asumir los roles de execution y task
      {
        Effect = "Allow"
        Action = "iam:PassRole"
        Resource = [
          aws_iam_role.ecs_execution_nuestroentorno.arn,
          aws_iam_role.ecs_task_nuestroentorno.arn,
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:ListTasks",
          "ecs:DescribeTasks",
          "ec2:DescribeNetworkInterfaces",
        ]
        Resource = "*"
      },

    ]
  })
}

resource "aws_iam_role_policy_attachment" "github_actions_nuestroentorno" {
  role       = aws_iam_role.github_actions_nuestroentorno.name
  policy_arn = aws_iam_policy.github_actions_nuestroentorno.arn
}
