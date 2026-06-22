# ─────────────────────────────────────────────────────────────────
#  variables.tf — Parámetros configurables de la infraestructura
# ─────────────────────────────────────────────────────────────────

variable "aws_region" {
  type        = string
  description = "Región de AWS donde vive toda la infraestructura"
}

variable "project_name" {
  type        = string
  description = "Nombre base que se usa para nombrar todos los recursos AWS"
}


variable "github_repository" {
  type        = string
  description = "Nombre del repositorio en GitHub (sin el owner)"
}

variable "environment" {
  type        = string
  description = "Nombre del entorno en cuestión"
}

variable "bucket_name" {
  type        = string
  description = "Nombre del bucket donde se almacena el estado de terraform"
}

variable "bucket_key" {
  type        = string
  description = "Key del bucket donde se almacena el estado de terraform"
}
