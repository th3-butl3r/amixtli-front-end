from typing import Optional

from dotenv import dotenv_values
from pydantic_settings import BaseSettings

env_file = dotenv_values("config/.env")


class BaseConfig(BaseSettings):
    """Global configurations."""

    PROJECT_NAME: Optional[str] = "Amixtli-front-end"
    ENV_STATE: str = env_file["ENV_STATE"]
    AMIXTLI_API_REPORTS: str = env_file[f"{ENV_STATE.upper()}_AMIXTLI_API_REPORTS"]
    ALLOWED_EMAILS: str = env_file[f"{ENV_STATE.upper()}_ALLOWED_EMAILS"]
    SECRET_KEY: str = env_file[f"{ENV_STATE.upper()}_SECRET_KEY"]


settings = BaseConfig()
