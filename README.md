# NuestroEntorno — Plataforma de datos ambientales

NuestroEntorno recopila y visualiza reportes ciudadanos de acumulación de residuos en México. Nació en 2024 como proyecto de tesis y busca convertirse en un banco de datos ambientales abiertos para apoyar a empresas, gobiernos y colectivos en la mejora de políticas de limpieza urbana.

---

## Contexto

En México miles de toneladas de residuos terminan cada día en calles, ríos y áreas naturales. NuestroEntorno parte de una premisa simple: **no hay malas decisiones, solo falta de datos.** Cada reporte ciudadano contribuye a identificar patrones, zonas críticas y oportunidades de mejora que de otro modo permanecerían invisibles.

Los datos recopilados se destinan a:

- Entrenar modelos de inteligencia artificial para la detección automática de residuos.
- Generar análisis estadísticos sobre distribución geográfica y tipos de acumulación.
- Publicarse como datos abiertos accesibles para investigadores, autoridades y sociedad civil.

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Lenguaje | Python 3.11 |
| Framework web | Flask 2.x |
| Configuración | pydantic-settings |
| Base de datos | Supabase (PostgreSQL) |
| Almacenamiento | Supabase Storage |
| Plantillas | Jinja2 |
| Mapa interactivo | Leaflet.js 1.9.4 |
| Gestor de dependencias | Poetry |
| Contenedores | Docker / docker-compose |
| Logging | loguru |
| Linting / formato | ruff, black, isort, bandit |
| Hooks | pre-commit |
| Infraestructura | Terraform + AWS |
| CI/CD | GitHub Actions |

---

## Arquitectura de la aplicación

```
app.py              ← Rutas Flask (controladores delgados)
config/
  settings.py       ← Singleton de configuración (pydantic-settings)
  .env              ← Variables de entorno (no versionado)
managers/
  supabase_manager.py  ← Operaciones a Supabase (reportes, conteos)
  storage_manager.py   ← URLs de imágenes en Supabase Storage
services/
  map.py            ← Construcción del mapa con Leaflet.js
templates/          ← Plantillas Jinja2
static/css/         ← Tema oscuro (CSS custom properties)
```

### Flujo de datos

```
Usuario → Flask (app.py) → services/ → managers/ → Supabase
                                ↓
                         Jinja2 template → HTML al navegador
```

---

## Infraestructura en AWS

```
                    ┌─────────────┐
                    │  Cloudflare │  CDN + WAF + HTTPS
                    └──────┬──────┘
                           │ HTTP (solo IPs Cloudflare)
                    ┌──────▼──────┐
                    │   AWS ECS   │  Fargate — contenedor Flask/gunicorn
                    │  (Fargate)  │  0.25 vCPU / 0.5 GB
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌─────────┐  ┌────────┐  ┌──────────┐
         │ Supabase│  │  ECR   │  │CloudWatch│
         │(externa)│  │ images │  │   Logs   │
         └─────────┘  └────────┘  └──────────┘
```

### Recursos de AWS gestionados con Terraform

| Archivo | Recursos |
|---------|----------|
| `ecr.tf` | Repositorio de imágenes Docker + política de ciclo de vida |
| `iam.tf` | Roles ECS execution, task y GitHub Actions OIDC |
| `vpc.tf` | VPC, subred pública, Internet Gateway, Route Table, Security Group |
| `ecs.tf` | Cluster, Task Definition y Service de ECS Fargate |
| `budget.tf` | Alerta de presupuesto mensual en AWS |

### Costos estimados

| Concepto | Costo/mes |
|----------|-----------|
| ECS Fargate (0.25 vCPU / 0.5 GB, 24/7) | ~$9.00 |
| ECR storage | ~$0.02 |
| CloudWatch Logs (7 días retención) | ~$0.05 |
| S3 estado Terraform | ~$0.01 |
| **Total estimado** | **~$9/mes** |

> Con `use_spot = true` el costo baja a ~$3/mes (Fargate Spot, puede interrumpirse).

---

## CI/CD

El pipeline de GitHub Actions se dispara en cada merge a `master`:

```
push a master
      │
      ▼
Autenticación AWS (OIDC — sin credenciales estáticas)
      │
      ▼
Build imagen Docker + push a ECR (tags: :latest y :<git-sha>)
      │
      ▼
Registrar nueva Task Definition con imagen + env vars
      │
      ▼
Actualizar ECS Service → esperar deploy estable
```

---

## Páginas disponibles

| Ruta | Descripción |
|------|-------------|
| `/` / `/inicio` | Página de inicio |
| `/mapa_reportes` | Mapa interactivo con reportes validados |
| `/app` | Presentación de la aplicación móvil |
| `/ayuda` | Preguntas frecuentes |
| `/contacto` | Información de contacto y colaboración |
| `/politica_privacidad` | Aviso de privacidad (LFPDPPP) |
| `/apoyo` | Información para apoyar el proyecto |
| `/health` | Health check (uso interno / ECS) |

