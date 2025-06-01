import json
from src.domain.services.ia_recipe_generator_service import IARecipeGeneratorService
from src.shared.exceptions.custom import InvalidResponseFormatException
from src.config.config import Config
import google.generativeai as genai
from typing import IO, List, Dict, Any

class GeminiRecipeGeneratorService(IARecipeGeneratorService):
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

    def _parse_response_text(self, text: str):
        clean_text = text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.strip("`").strip()
            if clean_text.startswith("json"):
                clean_text = clean_text[len("json"):].strip()
        try:
            return json.loads(clean_text)
        except Exception as e:
            raise InvalidResponseFormatException("No se pudo parsear la respuesta de la IA") from e

    def generate_recipes(self, data: Dict[str, Any], num_recipes) -> Dict[str, Any]:
        prompt = self._build_prompt(data, num_recipes)
        response = self.model.generate_content(prompt, generation_config={"temperature": 0.6})
        return self._parse_response_text(response.text)

    def _build_prompt(self, data: Dict[str, Any], num_recipes) -> str:
        ingredients = data.get("ingredients", [])
        priorities = data.get("priorities", [])
        preferences = data.get("preferences", [])

        ingredients_str = "\n".join(
            f"- {i['name']}: {i['quantity']} {i['unit']}" for i in ingredients
        )
        priorities_str = ", ".join(priorities) if priorities else "ninguno"
        preferences_str = ", ".join(preferences) if preferences else "ninguna"

        return f"""
        Eres un chef peruano experto en nutrición y cocina de aprovechamiento.
        Devuelve únicamente una **lista JSON** que contenga {num_recipes} recetas diferentes. Cada receta debe seguir esta estructura:
        {{
          "title": "Nombre del plato",
          "duration": "20 min",
          "difficulty": "Fácil, Intermedio o Difícil",
          "ingredients": [
            "ingrediente 1: Al gusto",
            "ingrediente 2: 1 unidad",
            ...
          ],
          "steps": [
            "Paso 1",
            "Paso 2",
            ...
          ],
          "footer": "Mensaje de concientización sobre el aprovechamiento de alimentos"
        }}

        Elige entre los siguientes ingredientes disponibles (No es necesario usar todos en cada receta):
        {ingredients_str}

        Prioriza el uso de: {priorities_str}.
        Preferencias del usuario: {preferences_str}.

        Responde únicamente con un arreglo JSON así:
        [
          {{
            "title": "Receta 1",
            "duration": "20 min",
            "difficulty": "Fácil",
            "ingredients": ["..."],
            "steps": ["..."],
            "footer": "..."
          }},
          {{
            "title": "Receta 2",
            "duration": "30 min",
            "difficulty": "Intermedio",
            "ingredients": ["..."],
            "steps": ["..."],
            "footer": "..."
          }}
        ]

        No incluyas saludos, código, ni texto adicional.
        """