from datetime import datetime
from typing import List, Optional

class RecipeIngredient:
    def __init__(self, name: str, quantity: float, type_unit: str):
        self.name = name
        self.quantity = quantity
        self.type_unit = type_unit

class RecipeStep:
    def __init__(self, step_order: int, description: str):
        self.step_order = step_order
        self.description = description

class Recipe:
    def __init__(
        self,
        uid: str,
        user_uid: str,
        title: str,
        duration: str,
        difficulty: str,
        ingredients: List[RecipeIngredient],
        steps: List[RecipeStep],
        footer: str,
        category: str,
        image_path: Optional[str],
        generated_by_ai: bool = True,
        saved_at: Optional[datetime] = None,
    ):
        self.uid = uid
        self.user_uid = user_uid
        self.title = title
        self.duration = duration
        self.difficulty = difficulty
        self.ingredients = ingredients
        self.steps = steps
        self.footer = footer
        self.saved_at = saved_at or datetime.now()
        self.generated_by_ai = generated_by_ai
        self.image_path = image_path
        self.category = category

    def __repr__(self):
        return f"Recipe(uid={self.uid}, title={self.title}, user_uid={self.user_uid})"
    def add_recipe_steps(self, steps: List[RecipeStep]):
        self.steps = steps
    def get_ingredients_names(self):
        return [ingredient.name for ingredient in self.ingredients]
    def add_recipe_ingredients(self, ingredients: List[RecipeIngredient]):
        self.ingredients = ingredients