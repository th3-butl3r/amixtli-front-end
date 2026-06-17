from typing import Optional

from dotenv import dotenv_values
from pydantic_settings import BaseSettings

env_file = dotenv_values("config/.env")


class BaseConfig(BaseSettings):
    """Global configurations."""

    PROJECT_NAME: Optional[str] = "NuestoEntorno"
    ENV_STATE: str = env_file["ENV_STATE"]
    # Admin credentials are optional by design: if absent the admin routes
    # return 404 automatically, making them invisible in any non-LOCAL deployment.
    ALLOWED_EMAILS: Optional[str] = env_file.get(f"{ENV_STATE.upper()}_ALLOWED_EMAILS")
    SECRET_KEY: Optional[str] = env_file.get(f"{ENV_STATE.upper()}_SECRET_KEY")
    SUPABASE_URL: str = env_file[f"{ENV_STATE.upper()}_SUPABASE_URL"]
    SUPABASE_KEY: str = env_file[f"{ENV_STATE.upper()}_SUPABASE_KEY"]
    SUPABASE_STORAGE_BUCKET: str = env_file[
        f"{ENV_STATE.upper()}_SUPABASE_STORAGE_BUCKET"
    ]
    BUY_ME_A_COFFEE_URL: str = env_file[f"{ENV_STATE.upper()}_BUY_ME_A_COFFEE_URL"]


settings = BaseConfig()
