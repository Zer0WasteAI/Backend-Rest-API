from datetime import datetime, timedelta
from typing import List, Optional
from src.domain.models.ingredient import Ingredient, IngredientStack
from src.domain.models.food_item import FoodItem

class Inventory:
    def __init__(self, user_uid: str):
        self.user_uid = user_uid
        self.ingredients: dict[str, Ingredient] = {}
        self.foods: List[FoodItem] = []

    def add_ingredient_stack(
        self,
        name: str,
        stack: IngredientStack,
        type_unit: str,
        storage_type: str,
        tips: str,
        image_path: str,
    ):
        if name not in self.ingredients:
            self.ingredients[name] = Ingredient(
                name=name,
                type_unit=type_unit,
                storage_type=storage_type,
                tips=tips,
                image_path=image_path,
            )
        self.ingredients[name].add_stack(stack)

    def add_food_item(self, food_item: FoodItem):
        self.foods.append(food_item)

    def get_ingredient(self, name: str) -> Optional[Ingredient]:
        return self.ingredients.get(name)

    def get_expiring_soon(self, within_days: int = 3) -> List[str]:
        today = datetime.now()
        expiring = []
        for ing in self.ingredients.values():
            exp = ing.get_nearest_expiration()
            if exp and today <= exp <= today + timedelta(days=within_days):
                expiring.append(ing.name)
        return expiring

    def __repr__(self):
        return f"Inventory(user_uid={self.user_uid}, ingredients={list(self.ingredients.keys())}, foods={len(self.foods)})"
