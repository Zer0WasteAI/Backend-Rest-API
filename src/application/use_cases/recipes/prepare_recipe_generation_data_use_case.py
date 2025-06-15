from typing import Dict, Any
from src.domain.models.inventory import Inventory
from src.application.factories.auth_usecase_factory import make_firestore_profile_service
from datetime import datetime

class PrepareRecipeGenerationDataUseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, user_uid: str) -> Dict[str, Any]:
        inventory: Inventory = self.repository.get_by_user_uid(user_uid)
        if not inventory:
            raise ValueError("Inventory not found for user")

        # Obtener preferencias del usuario desde Firestore
        firestore_service = make_firestore_profile_service()
        user_profile = firestore_service.get_profile(user_uid)
        
        ingredients = []
        priority_names = set()

        for ingredient in inventory.ingredients.values():
            # Filtrar ingredientes según alergias del usuario
            if user_profile and self._is_allergic_to_ingredient(ingredient.name, user_profile):
                continue  # Omitir ingredientes alergénicos
                
            for stack in ingredient.stacks:
                ingredients.append({
                    "name": ingredient.name,
                    "quantity": stack.quantity,
                    "unit": ingredient.type_unit
                })

                # Se prioriza si vence en menos de 7 días
                if (stack.expiration_date - datetime.utcnow()).days <= 7:
                    priority_names.add(ingredient.name)

        # Construir preferencias desde perfil de usuario
        preferences = []
        if user_profile:
            # Agregar alergias como restricciones
            if user_profile.get("allergies"):
                preferences.extend([f"sin {allergy}" for allergy in user_profile["allergies"]])
            
            if user_profile.get("allergyItems"):
                preferences.extend([f"sin {item}" for item in user_profile["allergyItems"]])
            
            # Agregar tipos de comida preferidos
            if user_profile.get("preferredFoodTypes"):
                preferences.extend(user_profile["preferredFoodTypes"])
            
            # Agregar dietas especiales
            if user_profile.get("specialDietItems"):
                preferences.extend(user_profile["specialDietItems"])
            
            # Agregar nivel de cocina
            cooking_level = user_profile.get("cookingLevel", "beginner")
            if cooking_level == "beginner":
                preferences.append("recetas fáciles")
            elif cooking_level == "intermediate":
                preferences.append("recetas de dificultad media")
            elif cooking_level == "advanced":
                preferences.append("recetas avanzadas")

        return {
            "ingredients": ingredients,
            "priorities": list(priority_names),
            "preferences": preferences,
            "user_profile": user_profile  # Incluir perfil para uso adicional
        }

    def _is_allergic_to_ingredient(self, ingredient_name: str, user_profile: dict) -> bool:

        #Verifica si el usuario es alérgico a un ingrediente específico

        allergies = user_profile.get("allergies", [])
        allergy_items = user_profile.get("allergyItems", [])
        
        ingredient_lower = ingredient_name.lower()
        
        # Verificar alergias generales
        for allergy in allergies:
            if allergy.lower() in ingredient_lower:
                return True
        
        # Verificar items específicos de alergia
        for item in allergy_items:
            if item.lower() in ingredient_lower:
                return True
        
        return False