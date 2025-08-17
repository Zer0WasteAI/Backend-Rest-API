from src.application.use_cases.image_management.unified_upload_use_case import UnifiedUploadUseCase
from src.application.services.image_upload_validator import ImageUploadValidator
from src.application.services.inventory_image_upload_validator import InventoryImageUploadValidator
from src.application.services.file_upload_service import FileUploadService
from src.application.services.inventory_image_upload_service import InventoryImageUploadService
from src.infrastructure.db.image_repository_impl import ImageRepositoryImpl


def make_unified_upload_use_case() -> UnifiedUploadUseCase:
    """
    Factory function to create a UnifiedUploadUseCase instance with all dependencies.
    """
    # Create validators
    image_validator = ImageUploadValidator()
    inventory_validator = InventoryImageUploadValidator()
    
    # Create upload services
    file_upload_service = FileUploadService()
    inventory_upload_service = InventoryImageUploadService()
    
    # Create image repository
    image_repository = ImageRepositoryImpl()
    
    return UnifiedUploadUseCase(
        image_validator=image_validator,
        inventory_validator=inventory_validator,
        file_upload_service=file_upload_service,
        inventory_upload_service=inventory_upload_service,
        image_repository=image_repository
    )