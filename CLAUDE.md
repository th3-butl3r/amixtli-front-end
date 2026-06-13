# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Amixtli is a Flask web application (Python 3.11) that serves as a front-end for a citizen reporting system. It displays geolocated waste/environmental reports on an interactive map and provides an admin interface for moderating incoming reports. The app communicates with an external Amixtli REST API — it has no local database.

## Development Commands

**Install dependencies (Poetry):**
```bash
poetry install
```

**Run locally:**
```bash
python app.py
```
Starts on `http://0.0.0.0:5000` in debug mode when `ENV_STATE` is `LOCAL` or `DEVELOPMENT`.

**Run with Docker:**
```bash
docker-compose up --build
```

**Linting / formatting (run manually or via pre-commit):**
```bash
pre-commit run --all-files
```
Pre-commit enforces: `black` (line length 88), `isort` (black profile), `flake8`, `autoflake`, `pycln`, `bandit`, and conventional commit messages.

## Configuration

All config is loaded from `config/.env` via `config/settings.py` (pydantic-settings). The active environment is selected by `ENV_STATE` (e.g. `LOCAL`, `DEVELOPMENT`, `PRODUCTION`), and all other keys are prefixed with that value:

```
ENV_STATE=LOCAL
LOCAL_AMIXTLI_API_REPORTS=<backend API URL>
LOCAL_ALLOWED_EMAILS=["admin@example.com"]
LOCAL_SECRET_KEY=<JWT secret>
```

`settings` is a module-level singleton imported wherever config values are needed.

## Architecture

```
app.py              ← Flask routes (thin controllers only)
config/settings.py  ← Pydantic config singleton
managers/
  amixtli_manager.py  ← HTTP client to external Amixtli API (requests)
services/
  map.py            ← Builds folium map HTML from validated reports
  reports.py        ← Fetches/structures unvalidated reports for moderation
templates/          ← Jinja2 HTML templates
static/css/         ← Static CSS assets
```

**Data flow:** `app.py` routes call `services/`, which delegate API calls to `managers/amixtli_manager.py`. `AmixtliManager` is a module-level singleton that wraps GET/PATCH calls to the reports API.

- The map page (`/mapa_reportes`) renders only `isValid=True` reports.
- The moderation page (`/reportes`) shows `isValid=False` reports, capped at 5 at a time.

**Authentication:** The `/validacion_reportes` login form accepts a personal JWT signed with `SECRET_KEY`. The email inside the decoded payload must be in `ALLOWED_EMAILS`. On success the token is passed as a query param to `/reportes` and forwarded as a Bearer token on PATCH requests to the backend.

**Map rendering:** `MapServices.build_map()` returns raw HTML via folium's `_repr_html_()` with inline string surgery at fixed character offsets (`services/map.py:131-133`) to strip folium's wrapper tags before embedding in the Jinja2 template.



## Project

WhyMex

## 🚀 Comandos Clave (Scripts)
- **Correr tests**: `pytest --cov=app tests/`
- **Formato y Lint**: `pre-commit run --all-files`

## 🛠️ Stack y Entorno
- **Python**: 3.11+
- **Gestor de dependencias**: Poetry (`poetry run ...`)
- **Linter/Formatter**: Ruff
- **Frameworks**: Flask

## 🛑 Reglas de Trabajo (Workflow)
- **Calidad**: Escribe type hints (módulo `typing`) en todas las funciones.
- **Documentación**: Añade docstrings estilo **Google** en clases y funciones públicas.
- **Pruebas**: Ejecuta `poetry run pytest` antes de proponer cualquier cambio.
- **Respuestas**: Sé conciso. No incluyas explicaciones largas ni introducciones a menos que se te pida.
- **Comentarios**: Añade comentarios en las partes complejas.
- **Logging**: Añade logs en las funciones con el formato: "BL > NAME_FUNCTION() - MESSAGE". Si la función esta dentro de una clase entonces es: "BL > NAME_CLASS.NAME_FUNCTION() - MESSAGE". Usa el módulo `loguru`. Evita usar `print()`.
- **Secrets**: Las credenciales se leen desde variables de entorno (`.env`), dicho archivo en desarrollo local vive dentro de la carpeta config. Nunca expongas tokens ni claves de API en el código fuente.
- **Tipado estático**: Usa `pydantic` para validación de datos en los endpoints.



## 📁 Estructura del proyecto
- `app.py`: La entra del programa, donde arranca todo.
- `docker-compose.yml`: Para correr el proyecto de manera desplegada y que sea posible desplegarlo en un futuro sin ningún problema.

### Backend
- `src/config/`: Lógica de las configuraciones y la carga de las variables de entorno.
- `src/managers`: Lógica de operaciones a la base de datos.
- `src/services`: Lógica del tratamiento de datos obtenidos de la base de datos.
- `tests/`: Pruebas unitarias y de integración.

### Frontend
- `src/web/static`: Manejo de archivos .css para UI
- `src/web/templates`: Manejo de archivos .html



## ⚠️ Lo que NUNCA debes hacer
- No instales dependencias globales ni uses `pip install` sin consultar.
- No modifiques los archivos de configuración (`pyproject.toml`). Cuando sea necesario añadir una librería, lo haré yo manualmente.
- Si no estás seguro de una ruta o función, detente y pregunta.
- Jamas exponer variables de entorno.
