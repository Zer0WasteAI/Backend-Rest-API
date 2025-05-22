import uuid
from pathlib import Path
from src.domain.models.image_reference import ImageReference

class ImageLoaderService:
    def __init__(self, storage_adapter, image_repository):
        self.storage_adapter = storage_adapter
        self.image_repository = image_repository

    def sync_all_images(self):
        folders = {
            "foods": "food",
            "ingredients": "ingredient",
            "default": "default"
        }

        count = 0
        for folder, image_type in folders.items():
            count += self.sync_folder(folder, image_type)

        return count

    def sync_folder(self, folder: str, image_type: str) -> int:
        blobs = self.storage_adapter.list_blobs(
            folder + "/",
            valid_extensions=[".jpg", ".jpeg", ".png"]
        )
        new_images = 0

        for blob in blobs:
            name = self._normalize_name(blob.name)

            if not self.image_repository.find_by_name(name):
                image_ref = ImageReference(
                    uid=str(uuid.uuid4()),
                    name=name,
                    image_path=blob.public_url,
                    image_type=image_type
                )
                self.image_repository.save(image_ref)
                print(f"📥 Nueva imagen registrada: {name} ({blob.name})")
                new_images += 1
            else:
                print(f"✅ Ya existía: {name} ({blob.name})")

        return new_images

    def _normalize_name(self, blob_name: str) -> str:
        return Path(blob_name).stem.lower().replace('-', ' ').replace('_', ' ')
