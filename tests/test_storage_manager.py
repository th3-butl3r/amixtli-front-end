"""Tests for managers/storage_manager.py."""

from unittest.mock import MagicMock, patch

import pytest

from managers.storage_manager import StorageManager


@pytest.fixture
def manager() -> StorageManager:
    return StorageManager()


# ─── get_image_url ────────────────────────────────────────────────────────────


class TestGetImageUrl:
    def test_empty_string_returns_none(self, manager: StorageManager):
        assert manager.get_image_url("") is None

    def test_whitespace_only_returns_none(self, manager: StorageManager):
        assert manager.get_image_url("   ") is None

    def test_valid_path_returns_url(self, manager: StorageManager):
        mock_sb = MagicMock()
        mock_sb.storage.from_.return_value.get_public_url.return_value = (
            "https://cdn.example.com/uuid/photo.jpg"
        )
        with patch("managers.storage_manager.supabase", mock_sb):
            result = manager.get_image_url("uuid/photo.jpg")
        assert result == "https://cdn.example.com/uuid/photo.jpg"
        mock_sb.storage.from_.return_value.get_public_url.assert_called_once_with(
            "uuid/photo.jpg"
        )

    def test_exception_returns_none(self, manager: StorageManager):
        mock_sb = MagicMock()
        mock_sb.storage.from_.return_value.get_public_url.side_effect = Exception(
            "storage error"
        )
        with patch("managers.storage_manager.supabase", mock_sb):
            result = manager.get_image_url("uuid/photo.jpg")
        assert result is None


# ─── delete_image ─────────────────────────────────────────────────────────────


class TestDeleteImage:
    def test_empty_string_returns_false(self, manager: StorageManager):
        assert manager.delete_image("") is False

    def test_whitespace_only_returns_false(self, manager: StorageManager):
        assert manager.delete_image("   ") is False

    def test_valid_path_returns_true(self, manager: StorageManager):
        mock_sb = MagicMock()
        with patch("managers.storage_manager.supabase", mock_sb):
            result = manager.delete_image("uuid/photo.jpg")
        assert result is True
        mock_sb.storage.from_.return_value.remove.assert_called_once_with(
            ["uuid/photo.jpg"]
        )

    def test_exception_returns_false(self, manager: StorageManager):
        mock_sb = MagicMock()
        mock_sb.storage.from_.return_value.remove.side_effect = Exception("storage error")
        with patch("managers.storage_manager.supabase", mock_sb):
            result = manager.delete_image("uuid/photo.jpg")
        assert result is False
