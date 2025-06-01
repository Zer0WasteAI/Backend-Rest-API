from datetime import datetime
from typing import List, Optional

class IngredientStack:
    def __init__(self, quantity: float, expiration_date: datetime, added_at: datetime):
        self.quantity = quantity
        self.expiration_date = expiration_date
        self.added_at = added_at

    def __repr__(self):
        return f"IngredientStack(quantity={self.quantity}, added_at={self.added_at.date()}, expiration_date={self.expiration_date.date()})"

class Ingredient:
    def __init__(
        self,
        name: str,
        type_unit: str,
        storage_type: str,
        tips: str,
        image_path: str,
    ):
        self.name = name
        self.type_unit = type_unit
        self.storage_type = storage_type
        self.tips = tips
        self.image_path = image_path
        self.stacks: List[IngredientStack] = []

    def add_stack(self, stack: IngredientStack):
        self.stacks.append(stack)

    def get_total_quantity(self) -> float:
        return sum(stack.quantity for stack in self.stacks)

    def get_nearest_expiration(self) -> Optional[datetime]:
        if not self.stacks:
            return None
        return min(stack.expiration_date for stack in self.stacks)

    def __repr__(self):
        return f"Ingredient(name={self.name}, stacks={self.stacks})"