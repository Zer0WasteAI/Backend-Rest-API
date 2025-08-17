from typing import List, Optional, Dict
from src.domain.models.mise_en_place import MiseEnPlace, PreheatInstruction, PrepTask, MeasuredIngredient
from src.domain.models.recipe import Recipe
from src.infrastructure.db.ingredient_batch_repository_impl import IngredientBatchRepository

class MiseEnPlaceService:
    def __init__(self, batch_repository: IngredientBatchRepository):
        self.batch_repository = batch_repository

    def generate_mise_en_place(self, recipe: Recipe, servings: int, user_uid: str) -> MiseEnPlace:
        """Generate mise en place for a recipe with specific servings"""
        
        # Scale base recipe for servings
        base_servings = 2  # Assume recipes are for 2 servings by default
        scale_factor = servings / base_servings
        
        # Generate tools list based on recipe complexity
        tools = self._generate_tools_list(recipe)
        
        # Generate preheat instructions
        preheat = self._generate_preheat_instructions(recipe)
        
        # Generate prep tasks from recipe ingredients
        prep_tasks = self._generate_prep_tasks(recipe, scale_factor)
        
        # Generate measured ingredients with FEFO suggestions
        measured_ingredients = self._generate_measured_ingredients(recipe, scale_factor, user_uid)
        
        mise_en_place = MiseEnPlace(
            recipe_uid=recipe.uid,
            servings=servings,
            tools=tools,
            preheat=preheat,
            prep_tasks=prep_tasks,
            measured_ingredients=measured_ingredients
        )
        
        return mise_en_place

    def _generate_tools_list(self, recipe: Recipe) -> List[str]:
        """Generate tools needed based on recipe"""
        # Basic tools for most recipes
        tools = ["cuchillo", "tabla de cortar"]
        
        # Analyze recipe steps for tool requirements
        recipe_text = (recipe.title + " " + recipe.description).lower()
        
        if any(word in recipe_text for word in ["freír", "sofrito", "saltear"]):
            tools.append("sartén")
        
        if any(word in recipe_text for word in ["hervir", "cocinar", "guiso"]):
            tools.append("olla mediana")
        
        if any(word in recipe_text for word in ["horno", "hornear"]):
            tools.append("bandeja de horno")
        
        if any(word in recipe_text for word in ["batir", "mezclar"]):
            tools.append("batidora")
        
        if any(word in recipe_text for word in ["rallar", "queso"]):
            tools.append("rallador")
        
        return tools

    def _generate_preheat_instructions(self, recipe: Recipe) -> List[PreheatInstruction]:
        """Generate preheat instructions"""
        preheat = []
        
        recipe_text = (recipe.title + " " + recipe.description).lower()
        
        # Check if oven is needed
        if any(word in recipe_text for word in ["horno", "hornear"]):
            preheat.append(PreheatInstruction(
                device="oven",
                setting="180°C",
                duration_ms=600000  # 10 minutes
            ))
        
        # Most recipes need stove preheating
        if any(word in recipe_text for word in ["freír", "sofrito", "cocinar", "saltear"]):
            preheat.append(PreheatInstruction(
                device="stove",
                setting="medium",
                duration_ms=60000  # 1 minute
            ))
        
        return preheat

    def _generate_prep_tasks(self, recipe: Recipe, scale_factor: float) -> List[PrepTask]:
        """Generate preparation tasks from recipe ingredients"""
        prep_tasks = []
        
        for i, ingredient in enumerate(recipe.ingredients):
            task_id = f"mp{i+1}"
            scaled_qty = ingredient.quantity * scale_factor
            
            # Generate prep instruction based on ingredient type
            prep_text = self._generate_prep_instruction(ingredient.name, scaled_qty, ingredient.type_unit)
            
            prep_tasks.append(PrepTask(
                id=task_id,
                text=prep_text,
                ingredient_uid=f"ing_{ingredient.name.lower().replace(' ', '_')}",
                suggested_qty=scaled_qty,
                unit=ingredient.type_unit
            ))
        
        return prep_tasks

    def _generate_prep_instruction(self, ingredient_name: str, qty: float, unit: str) -> str:
        """Generate preparation instruction for an ingredient"""
        ingredient_lower = ingredient_name.lower()
        
        # Common preparation instructions
        if "cebolla" in ingredient_lower:
            return f"Picar {ingredient_name} en cubos ({qty:.0f} {unit})"
        elif "ajo" in ingredient_lower:
            return f"Picar {ingredient_name} finamente ({qty:.0f} {unit})"
        elif "tomate" in ingredient_lower:
            return f"Cortar {ingredient_name} en rodajas ({qty:.0f} {unit})"
        elif "pollo" in ingredient_lower or "carne" in ingredient_lower:
            return f"Deshilachar {ingredient_name} ({qty:.0f} {unit})"
        elif "papa" in ingredient_lower or "patata" in ingredient_lower:
            return f"Pelar y cortar {ingredient_name} en cubos ({qty:.0f} {unit})"
        elif "zanahoria" in ingredient_lower:
            return f"Pelar y cortar {ingredient_name} en rodajas ({qty:.0f} {unit})"
        elif "queso" in ingredient_lower:
            return f"Rallar {ingredient_name} ({qty:.0f} {unit})"
        else:
            return f"Preparar {ingredient_name} ({qty:.0f} {unit})"

    def _generate_measured_ingredients(self, recipe: Recipe, scale_factor: float, user_uid: str) -> List[MeasuredIngredient]:
        """Generate measured ingredients with FEFO lot suggestions"""
        measured_ingredients = []
        
        for ingredient in recipe.ingredients:
            ingredient_uid = f"ing_{ingredient.name.lower().replace(' ', '_')}"
            scaled_qty = ingredient.quantity * scale_factor
            
            # Get FEFO suggestion for this ingredient
            batches = self.batch_repository.find_by_ingredient_fefo(
                ingredient_uid=ingredient_uid,
                user_uid=user_uid,
                required_qty=scaled_qty
            )
            
            lot_suggestion = batches[0].id if batches else None
            
            measured_ingredients.append(MeasuredIngredient(
                ingredient_uid=ingredient_uid,
                qty=scaled_qty,
                unit=ingredient.type_unit,
                lot_suggestion=lot_suggestion
            ))
        
        return measured_ingredients