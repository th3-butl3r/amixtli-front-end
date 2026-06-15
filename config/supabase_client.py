from supabase import Client, create_client
from loguru import logger

from config.settings import settings


def _build_client() -> Client:
    """Initialize and return the Supabase client using settings credentials.

    Returns:
        Authenticated Supabase Client instance.

    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY are not configured.
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY

    if not url or not key:
        logger.error(
            "BL > _build_client() - SUPABASE_URL or SUPABASE_KEY are not configured"
        )
        raise ValueError(
            "Supabase credentials are required but not set in the environment."
        )

    logger.info("BL > _build_client() - Supabase client initialized")
    return create_client(url, key)


# Module-level singleton — imported wherever DB access is needed.
supabase: Client = _build_client()