---

## Configuración local

Toda la configuración se lee desde `config/.env`. El entorno activo se selecciona con `ENV_STATE`:

```env
ENV_STATE=LOCAL

LOCAL_SUPABASE_URL=https://xxx.supabase.co
LOCAL_SUPABASE_KEY=eyJ...
LOCAL_SUPABASE_STORAGE_BUCKET=nombre-bucket
LOCAL_BUY_ME_A_COFFEE_URL=https://buymeacoffee.com/...

# Opcionales (solo entorno LOCAL para moderación de reportes)
LOCAL_SECRET_KEY=clave-jwt
LOCAL_ALLOWED_EMAILS=["admin@ejemplo.com"]
```

---

## Instalación y ejecución

### Requisitos

- Python 3.11+
- [Poetry](https://python-poetry.org/)
- Docker (opcional)

### Desarrollo local

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd amixtli-front-end

# 2. Instalar dependencias
poetry install

# 3. Crear el archivo de configuración
cp config/.env.example config/.env   # editar con tus valores

# 4. Ejecutar la aplicación
python app.py
# → http://localhost:5000
```

### Docker

```bash
docker-compose up --build
# → http://localhost:8080
```

---

## Despliegue con Terraform

### Prerequisitos

- [Terraform](https://www.terraform.io/) >= 1.10
- AWS CLI configurado con permisos suficientes
- Bucket S3 para el estado remoto (ver instrucciones abajo)

### Bootstrap del bucket S3 (una sola vez)

```bash
aws s3api create-bucket --bucket nuestroentorno-tf-state --region us-east-1

aws s3api put-bucket-versioning \
  --bucket nuestroentorno-tf-state \
  --versioning-configuration Status=Enabled

aws s3api put-public-access-block \
  --bucket nuestroentorno-tf-state \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### Desplegar infraestructura

```bash
cd terraform

# Copiar y editar variables
cp mapeo_variables.tfvars.sample terraform.tfvars

# Inicializar (conecta con el backend S3)
terraform init

# Previsualizar cambios
terraform plan

# Aplicar
terraform apply
```

### Secretos en GitHub Actions

Después de `terraform apply`, configura estos secretos en **Settings → Secrets and variables → Actions**:

| Secreto | Fuente |
|---------|--------|
| `AWS_ROLE_ARN` | Output `github_actions_role_arn` |
| `ECS_CLUSTER` | Output `ecs_cluster_name` |
| `ECS_SERVICE` | Output `ecs_service_name` |
| `ECS_TASK_FAMILY` | Output `ecs_task_family` |
| `PRODUCTION_SUPABASE_URL` | Tu cuenta Supabase |
| `PRODUCTION_SUPABASE_KEY` | Tu cuenta Supabase |
| `PRODUCTION_SUPABASE_STORAGE_BUCKET` | Tu cuenta Supabase |
| `PRODUCTION_BUY_ME_A_COFFEE_URL` | Tu cuenta Buy Me a Coffee |

Y esta variable (no secreto) en la pestaña **Variables**:

| Variable | Valor |
|----------|-------|
| `ENV_STATE` | `PRODUCTION` |

---

## Desarrollo

### Comandos útiles

```bash
# Tests con cobertura mínima 80%
poetry run pytest --cov=app --cov=services --cov=managers tests/

# Linting y formato
pre-commit run --all-files

# Instalar hooks
pre-commit install
```

### Convenciones de código

- **Type hints** en todas las funciones.
- **Docstrings** estilo Google en clases y funciones públicas.
- **Logging** con `loguru`: `BL > NombreClase.nombre_funcion() - Mensaje`.
- **Credenciales** exclusivamente en `config/.env`, nunca en el código fuente.
- **Commits** en formato Conventional Commits (validado por pre-commit).

---

## Seguridad

- Tráfico de entrada restringido exclusivamente a IPs de Cloudflare (Security Group).
- Autenticación CI/CD via OIDC — sin credenciales estáticas de AWS en GitHub.
- Imagen Docker no corre como root.
- Escaneo de vulnerabilidades automático en cada push a ECR.
- Credenciales gestionadas exclusivamente mediante variables de entorno.

---

## Contacto

¿Quieres colaborar técnicamente, contribuir datos o apoyar el proyecto?

**contacto@bastionlab.com.mx**

El proyecto es mantenido por una sola persona. No tiene anuncios ni patrocinadores. Si lo encuentras útil, considera apoyarlo en [/apoyo](/apoyo).

---

*NuestroEntorno — Datos para un México más limpio*
