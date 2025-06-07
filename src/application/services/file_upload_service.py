import uuid
import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage


class FileUploadService:
    """Servicio especializado en upload de archivos a almacenamiento"""
    
    def __init__(self, storage_adapter):
        self.storage_adapter = storage_adapter
    
    def upload_image(self, file: FileStorage, image_type: str, user_uid: str = None) -> tuple[str, str]:
        """
        Sube una imagen al almacenamiento
        
        Args:
            file: Archivo a subir
            image_type: Tipo de imagen (food, ingredient, etc.)
            user_uid: UID del usuario (opcional para retrocompatibilidad)
        
        Returns:
            tuple: (storage_path, public_url)
        """
        storage_path = self._generate_storage_path(file, image_type, user_uid)
        public_url = self._upload_to_storage(file, storage_path)
        return storage_path, public_url
    
    def _generate_storage_path(self, file: FileStorage, image_type: str, user_uid: str = None) -> str:
        """Genera un path único para el almacenamiento organizando por UID de usuario"""
        file_ext = os.path.splitext(secure_filename(file.filename))[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        if user_uid:
            # Nueva estructura: uploads/{user_uid}/{image_type}/{filename}
            return f"uploads/{user_uid}/{image_type}/{unique_filename}"
        else:
            # Estructura legacy para retrocompatibilidad
            return f"uploads/{image_type}/{unique_filename}"
    
    def _upload_to_storage(self, file: FileStorage, storage_path: str) -> str:
        """Sube el archivo al almacenamiento y retorna la URL pública"""
        blob = self.storage_adapter.bucket.blob(storage_path)
        
        # Upload file content
        file.seek(0)
        blob.upload_from_file(file, content_type=file.content_type)
        
        # Make blob publicly accessible
        blob.make_public()
        return blob.public_url 