# ─────────────────────────────────────────────────────────────────
#  outputs.tf — Manejo de salidas en terraform
#  Los valores resultantes son necesarios para la configuración
#  de Github Actions y Cloudflare
# ─────────────────────────────────────────────────────────────────

output "ecr_repository_url" {
  description = "URL del repositorio ECR. La usa el CI/CD para hacer docker push."
  value       = aws_ecr_repository.page_nuestroentorno.repository_url
}

output "ecs_cluster_name" {
  description = "→ Guarda como secreto ECS_CLUSTER en GitHub Actions."
  value       = aws_ecs_cluster.nuestroentorno.name
}

output "ecs_service_name" {
  description = "→ Guarda como secreto ECS_SERVICE en GitHub Actions."
  value       = aws_ecs_service.nuestroentorno.name
}

output "ecs_task_family" {
  description = "→ Guarda como secreto ECS_TASK_FAMILY en GitHub Actions."
  value       = aws_ecs_task_definition.nuestroentorno.family
}

output "github_actions_role_arn" {
  description = "→ Guarda como secreto AWS_ROLE_ARN en GitHub Actions."
  value       = aws_iam_role.github_actions_nuestroentorno.arn
}
