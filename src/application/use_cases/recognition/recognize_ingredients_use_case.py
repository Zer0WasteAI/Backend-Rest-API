import uuid
from datetime import datetime, timezone
from typing import List
from src.domain.models.recognition import Recognition

class RecognizeIngredientsUseCase:
    def __init__(self, ai_service, recognition_repository, storage_adapter, image_repository, fallback_name: str = "imagen defecto"):
        self.ai_service = ai_service
        self.recognition_repository = recognition_repository
        self.storage_adapter = storage_adapter
        self.image_repository = image_repository
        self.fallback_name = fallback_name

    def execute(self, user_uid: str, images_paths: List[str]) -> dict:
        images_files = []
        for path in images_paths:
            file = self.storage_adapter.get_image(path)
            images_files.append(file)

        result = self.ai_service.recognize_ingredients(images_files)

        recognition = Recognition(
            uid=str(uuid.uuid4()),
            user_uid=user_uid,
            images_paths=images_paths,
            recognized_at=datetime.now(timezone.utc),
            raw_result=result,
            is_validated=False,
            validated_at=None
        )
        self.recognition_repository.save(recognition)

        for ingredient in result["ingredients"]:
            similar = self.image_repository.find_best_match_name(ingredient["name"])
            if similar:
                ingredient["image_path"] = similar.image_path
            else:
                ingredient["image_path"] = self.image_repository.find_by_name(self.fallback_name).image_path

        return result