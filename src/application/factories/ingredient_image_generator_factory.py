from src.application.services.ingredient_image_generator_service import IngredientImageGeneratorService
from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
from src.infrastructure.firebase.firebase_storage_adapter import FirebaseStorageAdapter
from src.infrastructure.db.image_repository_impl import ImageRepositoryImpl


def make_ingredient_image_generator_service(db):
    """Factory to create IngredientImageGeneratorService with all dependencies."""
    return IngredientImageGeneratorService(
        ai_service=GeminiAdapterService(),
        storage_adapter=FirebaseStorageAdapter(),
        image_repository=ImageRepositoryImpl(db)
    ) 