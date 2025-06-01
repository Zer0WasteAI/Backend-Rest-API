from datetime import datetime
from typing import List, Optional

class FoodItem:
    def __init__(
        self,
        name: str,
        main_ingredients: List[str],
        category: str,
        calories: Optional[float],
        description: str,
        storage_type: str,
        expiration_time: int,
        time_unit: str,
        tips: str,
        serving_quantity: int,
        image_path: str,
        added_at: datetime,
        expiration_date: datetime
    ):
        self.name = name
        self.main_ingredients = main_ingredients
        self.category = category
        self.calories = calories
        self.description = description
        self.storage_type = storage_type
        self.expiration_time = expiration_time
        self.time_unit = time_unit
        self.tips = tips
        self.serving_quantity = serving_quantity
        self.image_path = image_path
        self.added_at = added_at
        self.expiration_date = expiration_date

    def __repr__(self):
        return f"FoodItem(name={self.name}, added_at={self.added_at.date()})"
