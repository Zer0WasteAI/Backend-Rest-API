from src.application.services.food_image_generator_service import FoodImageGeneratorService
from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
from src.infrastructure.firebase.firebase_storage_adapter import FirebaseStorageAdapter


def make_food_image_generator_service():
    """
    Factory para crear FoodImageGeneratorService.
    """
    return FoodImageGeneratorService(
        ai_service=GeminiAdapterService(),
        storage_adapter=FirebaseStorageAdapter()
    ) 