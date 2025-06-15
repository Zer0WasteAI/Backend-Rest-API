from typing import Optional
from abc import ABC, abstractmethod
from src.domain.models.inventory import Inventory

class InventoryRepository(ABC):
    @abstractmethod
    def get_by_user_uid(self, user_uid: str) -> Optional[Inventory]:
        pass

    @abstractmethod
    def save(self, inventory: Inventory) -> None:
        pass

    @abstractmethod
    def add_ingredient_stack(self, user_uid: str, stack, ingredient) -> None:
        pass

    def add_food_item(self, user_uid: str, food_item) -> None:
        pass

    def delete_ingredient_stack(self, user_uid: str, ingredient_name: str, added_at: str) -> None:
        pass

    def delete_food_item(self, user_uid: str, food_name: str, added_at: str) -> None:
        pass

    def update_food_item(self, user_uid: str, food_item) -> None:
        pass

    def update_ingredient_stack(self, user_uid: str, ingredient_name: str, added_at: str, new_stack, new_meta) -> None:
        pass