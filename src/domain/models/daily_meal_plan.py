from datetime import date
from typing import Optional
from .recipe import Recipe

class DailyMealPlan:
    def __init__(
        self,
        uid: str,
        user_uid: str,
        date_: date,
        breakfast: Optional[Recipe] = None,
        lunch: Optional[Recipe] = None,
        dinner: Optional[Recipe] = None,
        dessert: Optional[Recipe] = None
    ):
        self.uid = uid
        self.user_uid = user_uid
        self.date = date_
        self.breakfast = breakfast
        self.lunch = lunch
        self.dinner = dinner
        self.dessert = dessert

    def __repr__(self):
        return f"DailyMealPlan(date={self.date}, user={self.user_uid})"

    def is_empty(self) -> bool:
        return not any([self.breakfast, self.lunch, self.dinner, self.dessert])

    def assign_recipe(self, meal_type: str, recipe: Recipe):
        if meal_type in ["breakfast", "desayuno"]:
            self.breakfast = recipe
        elif meal_type in ["lunch", "almuerzo"]:
            self.lunch = recipe
        elif meal_type in ["dinner", "cena"]:
            self.dinner = recipe
        elif meal_type in ["dessert", "postre"]:
            self.dessert = recipe
        else:
            raise ValueError(f"Tipo de comida inválido: {meal_type}")
