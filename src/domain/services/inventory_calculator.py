from abc import ABC
from typing import Union
from datetime import datetime
from src.domain.models.ingredient import Ingredient
from src.domain.models.food_item import FoodItem

class InventoryCalculator(ABC):
    def calculate_expiration_date(self, added_at: datetime, time_value: int, time_unit: str) -> datetime:
        pass
    def calculate_value(self, item: Union[Ingredient, FoodItem]) -> dict:
        pass

    def get_next_expiration(self, ingredient: Ingredient) -> datetime:
        pass

    def total_quantity(self, ingredient: Ingredient) -> float:
        pass

    def expired_items(self, inventory_items: list, as_of: datetime) -> list:
        pass