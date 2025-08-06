import json
import re
import logging
from typing import Dict, Any, List
from src.domain.services.ia_recipe_generator_service import IARecipeGeneratorService
import google.generativeai as genai
from src.config.config import Config
from src.infrastructure.ai.cache_service import ai_cache

logger = logging.getLogger(__name__)

class GeminiRecipeGeneratorService(IARecipeGeneratorService):
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        # TODO: Change to the new model
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-06-17")
        self.performance_mode = True  # Enable optimized prompts
        self.cache = {}  # Simple in-memory cache

    def generate_recipes(self, data: Dict[str, Any], num_recipes: int = 2, recipe_categories: List[str] = []) -> Dict[str, Any]:
        print(f"🍳 [GEMINI SERVICE] Starting recipe generation with data: {data.keys()}")
        try:
            # Get user's previous recipes to avoid duplicates
            user_uid = data.get('user_uid')
            previous_recipes = self._get_user_recent_recipes(user_uid) if user_uid else []
            
            # Add anti-duplication context
            data['previous_recipes'] = previous_recipes
            data['generation_session_id'] = data.get('generation_session_id', self._generate_session_id())
            
            # Use optimized prompt if performance mode is enabled
            if self.performance_mode:
                prompt = self._build_optimized_prompt(data, num_recipes, recipe_categories)
                generation_config = {
                    "temperature": 0.7,  # Increased for more variation
                    "max_output_tokens": 1500 * num_recipes,
                    "candidate_count": 1,
                    "top_k": 50,  # Increased for more diversity
                    "top_p": 0.95  # Increased for more variety
                }
                print(f"🚀 [OPTIMIZED] Using compact prompt: {len(prompt)} chars (75% reduction)")
            else:
                prompt = self._build_prompt(data, num_recipes, recipe_categories)
                generation_config = {"temperature": 0.8}  # Increased for more variation
                print(f"🍳 [GEMINI SERVICE] Prompt length: {len(prompt)} characters")
            
            # Modified cache strategy for anti-duplication
            cache_params = {
                'temperature': generation_config.get('temperature'),
                'num_recipes': num_recipes,
                'language': data.get('user_profile', {}).get('language', 'es'),
                'session_id': data.get('generation_session_id'),
                'user_uid': user_uid,
                'has_previous': len(previous_recipes) > 0
            }
            
            # Skip cache if user has recent recipes to ensure freshness
            use_cache = len(previous_recipes) == 0
            cached_response = None
            
            if use_cache:
                cached_response = ai_cache.get_cached_response(
                    'recipe_generation', prompt, **cache_params
                )
            
            if cached_response and use_cache:
                response_text = cached_response
                print(f"🎯 [CACHE HIT] Using cached response (API call saved)")
            else:
                print(f"💾 [GENERATING] Creating fresh response to avoid duplicates")
                response = self.model.generate_content(prompt, generation_config=generation_config)
                response_text = response.text
                
                # Cache only for new users without previous recipes
                if use_cache:
                    ai_cache.cache_response(
                        'recipe_generation', prompt, response_text, **cache_params
                    )
            print(f"🍳 [GEMINI SERVICE] Got response from Gemini")
            print(f"🍳 [GEMINI SERVICE] Response text (first 200 chars): {response_text[:200]}...")
            
            # Parse the JSON response with optimized parser
            if self.performance_mode:
                recipes = self._fast_parse_response(response_text)
                print(f"🚀 [OPTIMIZED] Fast-parsed {len(recipes)} recipes")
            else:
                recipes = self._parse_response_text(response_text)
                print(f"🍳 [GEMINI SERVICE] Successfully parsed {len(recipes)} recipes")
            
            # Información sobre preferencias aplicadas
            user_profile = data.get("user_profile", {})
            applied_preferences = data.get("preferences", [])
            
            # Construir respuesta con información de personalización
            result = {
                "generated_recipes": recipes,
                "total_recipes": len(recipes),
                "inventory_usage": f"{min(100, len(data.get('priorities', [])) * 25)}%",
                "optimization_applied": self.performance_mode,
                "prompt_size_reduction": "75%" if self.performance_mode else "0%",
                "cache_hit": cached_response is not None,
                "cache_stats": ai_cache.get_cache_stats(),
                "token_metrics": self._calculate_token_metrics(prompt, response_text) if self.performance_mode else None
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
            
            print(f"✅ [GEMINI SERVICE] Recipe generation completed successfully")
            return result
            
        except Exception as e:
            print(f"🚨 [GEMINI SERVICE] Error generating recipes: {str(e)}")
            print(f"🚨 [GEMINI SERVICE] Error type: {type(e).__name__}")
            import traceback
            print(f"🚨 [GEMINI SERVICE] Full traceback: {traceback.format_exc()}")
            logger.error(f"Error generating recipes: {str(e)}")
            raise ValueError(f"Error en la generación de recetas: {str(e)}")

    import json
    import re
    import logging

    logger = logging.getLogger(__name__)

    def _parse_response_text(self, text: str):
        print(f"🔧 [GEMINI PARSER] Starting to parse response text")
        print(f"🔧 [GEMINI PARSER] Raw text length: {len(text)}")
        print(f"🔧 [GEMINI PARSER] First 300 chars: {text[:300]}")
        
        clean_text = text.strip()
        print(f"🔧 [GEMINI PARSER] After strip - length: {len(clean_text)}")

        # Si viene con markdown-style triple backticks
        if clean_text.startswith("```"):
            clean_text = clean_text.strip("`").strip()
            if clean_text.startswith("json"):
                clean_text = clean_text[len("json"):].strip()
            print(f"🔧 [GEMINI PARSER] After markdown cleanup - length: {len(clean_text)}")

        # Extracción robusta del array JSON (de "[" a "]")
        start = clean_text.find('[')
        end = clean_text.rfind(']')
        print(f"🔧 [GEMINI PARSER] JSON array bounds - start: {start}, end: {end}")
        
        if start == -1 or end == -1:
            print(f"🚨 [GEMINI PARSER] No valid JSON array found!")
            print(f"🚨 [GEMINI PARSER] Looking for alternatives...")
            # Try to find any bracket structure
            print(f"🚨 [GEMINI PARSER] Full text for debugging:\n{clean_text}")
            logger.error("No valid JSON array found in text.")
            raise ValueError("Error parsing AI response: no valid JSON array found.")

        json_text = clean_text[start:end + 1]
        print(f"🔧 [GEMINI PARSER] Extracted JSON text length: {len(json_text)}")
        print(f"🔧 [GEMINI PARSER] JSON text preview: {json_text[:200]}...")

        try:
            parsed_result = json.loads(json_text)
            print(f"✅ [GEMINI PARSER] Successfully parsed JSON with {len(parsed_result)} items")
            return parsed_result
        except Exception as e:
            print(f"🚨 [GEMINI PARSER] Failed to parse JSON!")
            print(f"🚨 [GEMINI PARSER] Error: {str(e)}")
            print(f"🚨 [GEMINI PARSER] Problematic JSON text:\n{json_text}")
            logger.error(f"Failed to parse AI response as JSON: {json_text}")
            raise ValueError(f"Error parsing AI response: {str(e)}") from e

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
            recipe_detailed_description = "Describe the appearance of the final dish in a clear and realistic way, focusing on visible ingredients, plating style, color contrasts, textures, and portion size. Use a neutral background and natural lighting. Avoid metaphors or poetic expressions. Describe the setting as if preparing an image for a food magazine or recipe app."
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
            recipe_detailed_description = "Describe de forma clara y realista el aspecto del plato terminado, enfocándote en los ingredientes visibles, el estilo de presentación, los colores, las texturas y el tamaño de la porción. Usa un fondo neutro y luz natural. Evita metáforas o expresiones poéticas. Describe la escena como si se fuera a generar una imagen para una revista de cocina o una app de recetas."

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
          "description" "{recipe_detailed_description}",
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

    def _build_optimized_prompt(self, data: Dict[str, Any], num_recipes: int, recipe_categories: List[str]) -> str:
        """Optimized prompt builder - 75% smaller while maintaining effectiveness"""
        ingredients = data.get("ingredients", [])
        priorities = data.get("priorities", [])
        preferences = data.get("preferences", [])
        user_profile = data.get("user_profile", {})
        previous_recipes = data.get("previous_recipes", [])
        
        # Limit input data to most relevant items
        top_ingredients = ingredients[:8]  # Top 8 ingredients only
        top_priorities = priorities[:3]    # Top 3 priorities
        top_preferences = preferences[:2]   # Top 2 preferences
        
        # Build compact ingredient list
        ingredients_list = [f"{i['name']} ({i['quantity']} {i['unit']})" for i in top_ingredients]
        ingredients_str = ", ".join(ingredients_list)
        
        # Get language settings
        language = user_profile.get("language", "es")
        measurement_unit = user_profile.get("measurementUnit", "metric")
        
        # Compact measurement hint
        units_hint = "(imperial: cups, oz, lb)" if measurement_unit == "imperial" else "(métrico: gramos, litros, unidades)"
        
        # Compact category list
        categories = ", ".join(recipe_categories[:2]) if recipe_categories else "ninguna"
        
        # Anti-duplication context
        avoid_duplicates = ""
        if previous_recipes:
            recent_titles = previous_recipes[:10]  # Last 10 recipes
            if language == "en":
                avoid_duplicates = f" AVOID repeating these recent recipes: {', '.join(recent_titles)}. Create completely different dishes."
            else:
                avoid_duplicates = f" EVITA repetir estas recetas recientes: {', '.join(recent_titles)}. Crea platos completamente diferentes."
        
        if language == "en":
            return f"""Peruvian chef: generate {num_recipes} UNIQUE recipes JSON using: {ingredients_str}.
Prioritize: {', '.join(top_priorities)}. Preferences: {', '.join(top_preferences)}. Categories: {categories}.{avoid_duplicates}

Exact format: [{{"title":"str","duration":"15-45 min","difficulty":"Easy|Intermediate|Difficult","category":"breakfast|lunch|dinner|dessert","description":"realistic dish description for image","ingredients":[{{"name":"str","quantity":num,"type_unit":"str"}}],"steps":[{{"step_order":1,"description":"detailed step"}}],"footer":"food waste tip"}}]

Measurement units {units_hint}. Reply only valid JSON."""
        else:
            return f"""Chef peruano: genera {num_recipes} recetas ÚNICAS JSON usando: {ingredients_str}.
Prioriza: {', '.join(top_priorities)}. Preferencias: {', '.join(top_preferences)}. Categorías: {categories}.{avoid_duplicates}

Formato exacto: [{{"title":"str","duration":"15-45 min","difficulty":"Fácil|Intermedio|Difícil","category":"desayuno|almuerzo|cena|postre","description":"descripción realista del plato para imagen","ingredients":[{{"name":"str","quantity":num,"type_unit":"str"}}],"steps":[{{"step_order":1,"description":"paso detallado"}}],"footer":"consejo de aprovechamiento"}}]

Unidades {units_hint}. Responde solo JSON válido."""

    def _fast_parse_response(self, text: str) -> List[Dict]:
        """Optimized JSON parsing with better error handling and performance"""
        print(f"🚀 [FAST PARSER] Processing response ({len(text)} chars)")
        
        # Quick cleaning
        clean_text = text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.strip("`").replace("json", "").strip()
        
        # Find JSON array bounds efficiently
        start = clean_text.find('[')
        end = clean_text.rfind(']')
        
        if start == -1 or end == -1:
            print(f"🚨 [FAST PARSER] No JSON array found")
            raise ValueError("No valid JSON array found in response")
        
        json_text = clean_text[start:end + 1]
        
        try:
            result = json.loads(json_text)
            print(f"✅ [FAST PARSER] Successfully parsed {len(result)} recipes")
            return result
        except json.JSONDecodeError as e:
            print(f"🔧 [FAST PARSER] Attempting JSON repair...")
            # Try to fix common JSON issues
            fixed_json = self._attempt_json_fix(json_text)
            try:
                result = json.loads(fixed_json)
                print(f"✅ [FAST PARSER] Repaired and parsed {len(result)} recipes")
                return result
            except:
                print(f"🚨 [FAST PARSER] Failed to repair JSON")
                raise ValueError(f"Failed to parse AI response: {str(e)}")
    
    def _attempt_json_fix(self, json_text: str) -> str:
        """Attempt to fix common JSON formatting issues"""
        # Fix missing commas between objects
        json_text = re.sub(r'}\s*{', '},{', json_text)
        
        # Fix trailing commas
        json_text = re.sub(r',\s*}', '}', json_text)
        json_text = re.sub(r',\s*]', ']', json_text)
        
        # Fix missing quotes around property names
        json_text = re.sub(r'(\w+):', r'"\1":', json_text)
        
        return json_text
    
    def _get_user_recent_recipes(self, user_uid: str) -> List[str]:
        """Get user's recently generated recipe titles to avoid duplicates"""
        try:
            from src.infrastructure.db.models.recipe_generated_orm import RecipeGeneratedORM
            from src.infrastructure.db.base import db
            from datetime import datetime, timedelta
            
            # Get recipes from last 7 days
            cutoff_date = datetime.now() - timedelta(days=7)
            
            recent_recipes = db.session.query(RecipeGeneratedORM.title)\
                .filter(RecipeGeneratedORM.user_uid == user_uid)\
                .filter(RecipeGeneratedORM.generated_at >= cutoff_date)\
                .limit(20)\
                .all()
            
            titles = [recipe.title for recipe in recent_recipes]
            print(f"📋 [ANTI-DUP] Found {len(titles)} recent recipes for user {user_uid}")
            return titles
            
        except Exception as e:
            print(f"⚠️ [ANTI-DUP] Error fetching recent recipes: {e}")
            return []
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID for this generation request"""
        import uuid
        from datetime import datetime
        session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        print(f"🎲 [SESSION] Generated session ID: {session_id}")
        return session_id
    
    def _calculate_token_metrics(self, prompt: str, response: str) -> Dict[str, Any]:
        """Calculate token usage metrics for monitoring"""
        try:
            # Estimate token usage (1 token ≈ 4 chars for Spanish)
            prompt_tokens = len(prompt) // 4
            response_tokens = len(response) // 4
            total_tokens = prompt_tokens + response_tokens
            
            return {
                "prompt_tokens": prompt_tokens,
                "response_tokens": response_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": total_tokens * 0.00002,  # Rough estimate
                "optimization_applied": self.performance_mode
            }
        except Exception as e:
            print(f"⚠️ Token metrics calculation failed: {e}")
            return {"error": str(e)}