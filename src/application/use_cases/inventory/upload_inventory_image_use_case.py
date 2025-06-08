from typing import Dict, Any
from werkzeug.datastructures import FileStorage


class UploadInventoryImageUseCase:
    """Use Case especializado para upload de imágenes del inventario"""
    
    def __init__(self, validator, upload_service):
        self.validator = validator
        self.upload_service = upload_service
    
    def execute(self, file: FileStorage, upload_type: str, user_uid: str, item_name: str = None) -> Dict[str, Any]:
        """
        Ejecuta el proceso de upload de imagen para inventario
        
        Args:
            file: Archivo de imagen a subir
            upload_type: Tipo de upload ('recognition', 'ingredient', 'food')
            user_uid: UID del usuario autenticado
            item_name: Nombre del item (opcional, para algunos tipos)
            
        Returns:
            Dict con información de la imagen subida
        """
        print(f"📤 [UPLOAD INVENTORY IMAGE] Starting upload for user: {user_uid}")
        print(f"   └─ Upload type: {upload_type}")
        print(f"   └─ File: {file.filename}")
        print(f"   └─ Item name: {item_name or 'N/A'}")
        
        # 1. Validar petición
        self.validator.validate_inventory_upload(file, upload_type, item_name)
        print(f"   └─ ✅ Validation passed")
        
        # 2. Subir archivo con la estructura específica de inventario
        storage_path, public_url = self.upload_service.upload_inventory_image(
            file=file,
            upload_type=upload_type,
            user_uid=user_uid
        )
        print(f"   └─ ✅ File uploaded to: {storage_path}")
        
        # 3. Preparar respuesta con metadatos
        result = {
            "message": f"Inventory image uploaded successfully",
            "upload_info": {
                "storage_path": storage_path,
                "public_url": public_url,
                "upload_type": upload_type,
                "folder": self.upload_service.INVENTORY_UPLOAD_TYPES[upload_type],
                "user_uid": user_uid,
                "item_name": item_name,
                "filename": file.filename
            }
        }
        
        print(f"✅ [UPLOAD INVENTORY IMAGE] Upload completed successfully")
        print(f"   └─ Public URL: {public_url}")
        
        return result 