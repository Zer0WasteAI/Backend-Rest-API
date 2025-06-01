import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from src.domain.value_objects.upload_request import UploadRequest
from src.shared.exceptions.custom import InvalidRequestDataException


class ImageUploadValidator:
    """Servicio especializado en validar uploads de imágenes"""
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_TYPES = ['food', 'ingredient', 'default']
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 100
    
    def __init__(self, image_repository):
        self.image_repository = image_repository
    
    def validate_upload_request(self, request: UploadRequest) -> None:
        """Valida completamente una petición de upload"""
        self._validate_file(request.image_file)
        self._validate_item_name(request.item_name)
        self._validate_image_type(request.image_type)
        self._validate_unique_name(request.item_name)
    
    def _validate_file(self, file: FileStorage) -> None:
        """Valida el archivo subido"""
        if not file or file.filename == '':
            raise InvalidRequestDataException("No file selected")
        
        self._validate_file_extension(file)
        self._validate_file_size(file)
    
    def _validate_file_extension(self, file: FileStorage) -> None:
        """Valida la extensión del archivo"""
        file_ext = os.path.splitext(secure_filename(file.filename))[1].lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise InvalidRequestDataException(
                f"File type {file_ext} not allowed. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
    
    def _validate_file_size(self, file: FileStorage) -> None:
        """Valida el tamaño del archivo"""
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > self.MAX_FILE_SIZE:
            raise InvalidRequestDataException(
                f"File size too large. Maximum {self.MAX_FILE_SIZE // (1024*1024)}MB allowed"
            )
    
    def _validate_item_name(self, item_name: str) -> None:
        """Valida el nombre del item"""
        if len(item_name) < self.MIN_NAME_LENGTH:
            raise InvalidRequestDataException(
                f"item_name must be at least {self.MIN_NAME_LENGTH} characters"
            )
        
        if len(item_name) > self.MAX_NAME_LENGTH:
            raise InvalidRequestDataException(
                f"item_name must be less than {self.MAX_NAME_LENGTH} characters"
            )
    
    def _validate_image_type(self, image_type: str) -> None:
        """Valida el tipo de imagen"""
        if image_type not in self.ALLOWED_TYPES:
            raise InvalidRequestDataException(
                f"image_type must be one of: {', '.join(self.ALLOWED_TYPES)}"
            )
    
    def _validate_unique_name(self, item_name: str) -> None:
        """Valida que el nombre sea único"""
        existing_image = self.image_repository.find_by_name(item_name)
        if existing_image:
            raise InvalidRequestDataException(
                f"Image with name '{item_name}' already exists",
                details={
                    "existing_image": {
                        "name": existing_image.name,
                        "image_path": existing_image.image_path,
                        "image_type": existing_image.image_type
                    }
                }
            ) 