from src.application.services.ingredient_image_generator_service import IngredientImageGeneratorService
from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
from src.infrastructure.firebase.firebase_storage_adapter import FirebaseStorageAdapter


def make_ingredient_image_generator_service(db):
    """
    Factory simplificada para crear IngredientImageGeneratorService.
    Ya no necesita image_repository porque solo maneja URLs directamente.
    """
    return IngredientImageGeneratorService(
        ai_service=GeminiAdapterService(),
        storage_adapter=FirebaseStorageAdapter()
    ) 