from supabase import Client, ClientOptions, create_client
from loguru import logger

from config.settings import settings

# Seconds before a query is considered timed out. Supabase free tier can be
# slow on the first request after inactivity (cold start), so we give it room.
_TIMEOUT = 20


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

    options = ClientOptions(
        postgrest_client_timeout=_TIMEOUT,
        storage_client_timeout=_TIMEOUT,
    )
    logger.info(
        f"BL > _build_client() - Supabase client initialized (timeout={_TIMEOUT}s)"
    )
    return create_client(url, key, options=options)


# Module-level singleton — imported wherever DB access is needed.
supabase: Client = _build_client()
