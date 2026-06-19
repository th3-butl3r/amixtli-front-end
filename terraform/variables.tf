# ─────────────────────────────────────────────────────────────────
#  variables.tf — Parámetros configurables de la infraestructura
# ─────────────────────────────────────────────────────────────────

variable "aws_region" {
  description = "Región de AWS donde vive toda la infraestructura"
  type        = string
}

variable "project_name" {
  description = "Nombre base que se usa para nombrar todos los recursos AWS"
  type        = string
}


variable "github_repository" {
  description = "Nombre del repositorio en GitHub (sin el owner)"
  type        = string
}

variable "environment" {
  description = "Nombre del entorno en cuestión"
  type = string
}

variable "bucket_name" {
  description = "Nombre del bucket donde se almacena el estado de terraform"
  type = string
}

variable "bucket_key" {
  description = "Key del bucket donde se almacena el estado de terraform"
  type = string
}
