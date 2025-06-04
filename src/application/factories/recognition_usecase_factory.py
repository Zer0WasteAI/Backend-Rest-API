from src.application.use_cases.recognition.recognize_ingredients_use_case import RecognizeIngredientsUseCase
from src.application.use_cases.recognition.recognize_foods_use_case import RecognizeFoodsUseCase
from src.application.use_cases.recognition.recognize_batch_use_case import RecognizeBatchUseCase

from src.infrastructure.db.recognition_repository_impl import RecognitionRepositoryImpl
from src.infrastructure.db.image_repository_impl import ImageRepositoryImpl
from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
from src.infrastructure.firebase.firebase_storage_adapter import FirebaseStorageAdapter
from src.application.factories.ingredient_image_generator_factory import make_ingredient_image_generator_service
from src.infrastructure.inventory.inventory_calcularor_impl import InventoryCalculatorImpl

def make_recognize_ingredients_use_case(db):
    return RecognizeIngredientsUseCase(
        ai_service=GeminiAdapterService(), 
        recognition_repository=RecognitionRepositoryImpl(db), 
        storage_adapter=FirebaseStorageAdapter(), 
        image_repository=ImageRepositoryImpl(db),
        ingredient_image_generator_service=make_ingredient_image_generator_service(db),
        calculator_service=InventoryCalculatorImpl()
    )

def make_recognize_foods_use_case(db):
    return RecognizeFoodsUseCase(
        ai_service=GeminiAdapterService(), 
        recognition_repository=RecognitionRepositoryImpl(db), 
        storage_adapter=FirebaseStorageAdapter(),
        calculator_service=InventoryCalculatorImpl()
    )

def make_recognize_batch_use_case(db):
    return RecognizeBatchUseCase(
        ai_service=GeminiAdapterService(), 
        recognition_repository=RecognitionRepositoryImpl(db), 
        storage_adapter=FirebaseStorageAdapter(),
        calculator_service=InventoryCalculatorImpl()
    )