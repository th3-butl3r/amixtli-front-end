# Amixtli — Plataforma de datos ambientales

Amixtli es una aplicación web que recopila y visualiza reportes ciudadanos de acumulación de residuos en México. Nació en 2024 como proyecto de tesis y busca convertirse en un banco de datos ambientales abiertos para apoyar a empresas, gobiernos y colectivos en la mejora de políticas de limpieza urbana.

---

## Contexto

En México miles de toneladas de residuos terminan cada día en calles, ríos y áreas naturales. Amixtli parte de una premisa simple: **no hay malas decisiones, solo falta de datos.** Cada reporte ciudadano contribuye a identificar patrones, zonas críticas y oportunidades de mejora que de otro modo permanecerían invisibles.

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
| Configuración | pydantic-settings (variables de entorno) |
| Cliente HTTP | requests |
| Plantillas | Jinja2 |
| Mapa interactivo | Leaflet.js 1.9.4 + CartoDB Dark Matter |
| Frontend | Bootstrap 5.3, Font Awesome 6, Inter (Google Fonts) |
| Gestor de dependencias | Poetry |
| Contenedores | Docker / docker-compose |
| Logging | loguru |
| Linting / formato | black, ruff, isort, flake8, bandit, autoflake |
| Hooks | pre-commit |

---

## Arquitectura

```
amixtli-front-end/
├── app.py                  # Punto de entrada — rutas Flask (controladores delgados)
├── config/
│   ├── .env                # Variables de entorno (no versionado)
│   └── settings.py         # Singleton de configuración (pydantic-settings)
├── managers/
│   └── amixtli_manager.py  # Cliente HTTP hacia la API externa de Amixtli
├── services/
│   ├── map.py              # Construcción del mapa con folium
│   └── reports.py          # Obtención y estructuración de reportes para moderación
├── templates/              # Plantillas Jinja2
│   ├── base_generic.html   # Layout base (nav, footer, scripts globales)
│   ├── index.html          # Página de inicio con animación de datos
│   ├── map.html            # Mapa interactivo full-screen (Leaflet.js)
│   ├── app.html            # Presentación de la app móvil
│   ├── help.html           # Preguntas frecuentes
│   ├── contact.html        # Contacto y colaboración
│   ├── privacy_policy.html # Aviso de privacidad (LFPDPPP)
│   └── support.html        # Página de apoyo / donativo
├── static/
│   └── css/styles.css      # Tema oscuro (CSS custom properties)
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

### Flujo de datos

```
Usuario → Flask (app.py) → services/ → managers/amixtli_manager.py → API REST externa
                                ↓
                         Jinja2 template → HTML al navegador
```

- **`/mapa_reportes`** — renderiza únicamente reportes con `isValid=True`.

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


---

## Configuración

Toda la configuración se lee desde `config/.env`. El entorno activo se selecciona con `ENV_STATE` y todas las claves restantes se prefijan con ese valor:

```env
ENV_STATE=LOCAL

LOCAL_AMIXTLI_API_REPORTS=https://tu-api.example.com/reports
```

Entornos soportados: `LOCAL`, `DEVELOPMENT`, `PRODUCTION`.

---

## Instalación y ejecución

### Requisitos previos

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
```

La aplicación quedará disponible en `http://localhost:5000`.

### Docker

```bash
docker-compose up --build
```

---

## Desarrollo

### Comandos útiles

```bash
# Ejecutar tests con cobertura
pytest --cov=app tests/

# Linting y formato (todos los archivos)
pre-commit run --all-files

# Instalar hooks de pre-commit
pre-commit install
```

### Convenciones de código

- **Type hints** en todas las funciones (`typing`).
- **Docstrings** estilo Google en clases y funciones públicas.
- **Logging** con `loguru`, formato: `BL > NombreClase.nombre_funcion() - Mensaje`.
- **Credenciales** exclusivamente en `config/.env`, nunca en el código fuente.
- **Commits** en formato Conventional Commits (validado por pre-commit).

### Hooks de pre-commit configurados

| Hook | Propósito |
|------|-----------|
| `black` | Formato de código (line-length 90) |
| `ruff` | Linting rápido |
| `check-ast` | Validación de sintaxis Python |
| `detect-private-key` | Prevención de filtración de secretos |
| `end-of-file-fixer` | Archivos terminan en nueva línea |
| `trailing-whitespace` | Elimina espacios sobrantes |

---

## Seguridad

- Los datos de la API se escapan con `html.escape()` antes de ser inyectados en HTML para prevenir XSS almacenado.
- Las credenciales se gestionan exclusivamente mediante variables de entorno.

---

## Contacto

¿Quieres colaborar técnicamente, contribuir datos o apoyar el proyecto?

**contacto@bastionlab.com.mx**

El proyecto es mantenido por una sola persona. No tiene anuncios ni patrocinadores. Si lo encuentras útil, considera apoyarlo en [/apoyo](/apoyo).
---

*Amixtli — Datos para un México más limpio*
