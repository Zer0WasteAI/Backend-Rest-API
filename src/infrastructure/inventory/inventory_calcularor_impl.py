from typing import Union
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from src.domain.services.inventory_calculator import InventoryCalculator
from src.domain.models.ingredient import Ingredient
from src.domain.models.food_item import FoodItem

class InventoryCalculatorImpl(InventoryCalculator):

    def calculate_expiration_date(self, added_at: datetime, time_value: int, time_unit: str) -> datetime:
        """
        Calcula la fecha de caducidad basada en el tiempo y unidad especificados.
        Maneja correctamente días, semanas, meses y años.
        """
        # Normalizar la unidad de tiempo para manejar singular/plural
        time_unit_normalized = time_unit.lower().strip()
        
        print(f"🧮 Calculating expiration: {time_value} {time_unit} from {added_at}")
        
        if time_unit_normalized in ["día", "días", "dia", "dias"]:
            result = added_at + timedelta(days=time_value)
        elif time_unit_normalized in ["semana", "semanas"]:
            result = added_at + timedelta(weeks=time_value)
        elif time_unit_normalized in ["mes", "meses"]:
            # Usar relativedelta para manejar meses correctamente
            result = added_at + relativedelta(months=time_value)
        elif time_unit_normalized in ["año", "años", "ano", "anos"]:
            # Usar relativedelta para manejar años correctamente
            result = added_at + relativedelta(years=time_value)
        else:
            # Fallback: si no reconoce la unidad, asumir días
            print(f"⚠️ Warning: Unidad de tiempo no reconocida '{time_unit}', usando días como fallback")
            result = added_at + timedelta(days=time_value)
        
        print(f"📅 Result: {result} (added {time_value} {time_unit})")
        return result

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