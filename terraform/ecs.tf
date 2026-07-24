# ────────────────────────────────────────────────────────────
#  ecs.tf - Elastic Container Service parael manejo del contenedor de la aplicación
# ────────────────────────────────────────────────────────────
# ── Logs ─────────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "nuestroentorno" {
  name              = "/ecs/${var.project_name}"
  retention_in_days = 7
}

# ── Cluster ───────────────────────────────────────────────────────
resource "aws_ecs_cluster" "nuestroentorno" {
  name = var.project_name
}

resource "aws_ecs_cluster_capacity_providers" "nuestroentorno" {
  cluster_name       = aws_ecs_cluster.nuestroentorno.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
}

# ── Task Definition ───────────────────────────────────────────────
# Terraform crea la revisión inicial con imagen placeholder.
# El CI/CD registra nuevas revisiones con la imagen real y env vars en cada deploy.
resource "aws_ecs_task_definition" "nuestroentorno" {
  family                   = var.project_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution_nuestroentorno.arn
  task_role_arn            = aws_iam_role.ecs_task_nuestroentorno.arn

  container_definitions = jsonencode([{
    name      = var.project_name
    image     = "${aws_ecr_repository.page_nuestroentorno.repository_url}:latest"
    essential = true

    portMappings = [{
      containerPort = 8080
      protocol      = "tcp"
    }]

    environment = [
      { name = "ENV_STATE", value = "PRODUCTION" }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.nuestroentorno.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# ── Service ───────────────────────────────────────────────────────
resource "aws_ecs_service" "nuestroentorno" {
  name                   = var.project_name
  cluster                = aws_ecs_cluster.nuestroentorno.id
  task_definition        = aws_ecs_task_definition.nuestroentorno.arn
  desired_count          = 1
  force_new_deployment   = true

  capacity_provider_strategy {
    capacity_provider = var.use_spot ? "FARGATE_SPOT" : "FARGATE"
    weight            = 1
    base              = 1
  }

  network_configuration {
    subnets          = [aws_subnet.public_nuestroentorno.id]
    security_groups  = [aws_security_group.nuestroentorno.id]
    assign_public_ip = true
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}
