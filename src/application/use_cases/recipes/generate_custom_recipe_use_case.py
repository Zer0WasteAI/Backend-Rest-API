from typing import Dict, Any, List
from src.application.factories.auth_usecase_factory import make_firestore_profile_service

class GenerateCustomRecipeUseCase:
    def __init__(self, recipe_service):
        self.recipe_service = recipe_service

    def execute(self, user_uid: str, custom_ingredients: List[str], preferences: List[str] = None, num_recipes: int = 2, recipe_categories: List[str] = None) -> Dict[str, Any]:
        # Obtener preferencias del usuario desde Firestore
        firestore_service = make_firestore_profile_service()
        user_profile = firestore_service.get_profile(user_uid)
        
        # Filtrar ingredientes según alergias del usuario
        filtered_ingredients = []
        if user_profile:
            for ingredient in custom_ingredients:
                if not self._is_allergic_to_ingredient(ingredient, user_profile):
                    filtered_ingredients.append(ingredient)
        else:
            filtered_ingredients = custom_ingredients
        
        # Combinar preferencias del request con las del perfil del usuario
        combined_preferences = list(preferences or [])
        
        if user_profile:
            # Agregar alergias como restricciones
            if user_profile.get("allergies"):
                for allergy in user_profile["allergies"]:
                    allergy_text = allergy.get("name", allergy) if isinstance(allergy, dict) else allergy
                    if isinstance(allergy_text, str):
                        combined_preferences.append(f"sin {allergy_text}")
            
            if user_profile.get("allergyItems"):
                for item in user_profile["allergyItems"]:
                    item_text = item.get("name", item) if isinstance(item, dict) else item
                    if isinstance(item_text, str):
                        combined_preferences.append(f"sin {item_text}")
            
            # Agregar tipos de comida preferidos (si no conflictan con preferencias del request)
            if user_profile.get("preferredFoodTypes"):
                for food_type in user_profile["preferredFoodTypes"]:
                    food_type_text = food_type.get("name", food_type) if isinstance(food_type, dict) else food_type
                    if isinstance(food_type_text, str):
                        combined_preferences.append(food_type_text)
            
            # Agregar dietas especiales
            if user_profile.get("specialDietItems"):
                for diet_item in user_profile["specialDietItems"]:
                    diet_text = diet_item.get("name", diet_item) if isinstance(diet_item, dict) else diet_item
                    if isinstance(diet_text, str):
                        combined_preferences.append(diet_text)
            
            # Agregar nivel de cocina
            cooking_level = user_profile.get("cookingLevel", "beginner")
            if cooking_level == "beginner":
                combined_preferences.append("recetas fáciles")
            elif cooking_level == "intermediate":
                combined_preferences.append("recetas de dificultad media")
            elif cooking_level == "advanced":
                combined_preferences.append("recetas avanzadas")
        
        # Remover duplicados preservando el orden
        combined_preferences = list(dict.fromkeys(combined_preferences))
        
        # Estructura los datos para la generación personalizada
        generation_data = {
            "ingredients": [{"name": ingredient, "quantity": "Al gusto", "unit": "porción"} for ingredient in filtered_ingredients],
            "priorities": filtered_ingredients,  # Priorizamos todos los ingredientes ingresados (ya filtrados)
            "preferences": combined_preferences,
            "user_profile": user_profile  # Incluir perfil para uso adicional (idioma, medidas, etc.)
        }
        
        return self.recipe_service.generate_recipes(generation_data, num_recipes, recipe_categories)
    
    def _is_allergic_to_ingredient(self, ingredient_name: str, user_profile: dict) -> bool:
        """
        Verifica si el usuario es alérgico a un ingrediente específico
        """
        allergies = user_profile.get("allergies", [])
        allergy_items = user_profile.get("allergyItems", [])
        
        ingredient_lower = ingredient_name.lower()
        
        # Verificar alergias generales
        for allergy in allergies:
            # Manejar tanto strings como diccionarios
            allergy_text = allergy.get("name", allergy) if isinstance(allergy, dict) else allergy
            if isinstance(allergy_text, str) and allergy_text.lower() in ingredient_lower:
                return True
        
        # Verificar items específicos de alergia
        for item in allergy_items:
            # Manejar tanto strings como diccionarios  
            item_text = item.get("name", item) if isinstance(item, dict) else item
            if isinstance(item_text, str) and item_text.lower() in ingredient_lower:
                return True
        
        return False 