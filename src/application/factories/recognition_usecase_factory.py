from src.application.use_cases.recognition.recognize_ingredients_use_case import RecognizeIngredientsUseCase
from src.application.use_cases.recognition.recognize_foods_use_case import RecognizeFoodsUseCase
from src.application.use_cases.recognition.recognize_batch_use_case import RecognizeBatchUseCase

from src.infrastructure.db.recognition_repository_impl import RecognitionRepositoryImpl
from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
from src.infrastructure.firebase.firebase_storage_adapter import FirebaseStorageAdapter

def make_recognize_ingredients_use_case(db):
    return RecognizeIngredientsUseCase(GeminiAdapterService(), RecognitionRepositoryImpl(db), FirebaseStorageAdapter())

def make_recognize_foods_use_case(db):
    return RecognizeFoodsUseCase(GeminiAdapterService(), RecognitionRepositoryImpl(db), FirebaseStorageAdapter())

def make_recognize_batch_use_case(db):
    return RecognizeBatchUseCase(GeminiAdapterService(), RecognitionRepositoryImpl(db), FirebaseStorageAdapter())