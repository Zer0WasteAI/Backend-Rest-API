from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from datetime import datetime, timezone


class BaseInventoryUseCase(ABC):
    """
    Abstract base class for inventory operations to reduce code duplication.
    Provides common functionality for inventory-related use cases.
    """
    
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Abstract method that must be implemented by concrete use cases"""
        pass
    
    def _validate_user_uid(self, user_uid: str) -> None:
        """Validate that user_uid is provided and not empty"""
        if not user_uid or not isinstance(user_uid, str):
            raise ValueError("User UID is required and must be a valid string")
    
    def _validate_quantity(self, quantity: Union[int, float]) -> None:
        """Validate that quantity is positive"""
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            raise ValueError("Quantity must be a positive number")
    
    def _validate_item_name(self, item_name: str) -> None:
        """Validate that item name is provided and not empty"""
        if not item_name or not isinstance(item_name, str):
            raise ValueError("Item name is required and must be a valid string")
    
    def _validate_date_string(self, date_string: str) -> datetime:
        """Validate and parse date string to datetime object"""
        if not date_string:
            raise ValueError("Date string is required")
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid date format: {date_string}")
    
    def _get_current_timestamp(self) -> datetime:
        """Get current UTC timestamp"""
        return datetime.now(timezone.utc)
    
    def _check_item_exists(self, user_uid: str, item_identifier: str, item_type: str) -> bool:
        """Check if an item exists in user's inventory"""
        try:
            if item_type == 'ingredient':
                result = self.inventory_repository.get_ingredient_stack(user_uid, item_identifier, '')
            elif item_type == 'food':
                result = self.inventory_repository.get_food_item(user_uid, item_identifier, '')
            else:
                raise ValueError(f"Unsupported item type: {item_type}")
            return result is not None
        except:
            return False


class BaseInventoryUpdateUseCase(BaseInventoryUseCase):
    """
    Base class for inventory update operations (quantity updates, status changes, etc.)
    """
    
    def _prepare_update_data(self, **kwargs) -> Dict[str, Any]:
        """Prepare common update data with timestamp"""
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        update_data['updated_at'] = self._get_current_timestamp()
        return update_data
    
    def _log_update_operation(self, operation: str, user_uid: str, item_name: str, **details) -> None:
        """Log update operations for audit trail"""
        print(f"🔄 [INVENTORY UPDATE] {operation}")
        print(f"   └─ User: {user_uid}")
        print(f"   └─ Item: {item_name}")
        for key, value in details.items():
            print(f"   └─ {key}: {value}")


class BaseInventoryDeleteUseCase(BaseInventoryUseCase):
    """
    Base class for inventory deletion operations
    """
    
    def _log_delete_operation(self, operation: str, user_uid: str, item_name: str, **details) -> None:
        """Log delete operations for audit trail"""
        print(f"🗑️ [INVENTORY DELETE] {operation}")
        print(f"   └─ User: {user_uid}")
        print(f"   └─ Item: {item_name}")
        for key, value in details.items():
            print(f"   └─ {key}: {value}")
    
    def _validate_delete_permission(self, user_uid: str, item_name: str, item_type: str) -> None:
        """Validate that user has permission to delete the item"""
        if not self._check_item_exists(user_uid, item_name, item_type):
            raise ValueError(f"{item_type.capitalize()} '{item_name}' not found in user's inventory")


class BaseInventoryQueryUseCase(BaseInventoryUseCase):
    """
    Base class for inventory query operations (get details, list items, etc.)
    """
    
    def _format_response(self, data: Any, message: str = "Operation completed successfully") -> Dict[str, Any]:
        """Format standard response structure"""
        return {
            "message": message,
            "data": data,
            "timestamp": self._get_current_timestamp().isoformat()
        }
    
    def _log_query_operation(self, operation: str, user_uid: str, **details) -> None:
        """Log query operations"""
        print(f"🔍 [INVENTORY QUERY] {operation}")
        print(f"   └─ User: {user_uid}")
        for key, value in details.items():
            print(f"   └─ {key}: {value}")