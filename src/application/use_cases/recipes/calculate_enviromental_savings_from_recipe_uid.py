from typing import List, Dict, Any
from src.domain.models.recipe import Recipe, RecipeIngredient
from src.domain.models.environmental_savings import EnvironmentalSavings
from src.shared.exceptions.custom import RecipeNotFoundException


class EstimateEnvironmentalSavingsFromRecipeUID:
    def __init__(self, recipe_repository, ai_adapter, savings_repository):
        self._repo = recipe_repository
        self._adapter = ai_adapter
        self._savings_repo = savings_repository

    def execute(self, recipe_uid: str) -> Dict[str, Any]:
        recipe: Recipe = self._repo.find_by_uid(recipe_uid)
        if recipe is None:
            raise RecipeNotFoundException(f"Recipe '{recipe_uid}' not found")

        existing = self._savings_repo.find_by_user_and_recipe(
            user_uid=recipe.user_uid,
            recipe_uid=recipe.uid
        )
        if existing:
            print(f"📦 Ya existe cálculo previo para receta {recipe.uid}, usuario {recipe.user_uid}")
            return {
                "recipe_uid": recipe.uid,
                "recipe_title": existing.recipe_title,
                "carbon_footprint": existing.carbon_footprint,
                "water_footprint": existing.water_footprint,
                "energy_footprint": existing.energy_footprint,
                "economic_cost": existing.economic_cost,
                "unit_carbon": existing.unit_carbon,
                "unit_water": existing.unit_water,
                "unit_energy": existing.unit_energy,
                "unit_cost": existing.unit_cost,
                "is_cooked": existing.is_cooked
            }

        ingredients_payload: List[Dict[str, Any]] = [
            {"name": ing.name, "quantity": ing.quantity, "type_unit": ing.type_unit}
            for ing in recipe.ingredients
        ]

        savings = self._adapter.estimate_extended_environmental_savings_from_ingredients(
            ingredients_payload
        )

        new_record = EnvironmentalSavings(
            user_uid=recipe.user_uid,
            recipe_uid=recipe.uid,
            recipe_title=recipe.title,
            carbon_footprint=savings["carbon_footprint"],
            water_footprint=savings["water_footprint"],
            energy_footprint=savings["energy_footprint"],
            economic_cost=savings["economic_cost"],
            unit_carbon=savings["unit_carbon"],
            unit_water=savings["unit_water"],
            unit_energy=savings["unit_energy"],
            unit_cost=savings["unit_cost"],
            is_cooked=False
        )
        self._savings_repo.save(new_record)

        return {
            "recipe_uid": recipe.uid,
            "recipe_title": recipe.title,
            "carbon_footprint": savings["carbon_footprint"],
            "water_footprint": savings["water_footprint"],
            "energy_footprint": savings["energy_footprint"],
            "economic_cost": savings["economic_cost"],
            "unit_carbon": savings["unit_carbon"],
            "unit_water": savings["unit_water"],
            "unit_energy": savings["unit_energy"],
            "unit_cost": savings["unit_cost"],
            "is_cooked": False
        }