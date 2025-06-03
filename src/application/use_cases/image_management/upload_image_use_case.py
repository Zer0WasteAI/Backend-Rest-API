import uuid
from typing import Dict, Any

from src.domain.models.image_reference import ImageReference
from src.domain.value_objects.upload_request import UploadRequest
from src.application.services.image_upload_validator import ImageUploadValidator
from src.application.services.file_upload_service import FileUploadService


class UploadImageUseCase:
    """Use Case que orquesta el proceso de upload de imágenes"""
    
    def __init__(self, validator: ImageUploadValidator, upload_service: FileUploadService, image_repository):
        self.validator = validator
        self.upload_service = upload_service
        self.image_repository = image_repository
    
    def execute(self, request: UploadRequest) -> Dict[str, Any]:
        """
        Ejecuta el proceso de upload de imagen
        
        Args:
            request: Value Object con todos los datos de la petición
            
        Returns:
            Dict con información de la imagen subida
        """
        # 1. Validar petición
        self.validator.validate_upload_request(request)
        
        # 2. Subir archivo
        storage_path, public_url = self.upload_service.upload_image(
            request.image_file, 
            request.image_type,
            request.user_uid
        )
        
        # 3. Crear referencia en BD
        image_ref = self._create_image_reference(request, public_url)
        saved_uid = self.image_repository.save(image_ref)
        
        # 4. Retornar resultado
        return {
            "message": "Image uploaded successfully",
            "image": {
                "uid": saved_uid,
                "name": image_ref.name,
                "image_path": image_ref.image_path,
                "image_type": image_ref.image_type,
                "storage_path": storage_path
            }
        }
    
    def _create_image_reference(self, request: UploadRequest, image_path: str) -> ImageReference:
        """Crea la entidad de dominio ImageReference"""
        return ImageReference(
            uid=str(uuid.uuid4()),
            name=request.item_name,
            image_path=image_path,
            image_type=request.image_type
        ) 