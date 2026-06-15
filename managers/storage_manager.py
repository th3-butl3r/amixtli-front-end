from typing import Optional

from loguru import logger

from config.supabase_client import supabase
from config.settings import settings


# Name of the Supabase Storage bucket that holds report images.
_BUCKET = settings.SUPABASE_STORAGE_BUCKET


class StorageManager:
    """Read-only manager for Supabase Storage.

    Provides URL resolution for report images stored in the configured bucket.
    All methods are non-destructive and safe to call in any environment.
    """

    def get_image_url(self, image_path: str) -> Optional[str]:
        """Return the public URL for a report image stored in the bucket.

        Args:
            image_path: The file path within the bucket as stored in the
                ``image_path`` column (e.g. ``"uuid/photo.jpg"``).

        Returns:
            Fully-qualified public URL string, or None if image_path is empty
            or an error occurs.
        """
        if not image_path or not image_path.strip():
            logger.warning(
                "BL > StorageManager.get_image_url() - Received empty image_path, skipping"
            )
            return None

        logger.info(
            f"BL > StorageManager.get_image_url() - Resolving URL for path={image_path}"
        )
        try:
            url: str = supabase.storage.from_(_BUCKET).get_public_url(image_path)
            logger.info(
                f"BL > StorageManager.get_image_url() - Resolved URL for path={image_path}"
            )

            return url
        except Exception as exc:
            logger.error(
                f"BL > StorageManager.get_image_url() - Failed for path={image_path}: {exc}"
            )
            return None


storage_manager = StorageManager()
