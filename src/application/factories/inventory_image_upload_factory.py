from src.application.use_cases.inventory.upload_inventory_image_use_case import UploadInventoryImageUseCase
from src.application.services.inventory_image_upload_service import InventoryImageUploadService
from src.application.services.inventory_image_upload_validator import InventoryImageUploadValidator
from src.infrastructure.firebase.firebase_storage_adapter import FirebaseStorageAdapter


def make_upload_inventory_image_use_case():
    """Factory para crear el caso de uso de upload de imágenes del inventario"""
    storage_adapter = FirebaseStorageAdapter()
    
    # Crear servicios especializados
    validator = InventoryImageUploadValidator()
    upload_service = InventoryImageUploadService(storage_adapter)
    
    # Crear Use Case con dependencias inyectadas
    return UploadInventoryImageUseCase(
        validator=validator,
        upload_service=upload_service
    ) 