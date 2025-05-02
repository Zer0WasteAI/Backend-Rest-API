import uuid
from datetime import datetime, timezone
from io import BytesIO
from src.domain.models.recognition import Recognition

class RecognizeIngredientsUseCase:
    def __init__(self, ai_service, recognition_repository):
        self.ai_service = ai_service
        self.recognition_repository = recognition_repository

    def execute(self, user_uid: str, image_file: BytesIO, image_path: str) -> dict:
        result = self.ai_service.recognize_ingredients(image_file)

        recognition = Recognition(
            uid=str(uuid.uuid4()),
            user_uid=user_uid,
            image_path=image_path,
            recognized_at=datetime.now(timezone.utc),
            raw_result=result,
            is_validated=False,
            validated_at=None
        )
        self.recognition_repository.save(recognition)
        return result