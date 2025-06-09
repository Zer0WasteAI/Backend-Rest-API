import json
import logging
from typing import Dict, Any, List
from src.domain.services.ia_recipe_generator_service import IARecipeGeneratorService
import google.generativeai as genai
from src.config.config import Config

logger = logging.getLogger(__name__)

class GeminiRecipeGeneratorService(IARecipeGeneratorService):
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

    def generate_recipes(self, data: Dict[str, Any], num_recipes: int = 2, recipe_categories: List[str] = []) -> Dict[str, Any]:
        try:
            prompt = self._build_prompt(data, num_recipes, recipe_categories)
            
            response = self.model.generate_content(prompt, generation_config={"temperature": 0.6})
            
            # Parse the JSON response
            recipes = self._parse_response_text(response.text)
            
            # Información sobre preferencias aplicadas
            user_profile = data.get("user_profile", {})
            applied_preferences = data.get("preferences", [])
            
            # Construir respuesta con información de personalización
            result = {
                "generated_recipes": recipes,
                "total_recipes": len(recipes),
                "inventory_usage": f"{min(100, len(data.get('priorities', [])) * 25)}%"
            }
            
            # Agregar información de personalización si hay perfil de usuario
            if user_profile:
                result["personalization_info"] = {
                    "language": user_profile.get("language", "es"),
                    "measurement_system": user_profile.get("measurementUnit", "metric"),
                    "cooking_level": user_profile.get("cookingLevel", "beginner"),
                    "preferences_applied": applied_preferences,
                    "allergies_filtered": user_profile.get("allergies", []) + user_profile.get("allergyItems", []),
                    "dietary_restrictions": user_profile.get("specialDietItems", []),
                    "preferred_food_types": user_profile.get("preferredFoodTypes", [])
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating recipes: {str(e)}")
            raise ValueError("Error en la generación de recetas")

    import json
    import re
    import logging

    logger = logging.getLogger(__name__)

    def _parse_response_text(self, text: str):
        clean_text = text.strip()

        # Si viene con markdown-style triple backticks
        if clean_text.startswith("```"):
            clean_text = clean_text.strip("`").strip()
            if clean_text.startswith("json"):
                clean_text = clean_text[len("json"):].strip()

        # Extracción robusta del array JSON (de "[" a "]")
        start = clean_text.find('[')
        end = clean_text.rfind(']')
        if start == -1 or end == -1:
            logger.error("No valid JSON array found in text.")
            raise ValueError("Error parsing AI response: no valid JSON array found.")

        json_text = clean_text[start:end + 1]

        try:
            return json.loads(json_text)
        except Exception as e:
            logger.error(f"Failed to parse AI response as JSON: {json_text}")
            raise ValueError("Error parsing AI response") from e

    def _build_prompt(self, data: Dict[str, Any], num_recipes, recipe_categories) -> str:
        ingredients = data.get("ingredients", [])
        priorities = data.get("priorities", [])
        preferences = data.get("preferences", [])
        user_profile = data.get("user_profile", {})
        
        # Obtener idioma y sistema de medidas del perfil
        language = user_profile.get("language", "es")
        measurement_unit = user_profile.get("measurementUnit", "metric")
        
        # Configurar idioma del prompt
        if language == "en":
            chef_nationality = "Peruvian chef expert in nutrition and waste-reduction cooking"
            recipe_categories_options = "breakfast, lunch, dinner, dessert, salad, soup"
            instruction_start = "You are a Peruvian chef expert in nutrition and waste-reduction cooking"
            json_instruction = "Return only a **JSON list** containing"
            different_recipes = "different recipes"
            each_recipe_structure = "Each recipe must follow this structure"
            dish_name = "Simple dish name"
            difficulty_options = "Easy, Intermediate, or Difficult"
            step_prefix = "Step"
            awareness_message = "Awareness message about food waste reduction"
            available_ingredients = "Choose from the following available ingredients (Not necessary to use all in each recipe)"
            prioritize_use = "Prioritize the use of"
            user_preferences = "User preferences"
            recipe_categories_preferences = "Recipe type preferences"
            respond_only = "Respond only with a JSON array like this"
            no_additional_text = "Do not include greetings, code, or additional text"
        else:
            chef_nationality = "chef peruano experto en nutrición y cocina de aprovechamiento"
            recipe_categories_options = "desayuno, almuerzo, cena, postre, ensalada, sopa"
            instruction_start = "Eres un chef peruano experto en nutrición y cocina de aprovechamiento"
            json_instruction = "Devuelve únicamente una **lista JSON** que contenga"
            different_recipes = "recetas diferentes"
            each_recipe_structure = "Cada receta debe seguir esta estructura"
            dish_name = "Nombre simple del plato"
            difficulty_options = "Fácil, Intermedio o Difícil"
            step_prefix = "Paso"
            awareness_message = "Mensaje de concientización sobre el aprovechamiento de alimentos"
            available_ingredients = "Elige entre los siguientes ingredientes disponibles (No es necesario usar todos en cada receta)"
            prioritize_use = "Prioriza el uso de"
            user_preferences = "Preferencias del usuario"
            recipe_categories_preferences = "Preferencias de tipo de receta"
            respond_only = "Responde únicamente con un arreglo JSON así"
            no_additional_text = "No incluyas saludos, código, ni texto adicional"

        # Configurar sistema de medidas
        if measurement_unit == "imperial":
            unit_examples = ["1 cup", "2 oz", "1 lb", "1 tsp", "1 tbsp"]
            quantity_instruction = "(Use imperial units: cups, oz, lb, tsp, tbsp, etc.)"
        else:
            unit_examples = ["200g", "1 litro", "2 unidades", "1 cucharada"]
            quantity_instruction = "(Usa unidades métricas: gramos, litros, unidades, cucharadas, etc.)"

        ingredients_str = "\n".join(
            f"- {i['name']}: {i['quantity']} {i['unit']}" for i in ingredients
        )
        priorities_str = ", ".join(priorities) if priorities else ("none" if language == "en" else "ninguno")
        preferences_str = ", ".join(preferences) if preferences else ("none" if language == "en" else "ninguna")
        recipe_categories_str = ", ".join(recipe_categories) if recipe_categories else ("none" if language == "en" else "ninguna")

        return f"""
        {instruction_start}.
        {json_instruction} {num_recipes} {different_recipes}. {each_recipe_structure}:
        {{
          "title": "{dish_name}",
          "duration": "20 min",
          "difficulty": "{difficulty_options}",
          "category": "{recipe_categories_options}",
          "ingredients": [
            {{
              "name": "Nombre del ingrediente",
              "quantity": 200,
              "type_unit": "g"
            }},         
            ...
          ],
          "steps": [
            {{
              "step_order": 1,
              "description": "{step_prefix} 1: Describe el paso aquí"
            }},
            ...
          ],
          "footer": "{awareness_message}"
        }}

        {available_ingredients}:
        {ingredients_str}

        {prioritize_use}: {priorities_str}.
        {user_preferences}: {preferences_str}.
        {recipe_categories_preferences}: {recipe_categories_str}.

        {respond_only}:
        [
          {{
            "title": "Receta 1",
            "duration": "20 min",
            "difficulty": "Fácil",
            "category": "desayuno",
            "ingredients": ["..."],
            "steps": ["..."],
            "footer": "..."
          }},
          {{
            "title": "Receta 2",
            "duration": "30 min",
            "difficulty": "Intermedio",
            "category": "postre",
            "ingredients": [
              {{
                "name": "Papa",
                "quantity": 2,
                "type_unit": "unidades"
              }}
            ],
            "steps": [
              {{
                "step_order": 1,
                "description": "Lavar las papas"
              }}
            ],
            "footer": "..."
          }}
        ]

        {no_additional_text}.
        """