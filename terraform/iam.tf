# ─────────────────────────────────────────────────────────────────
# iam.tf — Rol para que App Runner descargue imágenes de ECR
# ─────────────────────────────────────────────────────────────────
resource "aws_iam_role" "apprunner_ecr_nuestroentorno" {
  name = "${var.project_name}-apprunner-ecr-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "build.apprunner.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr_nuestroentorno" {
  role       = aws_iam_role.apprunner_ecr_nuestroentorno.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# ── 2. Rol para el contenedor en runtime ─────────────────────────

resource "aws_iam_role" "apprunner_instance_nuestroentorno" {
  name = "${var.project_name}-apprunner-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "tasks.apprunner.amazonaws.com" }
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
      {
        Effect   = "Allow"
        Action   = ["apprunner:UpdateService", "apprunner:DescribeService"]
        Resource = "*"  # Se reemplazará con el ARN de App Runner en el siguiente paso
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "github_actions_nuestroentorno" {
  role       = aws_iam_role.github_actions_nuestroentorno.name
  policy_arn = aws_iam_policy.github_actions_nuestroentorno.arn
}
