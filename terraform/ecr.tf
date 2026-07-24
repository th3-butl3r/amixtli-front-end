# ─────────────────────────────────────────────────────────────────
# ecr.tf — Especificaciones del recurso ECR donde vivirán las imágenes Docker en AWS
# ─────────────────────────────────────────────────────────────────

resource "aws_ecr_repository" "page_nuestroentorno" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }
}

resource "aws_ecr_lifecycle_policy" "page_nuestroentorno" {
  repository = aws_ecr_repository.page_nuestroentorno.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Conservar solo las 2 imágenes más recientes"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 2
        }
        action = { type = "expire" }
      }
    ]
  })
}
