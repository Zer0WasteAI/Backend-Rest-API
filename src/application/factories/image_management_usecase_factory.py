from src.application.use_cases.image_management.find_image_by_name_use_case import FindImageByNameUseCase
from src.application.use_cases.image_management.search_similar_images_use_case import SearchSimilarImagesUseCase
from src.application.use_cases.image_management.assign_image_reference_use_case import AssignImageReferenceUseCase
from src.application.use_cases.image_management.sync_image_loader_use_case import SyncImageLoaderUseCase

from src.infrastructure.db.image_repository_impl import ImageRepositoryImpl
from src.infrastructure.firebase.image_loader_service import ImageLoaderService
from src.infrastructure.firebase.firebase_storage_adapter import FirebaseStorageAdapter

def make_search_similar_images_use_case(db):
    return SearchSimilarImagesUseCase(ImageRepositoryImpl(db))

def make_assign_image_reference_use_case(db):
    return AssignImageReferenceUseCase(ImageRepositoryImpl(db))

def make_find_images_by_name_use_case(db):
    return FindImageByNameUseCase(ImageRepositoryImpl(db))

def make_sync_image_loader_use_case(db):
    return SyncImageLoaderUseCase(
        ImageLoaderService(FirebaseStorageAdapter(), ImageRepositoryImpl(db))
    )