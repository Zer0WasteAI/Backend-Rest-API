import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
import json
from typing import List, Dict
from domain.interfaces.ia_food_analyzer import IAFoodAnalyzer

load_dotenv()

class GeminiAdapter(IAFoodAnalyzer):

    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-1.5-pro")

    def _parse_response_text(self, text: str):
        clean_text = text.strip()

        if clean_text.startswith("```"):
            clean_text = clean_text.strip("`").strip()
            if clean_text.startswith("json"):
                clean_text = clean_text[len("json"):].strip()

        try:
            return json.loads(clean_text)
        except Exception as e:
            return [{"error": "Error al estructurar respuesta", "raw": text, "details": str(e)}]

    def recognize_ingredients(self, image_file) -> List[Dict]:
        image = Image.open(image_file)

        prompt = """
        Actúa como un chef experto con conocimientos en conservación de alimentos y análisis visual.
        Recibirás una imagen con uno o varios ingredientes. Reconócelos y devuelve una lista JSON estructurada con la siguiente información por cada uno:
        - name: nombre del ingrediente
        - quantity: cantidad aproximada
        - type_unit: unidad (puede ser 'unidades', 'gramos', 'kilos', etc.)
        - storage_type: tipo de almacenamiento ideal ('Refrigerado', 'Congelado', o 'Ambiente')
        - expiration_time: tiempo aproximado antes de que se deteriore, expresado en DÍAS
        - tips: consejo breve para conservarlo correctamente
        Formato de respuesta:
        [
          {
            "name": "Nombre del ingrediente",
            "quantity": 2,
            "type_unit": "unidades",
            "storage_type": "Refrigerado",
            "expiration_time": "5",
            "tips": "Consejo de conservación"
          }
        ]
        """
        
        response = self.model.generate_content([prompt, image], generation_config={"temperature": 0.4})
        return self._parse_response_text(response.text)
    
    def recognize_food(self, image_file) -> List[Dict]:
        image = Image.open(image_file)

        prompt = """
        Actúa como un chef experto en cocina internacional. Analiza la siguiente imagen que contiene uno o más platos preparados.
        Devuélveme una lista JSON donde por cada plato se detalle lo siguiente:
        - name: nombre del plato
        - main_ingredients: lista de ingredientes principales (en español)
        - category: tipo de plato (por ejemplo: Entrada, Plato principal, Postre, Bebida)
        - calories: cantidad aproximada de calorías (solo si es razonable estimarlo)
        - description: una breve descripción del plato y su preparación típica
        Formato esperado:
        [
          {
            "name": "Lomo saltado",
            "main_ingredients": ["Carne de res", "Papas", "Cebolla", "Tomate", "Sillao"],
            "category": "Plato principal",
            "calories": 600,
            "description": "Plato típico peruano que mezcla carne salteada con papas fritas, cebolla y tomate."
          }
        ]
        """

        response = self.model.generate_content([prompt, image], generation_config={"temperature": 0.4})

        return self._parse_response_text(response.text)

    def recognize_batch(self, image_files: List) -> List[Dict]:
        raise NotImplementedError("Este método aún no está implementado.")

    def suggest_storage_type(self, food_name: str) -> str:
        raise NotImplementedError("Este método aún no está implementado.")

    def category_autotag(self, food_name: str) -> List[str]:
        raise NotImplementedError("Este método aún no está implementado.")

    def match_allergens(self, food_name: str, user_allergens: List[str]) -> List[str]:
        raise NotImplementedError("Este método aún no está implementado.")
