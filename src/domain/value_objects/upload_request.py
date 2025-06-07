from dataclasses import dataclass
from werkzeug.datastructures import FileStorage


@dataclass(frozen=True)
class UploadRequest:
    """Value Object que encapsula los datos de una petición de upload"""
    image_file: FileStorage
    item_name: str
    image_type: str
    user_uid: str
    
    def __post_init__(self):
        """Validaciones básicas en el constructor"""
        if not self.item_name or not self.item_name.strip():
            raise ValueError("item_name cannot be empty")
        
        if not self.image_file:
            raise ValueError("image_file cannot be empty")
            
        # Normalize item_name
        object.__setattr__(self, 'item_name', self.item_name.strip().lower()) 