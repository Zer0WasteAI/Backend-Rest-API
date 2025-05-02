import google.generativeai as genai
import json

from PIL import Image
from src.config.config import Config
from typing import IO, List, Dict, Any

from src.domain.services.ia_food_analyzer_service import IAFoodAnalyzerService
from src.shared.exceptions.custom import UnidentifiedImageException, InvalidResponseFormatException

class GeminiAdapterService(IAFoodAnalyzerService):
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
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
            raise InvalidResponseFormatException() from e

    def recognize_ingredients(self, image_file: IO[bytes]) -> Dict[str, List[Dict[str, Any]]]:
        try:
            image = Image.open(image_file)
        except Exception as e:
            raise UnidentifiedImageException() from e
            
        prompt = """
        Actúa como un chef experto con conocimientos en conservación de alimentos y análisis visual.
        Recibirás una imagen con uno o varios ingredientes. Reconócelos y devuelve una lista JSON estructurada con la siguiente información por cada uno:
        - name: nombre del ingrediente
        - quantity: cantidad aproximada
        - type_unit: unidad (puede ser 'unidades', 'gramos', 'kilos', etc.)
        - storage_type: tipo de almacenamiento ideal ('Refrigerado', 'Congelado', o 'Ambiente')
        - expiration_time: tiempo aproximado antes de que se deteriore, expresado en time_unit
        - time_unit: unidad de tiempo (Días, Semanas, Meses)
        - tips: consejo breve para conservarlo correctamente
        Formato de respuesta:
        {
            "ingredients": [
                {
                    "name": "Nombre del ingrediente",
                    "quantity": 2.0,
                    "type_unit": "unidades",
                    "storage_type": "Refrigerado",
                    "expiration_time": 5,
                    "time_unit": "Días",
                    "tips": "Consejo de conservación"
                }
            ]
        }
        """
        response = self.model.generate_content([prompt, image], generation_config={"temperature": 0.4})
        raw = self._parse_response_text(response.text)
        return {
        "ingredients": raw.get("ingredients", [])
        }
    
    def recognize_food(self, image_file: IO[bytes]) -> Dict[str, List[Dict[str, Any]]]:
        try:
            image = Image.open(image_file)
        except Exception as e:
            raise UnidentifiedImageException() from e

        prompt = """
        Actúa como un chef experto en cocina internacional. Analiza la siguiente imagen que contiene uno o más platos preparados.
        Devuélveme una lista JSON donde por cada plato se detalle lo siguiente:
        - name: nombre del plato
        - main_ingredients: lista de ingredientes principales (en español)
        - category: tipo de plato (por ejemplo: Entrada, Plato principal, Postre, Bebida)
        - calories: cantidad aproximada de calorías (solo si es razonable estimarlo)
        - description: una breve descripción del plato y su preparación típica
        - storage_type: tipo de almacenamiento ideal ('Refrigerado', 'Congelado', o 'Ambiente')
        - expiration_time: tiempo aproximado antes de que se deteriore, expresado en time_unit
        - time_unit: unidad de tiempo (Días, Semanas, Meses)
        - tips: consejo breve para conservarlo correctamente
        - serving_quantity: cantidad de porciones que aparecen (expresado en Platos)
        Formato esperado:
        { 
            "foods": [
                {
                    "name": "Lomo saltado",
                    "main_ingredients": ["Carne de res", "Papas", "Cebolla", "Tomate", "Sillao"],
                    "category": "Plato principal",
                    "calories": 600,
                    "description": "Plato típico peruano que mezcla carne salteada con papas fritas, cebolla y tomate.",
                    "storage_type": "Refrigerado",
                    "expiration_time": 5,
                    "time_unit": "Días",
                    "tips": "Consejo de conservación"
                    "serving_quantity": 2
                }
            ]
        }
        """

        response = self.model.generate_content([prompt, image], generation_config={"temperature": 0.4})

        raw = self._parse_response_text(response.text)
        return {
            "foods": raw.get("foods", [])
        }
    
    def recognize_batch(self, image_files: List[IO[bytes]]) -> Dict[str, List]:
        try:
            images = [Image.open(f) for f in image_files]
        except Exception as e:
            raise UnidentifiedImageException() from e
    
        prompt = """
        Actúa como un chef experto en cocina internacional, análisis visual de alimentos y conservación.
        Recibirás imágenes que pueden contener:
        1. Ingredientes (como frutas, vegetales, carnes, etc.)
        2. Platos preparados (como ceviche, arroz chaufa, etc.)
        Analiza TODAS las imágenes y devuelve un único JSON que contenga **dos arreglos separados**:
        # ingredients: si hay ingredientes individuales, incluye una lista con:
        - name: nombre del ingrediente
        - quantity: cantidad aproximada
        - type_unit: unidad (puede ser 'unidades', 'gramos', 'kilos', etc.)
        - storage_type: tipo de almacenamiento ideal ('Refrigerado', 'Congelado', o 'Ambiente')
        - expiration_time: tiempo aproximado antes de que se deteriore, expresado en time_unit
        - time_unit: unidad de tiempo (Días, Semanas, Meses)
        - tips: consejo breve para conservarlo correctamente
        # foods: si hay platos preparados, incluye una lista con:
        - name: nombre del plato
        - main_ingredients: lista de ingredientes principales (en español)
        - category: tipo de plato (por ejemplo: Entrada, Plato principal, Postre, Bebida)
        - calories: cantidad aproximada de calorías (solo si es razonable estimarlo)
        - description: una breve descripción del plato y su preparación típica
        - storage_type: tipo de almacenamiento ideal ('Refrigerado', 'Congelado', o 'Ambiente')
        - expiration_time: tiempo aproximado antes de que se deteriore, expresado en time_unit
        - time_unit: unidad de tiempo (Días, Semanas, Meses)
        - tips: consejo breve para conservarlo correctamente
        - serving_quantity: cantidad de porciones que aparecen (expresado en Platos)
        Formato de respuesta esperado:
        {
          "ingredients": [
            {
                "name": "Nombre del ingrediente",
                "quantity": 2.0,
                "type_unit": "unidades",
                "storage_type": "Refrigerado",
                "expiration_time": 5,
                "time_unit": "Días",
                "tips": "Consejo de conservación"
            }
          ],
          "foods": [
            {
                "name": "Lomo saltado",
                "main_ingredients": ["Carne de res", "Papas", "Cebolla", "Tomate", "Sillao"],
                "category": "Plato principal",
                "calories": 600,
                "description": "Plato típico peruano que mezcla carne salteada con papas fritas, cebolla y tomate.",
                "storage_type": "Refrigerado",
                "expiration_time": 5,
                "time_unit": "Días",
                "tips": "Consejo de conservación",
                "serving_quantity": 2
            }
          ]
        }
        """
         
        response = self.model.generate_content([prompt] + images, generation_config={"temperature": 0.4})
        raw = self._parse_response_text(response.text)
        ingredients = raw.get("ingredients", [])
        foods = raw.get("foods", [])
        return {
            "ingredients": ingredients,
            "foods": foods
        }

    def suggest_storage_type(self, food_name: str) -> str:
        return "Refrigerado"  # valor por defecto

    def category_autotag(self, food_name: str) -> str:
        return "Ingrediente"  # valor por defecto

    def match_allergens(self, food_name: str, user_allergens: List[str]) -> list:
        return []  # retorno vacío como base