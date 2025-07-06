from typing import Dict, Any
from src.domain.models.inventory import Inventory
from src.application.factories.auth_usecase_factory import make_firestore_profile_service
from datetime import datetime

class PrepareRecipeGenerationDataUseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, user_uid: str) -> Dict[str, Any]:
        print(f"🍳 [RECIPE PREP] Starting recipe preparation for user: {user_uid}")
        
        inventory: Inventory = self.repository.get_by_user_uid(user_uid)
        if not inventory:
            raise ValueError("Inventory not found for user")

        # Obtener preferencias del usuario desde Firestore
        firestore_service = make_firestore_profile_service()
        user_profile = firestore_service.get_profile(user_uid)
        
        print(f"🍳 [RECIPE PREP] User profile keys: {list(user_profile.keys()) if user_profile else 'None'}")
        if user_profile:
            print(f"🍳 [RECIPE PREP] Allergies type: {type(user_profile.get('allergies'))}")
            print(f"🍳 [RECIPE PREP] AllergyItems type: {type(user_profile.get('allergyItems'))}")
            if user_profile.get('allergyItems'):
                print(f"🍳 [RECIPE PREP] First allergyItem type: {type(user_profile['allergyItems'][0]) if user_profile['allergyItems'] else 'empty'}")
        
        ingredients = []
        priority_names = set()

        for ingredient in inventory.ingredients.values():
            # Filtrar ingredientes según alergias del usuario
            try:
                if user_profile and self._is_allergic_to_ingredient(ingredient.name, user_profile):
                    print(f"🚫 [RECIPE PREP] Skipping allergenic ingredient: {ingredient.name}")
                    continue  # Omitir ingredientes alergénicos
            except Exception as e:
                print(f"🚨 [RECIPE PREP] Error checking allergies for {ingredient.name}: {str(e)}")
                # En caso de error, incluir el ingrediente para no bloquear la generación
                
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
            try:
                # Agregar alergias como restricciones
                if user_profile.get("allergies"):
                    for allergy in user_profile["allergies"]:
                        if isinstance(allergy, str):
                            preferences.append(f"sin {allergy}")
                
                if user_profile.get("allergyItems"):
                    for item in user_profile["allergyItems"]:
                        if isinstance(item, str):
                            preferences.append(f"sin {item}")
                        elif isinstance(item, dict):
                            # Extraer nombre del item si es dict
                            item_name = item.get('name') or item.get('label') or item.get('value')
                            if isinstance(item_name, str):
                                preferences.append(f"sin {item_name}")
                
                # Agregar tipos de comida preferidos
                if user_profile.get("preferredFoodTypes"):
                    for food_type in user_profile["preferredFoodTypes"]:
                        if isinstance(food_type, str):
                            preferences.append(food_type)
                
                # Agregar dietas especiales
                if user_profile.get("specialDietItems"):
                    for diet_item in user_profile["specialDietItems"]:
                        if isinstance(diet_item, str):
                            preferences.append(diet_item)
                
                # Agregar nivel de cocina
                cooking_level = user_profile.get("cookingLevel", "beginner")
                if cooking_level == "beginner":
                    preferences.append("recetas fáciles")
                elif cooking_level == "intermediate":
                    preferences.append("recetas de dificultad media")
                elif cooking_level == "advanced":
                    preferences.append("recetas avanzadas")
                    
            except Exception as e:
                print(f"🚨 [RECIPE PREP] Error building preferences: {str(e)}")
                print(f"🚨 [RECIPE PREP] User profile structure: {user_profile}")
                # Continuar con preferencias vacías en caso de error

        return {
            "ingredients": ingredients,
            "priorities": list(priority_names),
            "preferences": preferences,
            "user_profile": user_profile  # Incluir perfil para uso adicional
        }

    def _is_allergic_to_ingredient(self, ingredient_name: str, user_profile: dict) -> bool:
        """
        Verifica si el usuario es alérgico a un ingrediente específico.
        Maneja tanto strings como objetos dict en allergyItems.
        """
        allergies = user_profile.get("allergies", [])
        allergy_items = user_profile.get("allergyItems", [])
        
        ingredient_lower = ingredient_name.lower()
        
        # Verificar alergias generales
        for allergy in allergies:
            if isinstance(allergy, str) and allergy.lower() in ingredient_lower:
                return True
        
        # Verificar items específicos de alergia
        for item in allergy_items:
            if isinstance(item, str):
                # Si es string, comparar directamente
                if item.lower() in ingredient_lower:
                    return True
            elif isinstance(item, dict):
                # Si es dict, buscar en campos comunes como 'name', 'label', etc.
                item_name = item.get('name') or item.get('label') or item.get('value') or str(item)
                if isinstance(item_name, str) and item_name.lower() in ingredient_lower:
                    return True
        
        return False