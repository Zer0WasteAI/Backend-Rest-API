from abc import ABC, abstractmethod
from src.domain.models.inventory import Inventory

class InventoryRepository(ABC):
    @abstractmethod
    def get_by_user_uid(self, user_uid: str) -> Inventory:
        pass

    @abstractmethod
    def save(self, inventory: Inventory) -> None:
        pass

    @abstractmethod
    def update(self, inventory: Inventory) -> None:
        pass