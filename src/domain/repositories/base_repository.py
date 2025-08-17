from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class BaseRepository(ABC):
    """
    Abstract base repository interface that defines common patterns
    for all repositories in the system.
    """
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Any:
        """Create a new entity"""
        pass
    
    @abstractmethod
    def find_by_uid(self, uid: str) -> Optional[Any]:
        """Find entity by unique identifier"""
        pass
    
    @abstractmethod
    def find_by_user(self, user_uid: str, **kwargs) -> List[Any]:
        """Find entities belonging to a specific user"""
        pass
    
    @abstractmethod
    def update(self, uid: str, data: Dict[str, Any]) -> None:
        """Update entity by unique identifier"""
        pass
    
    @abstractmethod
    def delete(self, uid: str) -> None:
        """Delete entity by unique identifier"""
        pass
    
    def exists(self, uid: str) -> bool:
        """Check if entity exists by unique identifier"""
        return self.find_by_uid(uid) is not None
    
    def _get_current_timestamp(self) -> datetime:
        """Get current UTC timestamp for operations"""
        from datetime import timezone
        return datetime.now(timezone.utc)
    
    def _prepare_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for creation with timestamps"""
        prepared_data = data.copy()
        timestamp = self._get_current_timestamp()
        prepared_data.setdefault('created_at', timestamp)
        prepared_data.setdefault('updated_at', timestamp)
        return prepared_data
    
    def _prepare_update_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for update with timestamp"""
        prepared_data = data.copy()
        prepared_data['updated_at'] = self._get_current_timestamp()
        return prepared_data


class BaseUserScopedRepository(BaseRepository):
    """
    Extended base repository for entities that are scoped to users.
    Provides additional methods for user-specific operations.
    """
    
    @abstractmethod
    def find_by_user_and_name(self, user_uid: str, name: str) -> Optional[Any]:
        """Find entity by user and name"""
        pass
    
    def delete_by_user_and_name(self, user_uid: str, name: str) -> None:
        """Delete entity by user and name"""
        entity = self.find_by_user_and_name(user_uid, name)
        if entity:
            self.delete(entity.uid)
    
    def count_by_user(self, user_uid: str) -> int:
        """Count entities belonging to a user"""
        return len(self.find_by_user(user_uid))


class BaseValidatedRepository(BaseRepository):
    """
    Extended base repository for entities that require validation.
    """
    
    @abstractmethod
    def find_by_user_and_status(self, user_uid: str, validated: bool) -> List[Any]:
        """Find entities by user and validation status"""
        pass
    
    @abstractmethod
    def update_validation_status(self, uid: str, validated: bool) -> None:
        """Update validation status of entity"""
        pass
    
    def get_validated_by_user(self, user_uid: str) -> List[Any]:
        """Get all validated entities for user"""
        return self.find_by_user_and_status(user_uid, validated=True)
    
    def get_unvalidated_by_user(self, user_uid: str) -> List[Any]:
        """Get all unvalidated entities for user"""
        return self.find_by_user_and_status(user_uid, validated=False)


class BaseExpirationRepository(BaseRepository):
    """
    Extended base repository for entities with expiration functionality.
    """
    
    @abstractmethod
    def find_expiring_soon(self, user_uid: str, days_ahead: int = 3) -> List[Any]:
        """Find entities expiring within specified days"""
        pass
    
    @abstractmethod
    def find_expired(self, user_uid: str) -> List[Any]:
        """Find expired entities"""
        pass
    
    @abstractmethod
    def update_expired_status(self) -> int:
        """Update expired status for all entities, returns count updated"""
        pass