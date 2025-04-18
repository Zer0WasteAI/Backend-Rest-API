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
        Analiza esta imagen y devuelve una lista JSON con metadatos de cada ingrediente.
        Formato esperado:
        [
        {
        "name": "Nombre del ingrediente",
        "quantity": 2,
        "type_unit": "unidades",
        "storage_type": "Refrigerado",
        "expiration_time": "5",
        "tips": "Consejo de conservación"
        },
        ...
        ]
        """
        
        response = self.model.generate_content([prompt, image], generation_config={"temperature": 0.4})
        return self._parse_response_text(response.text)
    
    def recognize_food(self, image_file) -> List[Dict]:
        raise NotImplementedError("Este método aún no está implementado.")

    def recognize_batch(self, image_files: List) -> List[Dict]:
        raise NotImplementedError("Este método aún no está implementado.")

    def suggest_storage_type(self, food_name: str) -> str:
        raise NotImplementedError("Este método aún no está implementado.")

    def category_autotag(self, food_name: str) -> List[str]:
        raise NotImplementedError("Este método aún no está implementado.")

    def match_allergens(self, food_name: str, user_allergens: List[str]) -> List[str]:
        raise NotImplementedError("Este método aún no está implementado.")
