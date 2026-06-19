import os
from typing import Optional

from dotenv import dotenv_values
from pydantic_settings import BaseSettings

_CONFIG_PATH = "config/.env"

# En desarrollo local el archivo .env existe; en producción (App Runner) no existe
# y las variables llegan como env vars inyectadas por Secrets Manager.
_file: dict = dotenv_values(_CONFIG_PATH) if os.path.exists(_CONFIG_PATH) else {}


def _get(key: str) -> str:
    """Lee del archivo .env primero; si no existe, cae a os.environ."""
    value = _file.get(key) or os.environ.get(key)
    if not value:
        raise RuntimeError(f"BL > settings._get() - Missing required config: {key}")
    return value


def _get_optional(key: str) -> Optional[str]:
    """Como _get pero devuelve None si la clave no existe."""
    return _file.get(key) or os.environ.get(key)


_ENV_STATE = _get("ENV_STATE")


class BaseConfig(BaseSettings):
    """Global configurations."""

    PROJECT_NAME: Optional[str] = "NuestroEntorno"
    ENV_STATE: str = _ENV_STATE
    # Admin credentials are optional by design: if absent the admin routes
    # return 404 automatically, making them invisible in any non-LOCAL deployment.
    ALLOWED_EMAILS: Optional[str] = _get_optional(f"{_ENV_STATE.upper()}_ALLOWED_EMAILS")
    SECRET_KEY: Optional[str] = _get_optional(f"{_ENV_STATE.upper()}_SECRET_KEY")
    SUPABASE_URL: str = _get(f"{_ENV_STATE.upper()}_SUPABASE_URL")
    SUPABASE_KEY: str = _get(f"{_ENV_STATE.upper()}_SUPABASE_KEY")
    SUPABASE_STORAGE_BUCKET: str = _get(f"{_ENV_STATE.upper()}_SUPABASE_STORAGE_BUCKET")
    BUY_ME_A_COFFEE_URL: str = _get(f"{_ENV_STATE.upper()}_BUY_ME_A_COFFEE_URL")


settings = BaseConfig()
