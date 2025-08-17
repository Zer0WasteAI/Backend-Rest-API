import pytest
from unittest.mock import MagicMock


def test_firebase_storage_extract_bucket_path(monkeypatch):
    # Avoid firebase_admin initialization in module import
    import types
    fake_fb = types.SimpleNamespace(_apps={'x': object()})
    monkeypatch.setitem(__import__('sys').modules, 'firebase_admin', fake_fb)

    from src.infrastructure.firebase.firebase_storage_adapter import FirebaseStorageAdapter
    adapter = FirebaseStorageAdapter.__new__(FirebaseStorageAdapter)
    # Mock bucket to avoid network
    adapter.bucket = MagicMock()
    # Test URL parsing helper
    path = FirebaseStorageAdapter._extract_bucket_path_from_url(adapter, 'https://storage.googleapis.com/bucket/uploads/file.jpg?Expires=123')
    assert path == 'uploads/file.jpg'


def test_image_loader_service_sync_folder():
    from src.infrastructure.firebase.image_loader_service import ImageLoaderService

    storage = MagicMock()
    # Mock blobs
    blob1 = MagicMock()
    blob1.name = 'ingredients/tomato.jpg'
    blob1.public_url = 'http://x/ingredients/tomato.jpg'
    blob2 = MagicMock()
    blob2.name = 'ingredients/onion.jpg'
    blob2.public_url = 'http://x/ingredients/onion.jpg'
    storage.list_blobs.return_value = [blob1, blob2]

    repo = MagicMock()
    repo.find_by_name.side_effect = [None, MagicMock()]  # first not exists, second exists

    service = ImageLoaderService(storage, repo)
    added = service.sync_folder('ingredients', 'ingredient')
    assert added == 1
    repo.save.assert_called_once()

