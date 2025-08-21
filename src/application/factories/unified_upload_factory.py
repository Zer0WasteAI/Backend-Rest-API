from src.application.use_cases.image_management.unified_upload_use_case import UnifiedUploadUseCase
from src.application.services.image_upload_validator import ImageUploadValidator
from src.application.services.inventory_image_upload_validator import InventoryImageUploadValidator
from src.application.services.file_upload_service import FileUploadService
from src.application.services.inventory_image_upload_service import InventoryImageUploadService
from src.infrastructure.db.image_repository_impl import ImageRepositoryImpl
from src.infrastructure.firebase.firebase_storage_adapter import FirebaseStorageAdapter
from src.infrastructure.db.base import db


def make_unified_upload_use_case() -> UnifiedUploadUseCase:
    """
    Factory function to create a UnifiedUploadUseCase instance with all dependencies.
    """
    # Create image repository (requires db) and validators
    image_repository = ImageRepositoryImpl(db)
    image_validator = ImageUploadValidator(image_repository)
    inventory_validator = InventoryImageUploadValidator()
    
    # Create storage adapter
    storage_adapter = FirebaseStorageAdapter()
    
    # Create upload services
    file_upload_service = FileUploadService(storage_adapter)
    inventory_upload_service = InventoryImageUploadService(storage_adapter)
    
    return UnifiedUploadUseCase(
        image_validator=image_validator,
        inventory_validator=inventory_validator,
        file_upload_service=file_upload_service,
        inventory_upload_service=inventory_upload_service,
        image_repository=image_repository
    )
