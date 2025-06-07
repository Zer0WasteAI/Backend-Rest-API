from typing import Dict, Any, List
from src.application.factories.auth_usecase_factory import make_firestore_profile_service

class GenerateCustomRecipeUseCase:
    def __init__(self, recipe_service):
        self.recipe_service = recipe_service

    def execute(self, user_uid: str, custom_ingredients: List[str], preferences: List[str] = None, num_recipes: int = 2) -> Dict[str, Any]:
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
                combined_preferences.extend([f"sin {allergy}" for allergy in user_profile["allergies"]])
            
            if user_profile.get("allergyItems"):
                combined_preferences.extend([f"sin {item}" for item in user_profile["allergyItems"]])
            
            # Agregar tipos de comida preferidos (si no conflictan con preferencias del request)
            if user_profile.get("preferredFoodTypes"):
                combined_preferences.extend(user_profile["preferredFoodTypes"])
            
            # Agregar dietas especiales
            if user_profile.get("specialDietItems"):
                combined_preferences.extend(user_profile["specialDietItems"])
            
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
        
        return self.recipe_service.generate_recipes(generation_data, num_recipes)
    
    def _is_allergic_to_ingredient(self, ingredient_name: str, user_profile: dict) -> bool:
        """
        Verifica si el usuario es alérgico a un ingrediente específico
        """
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