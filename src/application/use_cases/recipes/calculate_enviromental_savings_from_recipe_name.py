from typing import List, Dict, Any
from src.domain.models.recipe import Recipe, RecipeIngredient
from src.domain.models.environmental_savings import EnvironmentalSavings
from src.shared.exceptions.custom import RecipeNotFoundException


class EstimateEnvironmentalSavingsFromRecipeName:
    def __init__(self, recipe_repository, ai_adapter, savings_repository, recipe_generated_repository=None):
        self._repo = recipe_repository
        self._adapter = ai_adapter
        self._savings_repo = savings_repository
        self._generated_repo = recipe_generated_repository

    def execute(self, user_uid, recipe_title: str) -> Dict[str, Any]:
        # Primero buscar en recetas guardadas manualmente
        recipe: Recipe = self._repo.find_by_user_and_title(user_uid, recipe_title)
        recipe_source = "saved"
        recipe_uid = None
        ingredients_data = []
        
        if recipe is not None:
            # Encontrada en recetas guardadas
            recipe_uid = recipe.uid
            ingredients_data = [
                {"name": ing.name, "quantity": ing.quantity, "type_unit": ing.type_unit}
                for ing in recipe.ingredients
            ]
        elif self._generated_repo is not None:
            # Buscar en recetas generadas automáticamente
            generated_recipe = self._generated_repo.find_by_user_and_title(user_uid, recipe_title)
            if generated_recipe is not None:
                recipe_source = "generated"
                recipe_uid = generated_recipe.uid
                recipe_data = generated_recipe.recipe_data
                
                # Extraer ingredientes del JSON almacenado
                if 'ingredients' in recipe_data:
                    ingredients_data = []
                    for ing in recipe_data['ingredients']:
                        ingredients_data.append({
                            "name": ing.get('name', ''),
                            "quantity": ing.get('quantity', 0),
                            "type_unit": ing.get('unit', ing.get('type_unit', ''))
                        })
                else:
                    raise RecipeNotFoundException(f"Recipe '{recipe_title}' found but has no ingredients data")
                
                # Crear objeto Recipe temporal para compatibilidad
                recipe = type('Recipe', (), {
                    'uid': recipe_uid,
                    'title': generated_recipe.title,
                    'ingredients': []
                })()
        
        if recipe is None or not ingredients_data:
            raise RecipeNotFoundException(f"Recipe '{recipe_title}' not found in saved or generated recipes")

        # Verificar si ya existe un cálculo previo
        existing = self._savings_repo.find_by_user_and_recipe(
            user_uid=user_uid,
            recipe_uid=recipe_uid
        )
        if existing:
            print(f"📦 Ya existe cálculo previo para receta {recipe_title}, usuario {user_uid}")
            return {
                "recipe_uid": recipe_uid,
                "recipe_title": existing.recipe_title,
                "recipe_source": recipe_source,
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

        # Calcular savings usando la IA
        savings = self._adapter.estimate_extended_environmental_savings_from_ingredients(
            ingredients_data
        )

        # Determinar el tipo de fuente de la receta
        recipe_source_type = "generated" if recipe_source == "generated" else "manual"
        
        # Guardar nuevo cálculo
        new_record = EnvironmentalSavings(
            user_uid=user_uid,
            recipe_uid=recipe_uid,
            recipe_title=recipe_title,
            carbon_footprint=savings["carbon_footprint"],
            water_footprint=savings["water_footprint"],
            energy_footprint=savings["energy_footprint"],
            economic_cost=savings["economic_cost"],
            unit_carbon=savings["unit_carbon"],
            unit_water=savings["unit_water"],
            unit_energy=savings["unit_energy"],
            unit_cost=savings["unit_cost"],
            recipe_source_type=recipe_source_type,
            is_cooked=False
        )
        self._savings_repo.save(new_record)

        return {
            "recipe_uid": recipe_uid,
            "recipe_title": recipe_title,
            "recipe_source": recipe_source,
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