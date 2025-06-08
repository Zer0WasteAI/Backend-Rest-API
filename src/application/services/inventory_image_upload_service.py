import uuid
import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage


class InventoryImageUploadService:
    """Servicio especializado en upload de imágenes para el inventario"""
    
    # Mapeo de tipos de upload del inventario a carpetas
    INVENTORY_UPLOAD_TYPES = {
        'recognition': 'recognitions',      # Imágenes para reconocimiento
        'ingredient': 'items',              # Imágenes de ingredientes manuales
        'food': 'items'                     # Imágenes de comidas manuales
    }
    
    def __init__(self, storage_adapter):
        self.storage_adapter = storage_adapter
    
    def upload_inventory_image(self, file: FileStorage, upload_type: str, user_uid: str) -> tuple[str, str]:
        """
        Sube una imagen específica del inventario al almacenamiento organizado por usuario.
        
        Args:
            file: Archivo a subir
            upload_type: Tipo de upload ('recognition', 'ingredient', 'food')
            user_uid: UID del usuario
        
        Returns:
            tuple: (storage_path, public_url)
        """
        if upload_type not in self.INVENTORY_UPLOAD_TYPES:
            raise ValueError(f"Invalid upload_type. Must be one of: {list(self.INVENTORY_UPLOAD_TYPES.keys())}")
        
        storage_path = self._generate_inventory_storage_path(file, upload_type, user_uid)
        public_url = self._upload_to_storage(file, storage_path)
        return storage_path, public_url
    
    def _generate_inventory_storage_path(self, file: FileStorage, upload_type: str, user_uid: str) -> str:
        """
        Genera un path para almacenamiento de inventario con la estructura específica:
        uploads/{user_uid}/recognitions/{filename}   - Para imágenes de reconocimiento
        uploads/{user_uid}/items/{filename}          - Para ingredientes y comidas manuales
        """
        file_ext = os.path.splitext(secure_filename(file.filename))[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        # Obtener la carpeta específica según el tipo
        folder = self.INVENTORY_UPLOAD_TYPES[upload_type]
        
        # Estructura: uploads/{user_uid}/{folder_especifica}/{filename}
        return f"uploads/{user_uid}/{folder}/{unique_filename}"
    
    def _upload_to_storage(self, file: FileStorage, storage_path: str) -> str:
        """Sube el archivo al almacenamiento y retorna la URL pública"""
        blob = self.storage_adapter.bucket.blob(storage_path)
        
        # Upload file content
        file.seek(0)
        blob.upload_from_file(file, content_type=file.content_type)
        
        # Make blob publicly accessible
        blob.make_public()
        return blob.public_url
    
    def get_user_inventory_images(self, user_uid: str, upload_type: str = None) -> list:
        """
        Lista las imágenes del inventario de un usuario específico.
        
        Args:
            user_uid: UID del usuario
            upload_type: Tipo específico a filtrar (opcional)
            
        Returns:
            list: Lista de imágenes con sus metadatos
        """
        images = []
        
        if upload_type:
            # Buscar solo en un tipo específico
            if upload_type not in self.INVENTORY_UPLOAD_TYPES:
                raise ValueError(f"Invalid upload_type. Must be one of: {list(self.INVENTORY_UPLOAD_TYPES.keys())}")
            
            folder = self.INVENTORY_UPLOAD_TYPES[upload_type]
            prefix = f"uploads/{user_uid}/{folder}/"
            images.extend(self._list_images_in_folder(prefix, upload_type))
        else:
            # Buscar en todas las carpetas de inventario
            for upload_type, folder in self.INVENTORY_UPLOAD_TYPES.items():
                prefix = f"uploads/{user_uid}/{folder}/"
                images.extend(self._list_images_in_folder(prefix, upload_type))
        
        return images
    
    def _list_images_in_folder(self, prefix: str, upload_type: str) -> list:
        """Lista imágenes en una carpeta específica"""
        images = []
        
        try:
            blobs = self.storage_adapter.bucket.list_blobs(prefix=prefix)
            
            for blob in blobs:
                if blob.name.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                    # Extraer el nombre del archivo
                    filename = blob.name.split('/')[-1]
                    
                    images.append({
                        'filename': filename,
                        'storage_path': blob.name,
                        'public_url': blob.public_url,
                        'upload_type': upload_type,
                        'folder': self.INVENTORY_UPLOAD_TYPES[upload_type],
                        'size': blob.size if hasattr(blob, 'size') else None,
                        'created': blob.time_created.isoformat() if hasattr(blob, 'time_created') and blob.time_created else None
                    })
            
        except Exception as e:
            print(f"🚨 Error listing images in {prefix}: {str(e)}")
        
        return images
    
    def delete_inventory_image(self, user_uid: str, upload_type: str, filename: str) -> bool:
        """
        Elimina una imagen específica del inventario del usuario.
        
        Args:
            user_uid: UID del usuario
            upload_type: Tipo de upload ('recognition', 'ingredient', 'food')
            filename: Nombre del archivo a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente, False si no existe
        """
        if upload_type not in self.INVENTORY_UPLOAD_TYPES:
            raise ValueError(f"Invalid upload_type. Must be one of: {list(self.INVENTORY_UPLOAD_TYPES.keys())}")
        
        folder = self.INVENTORY_UPLOAD_TYPES[upload_type]
        storage_path = f"uploads/{user_uid}/{folder}/{filename}"
        
        try:
            blob = self.storage_adapter.bucket.blob(storage_path)
            if blob.exists():
                blob.delete()
                print(f"✅ Deleted inventory image: {storage_path}")
                return True
            else:
                print(f"❌ Image not found: {storage_path}")
                return False
                
        except Exception as e:
            print(f"🚨 Error deleting image {storage_path}: {str(e)}")
            return False 