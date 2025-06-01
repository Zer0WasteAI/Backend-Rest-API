from typing import Union
from datetime import datetime, timedelta

from src.domain.services.inventory_calculator import InventoryCalculator
from src.domain.models.ingredient import Ingredient
from src.domain.models.food_item import FoodItem

class InventoryCalculatorImpl(InventoryCalculator):

    def calculate_expiration_date(self, added_at: datetime, time_value: int, time_unit: str) -> datetime:
        unit_map = {
            "Días": "days",
            "Semanas": "weeks",
            "Meses": "days"  # 30 días por mes
        }
        kwargs = {unit_map[time_unit]: time_value if time_unit != "Meses" else time_value * 30}
        return added_at + timedelta(**kwargs)
    def calculate_value(self, item: Union[Ingredient, FoodItem]) -> dict:
        # Placeholder para huellas y costos, ajustar según data
        return {
            "carbon_footprint": 1.5,  # kg CO2e
            "water_footprint": 50,    # litros
            "energy_footprint": 0.8,  # kWh
            "estimated_cost": 3.2      # soles
        }

    def get_next_expiration(self, item: Union[Ingredient, FoodItem]) -> datetime:
        if isinstance(item, Ingredient):
            expirations = [stack.expiration_date for stack in item.stacks]
            return min(expirations) if expirations else None
        elif isinstance(item, FoodItem):
            return item.expiration_date
        return None

    def total_quantity(self, item: Union[Ingredient, FoodItem]) -> float:
        if isinstance(item, Ingredient):
            return sum(stack.quantity for stack in item.stacks)
        elif isinstance(item, FoodItem):
            return item.serving_quantity
        return 0.0

    def expired_items(self, inventory_items: list, as_of: datetime) -> list:
        expired = []

        for item in inventory_items:
            if isinstance(item, Ingredient):
                for stack in item.stacks:
                    if stack.expiration_date < as_of:
                        expired.append(item)
                        break  # basta un stack vencido
            elif isinstance(item, FoodItem):
                if item.expiration_date < as_of:
                    expired.append(item)

        return expired