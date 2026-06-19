# ── Stage 1: builder ─────────────────────────────────────────────
# Exporta requirements.txt sin dependencias de desarrollo.
FROM python:3.11-slim AS builder

RUN pip install --no-cache-dir "poetry==1.8.5"

WORKDIR /build
COPY pyproject.toml poetry.lock ./

RUN poetry export \
    --format requirements.txt \
    --output requirements.txt \
    --without dev \
    --without-hashes

# ── Stage 2: runtime ─────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# curl es necesario para el healthcheck del docker-compose
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Usuario sin privilegios para no correr como root
RUN useradd --system --uid 1001 --no-create-home appuser

WORKDIR /app

# Dependencias de la app + gunicorn (WSGI server para producción)
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "gunicorn==23.0.0"

# Código fuente (config/.env excluido por .dockerignore)
COPY . .

USER appuser

EXPOSE 8080

# 2 workers es adecuado para instancias pequeñas (App Runner 0.25 vCPU).
# Cada instancia escala horizontalmente, no con más workers.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "60", "app:app"]
