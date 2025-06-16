from typing import List, Dict
from src.domain.models.environmental_savings import EnvironmentalSavings

class GetAllEnvironmentalCalculationsByUser:
    def __init__(self, savings_repository):
        self._savings_repo = savings_repository

    def execute(self, user_uid: str) -> List[Dict]:
        calculations: List[EnvironmentalSavings] = self._savings_repo.find_by_user(user_uid)
        return [
            {
                "recipe_uid": calc.recipe_uid,
                "recipe_title": calc.recipe_title,
                "carbon_footprint": calc.carbon_footprint,
                "water_footprint": calc.water_footprint,
                "energy_footprint": calc.energy_footprint,
                "economic_cost": calc.economic_cost,
                "unit_carbon": calc.unit_carbon,
                "unit_water": calc.unit_water,
                "unit_energy": calc.unit_energy,
                "unit_cost": calc.unit_cost,
                "is_cooked": calc.is_cooked,
                "saved_at": calc.saved_at.isoformat()
            }
            for calc in calculations
        ]
