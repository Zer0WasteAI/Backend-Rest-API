import uuid
from typing import Dict, Any, Optional
from werkzeug.datastructures import FileStorage

from src.domain.models.image_reference import ImageReference
from src.domain.value_objects.upload_request import UploadRequest


class UnifiedUploadUseCase:
    """
    Unified Use Case for handling all image uploads in the system.
    Consolidates functionality from UploadImageUseCase and UploadInventoryImageUseCase.
    """
    
    def __init__(self, 
                 image_validator, 
                 inventory_validator, 
                 file_upload_service, 
                 inventory_upload_service, 
                 image_repository):
        self.image_validator = image_validator
        self.inventory_validator = inventory_validator
        self.file_upload_service = file_upload_service
        self.inventory_upload_service = inventory_upload_service
        self.image_repository = image_repository
    
    def execute(self, 
                file: FileStorage, 
                upload_context: str, 
                user_uid: str,
                upload_type: Optional[str] = None,
                item_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Unified upload execution method.
        
        Args:
            file: File to upload
            upload_context: Context of upload ('inventory', 'general', 'recipe', 'recognition')
            user_uid: User identifier
            upload_type: Type of upload (required for inventory context)
            item_name: Name of the item (optional)
            
        Returns:
            Dict with upload information
        """
        print(f"📤 [UNIFIED UPLOAD] Starting upload for user: {user_uid}")
        print(f"   └─ Context: {upload_context}")
        print(f"   └─ File: {file.filename}")
        print(f"   └─ Upload type: {upload_type or 'N/A'}")
        print(f"   └─ Item name: {item_name or 'N/A'}")
        
        if upload_context == 'inventory':
            return self._handle_inventory_upload(file, upload_type, user_uid, item_name)
        elif upload_context == 'general':
            return self._handle_general_upload(file, user_uid, item_name, upload_type)
        else:
            raise ValueError(f"Unsupported upload context: {upload_context}")
    
    def _handle_inventory_upload(self, 
                               file: FileStorage, 
                               upload_type: str, 
                               user_uid: str, 
                               item_name: Optional[str]) -> Dict[str, Any]:
        """Handle inventory-specific uploads"""
        # Validate using inventory validator
        self.inventory_validator.validate_inventory_upload(file, upload_type, item_name)
        print(f"   └─ ✅ Inventory validation passed")
        
        # Upload using inventory service
        storage_path, public_url = self.inventory_upload_service.upload_inventory_image(
            file=file,
            upload_type=upload_type,
            user_uid=user_uid
        )
        print(f"   └─ ✅ File uploaded to: {storage_path}")
        
        return {
            "message": f"Inventory image uploaded successfully",
            "context": "inventory",
            "upload_info": {
                "storage_path": storage_path,
                "public_url": public_url,
                "upload_type": upload_type,
                "folder": self.inventory_upload_service.INVENTORY_UPLOAD_TYPES[upload_type],
                "user_uid": user_uid,
                "item_name": item_name,
                "filename": file.filename
            }
        }
    
    def _handle_general_upload(self, 
                             file: FileStorage, 
                             user_uid: str, 
                             item_name: Optional[str],
                             image_type: Optional[str]) -> Dict[str, Any]:
        """Handle general image uploads with database reference creation"""
        # Create upload request object
        request = UploadRequest(
            image_file=file,
            image_type=image_type or 'general',
            user_uid=user_uid,
            item_name=item_name or file.filename
        )
        
        # Validate using general validator
        self.image_validator.validate_upload_request(request)
        print(f"   └─ ✅ General validation passed")
        
        # Upload using general service
        storage_path, public_url = self.file_upload_service.upload_image(
            request.image_file, 
            request.image_type,
            request.user_uid
        )
        print(f"   └─ ✅ File uploaded to: {storage_path}")
        
        # Create database reference
        image_ref = self._create_image_reference(request, public_url)
        saved_uid = self.image_repository.save(image_ref)
        
        return {
            "message": "Image uploaded successfully",
            "context": "general",
            "image": {
                "uid": saved_uid,
                "name": image_ref.name,
                "image_path": image_ref.image_path,
                "image_type": image_ref.image_type,
                "storage_path": storage_path
            }
        }
    
    def _create_image_reference(self, request: UploadRequest, image_path: str) -> ImageReference:
        """Create domain entity ImageReference"""
        return ImageReference(
            uid=str(uuid.uuid4()),
            name=request.item_name,
            image_path=image_path,
            image_type=request.image_type
        )