from typing import Dict, Any
from src.domain.models.inventory import Inventory
from datetime import datetime
class PrepareRecipeGenerationDataUseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, user_uid: str) -> Dict[str, Any]:
        inventory: Inventory = self.repository.get_by_user_uid(user_uid)
        if not inventory:
            raise ValueError("Inventory not found for user")

        ingredients = []
        priority_names = set()

        for ingredient in inventory.ingredients.values():
            for stack in ingredient.stacks:
                ingredients.append({
                    "name": ingredient.name,
                    "quantity": stack.quantity,
                    "unit": ingredient.type_unit
                })

                # Se prioriza si vence en menos de 7 días
                if (stack.expiration_date - datetime.utcnow()).days <= 7:
                    priority_names.add(ingredient.name)

        return {
            "ingredients": ingredients,
            "priorities": list(priority_names),
            "preferences": []  # En el futuro desde firebase: ["vegetariano", "sin gluten", ...]
        }