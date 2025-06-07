from datetime import datetime
from typing import List, Optional

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
        generated_by_ai: bool = True,
        is_custom: bool = False,
        saved_at: Optional[datetime] = None
    ):
        self.uid = uid
        self.user_uid = user_uid
        self.title = title
        self.duration = duration
        self.difficulty = difficulty
        self.ingredients = ingredients
        self.steps = steps
        self.footer = footer
        self.is_custom = is_custom
        self.saved_at = saved_at or datetime.now()
        self.generated_by_ai = generated_by_ai

    def add_recipe_ingredients(self, ingredients: List[RecipeIngredient]):
        self.ingredients = ingredients

    def __repr__(self):
        return f"Recipe(uid={self.uid}, title={self.title}, user_uid={self.user_uid})"
    def add_recipe_steps(self, steps: List[RecipeStep]):
        self.steps = steps

    def get_ingredients_names(self):
        return [ingredient.name for ingredient in self.ingredients]