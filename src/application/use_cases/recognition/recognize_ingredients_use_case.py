import uuid
from datetime import datetime, timezone
from typing import IO, List
from src.domain.models.recognition import Recognition

class RecognizeIngredientsUseCase:
    def __init__(self, ai_service, recognition_repository):
        self.ai_service = ai_service
        self.recognition_repository = recognition_repository

    def execute(self, user_uid: str, images_files: List[IO[bytes]], images_paths: List[str]) -> dict:
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
        return result