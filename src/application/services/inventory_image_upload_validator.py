import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from src.shared.exceptions.custom import InvalidRequestDataException


class InventoryImageUploadValidator:
    """Servicio especializado en validar uploads de imágenes para inventario"""
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_TYPES = ['recognition', 'ingredient', 'food']
    MIN_ITEM_NAME_LENGTH = 2
    MAX_ITEM_NAME_LENGTH = 100
    
    def validate_inventory_upload(self, file: FileStorage, upload_type: str, item_name: str = None) -> None:
        """Valida completamente una petición de upload para inventario"""
        self._validate_file(file)
        self._validate_upload_type(upload_type)
        
        # item_name es opcional para algunos casos (como reconocimiento)
        if item_name is not None:
            self._validate_item_name(item_name)
    
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
    
    def _validate_upload_type(self, upload_type: str) -> None:
        """Valida el tipo de upload específico para inventario"""
        if upload_type not in self.ALLOWED_UPLOAD_TYPES:
            raise InvalidRequestDataException(
                f"upload_type must be one of: {', '.join(self.ALLOWED_UPLOAD_TYPES)}"
            )
    
    def _validate_item_name(self, item_name: str) -> None:
        """Valida el nombre del item (cuando sea requerido)"""
        if not item_name or not item_name.strip():
            raise InvalidRequestDataException("item_name cannot be empty")
        
        item_name = item_name.strip()
        
        if len(item_name) < self.MIN_ITEM_NAME_LENGTH:
            raise InvalidRequestDataException(
                f"item_name must be at least {self.MIN_ITEM_NAME_LENGTH} characters"
            )
        
        if len(item_name) > self.MAX_ITEM_NAME_LENGTH:
            raise InvalidRequestDataException(
                f"item_name must be less than {self.MAX_ITEM_NAME_LENGTH} characters"
            ) 