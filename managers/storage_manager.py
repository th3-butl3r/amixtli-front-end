from typing import Optional

from loguru import logger

from config.supabase_client import supabase
from config.settings import settings


# Name of the Supabase Storage bucket that holds report images.
_BUCKET = settings.SUPABASE_STORAGE_BUCKET


class StorageManager:
    """Manager for Supabase Storage read and delete operations on report images."""

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

    def delete_image(self, image_path: str) -> bool:
        """Delete a report image from the bucket.

        Called only on the 'eliminar' moderation action. The 'rechazar' action
        deliberately skips this so the image is kept for model training.

        Args:
            image_path: The file path within the bucket (value from image_path column).

        Returns:
            True on success, False if image_path is empty or an error occurs.
        """
        if not image_path or not image_path.strip():
            logger.warning(
                "BL > StorageManager.delete_image() - Received empty image_path, skipping"
            )
            return False

        logger.info(f"BL > StorageManager.delete_image() - Deleting path={image_path}")
        try:
            supabase.storage.from_(_BUCKET).remove([image_path])
            logger.info(f"BL > StorageManager.delete_image() - Deleted path={image_path}")
            return True
        except Exception as exc:
            logger.error(
                f"BL > StorageManager.delete_image() - Failed for path={image_path}: {exc}"
            )
            return False


storage_manager = StorageManager()
