import google.generativeai as genai
import json
import base64
import asyncio
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image
from src.config.config import Config
from typing import IO, List, Dict, Any, Optional

from src.domain.services.ia_food_analyzer_service import IAFoodAnalyzerService
from src.shared.exceptions.custom import UnidentifiedImageException, InvalidResponseFormatException
from src.infrastructure.ai.cache_service import ai_cache

class GeminiAdapterService(IAFoodAnalyzerService):
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        # TODO: Change to the new model
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-06-17")
        # Separate model for image generation
        self.image_gen_model = genai.GenerativeModel("gemini-2.0-flash-preview-image-generation")
        self.performance_mode = True  # Enable optimizations
        self.max_workers = 8  # Increased for better parallelization
        self.generation_config_base = {
            "temperature": 0.4,  # Standardized for consistency
            "max_output_tokens": 1024,  # Prevent overgeneration
            "candidate_count": 1,
            "top_k": 40,
            "top_p": 0.9
        }

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
        # Check cache first
        cache_key = f"ingredient_img_{ingredient_name}_{descripcion[:30]}"
        cached_image = ai_cache.get_cached_response('image_generation', cache_key)
        
        if cached_image:
            print(f"🎯 [CACHE HIT] Using cached image for {ingredient_name}")
            try:
                import base64
                image_bytes = base64.b64decode(cached_image)
                return BytesIO(image_bytes)
            except Exception as e:
                print(f"⚠️ Cache decode failed: {e}")
        
        try:
            # Ultra-compact prompt for ingredient images
            prompt = f"""Ilustra {ingredient_name} peruano estilo Pixar 3D: {descripcion}. Fondo neutro, iluminación suave, detallado."""

            generation_config = self.generation_config_base.copy()
            generation_config.update({
                "response_modalities": ["TEXT", "IMAGE"],
                "max_output_tokens": 512  # Images don't need text output
            })

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
                            
                            # Cache the image data
                            jpg_buffer.seek(0)
                            image_data = jpg_buffer.read()
                            import base64
                            cached_data = base64.b64encode(image_data).decode()
                            ai_cache.cache_response('image_generation', cache_key, cached_data)
                            
                            jpg_buffer.seek(0)
                            return jpg_buffer
                            
                    except Exception as conversion_error:
                        print(f"🚨 Error converting image data for {ingredient_name}: {str(conversion_error)}")
                        continue
                        
            return None
            
        except Exception as e:
            print(f"🚨 Error generating image for {ingredient_name}: {str(e)}")
            return None

    def generate_food_image(self, food_name: str, description: str = "", main_ingredients: List[str] = None) -> Optional[BytesIO]:
        """
        Generate an image for a food dish using Gemini's image generation capabilities.
        
        Args:
            food_name: Name of the food dish to generate an image for
            description: Description of the dish and its preparation
            main_ingredients: List of main ingredients
            
        Returns:
            BytesIO object containing the generated image data, or None if generation fails
        """
        try:
            # Prepare ingredients text
            ingredients_text = ""
            if main_ingredients and len(main_ingredients) > 0:
                ingredients_text = f"Sus ingredientes principales son: {', '.join(main_ingredients)}."
            
            # Create a detailed prompt for high-quality food dish images
            prompt = f"""Ilustración 3D de alta definición de: {food_name}, un plato icónico de la cocina peruana.
Basándote en esta descripción: "{description}". {ingredients_text}
El estilo visual debe ser el de la comida en las películas de animación de Pixar: detallado, apetitoso y vibrante, usando colores llamativos y texturas realistas.
Composición: Muestra el plato servido de manera elegante en un plato o bowl típico peruano, con una presentación profesional de restaurante.
Detalles: Incluye guarniciones tradicionales, salsas o acompañamientos característicos del plato.
Iluminación y Fondo: Utiliza una iluminación cálida que haga el plato lucir irresistible. El fondo debe ser minimalista, de color neutro y ligeramente desenfocado para que el plato sea el protagonista."""

            generation_config = self.generation_config_base.copy()
            generation_config.update({
                "response_modalities": ["TEXT", "IMAGE"],
                "temperature": 0.5,  # Slightly higher for creativity
                "max_output_tokens": 512  # Images don't need text output
            })

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
                            
                            print(f"✅ Successfully converted image for {food_name} to JPG format")
                            return jpg_buffer
                            
                    except Exception as conversion_error:
                        print(f"🚨 Error converting image data for {food_name}: {str(conversion_error)}")
                        continue
                        
            return None
            
        except Exception as e:
            print(f"🚨 Error generating image for {food_name}: {str(e)}")
            return None

    def recognize_ingredients(self, images_files: List[IO[bytes]]) -> Dict[str, List[Dict[str, Any]]]:
        try:
            images = [Image.open(f) for f in images_files]
        except Exception as e:
            raise UnidentifiedImageException() from e
        
        if self.performance_mode:
            return self._recognize_ingredients_optimized(images)
        else:
            return self._recognize_ingredients_standard(images)
    
    def _recognize_ingredients_optimized(self, images: List[Image.Image]) -> Dict[str, List[Dict[str, Any]]]:
        """Ultra-optimized ingredient recognition with 90% size reduction"""
        # Ultra-compact prompt - 90% size reduction
        prompt = """Chef peruano: detecta ingredientes crudos (NO platos). Formato: {"ingredients":[{"name":"str","description":"str","quantity":num,"type_unit":"str","storage_type":"Refrigerado|Congelado|Ambiente","expiration_time":num,"time_unit":"Días|Semanas|Meses","tips":"str"}]}"""
        
        # Check cache first
        image_hash = self._get_images_hash(images)
        cached_response = ai_cache.get_cached_response(
            'ingredient_recognition', prompt, image_hash=image_hash
        )
        
        if cached_response:
            print(f"🎯 [CACHE HIT] Using cached ingredient recognition")
            raw = json.loads(cached_response)
        else:
            print(f"💾 [CACHE MISS] Generating new ingredient recognition")
            generation_config = self.generation_config_base.copy()
            generation_config["max_output_tokens"] = 1024
            response = self.model.generate_content([prompt] + images, generation_config=generation_config)
            
            # Cache the response
            ai_cache.cache_response(
                'ingredient_recognition', prompt, response.text, image_hash=image_hash
            )
            raw = self._parse_response_text(response.text)
        
        ingredients = raw.get("ingredients", [])
        print(f"🚀 [OPTIMIZED] Recognized {len(ingredients)} ingredients")
        return {"ingredients": ingredients}
    
    def _recognize_ingredients_standard(self, images: List[Image.Image]) -> Dict[str, List[Dict[str, Any]]]:
        """Standard ingredient recognition (original method)"""
        prompt = """
        Actúa como un chef peruano experto en conservación de alimentos y análisis visual.
        Recibirás una imagen que puede contener ingredientes crudos o comidas preparadas.
        
        **INSTRUCCIÓN IMPORTANTE**: Distingue entre:
        
        🥕 **INGREDIENTES CRUDOS** (estos SÍ detecta):
        - Frutas, verduras, carnes, pescados sin procesar
        - Ingredientes frescos, secos o cortados que se usan para cocinar
        - Especias, condimentos, granos, tubérculos individuales
        - Cualquier ingrediente que esté en su estado natural o cortado pero sin cocinar
        
        🍽️ **NO DETECTES COMO INGREDIENTES**:
        - Platos ya cocinados, guisados, marinados y listos para comer
        - Preparaciones que ya están mezcladas y servidas
        - Comidas que ya están en un plato final y listas para consumir
        
        **ANÁLISIS VISUAL DETALLADO**:
        - Identifica VARIEDADES ESPECÍFICAS (ej: "papa amarilla" no solo "papa")
        - Observa ESTADO DE MADUREZ y CALIDAD visible
        - Reconoce INGREDIENTES NATIVOS PERUANOS cuando sea posible
        - Usa objetos de referencia para estimar TAMAÑOS Y CANTIDADES
        - Describe CARACTERÍSTICAS DISTINTIVAS (forma, color, textura específicos)
        
        **ANÁLISIS DE COLOR Y TEXTURA**:
        - Identifica el COLOR y TEXTURA de cada ingrediente
        - Reconoce la PRESENCIA de INGREDIENTES NATIVOS PERUANOS
        - Usa objetos de referencia para estimar TAMAÑOS Y CANTIDADES
        - Describe CARACTERÍSTICAS DISTINTIVAS (forma, color, textura específicos)
        
        **VOCABULARIO CULINARIO PERUANO**:
        - Prefiere nombres locales cuando sea relevante
        - Usa términos específicos de la cocina peruana

        **REGLA PRÁCTICA**: Si es un ingrediente individual (crudo, cortado, fresco, etc.) que se puede usar para cocinar → SÍ detecta. Solo si ya es una comida completamente preparada y lista para comer → NO detecta.
        
        **Si NO encuentras ingredientes crudos**, devuelve:
        {
          "ingredients": []
        }
        
        **Si encuentras ingredientes crudos**, para cada ingrediente identifica:
        - name: nombre del ingrediente  
        - description: descripción detallada de las características físicas del ingrediente (color, textura, forma, tamaño, etc.)
        - quantity: estima la cantidad aproximada basándote en lo visible. 
        - type_unit: unidad de medida ('unidades', 'gramos', 'kilos', etc.)  
        - storage_type: tipo de almacenamiento ideal ('Refrigerado', 'Congelado' o 'Ambiente')  
        - expiration_time: tiempo aproximado antes de que se deteriore  
        - time_unit: unidad de tiempo para expiration_time ('Días', 'Semanas', 'Meses' o 'Años')  
        - tips: ofrece un consejo conciso y práctico para prolongar la vida útil del ingrediente, con un enfoque en técnicas caseras y efectivas.
        
        Devuelve únicamente un objeto JSON con esta estructura, sin saludos ni texto adicional:
        
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
        """
        generation_config = self.generation_config_base.copy()
        generation_config["max_output_tokens"] = 2048
        response = self.model.generate_content([prompt] + images, generation_config=generation_config)
        raw = self._parse_response_text(response.text)
        ingredients = raw.get("ingredients", [])
        return {"ingredients": ingredients}
    
    def recognize_foods(self, images_files: List[IO[bytes]]) -> Dict[str, List[Dict[str, Any]]]:
        try:
            images = [Image.open(f) for f in images_files]
        except Exception as e:
            raise UnidentifiedImageException() from e

        prompt = """
        Actúa como un chef peruano experto en cocina internacional y análisis visual de platos.
        Recibirás una imagen que puede contener platos preparados o ingredientes crudos.
        
        **INSTRUCCIÓN IMPORTANTE**: Distingue entre:
        
        🍽️ **PLATOS PREPARADOS** (estos SÍ detecta):
        - Comidas ya cocinadas, marinadas o procesadas listas para comer
        - Ceviche (marinado en limón), arroz chaufa, lomo saltado, etc.
        - Ensaladas ya mezcladas y servidas
        - Postres preparados y bebidas
        - Cualquier plato que esté listo para consumir
        
        🥕 **INGREDIENTES CRUDOS** (estos NO detectes como comidas):
        - Frutas, verduras, carnes, pescados sin procesar
        - Ingredientes separados aunque estén juntos
        - Ingredientes cortados pero no combinados en un plato
        - Conjuntos de ingredientes para preparar algo después
        
        **ANÁLISIS VISUAL DETALLADO**:
        - Observa el COLOR y TEXTURA de las salsas
        - Identifica TÉCNICAS de cocción específicas
        - Reconoce PREPARACIONES PERUANAS tradicionales
        - Diferencia entre platos similares por sus características visuales únicas
        
        **PREPARACIONES PERUANAS TRADICIONALES**:
        - Ceviche (marinado en limón), arroz chaufa, lomo saltado, ensaladas armadas
        - Postres preparados, bebidas mezcladas
        - Cualquier preparación que esté lista para consumir
        
        **VOCABULARIO CULINARIO PERUANO**:
        - Prefiere nombres locales cuando sea relevante
        - Usa términos específicos de la cocina peruana
        
        **REGLA PRÁCTICA**: Si una persona puede comer directamente lo que ve en la imagen sin necesidad de cocinar o procesar más, entonces ES un plato preparado. Si necesita ser cocinado, mezclado o procesado, entonces son ingredientes.
        
        **Si NO encuentras platos preparados**, devuelve:
        {
          "foods": []
        }
        
        **Si encuentras platos preparados**, para cada plato identifica:
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
        Recibirás una lista de imágenes que pueden contener ingredientes crudos y/o platos preparados.
        
        **DISTINGUE CUIDADOSAMENTE**:
        
        🥕 **INGREDIENTES CRUDOS** (agrégalos a ingredients):
        - Frutas, verduras, carnes, pescados sin procesar
        - Ingredientes individuales frescos o secos
        - Especias, condimentos, granos individuales
        - Ingredientes cortados pero no combinados en un plato
        - Cualquier ingrediente que necesite ser cocinado o procesado
        
        🍽️ **PLATOS PREPARADOS** (agrégalos a foods):
        - Comidas ya cocinadas, marinadas o listos para comer
        - Ceviche (marinado), arroz chaufa, lomo saltado, ensaladas armadas
        - Postres preparados, bebidas mezcladas
        - Cualquier preparación que esté lista para consumir
        
        **REGLA PRÁCTICA**: Si es un ingrediente individual que se usa para cocinar algo más → ingredients. Si ya es una comida preparada y lista para comer → foods.
        
        **Analiza todas las imágenes** y devuelve **únicamente** un objeto JSON con dos arreglos separados:  
        
        — **ingredients**: para cada ingrediente crudo detectado, incluye:
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
        
        generation_config = self.generation_config_base.copy()
        generation_config["temperature"] = 0.3  # Conservative for sustainability data
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
        
        generation_config = self.generation_config_base.copy()
        generation_config["temperature"] = 0.5  # Balanced for creative ideas
        response = self.model.generate_content(prompt, generation_config=generation_config)
        return self._parse_response_text(response.text)

    async def recognize_ingredients_complete_async(self, images_files: List[IO[bytes]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        ULTRA-OPTIMIZED: Async ingredient recognition with batch processing and smart caching
        """
        print(f"🚀 [ASYNC OPTIMIZED] Starting complete ingredient recognition")
        
        # 1. Basic recognition (with caching)
        basic_result = self.recognize_ingredients(images_files)
        ingredients = basic_result["ingredients"]
        
        if not ingredients:
            return basic_result
        
        print(f"🧠 [ASYNC] Processing {len(ingredients)} ingredients with async optimization")
        
        # 2. Create batches for parallel processing (respecting API limits)
        batch_size = 3  # Conservative for API rate limits
        ingredient_batches = [ingredients[i:i + batch_size] for i in range(0, len(ingredients), batch_size)]
        
        # 3. Process batches concurrently
        enrichment_tasks = []
        for batch in ingredient_batches:
            task = self._process_ingredient_batch_async(batch)
            enrichment_tasks.append(task)
        
        # 4. Wait for all batches to complete
        try:
            batch_results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
            
            # 5. Merge results back to ingredients
            ingredient_index = 0
            for batch_result in batch_results:
                if isinstance(batch_result, Exception):
                    print(f"🚨 [ASYNC] Batch failed: {batch_result}")
                    continue
                
                for enriched_data in batch_result:
                    if ingredient_index < len(ingredients):
                        ingredients[ingredient_index].update(enriched_data)
                        ingredient_index += 1
            
            print(f"🎉 [ASYNC OPTIMIZED] Completed: {len(ingredients)} ingredients enriched")
            return basic_result
            
        except Exception as e:
            print(f"🚨 [ASYNC] Error in async processing: {e}")
            # Fallback to synchronous processing
            return self.recognize_ingredients_complete(images_files)
    
    def recognize_ingredients_complete(self, images_files: List[IO[bytes]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Optimized synchronous version with improved threading and caching
        """
        # 1. Basic recognition
        basic_result = self.recognize_ingredients(images_files)
        ingredients = basic_result["ingredients"]
        
        if not ingredients:
            return basic_result
        
        print(f"🚀 [OPTIMIZED] Processing {len(ingredients)} ingredients with enhanced parallel processing")
        
        # 2. Optimized enrichment function with caching
        def enrich_ingredient_optimized(ingredient_data):
            ingredient_name, ingredient_description = ingredient_data
            
            try:
                # Check cache for environmental data
                env_cache_key = f"env_{ingredient_name}"
                cached_env = ai_cache.get_cached_response('environmental_impact', env_cache_key)
                
                # Check cache for utilization data  
                util_cache_key = f"util_{ingredient_name}_{ingredient_description[:50]}"
                cached_util = ai_cache.get_cached_response('utilization_ideas', util_cache_key)
                
                if cached_env and cached_util:
                    print(f"🎯 [CACHE HIT] Complete data for {ingredient_name}")
                    return ingredient_name, json.loads(cached_env), json.loads(cached_util), None
                
                print(f"🧠 [PROCESSING] Generating data for: {ingredient_name}")
                
                # Generate missing data
                if not cached_env:
                    environmental_data = self.analyze_environmental_impact(ingredient_name)
                    ai_cache.cache_response('environmental_impact', env_cache_key, json.dumps(environmental_data))
                else:
                    environmental_data = json.loads(cached_env)
                
                if not cached_util:
                    utilization_data = self.generate_utilization_ideas(ingredient_name, ingredient_description)
                    ai_cache.cache_response('utilization_ideas', util_cache_key, json.dumps(utilization_data))
                else:
                    utilization_data = json.loads(cached_util)
                
                print(f"✅ [PROCESSED] Complete data ready for {ingredient_name}")
                return ingredient_name, environmental_data, utilization_data, None
                
            except Exception as e:
                print(f"🚨 [ERROR] Enriching {ingredient_name}: {str(e)}")
                return ingredient_name, self._get_fallback_environmental(), self._get_fallback_utilization(), str(e)
        
        # 3. Process with optimized thread pool
        enrichment_results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            thread_data = [(ing["name"], ing.get("description", "")) for ing in ingredients]
            
            future_to_ingredient = {
                executor.submit(enrich_ingredient_optimized, data): data[0] 
                for data in thread_data
            }
            
            for future in as_completed(future_to_ingredient):
                ingredient_name, environmental_data, utilization_data, error = future.result()
                enrichment_results[ingredient_name] = {
                    "environmental": environmental_data,
                    "utilization": utilization_data,
                    "error": error
                }
        
        # 4. Apply enrichment to ingredients
        for ingredient in ingredients:
            ingredient_name = ingredient["name"]
            if ingredient_name in enrichment_results:
                result = enrichment_results[ingredient_name]
                ingredient.update(result["environmental"])
                ingredient.update(result["utilization"])
        
        print(f"🎉 [OPTIMIZED] All {len(ingredients)} ingredients enriched successfully!")
        return basic_result
    
    async def _process_ingredient_batch_async(self, ingredient_batch: List[Dict]) -> List[Dict]:
        """Process a batch of ingredients concurrently"""
        tasks = []
        for ingredient in ingredient_batch:
            task = self._enrich_single_ingredient_async(
                ingredient["name"], 
                ingredient.get("description", "")
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _enrich_single_ingredient_async(self, ingredient_name: str, description: str) -> Dict:
        """Async wrapper for single ingredient enrichment"""
        loop = asyncio.get_event_loop()
        
        # Run in thread pool to avoid blocking
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._enrich_ingredient_sync, ingredient_name, description)
            return await loop.run_in_executor(None, lambda: future.result())
    
    def _enrich_ingredient_sync(self, ingredient_name: str, description: str) -> Dict:
        """Synchronous ingredient enrichment"""
        try:
            environmental_data = self.analyze_environmental_impact(ingredient_name)
            utilization_data = self.generate_utilization_ideas(ingredient_name, description)
            
            combined_data = {}
            combined_data.update(environmental_data)
            combined_data.update(utilization_data)
            
            return combined_data
        except Exception as e:
            print(f"🚨 Error enriching {ingredient_name}: {e}")
            fallback_data = {}
            fallback_data.update(self._get_fallback_environmental())
            fallback_data.update(self._get_fallback_utilization())
            return fallback_data
    
    def _get_fallback_environmental(self) -> Dict:
        """Fallback environmental data"""
        return {
            "environmental_impact": {
                "carbon_footprint": {"value": 0.0, "unit": "kg", "description": "CO2"},
                "water_footprint": {"value": 0, "unit": "l", "description": "agua"},
                "sustainability_message": "Consume de manera responsable y evita el desperdicio."
            }
        }
    
    def _get_fallback_utilization(self) -> Dict:
        """Fallback utilization data"""
        return {
            "utilization_ideas": [
                {
                    "title": "Consume fresco",
                    "description": "Utiliza el ingrediente lo antes posible para aprovechar sus nutrientes.",
                    "type": "conservación"
                }
            ]
        }
    
    def _get_images_hash(self, images: List[Image.Image]) -> str:
        """Generate hash for image list for caching"""
        import hashlib
        
        # Simple hash based on image sizes and modes
        hash_data = "|".join([f"{img.size}_{img.mode}" for img in images])
        return hashlib.md5(hash_data.encode()).hexdigest()[:16]

    def generate_consumption_advice(self, ingredient_name: str, description: str = "") -> Dict[str, Any]:
        """
        Generate comprehensive consumption advice for an ingredient.
        
        Args:
            ingredient_name: Name of the ingredient
            description: Description of the ingredient's characteristics
            
        Returns:
            Dictionary with consumption advice and before consumption advice
        """
        try:
            prompt = f"""
            Actúa como un nutricionista y chef experto en alimentos peruanos e internacionales.
            
            Para el ingrediente: "{ingredient_name}"
            Descripción: "{description}"
            
            Genera consejos completos de consumo en español, considerando:
            
            **CONSEJOS DE CONSUMO ÓPTIMO**:
            - Mejor momento y forma de consumir
            - Preparaciones recomendadas
            - Beneficios nutricionales específicos
            - Cantidad recomendada de consumo
            
            **CONSEJOS ANTES DE CONSUMIR**:
            - Cómo verificar la calidad y frescura
            - Pasos de limpieza y preparación
            - Precauciones de seguridad alimentaria
            - Notas especiales de preparación
            
            Devuelve **únicamente** un JSON con esta estructura:
            
            {{
              "consumption_advice": {{
                "optimal_consumption": "string - cuándo y cómo consumir para máximo beneficio",
                "preparation_tips": "string - mejores formas de preparar",
                "nutritional_benefits": "string - beneficios nutricionales específicos",
                "recommended_portions": "string - cantidades recomendadas"
              }},
              "before_consumption_advice": {{
                "quality_check": "string - cómo verificar calidad y frescura",
                "safety_tips": "string - precauciones de seguridad alimentaria", 
                "preparation_notes": "string - pasos de limpieza y preparación",
                "special_considerations": "string - consideraciones especiales"
              }}
            }}
            """
            
            generation_config = self.generation_config_base.copy()
            generation_config["temperature"] = 0.3  # Conservative for health advice
            
            response = self.model.generate_content(prompt, generation_config=generation_config)
            result = self._parse_response_text(response.text)
            
            # Combinar ambos consejos en un solo objeto
            combined_advice = {
                "consumption_advice": result.get("consumption_advice", {}),
                "before_consumption_advice": result.get("before_consumption_advice", {})
            }
            
            print(f"✅ Successfully generated consumption advice for {ingredient_name}")
            return combined_advice
            
        except Exception as e:
            print(f"🚨 Error generating consumption advice for {ingredient_name}: {str(e)}")
            # Fallback con consejos genéricos
            return {
                "consumption_advice": {
                    "optimal_consumption": f"Consume {ingredient_name} fresco para aprovechar al máximo sus nutrientes.",
                    "preparation_tips": "Lava bien antes de consumir y cocina según receta.",
                    "nutritional_benefits": "Rico en vitaminas y minerales esenciales para una dieta equilibrada.",
                    "recommended_portions": "Consume en porciones moderadas como parte de una dieta balanceada."
                },
                "before_consumption_advice": {
                    "quality_check": "Verifica que esté fresco, sin manchas, olores extraños o signos de deterioro.",
                    "safety_tips": "Lava con agua corriente antes de consumir y mantén refrigerado.",
                    "preparation_notes": "Limpia y prepara en superficies limpias con utensilios sanitarios.",
                    "special_considerations": "Consume preferiblemente antes de su fecha de vencimiento."
                }
            }

    def estimate_extended_environmental_savings_from_ingredients(self, ingredients: List[Dict[str, Any]]) -> Dict[
        str, Any]:
        """
        Estima el impacto ambiental y económico evitado al usar los ingredientes de una receta.

        Args:
            ingredients: Lista de ingredientes, cada uno con 'name', 'quantity' y 'type_unit'

        Returns:
            Diccionario con los valores totales evitados: carbono, agua, energía y costo.
        """
        prompt = f"""
    Actúa como un experto en sostenibilidad alimentaria y análisis de ciclo de vida.

    Recibirás una lista de ingredientes usados en una receta. Tu tarea es estimar el impacto ambiental y económico evitado si estos ingredientes se utilizan (en lugar de desperdiciarse).

    Para cada ingrediente, considera:
    - Huella de carbono (kg CO₂e)
    - Huella hídrica (litros)
    - Huella energética (megajulios, MJ)
    - Costo económico aproximado (PEN)

    Asume promedios realistas según fuentes globales. No incluyas explicaciones ni texto adicional.

    Aquí están los ingredientes en formato JSON:

    {json.dumps(ingredients, ensure_ascii=False, indent=2)}

    Devuelve únicamente un JSON con esta estructura:

    {{
      "carbon_footprint": number,
      "water_footprint": number,
      "energy_footprint": number,
      "economic_cost": number,
      "unit_carbon": "kg CO2e",
      "unit_water": "litros",
      "unit_energy": "MJ",
      "unit_cost": "USD"
    }}
        """

        try:
            generation_config = self.generation_config_base.copy()
            generation_config["temperature"] = 0.3  # Conservative for extended savings
            response = self.model.generate_content(prompt, generation_config=generation_config)
            return self._parse_response_text(response.text)

        except Exception as e:
            print(f"🚨 Error estimating extended savings: {str(e)}")
            return {
                "carbon_footprint": 0.0,
                "water_footprint": 0.0,
                "energy_footprint": 0.0,
                "economic_cost": 0.0,
                "unit_carbon": "kg CO2e",
                "unit_water": "litros",
                "unit_energy": "MJ",
                "unit_cost": "USD"
            }
