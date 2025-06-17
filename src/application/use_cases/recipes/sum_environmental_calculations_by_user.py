from typing import Dict
from src.domain.repositories.environmental_savings_repository import EnvironmentalSavingsRepository
from src.domain.models.environmental_savings import EnvironmentalSavings


class SumEnvironmentalCalculationsByUser:
    def __init__(self, savings_repository: EnvironmentalSavingsRepository):
        self._savings_repo = savings_repository

    def execute(self, user_uid: str) -> Dict:
        calculations = self._savings_repo.find_by_user(user_uid)

        if not calculations:
            return {
                "total_carbon_footprint": 0.0,
                "total_water_footprint": 0.0,
                "total_energy_footprint": 0.0,
                "total_economic_cost": 0.0,
                "unit_carbon": "kg CO2e",
                "unit_water": "litros",
                "unit_energy": "kWh",
                "unit_cost": "S/"
            }

        total_carbon = sum(calc.carbon_footprint for calc in calculations)
        total_water = sum(calc.water_footprint for calc in calculations)
        total_energy = sum(calc.energy_footprint for calc in calculations)
        total_cost = sum(calc.economic_cost for calc in calculations)

        # Suponemos que las unidades son iguales para todas las entradas
        sample = calculations[0]

        return {
            "total_carbon_footprint": round(total_carbon, 2),
            "total_water_footprint": round(total_water, 1),
            "total_energy_footprint": round(total_energy, 2),
            "total_economic_cost": round(total_cost, 2),
            "unit_carbon": sample.unit_carbon,
            "unit_water": sample.unit_water,
            "unit_energy": sample.unit_energy,
            "unit_cost": sample.unit_cost
        }