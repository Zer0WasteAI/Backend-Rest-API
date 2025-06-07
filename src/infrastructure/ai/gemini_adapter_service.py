import google.generativeai as genai
import json
import base64
from io import BytesIO

from PIL import Image
from src.config.config import Config
from typing import IO, List, Dict, Any, Optional

from src.domain.services.ia_food_analyzer_service import IAFoodAnalyzerService
from src.shared.exceptions.custom import UnidentifiedImageException, InvalidResponseFormatException

class GeminiAdapterService(IAFoodAnalyzerService):
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")
        # Separate model for image generation
        self.image_gen_model = genai.GenerativeModel("gemini-2.0-flash-preview-image-generation")

    def _parse_response_text(self, text: str):
        clean_text = text.strip()

        if clean_text.startswith("```"):
            clean_text = clean_text.strip("`").strip()
            if clean_text.startswith("json"):
                clean_text = clean_text[len("json"):].strip()

        try:
            return json.loads(clean_text)
        except Exception as e:
            raise InvalidResponseFormatException(f"No se pudo parsear:\n{clean_text}") from e

    def generate_ingredient_image(self, ingredient_name: str, descripcion: str = "") -> Optional[BytesIO]:
        """
        Generate an image for an ingredient using Gemini's image generation capabilities.
        
        Args:
            ingredient_name: Name of the ingredient to generate an image for
            descripcion: Description of the ingredient's characteristics
            
        Returns:
            BytesIO object containing the generated image data, or None if generation fails
        """
        try:
            # Create a detailed prompt for high-quality ingredient images using Pixar style
            prompt = f"""Ilustración 3D de alta definición de: {ingredient_name}, un ingrediente icónico de Perú.
Enfócate en representar fielmente sus características únicas basándote en esta descripción: "{descripcion}".
El estilo visual debe ser el de la comida en las películas de animación de Pixar: detallado, apetitoso y con volumen, usando colores vibrantes y texturas definidas.
Composición: Muestra un {ingredient_name} entero junto a otro cortado limpiamente por la mitad para revelar su interior.
Iluminación y Fondo: Utiliza una iluminación de estudio suave que resalte la frescura. El fondo debe ser minimalista, de un color gris claro neutro y desenfocado."""

            generation_config = {
                "response_modalities": ["TEXT", "IMAGE"],
                "temperature": 0.4,
            }

            response = self.image_gen_model.generate_content(
                prompt,
                generation_config=generation_config
            )

            # Extract and properly convert the image from the response
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    try:
                        # Get the image data
                        image_data = part.inline_data.data
                        
                        # If data is base64 string, decode it
                        if isinstance(image_data, str):
                            image_bytes = base64.b64decode(image_data)
                        else:
                            # If it's already bytes, use directly
                            image_bytes = image_data
                        
                        # Open the image with PIL to ensure it's valid and convert to JPG
                        with Image.open(BytesIO(image_bytes)) as img:
                            # Convert to RGB if necessary (removes alpha channel)
                            if img.mode in ('RGBA', 'LA', 'P'):
                                img = img.convert('RGB')
                            
                            # Create a new BytesIO object for the JPG
                            jpg_buffer = BytesIO()
                            img.save(jpg_buffer, format='JPEG', quality=90, optimize=True)
                            jpg_buffer.seek(0)
                            
                            print(f"✅ Successfully converted image for {ingredient_name} to JPG format")
                            return jpg_buffer
                            
                    except Exception as conversion_error:
                        print(f"🚨 Error converting image data for {ingredient_name}: {str(conversion_error)}")
                        continue
                        
            return None
            
        except Exception as e:
            print(f"🚨 Error generating image for {ingredient_name}: {str(e)}")
            return None

    def recognize_ingredients(self, images_files: List[IO[bytes]]) -> Dict[str, List[Dict[str, Any]]]:
        try:
            images = [Image.open(f) for f in images_files]
        except Exception as e:
            raise UnidentifiedImageException() from e
            
        prompt = """
        Actúa como un chef peruano experto en conservación de alimentos y análisis visual.
        Recibirás una **lista de imágenes** que puede contener uno o varios ingredientes.
        Considera estos datos para los campos de cada ingrediente:
        - name: nombre del ingrediente  
        - description: descripción detallada de las características físicas del ingrediente (color, textura, forma, tamaño, etc.)
        - quantity: estima la cantidad aproximada basándote en lo visible. 
        - type_unit: unidad de medida ('unidades', 'gramos', 'kilos', etc.)  
        - storage_type: tipo de almacenamiento ideal ('Refrigerado', 'Congelado' o 'Ambiente')  
        - expiration_time: tiempo aproximado antes de que se deteriore  
        - time_unit: unidad de tiempo para expiration_time ('Días', 'Semanas', 'Meses' o 'Años')  
        - tips: ofrece un consejo conciso y práctico para prolongar la vida útil del ingrediente, con un enfoque en técnicas caseras y efectivas.
        **Identifica y lista todos los ingredientes presentes** y devuelve únicamente un objeto JSON con esta estructura:
        {
          "ingredients": [
            {
              "name": "string",
              "description": "string",
              "quantity": number,
              "type_unit": "string",
              "storage_type": "string",
              "expiration_time": number,
              "time_unit": "string",
              "tips": "string"
            }
          ]
        }
        - NO incluyas saludos, explicaciones, marcas de código ni texto adicional. Solo entrega el JSON puro.
        """
        generation_config = {
            "temperature": 0.4,
        }
        response = self.model.generate_content([prompt] + images, generation_config=generation_config)
        raw = self._parse_response_text(response.text)
        ingredients = raw.get("ingredients", [])
        return {
            "ingredients": ingredients,
        }
    
    def recognize_foods(self, images_files: List[IO[bytes]]) -> Dict[str, List[Dict[str, Any]]]:
        try:
            images = [Image.open(f) for f in images_files]
        except Exception as e:
            raise UnidentifiedImageException() from e

        prompt = """
        Actúa como un chef peruano experto en cocina internacional y análisis visual de platos.
        Recibirás una imagen con uno o más platos preparados.
        Para cada plato identifica **únicamente** estos campos:
        
        - name: nombre del plato  
        - main_ingredients: lista de ingredientes principales (en español)  
        - category: tipo de plato ('Entrada', 'Plato principal', 'Postre', 'Bebida')  
        - calories: cantidad aproximada de calorías (solo si es razonable estimarlo)  
        - description: breve descripción del plato y su preparación típica  
        - storage_type: tipo de almacenamiento ideal ('Refrigerado', 'Congelado' o 'Ambiente')  
        - expiration_time: tiempo aproximado antes de que se deteriore  
        - time_unit: unidad de tiempo para expiration_time ('Días', 'Semanas', 'Meses' o 'Años')  
        - tips: consejo breve para conservarlo correctamente  
        - serving_quantity: cantidad de porciones que aparecen (en Platos)  
        
        Devuelve **únicamente** un JSON con esta estructura, sin saludos ni texto adicional:
        
        {
          "foods": [
            {
              "name": "string",                   # nombre del plato
              "main_ingredients": [               # lista de ingredientes principales (en español)
                "string",
                "..."
              ],
              "category": "string",               # Entrada, Plato principal, Postre o Bebida
              "calories": number,                 # solo si es razonable estimarlo
              "description": "string",            # breve descripción del plato
              "storage_type": "string",           # Refrigerado, Congelado o Ambiente
              "expiration_time": number,          # tiempo aproximado antes de deteriorarse
              "time_unit": "string",              # Días, Semanas, Meses o Años
              "tips": "string",                   # consejo breve de conservación
              "serving_quantity": number          # cantidad de porciones (Platos)
            }
            // ...más platos
          ]
        }
        """

        response = self.model.generate_content([prompt] + images, generation_config={"temperature": 0.4})
        raw = self._parse_response_text(response.text)
        foods = raw.get("foods", [])
        return {
            "foods": foods
        }
    
    def recognize_batch(self, images_files: List[IO[bytes]]) -> Dict[str, List]:
        try:
            images = [Image.open(f) for f in images_files]
        except Exception as e:
            raise UnidentifiedImageException() from e
    
        prompt = """
        Actúa como un chef peruano experto en cocina internacional, análisis visual de alimentos y conservación.
        Recibirás una lista de imágenes que pueden contener:
        1. Ingredientes (frutas, vegetales, carnes, etc.)
        2. Platos preparados (ceviche, arroz chaufa, etc.)
        
        **Analiza todas las imágenes** y devuelve **únicamente** un objeto JSON con dos arreglos separados:  
        
        — **ingredients**: para cada ingrediente detectado, incluye:
          - name: nombre del ingrediente  
          - description: descripción detallada de las características físicas del ingrediente (color, textura, forma, tamaño, etc.)
          - quantity: cantidad aproximada  
          - type_unit: unidad de medida ('unidades', 'gramos', 'kilos', etc.)  
          - storage_type: tipo de almacenamiento ideal ('Refrigerado', 'Congelado' o 'Ambiente')  
          - expiration_time: tiempo aproximado antes de deteriorarse  
          - time_unit: unidad de tiempo ('Días', 'Semanas', 'Meses' o 'Años')  
          - tips: consejo breve para conservarlo correctamente  
        
        — **foods**: para cada plato preparado detectado, incluye:
          - name: nombre del plato  
          - main_ingredients: lista de ingredientes principales (en español)  
          - category: tipo de plato ('Entrada', 'Plato principal', 'Postre', 'Bebida')  
          - calories: calorías aproximadas (solo si es razonable estimarlo)  
          - description: breve descripción del plato y su preparación típica  
          - storage_type: tipo de almacenamiento ideal ('Refrigerado', 'Congelado' o 'Ambiente')  
          - expiration_time: tiempo aproximado antes de deteriorarse  
          - time_unit: unidad de tiempo ('Días', 'Semanas', 'Meses' o 'Años')  
          - tips: consejo breve para conservarlo correctamente  
          - serving_quantity: cantidad de porciones que aparecen (en Platos)  
        
        Devuelve solo el JSON con esta estructura, sin saludos, sin explicaciones ni marcas de código:
        
        {
          "ingredients": [
            {
              "name": "string",
              "description": "string",
              "quantity": number,
              "type_unit": "string",
              "storage_type": "string",
              "expiration_time": number,
              "time_unit": "string",
              "tips": "string"
            }
            // ...más ingredientes
          ],
          "foods": [
            {
              "name": "string",
              "main_ingredients": ["string", "..."],
              "category": "string",
              "calories": number,
              "description": "string",
              "storage_type": "string",
              "expiration_time": number,
              "time_unit": "string",
              "tips": "string",
              "serving_quantity": number
            }
            // ...más platos
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

    def analyze_environmental_impact(self, ingredient_name: str) -> Dict[str, Any]:
        """
        Analiza el impacto ambiental de un ingrediente específico.
        """
        prompt = f"""
        Actúa como un experto en sostenibilidad alimentaria y análisis de ciclo de vida.
        
        Para el ingrediente: {ingredient_name}
        
        Analiza su impacto ambiental considerando:
        - Huella de carbono promedio desde la producción hasta el consumo
        - Huella hídrica necesaria para su producción
        - Considera el contexto peruano y regional
        
        Devuelve únicamente un JSON con esta estructura:
        {{
          "environmental_impact": {{
            "carbon_footprint": {{
              "value": number,
              "unit": "kg",
              "description": "CO2"
            }},
            "water_footprint": {{
              "value": number,
              "unit": "l",
              "description": "agua"
            }},
            "sustainability_message": "string"
          }}
        }}
        
        - Los valores deben ser aproximados pero realistas
        - carbon_footprint.value: kg de CO2 equivalente para producir 1kg del ingrediente
        - water_footprint.value: litros de agua necesarios para producir 1kg del ingrediente
        - sustainability_message: mensaje breve sobre cómo reducir el impacto ambiental
        - NO incluyas saludos, explicaciones ni texto adicional. Solo el JSON.
        """
        
        generation_config = {"temperature": 0.3}
        response = self.model.generate_content(prompt, generation_config=generation_config)
        return self._parse_response_text(response.text)

    def generate_utilization_ideas(self, ingredient_name: str, description: str = "") -> Dict[str, Any]:
        """
        Genera ideas de aprovechamiento para un ingrediente específico.
        """
        prompt = f"""
        Actúa como un chef peruano experto en aprovechamiento de alimentos y reducción del desperdicio.
        
        Para el ingrediente: {ingredient_name}
        Descripción: {description}
        
        Genera ideas prácticas de aprovechamiento considerando:
        - Formas de usar el ingrediente cuando está fresco
        - Técnicas de conservación caseras
        - Maneras de aprovechar partes que normalmente se descartan
        - Recetas o preparaciones específicas de la cocina peruana
        
        Devuelve únicamente un JSON con esta estructura:
        {{
          "utilization_ideas": [
            {{
              "title": "string",
              "description": "string",
              "type": "string"
            }}
          ]
        }}
        
        - Incluye 3-4 ideas diferentes
        - title: nombre corto de la idea (ej: "Congelar en porciones pequeñas")
        - description: explicación práctica de cómo implementarla
        - type: categoría ("conservación", "preparación", "aprovechamiento" o "reciclaje")
        - Enfócate en técnicas caseras y efectivas
        - NO incluyas saludos, explicaciones ni texto adicional. Solo el JSON.
        """
        
        generation_config = {"temperature": 0.5}
        response = self.model.generate_content(prompt, generation_config=generation_config)
        return self._parse_response_text(response.text)

    def recognize_ingredients_complete(self, images_files: List[IO[bytes]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Reconoce ingredientes con información completa: básica + impacto ambiental + aprovechamiento
        TODO PROCESADO EN PARALELO PARA MÁXIMA VELOCIDAD
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # 1. Reconocimiento básico
        basic_result = self.recognize_ingredients(images_files)
        
        print(f"🚀 Processing complete data for {len(basic_result['ingredients'])} ingredients in parallel...")
        
        # 2. Función para enriquecer cada ingrediente en paralelo
        def enrich_ingredient(ingredient_data):
            ingredient_name, ingredient_description = ingredient_data
            
            try:
                print(f"🧠 [Thread] Processing complete data for: {ingredient_name}")
                
                # Procesar environmental impact y utilization ideas en paralelo dentro del thread
                environmental_data = self.analyze_environmental_impact(ingredient_name)
                utilization_data = self.generate_utilization_ideas(ingredient_name, ingredient_description)
                
                print(f"✅ [Thread] Complete data ready for {ingredient_name}")
                return ingredient_name, environmental_data, utilization_data, None
                
            except Exception as e:
                print(f"🚨 [Thread] Error enriching {ingredient_name}: {str(e)}")
                # Datos por defecto
                environmental_data = {
                    "environmental_impact": {
                        "carbon_footprint": {"value": 0.0, "unit": "kg", "description": "CO2"},
                        "water_footprint": {"value": 0, "unit": "l", "description": "agua"},
                        "sustainability_message": "Consume de manera responsable y evita el desperdicio."
                    }
                }
                utilization_data = {
                    "utilization_ideas": [
                        {
                            "title": "Consume fresco",
                            "description": "Utiliza el ingrediente lo antes posible para aprovechar sus nutrientes.",
                            "type": "conservación"
                        }
                    ]
                }
                return ingredient_name, environmental_data, utilization_data, str(e)
        
        # 3. Procesar todos los ingredientes en paralelo (máximo 4 threads para Gemini)
        enrichment_results = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Preparar datos para threads
            thread_data = [
                (ingredient["name"], ingredient.get("description", "")) 
                for ingredient in basic_result["ingredients"]
            ]
            
            # Enviar todas las tareas
            future_to_ingredient = {
                executor.submit(enrich_ingredient, data): data[0] 
                for data in thread_data
            }
            
            # Recoger resultados
            for future in as_completed(future_to_ingredient):
                ingredient_name, environmental_data, utilization_data, error = future.result()
                enrichment_results[ingredient_name] = {
                    "environmental": environmental_data,
                    "utilization": utilization_data,
                    "error": error
                }
                
                if error:
                    print(f"⚠️ Fallback data used for {ingredient_name}")
                else:
                    print(f"🎯 Complete enrichment ready for {ingredient_name}")
        
        # 4. Aplicar resultados a los ingredientes originales
        for ingredient in basic_result["ingredients"]:
            ingredient_name = ingredient["name"]
            if ingredient_name in enrichment_results:
                result = enrichment_results[ingredient_name]
                ingredient.update(result["environmental"])
                ingredient.update(result["utilization"])
                print(f"✅ Applied complete data to {ingredient_name}")
        
        print(f"🎉 All {len(basic_result['ingredients'])} ingredients enriched with parallel processing!")
        return basic_result