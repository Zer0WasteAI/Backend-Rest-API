from flasgger import swag_from # type: ignore
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.application.factories.generation_usecase_factory import make_generation_repository
from src.domain.models.generation import Generation
from src.infrastructure.ai.gemini_recipe_generator_service import logger
from src.interface.serializers.recipe_serializers import (
    CustomRecipeRequestSchema,
    SaveRecipeRequestSchema,
    RecipeSchema
)

from src.application.factories.recipe_usecase_factory import (
    make_generate_recipes_use_case,
    make_prepare_recipe_generation_data_use_case,
    make_generate_custom_recipe_use_case,
    make_save_recipe_use_case,
    make_get_saved_recipes_use_case,
    make_get_all_recipes_use_case,
    make_delete_user_recipe_use_case,
    make_recipe_image_generator_service,
    make_add_recipe_to_favorites_use_case,
    make_get_favorite_recipes_use_case,
    make_remove_recipe_from_favorites_use_case
)

from src.infrastructure.async_tasks.async_task_service import async_task_service
from src.infrastructure.optimization.rate_limiter import smart_rate_limit
from src.infrastructure.optimization.cache_service import smart_cache, cache_user_data
from src.shared.exceptions.custom import InvalidRequestDataException, RecipeNotFoundException
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select
import uuid

recipes_bp = Blueprint("recipes", __name__)

@recipes_bp.route("/generate-from-inventory", methods=["POST"])
@jwt_required()
@smart_rate_limit('ai_recipe_generation')  # 🛡️ Rate limit: 8 requests/min for AI recipe generation
@cache_user_data('ai_recipe_generation', timeout=1800)  # 🚀 Cache: 30 min for recipe generation
@swag_from({
    'tags': ['Recipe'],
    'summary': 'Generar recetas inteligentes basadas en inventario',
    'description': '''
Genera recetas personalizadas usando los ingredientes disponibles en el inventario del usuario.

### Proceso de Generación:
1. **Análisis de Inventario**: Revisa ingredientes disponibles del usuario
2. **Generación IA**: Crea recetas utilizando ingredientes disponibles
3. **Personalización**: Considera preferencias dietéticas y nivel de cocina
4. **Imágenes Asíncronas**: Genera imágenes de recetas en segundo plano
5. **Impacto Ambiental**: Calcula beneficios ambientales de usar ingredientes

### Características de las Recetas:
- **Basadas en Inventario**: Usa ingredientes que ya tienes
- **Personalizadas**: Adaptadas a tu perfil y preferencias
- **Completas**: Incluye ingredientes, pasos, tiempo, dificultad
- **Sostenibles**: Prioriza uso de ingredientes próximos a vencer
- **Con Imágenes**: Genera imágenes atractivas automáticamente

### Algoritmo de Selección:
- Prioriza ingredientes próximos a vencer
- Respeta restricciones dietéticas del usuario
- Considera nivel de cocina (principiante/intermedio/avanzado)
- Optimiza uso de ingredientes disponibles
- Sugiere alternativas si faltan ingredientes menores

### Respuesta Inmediata:
- Recetas completas sin esperar imágenes
- Estado de generación de imágenes
- URL para verificar progreso de imágenes
- Tiempo estimado de finalización
    ''',
    'responses': {
        200: {
            'description': 'Recetas generadas exitosamente',
            'examples': {
                'application/json': {
                    "generated_recipes": [
                        {
                            "name": "Ensalada de Tomates Cherry con Queso",
                            "description": "Ensalada fresca y saludable aprovechando los tomates cherry del refrigerador",
                            "ingredients": [
                                {
                                    "name": "Tomates cherry",
                                    "quantity": 300,
                                    "unit": "gr",
                                    "available_in_inventory": True,
                                    "expiring_soon": True
                                },
                                {
                                    "name": "Queso manchego",
                                    "quantity": 100,
                                    "unit": "gr", 
                                    "available_in_inventory": True,
                                    "expiring_soon": False
                                },
                                {
                                    "name": "Aceite de oliva",
                                    "quantity": 2,
                                    "unit": "cucharadas",
                                    "available_in_inventory": False,
                                    "suggestion": "Ingrediente común de despensa"
                                }
                            ],
                            "steps": [
                                "Lavar y cortar los tomates cherry por la mitad",
                                "Cortar el queso en cubos pequeños",
                                "Mezclar tomates y queso en un bowl",
                                "Aliñar con aceite de oliva y sal al gusto",
                                "Servir inmediatamente"
                            ],
                            "cooking_time_minutes": 10,
                            "difficulty": "easy",
                            "servings": 2,
                            "calories_per_serving": 180,
                            "image_path": None,
                            "image_status": "generating",
                            "generated_at": "2024-01-15T10:30:00Z",
                            "uses_expiring_ingredients": True,
                            "inventory_coverage": 0.85,
                            "environmental_impact": {
                                "co2_saved_kg": 0.5,
                                "water_saved_liters": 12.3,
                                "food_waste_reduced": True
                            }
                        }
                    ],
                    "generation_summary": {
                        "total_recipes": 3,
                        "recipes_using_expiring_items": 2,
                        "inventory_utilization": 0.78,
                        "environmental_benefits": {
                            "total_co2_saved": 1.2,
                            "total_water_saved": 34.5,
                            "ingredients_saved_from_waste": 5
                        }
                    },
                    "images": {
                        "status": "generating",
                        "task_id": "task_abc123def456",
                        "check_images_url": "/api/generation/images/status/task_abc123def456",
                        "estimated_time": "15-30 segundos"
                    },
                    "generation_id": "gen_789xyz456",
                    "message": "Recetas generadas exitosamente. Imágenes generándose en segundo plano."
                }
            }
        },
        404: {
            'description': 'Inventario vacío o insuficiente',
            'examples': {
                'application/json': {
                    'error': 'Insufficient inventory',
                    'details': 'No hay suficientes ingredientes para generar recetas',
                    'suggestion': 'Agrega ingredientes a tu inventario primero'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido',
            'examples': {
                'application/json': {
                    'error': 'Unauthorized',
                    'details': 'Invalid or expired token'
                }
            }
        },
        500: {
            'description': 'Error en la generación de recetas',
            'examples': {
                'application/json': {
                    'error': 'Failed to generate recipes from inventory',
                    'details': 'AI service temporarily unavailable',
                    'error_type': 'RecipeGenerationException'
                }
            }
        }
    }
})
def generate_recipes():
    user_uid = get_jwt_identity()
    print(f"🍳 [RECIPE CONTROLLER] Starting recipe generation for user: {user_uid}")

    try:
        prepare_use_case = make_prepare_recipe_generation_data_use_case()
        print(f"🍳 [RECIPE CONTROLLER] Preparing data...")
        structured_data = prepare_use_case.execute(user_uid)
        print(f"🍳 [RECIPE CONTROLLER] Data prepared successfully. Ingredients: {len(structured_data.get('ingredients', []))}")

        generate_use_case = make_generate_recipes_use_case()
        print(f"🍳 [RECIPE CONTROLLER] Generating recipes...")
        result = generate_use_case.execute(structured_data)
        print(f"🍳 [RECIPE CONTROLLER] Recipes generated successfully. Count: {len(result.get('generated_recipes', []))}")
        
    except Exception as e:

        
        error_details = {

        
            "error_type": type(e).__name__,

        
            "error_message": str(e),

        
            "traceback": str(e.__traceback__.tb_frame.f_code.co_filename) + ":" + str(e.__traceback__.tb_lineno) if e.__traceback__ else "No traceback"

        
        }

        
        

        
        # Log the detailed error

        
        print(f"ERROR: {error_details}")

        
        

        print(f"🚨 [RECIPE CONTROLLER] Error in recipe generation: {str(e)}")
        print(f"🚨 [RECIPE CONTROLLER] Error type: {type(e).__name__}")
        import traceback
        print(f"🚨 [RECIPE CONTROLLER] Full traceback: {traceback.format_exc()}")
        
        return jsonify({
            "error": "Failed to generate recipes from inventory",
            "details": str(e),
            "error_type": type(e).__name__
        }), 500

    generation_id = str(uuid.uuid4())

    # Guardar Generation
    generation_repository = make_generation_repository()
    generation = Generation(
        uid=generation_id,
        user_uid=user_uid,
        generated_at=datetime.now(timezone.utc),
        raw_result=result,
        generation_type="inventory",
        recipes_ids=None
    )
    generation_repository.save(generation)
    
    # Guardar recetas generadas automáticamente en recipes_generated
    from src.application.factories.environmental_savings_factory import make_recipe_generated_repository
    recipe_generated_repo = make_recipe_generated_repository()
    generated_recipe_uids = []
    
    for recipe_data in result["generated_recipes"]:
        recipe_uid = recipe_generated_repo.save_generated_recipe(
            user_uid=user_uid,
            generation_id=generation_id,
            recipe_data=recipe_data,
            generation_type="inventory"
        )
        generated_recipe_uids.append(recipe_uid)
    
    print(f"🍳 [RECIPE CONTROLLER] Saved {len(generated_recipe_uids)} recipes to recipes_generated table")

    # Crear tarea de imagen
    image_task_id = async_task_service.create_task(
        user_uid=user_uid,
        task_type='recipe_images',
        input_data={
            'generation_id': generation_id,
            'recipes': result["generated_recipes"]
        }
    )

    recipe_image_generator_service = make_recipe_image_generator_service()

    async_task_service.run_async_recipe_image_generation(
        task_id=image_task_id,
        user_uid=user_uid,
        recipes=result["generated_recipes"],
        recipe_image_generator_service=recipe_image_generator_service,
        generation_repository=generation_repository,
        generation_id=generation_id
    )
    current_time = datetime.now(timezone.utc)
    for recipe in result["generated_recipes"]:
        recipe["image_path"] = None
        recipe["image_status"] = "generating"
        recipe["generated_at"] = current_time.isoformat()

    result["images"] = {
        "status": "generating",
        "task_id": image_task_id,
        "check_images_url": f"/api/generation/images/status/{image_task_id}",
        "estimated_time": "15-30 segundos"
    }

    return jsonify(result), 200

@recipes_bp.route("/generate-custom", methods=["POST"])
@jwt_required()
@smart_rate_limit('ai_recipe_generation')  # 🛡️ Rate limit: 8 requests/min for AI recipe generation
@swag_from({
    'tags': ['Recipes'],
    'summary': 'Generar receta personalizada con ingredientes específicos',
    'description': '''
Genera una receta completamente personalizada usando ingredientes específicos proporcionados por el usuario.

### Características de la Generación:
- **Ingredientes específicos**: Usa exactamente los ingredientes proporcionados
- **Personalización avanzada**: Considera preferencias dietéticas y restricciones
- **Adaptación inteligente**: Ajusta cantidades según disponibilidad
- **Variedad creativa**: Genera múltiples opciones de preparación
- **Análisis nutricional**: Calcula información nutricional completa

### Parámetros de Personalización:
- **Tipo de cocina**: Italiana, mexicana, asiática, mediterránea, etc.
- **Dificultad**: Fácil, intermedio, avanzado
- **Tiempo de preparación**: Rápido (<30min), medio (30-60min), elaborado (>60min)
- **Restricciones dietéticas**: Vegetariano, vegano, sin gluten, bajo en sodio, etc.
- **Ocasión**: Desayuno, almuerzo, cena, snack, especial

### Proceso de Generación:
1. **Análisis de ingredientes**: Evalúa compatibilidad y proporciones
2. **Selección de técnicas**: Escoge métodos de cocción apropiados
3. **Optimización nutricional**: Balancea macronutrientes
4. **Generación de pasos**: Crea instrucciones detalladas y claras
5. **Validación culinaria**: Verifica viabilidad de la receta

### Casos de Uso:
- Crear recetas con ingredientes disponibles específicos
- Experimentar con combinaciones nuevas de ingredientes
- Generar recetas adaptadas a dietas especiales
- Crear versiones personalizadas de platos clásicos
    ''',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['ingredients'],
                'properties': {
                    'ingredients': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string', 'example': 'Pollo'},
                                'quantity': {'type': 'number', 'example': 500},
                                'unit': {'type': 'string', 'example': 'gr'}
                            }
                        },
                        'description': 'Lista de ingredientes específicos para la receta'
                    },
                    'cuisine_type': {
                        'type': 'string',
                        'enum': ['italiana', 'mexicana', 'asiática', 'mediterránea', 'francesa', 'india', 'cualquiera'],
                        'description': 'Tipo de cocina deseado',
                        'example': 'italiana'
                    },
                    'difficulty': {
                        'type': 'string',
                        'enum': ['fácil', 'intermedio', 'avanzado'],
                        'description': 'Nivel de dificultad deseado',
                        'example': 'intermedio'
                    },
                    'prep_time': {
                        'type': 'string',
                        'enum': ['rápido', 'medio', 'elaborado'],
                        'description': 'Tiempo de preparación preferido',
                        'example': 'medio'
                    },
                    'dietary_restrictions': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Restricciones dietéticas (vegetariano, vegano, sin gluten, etc.)',
                        'example': ['sin gluten']
                    },
                    'meal_type': {
                        'type': 'string',
                        'enum': ['desayuno', 'almuerzo', 'cena', 'snack', 'postre'],
                        'description': 'Tipo de comida',
                        'example': 'almuerzo'
                    },
                    'servings': {
                        'type': 'integer',
                        'minimum': 1,
                        'maximum': 10,
                        'description': 'Número de porciones deseadas',
                        'example': 4
                    }
                },
                'example': {
                    'ingredients': [
                        {'name': 'Pollo', 'quantity': 500, 'unit': 'gr'},
                        {'name': 'Pasta', 'quantity': 300, 'unit': 'gr'},
                        {'name': 'Tomates', 'quantity': 400, 'unit': 'gr'},
                        {'name': 'Queso parmesano', 'quantity': 100, 'unit': 'gr'}
                    ],
                    'cuisine_type': 'italiana',
                    'difficulty': 'intermedio',
                    'prep_time': 'medio',
                    'dietary_restrictions': [],
                    'meal_type': 'almuerzo',
                    'servings': 4
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Receta personalizada generada exitosamente',
            'examples': {
                'application/json': {
                    "recipe": {
                        "name": "Pasta al Pollo con Tomates Frescos",
                        "description": "Una deliciosa pasta italiana con pollo tierno y tomates frescos, perfecta para un almuerzo familiar",
                        "cuisine_type": "italiana",  
                        "difficulty": "intermedio",
                        "prep_time": 45,
                        "cook_time": 25,
                        "total_time": 70,
                        "servings": 4,
                        "ingredients": [
                            {
                                "name": "Pollo",
                                "quantity": 500,
                                "unit": "gr",
                                "preparation": "cortado en trozos medianos"
                            },
                            {
                                "name": "Pasta",
                                "quantity": 300,
                                "unit": "gr", 
                                "preparation": "tipo penne o fusilli"
                            }
                        ],
                        "instructions": [
                            {
                                "step": 1,
                                "description": "Cortar el pollo en trozos medianos y sazonar con sal y pimienta",
                                "time": 5,
                                "temperature": None
                            }
                        ],
                        "nutritional_info": {
                            "calories_per_serving": 520,
                            "protein": 35,
                            "carbs": 58,
                            "fat": 14,
                            "fiber": 4,
                            "sodium": 380
                        },
                        "tips": [
                            "Usar tomates muy maduros para mejor sabor",
                            "No sobrecocinar la pasta para mantener textura al dente"
                        ]
                    }
                }
            }
        },
        400: {
            'description': 'Datos de entrada inválidos'
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno en la generación de la receta'
        }
    }
})
def generate_custom_recipes():
    user_uid = get_jwt_identity()
    schema = CustomRecipeRequestSchema()
    json_data = request.get_json()

    errors = schema.validate(json_data)
    if errors:
        raise InvalidRequestDataException(details=errors)

    use_case = make_generate_custom_recipe_use_case()
    result = use_case.execute(
        user_uid=user_uid,
        custom_ingredients=json_data["ingredients"],
        preferences=json_data.get("preferences", []),
        num_recipes=json_data.get("num_recipes", 2),
        recipe_categories=json_data.get("recipe_categories", [])
    )

    generation_id = str(uuid.uuid4())

    generation_repository = make_generation_repository()
    generation = Generation(
        uid=generation_id,
        user_uid=user_uid,
        generated_at=datetime.now(timezone.utc),
        raw_result=result,
        generation_type="custom",
        recipes_ids=None
    )
    generation_repository.save(generation)
    
    # Guardar recetas generadas automáticamente en recipes_generated
    from src.application.factories.environmental_savings_factory import make_recipe_generated_repository
    recipe_generated_repo = make_recipe_generated_repository()
    generated_recipe_uids = []
    
    for recipe_data in result["generated_recipes"]:
        recipe_uid = recipe_generated_repo.save_generated_recipe(
            user_uid=user_uid,
            generation_id=generation_id,
            recipe_data=recipe_data,
            generation_type="custom"
        )
        generated_recipe_uids.append(recipe_uid)
    
    print(f"🍳 [RECIPE CONTROLLER] Saved {len(generated_recipe_uids)} recipes to recipes_generated table")

    image_task_id = async_task_service.create_task(
        user_uid=user_uid,
        task_type='recipe_images',
        input_data={
            'generation_id': generation_id,
            'recipes': result["generated_recipes"]
        }
    )

    recipe_image_generator_service = make_recipe_image_generator_service()

    async_task_service.run_async_recipe_image_generation(
        task_id=image_task_id,
        user_uid=user_uid,
        recipes=result["generated_recipes"],
        recipe_image_generator_service=recipe_image_generator_service,
        generation_repository=generation_repository,
        generation_id=generation_id
    )

    current_time = datetime.now(timezone.utc)
    for recipe in result["generated_recipes"]:
        recipe["image_path"] = None
        recipe["image_status"] = "generating"
        recipe["generated_at"] = current_time.isoformat()

    result["images"] = {
        "status": "generating",
        "task_id": image_task_id,
        "check_images_url": f"/api/generation/images/status/{image_task_id}",
        "estimated_time": "15-30 segundos"
    }

    return jsonify(result), 200

# ENDPOINT ELIMINADO: /save era confuso y duplicaba funcionalidad
# Las recetas generadas se guardan automáticamente en recipes_generated
# Para favoritos, usar los nuevos endpoints de favoritos más abajo

@recipes_bp.route("/saved", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Recipes'],
    'summary': 'Obtener recetas guardadas del usuario',
    'description': '''
Obtiene la colección completa de recetas guardadas por el usuario con opciones de filtrado y ordenamiento.

### Funcionalidades de Consulta:
- **Filtrado avanzado**: Por categoría, dificultad, tiempo de preparación, valoración
- **Ordenamiento múltiple**: Por fecha guardada, valoración, frecuencia de uso, nombre
- **Búsqueda de texto**: En nombres, ingredientes, instrucciones y notas
- **Paginación**: Para colecciones grandes de recetas
- **Estadísticas incluidas**: Métricas de uso y preferencias

### Opciones de Filtrado:
- **Categoría**: Filtrar por categorías personalizadas del usuario
- **Dificultad**: fácil, intermedio, avanzado
- **Tiempo**: Rangos de tiempo de preparación
- **Valoración**: Mínima valoración (estrellas)
- **Etiquetas**: Filtrar por tags específicos
- **Fecha**: Recetas guardadas en período específico

### Casos de Uso:
- Explorar biblioteca personal de recetas
- Buscar recetas para ocasiones específicas
- Planificar menús basados en recetas favoritas
- Revisar estadísticas de uso de recetas
- Encontrar recetas según tiempo disponible
    ''',
    'parameters': [
        {
            'name': 'category',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Filtrar por categoría personalizada',
            'example': 'Comidas familiares'
        },
        {
            'name': 'difficulty',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['fácil', 'intermedio', 'avanzado'],
            'description': 'Filtrar por nivel de dificultad'
        },
        {
            'name': 'max_prep_time',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'description': 'Tiempo máximo de preparación en minutos',
            'example': 30
        },
        {
            'name': 'min_rating',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'minimum': 1,
            'maximum': 5,
            'description': 'Valoración mínima (estrellas)',
            'example': 4
        },
        {
            'name': 'search',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Búsqueda de texto en nombres e ingredientes',
            'example': 'pasta'
        },
        {
            'name': 'sort_by',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['saved_date', 'rating', 'prep_time', 'name', 'usage_frequency'],
            'default': 'saved_date',
            'description': 'Campo para ordenamiento'
        },
        {
            'name': 'sort_order',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['asc', 'desc'],
            'default': 'desc',
            'description': 'Dirección del ordenamiento'
        },
        {
            'name': 'page',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 1,
            'description': 'Número de página para paginación'
        },
        {
            'name': 'per_page',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 20,
            'maximum': 100,
            'description': 'Recetas por página'
        }
    ],
    'responses': {
        200: {
            'description': 'Recetas guardadas obtenidas exitosamente',
            'examples': {
                'application/json': {
                    "saved_recipes": [
                        {
                            "recipe_uid": "user_recipe_123456789",
                            "name": "Pasta carbonara casera",
                            "description": "Una deliciosa pasta italiana con huevos y bacon",
                            "prep_time": 30,
                            "servings": 4,
                            "difficulty": "intermedio",
                            "cuisine_type": "italiana",
                            "user_rating": 5,
                            "user_notes": "Receta favorita para domingos familiares",
                            "custom_category": "Comidas familiares",
                            "tags": ["pasta", "italiana", "familiar", "rápida"],
                            "saved_at": "2024-01-10T16:00:00Z",
                            "usage_stats": {
                                "times_prepared": 8,
                                "last_prepared": "2024-01-14T19:00:00Z",
                                "favorite": True,
                                "average_prep_time_actual": 25
                            },
                            "ingredients_summary": {
                                "total_ingredients": 6,
                                "main_ingredients": ["pasta", "huevos", "bacon", "queso parmesano"]
                            }
                        },
                        {
                            "recipe_uid": "user_recipe_987654321",
                            "name": "Ensalada mediterránea",
                            "description": "Ensalada fresca con ingredientes mediterráneos",
                            "prep_time": 15,
                            "servings": 2,
                            "difficulty": "fácil",
                            "cuisine_type": "mediterránea",
                            "user_rating": 4,
                            "user_notes": "Perfecta para veranos",
                            "custom_category": "Ensaladas",
                            "tags": ["ensalada", "saludable", "rápida", "vegetariana"],
                            "saved_at": "2024-01-08T12:30:00Z",
                            "usage_stats": {
                                "times_prepared": 5,
                                "last_prepared": "2024-01-12T13:00:00Z",
                                "favorite": False,
                                "average_prep_time_actual": 12
                            },
                            "ingredients_summary": {
                                "total_ingredients": 8,
                                "main_ingredients": ["lechuga", "tomate", "pepino", "aceitunas"]
                            }
                        }
                    ],
                    "pagination": {
                        "current_page": 1,
                        "per_page": 20,
                        "total_recipes": 25,
                        "total_pages": 2,
                        "has_next": True,
                        "has_previous": False
                    },
                    "collection_stats": {
                        "total_saved_recipes": 25,
                        "categories_count": {
                            "Comidas familiares": 8,
                            "Ensaladas": 5,
                            "Postres": 4,
                            "Aperitivos": 3,
                            "Sin categoría": 5
                        },
                        "difficulty_distribution": {
                            "fácil": 12,
                            "intermedio": 10,
                            "avanzado": 3
                        },
                        "average_rating": 4.2,
                        "most_prepared_recipe": {
                            "name": "Pasta carbonara casera",
                            "times_prepared": 8
                        }
                    },
                    "filter_applied": {
                        "category": None,
                        "difficulty": None,
                        "max_prep_time": None,
                        "min_rating": None,
                        "search": None
                    }
                }
            }
        },
        404: {
            'description': 'No se encontraron recetas guardadas',
            'examples': {
                'application/json': {
                    'message': 'No saved recipes found',
                    'saved_recipes': [],
                    'collection_stats': {
                        'total_saved_recipes': 0
                    }
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno del servidor'
        }
    }
})
def get_saved_recipes():
    user_uid = get_jwt_identity()

    use_case = make_get_saved_recipes_use_case()
    saved_recipes = use_case.execute(user_uid)

    recipe_schema = RecipeSchema()
    result = recipe_schema.dump(saved_recipes, many=True)

    return jsonify({
        "recipes": result,
        "count": len(result)
    }), 200

@recipes_bp.route("/all", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Recipes'],
    'summary': 'Obtener todas las recetas del sistema',
    'description': '''
Obtiene todas las recetas disponibles en el sistema, incluyendo recetas públicas y generadas por IA.

### Contenido de la Respuesta:
- **Recetas públicas**: Recetas disponibles para todos los usuarios
- **Recetas de la comunidad**: Recetas compartidas por otros usuarios
- **Recetas destacadas**: Selección curada de recetas populares
- **Metadatos completos**: Información nutricional, dificultad, tiempo, etc.

### Características:
- **Paginación**: Manejo eficiente de grandes volúmenes de recetas
- **Filtrado básico**: Opciones de filtrado por tipo de cocina, dificultad
- **Ordenamiento**: Por popularidad, fecha de creación, valoración
- **Búsqueda**: Capacidad de búsqueda por texto en nombres e ingredientes

### Casos de Uso:
- Explorar catálogo completo de recetas disponibles
- Descubrir nuevas recetas populares
- Buscar inspiración culinaria
- Acceder a biblioteca completa para planificación
- Encontrar recetas por tipo de cocina o ingredientes

### Diferencias vs. Recetas Guardadas:
- **Todas**: Catálogo completo del sistema, no personalizadas
- **Guardadas**: Solo recetas que el usuario ha guardado en su colección personal
    ''',
    'responses': {
        200: {
            'description': 'Todas las recetas del sistema obtenidas exitosamente',
            'examples': {
                'application/json': {
                    "recipes": [
                        {
                            "recipe_uid": "system_recipe_001",
                            "name": "Pasta Carbonara Clásica",
                            "description": "La auténtica receta italiana de carbonara con huevos, bacon y queso parmesano",
                            "cuisine_type": "italiana",
                            "difficulty": "intermedio",
                            "prep_time": 25,
                            "cook_time": 15,
                            "total_time": 40,
                            "servings": 4,
                            "source": "community",
                            "author": "Chef Mario Rossi",
                            "created_at": "2024-01-10T12:00:00Z",
                            "popularity_score": 9.2,
                            "rating_average": 4.7,
                            "times_prepared": 1250,
                            "ingredients_count": 6,
                            "main_ingredients": ["pasta", "huevos", "bacon", "queso parmesano"],
                            "dietary_tags": ["no vegetariano"],
                            "nutritional_summary": {
                                "calories_per_serving": 520,
                                "protein": 28,
                                "carbs": 45,
                                "fat": 24
                            }
                        },
                        {
                            "recipe_uid": "system_recipe_002",
                            "name": "Ensalada Mediterránea",
                            "description": "Ensalada fresca con ingredientes típicos del mediterráneo",
                            "cuisine_type": "mediterránea",
                            "difficulty": "fácil",
                            "prep_time": 15,
                            "cook_time": 0,
                            "total_time": 15,
                            "servings": 2,
                            "source": "curated",
                            "author": "ZeroWasteAI Team",
                            "created_at": "2024-01-08T10:30:00Z",
                            "popularity_score": 8.5,
                            "rating_average": 4.4,
                            "times_prepared": 890,
                            "ingredients_count": 8,
                            "main_ingredients": ["lechuga", "tomate", "pepino", "aceitunas", "queso feta"],
                            "dietary_tags": ["vegetariano", "sin gluten"],
                            "nutritional_summary": {
                                "calories_per_serving": 180,
                                "protein": 8,
                                "carbs": 12,
                                "fat": 12
                            }
                        },
                        {
                            "recipe_uid": "ai_recipe_003",
                            "name": "Curry de Lentejas Especiado",
                            "description": "Curry vegano rico en proteínas con lentejas y especias aromáticas",
                            "cuisine_type": "india",
                            "difficulty": "intermedio",
                            "prep_time": 20,
                            "cook_time": 35,
                            "total_time": 55,
                            "servings": 6,
                            "source": "ai_generated",
                            "author": "ZeroWasteAI",
                            "created_at": "2024-01-12T14:45:00Z",
                            "popularity_score": 8.8,
                            "rating_average": 4.6,
                            "times_prepared": 445,
                            "ingredients_count": 12,
                            "main_ingredients": ["lentejas", "coco", "especias", "tomate", "cebolla"],
                            "dietary_tags": ["vegano", "sin gluten", "alto en proteína"],
                            "nutritional_summary": {
                                "calories_per_serving": 320,
                                "protein": 18,
                                "carbs": 42,
                                "fat": 8
                            }
                        }
                    ],
                    "catalog_summary": {
                        "total_recipes": 1250,
                        "cuisine_distribution": {
                            "italiana": 285,
                            "mediterránea": 210,
                            "mexicana": 180,
                            "asiática": 165,
                            "india": 125,
                            "francesa": 110,
                            "otras": 175
                        },
                        "difficulty_distribution": {
                            "fácil": 520,
                            "intermedio": 580,
                            "avanzado": 150
                        },
                        "source_distribution": {
                            "community": 650,
                            "curated": 400,
                            "ai_generated": 200
                        },
                        "average_rating": 4.3,
                        "most_popular_ingredients": [
                            "tomate", "cebolla", "ajo", "aceite de oliva", "pasta"
                        ]
                    },
                    "featured_collections": [
                        {
                            "name": "Recetas Rápidas",
                            "description": "Comidas deliciosas en menos de 30 minutos",
                            "recipe_count": 180
                        },
                        {
                            "name": "Cocina Saludable",
                            "description": "Recetas nutritivas y balanceadas",
                            "recipe_count": 220
                        },
                        {
                            "name": "Favoritos de la Comunidad",
                            "description": "Las recetas más populares entre usuarios",
                            "recipe_count": 50
                        }
                    ]
                }
            }
        },
        500: {
            'description': 'Error interno del servidor'
        }
    }
})
def get_all_recipes():

    use_case = make_get_all_recipes_use_case()
    all_recipes = use_case.execute()

    recipe_schema = RecipeSchema()
    result = recipe_schema.dump(all_recipes, many=True)

    return jsonify({
        "recipes": result,
        "count": len(result)
    }), 200

@recipes_bp.route("/delete", methods=["DELETE"])
@jwt_required()
@swag_from({
    'tags': ['Recipes'],
    'summary': 'Eliminar receta guardada del usuario',
    'description': '''
Elimina una receta específica de la colección personal de recetas guardadas del usuario.

### Comportamiento de Eliminación:
- **Eliminación de colección**: Solo elimina de la colección personal, no del sistema
- **Preservación de datos**: La receta original permanece disponible en el catálogo general
- **Limpieza de referencias**: Elimina referencias en planes de comidas y favoritos
- **Irreversible**: La operación no se puede deshacer (pero se puede volver a guardar)
- **Validación de propiedad**: Solo el propietario puede eliminar sus recetas guardadas

### Datos Eliminados:
- Entrada en la colección personal del usuario
- Valoraciones y notas personales
- Categorización personalizada
- Estadísticas de uso personal
- Referencias en planes de comidas (opcional)

### Casos de Uso:
- Limpiar colección de recetas no deseadas
- Eliminar recetas que ya no se usan
- Reorganizar biblioteca personal
- Liberar espacio en colección personal
- Corregir errores de guardado

### Consideraciones:
- La receta puede volver a guardarse en cualquier momento
- No afecta las estadísticas globales de la receta
- Los planes de comidas que usen esta receta pueden verse afectados
- Se mantiene historial de eliminación para estadísticas
    ''',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['title'],
                'properties': {
                    'title': {
                        'type': 'string',
                        'description': 'Título exacto de la receta a eliminar de la colección',
                        'example': 'Pasta carbonara casera'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Receta eliminada exitosamente de la colección',
            'examples': {
                'application/json': {
                    "message": "Receta 'Pasta carbonara casera' eliminada exitosamente",
                    "deleted_recipe": {
                        "title": "Pasta carbonara casera",
                        "recipe_uid": "user_recipe_123456789",
                        "user_uid": "firebase_uid_123",
                        "deleted_at": "2024-01-16T18:30:00Z",
                        "was_favorite": True,
                        "user_rating": 5,
                        "times_prepared": 8,
                        "saved_duration_days": 45
                    },
                    "impact_summary": {
                        "meal_plans_affected": 2,
                        "favorite_status_removed": True,
                        "collection_size_after": 24,
                        "can_be_resaved": True
                    },
                    "suggestions": [
                        "La receta sigue disponible en el catálogo general",
                        "Puedes volver a guardarla en cualquier momento",
                        "Considera revisar tus planes de comidas que la incluían"
                    ]
                }
            }
        },
        400: {
            'description': 'Datos de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid request data',
                    'details': {
                        'title': 'El campo title es obligatorio'
                    }
                }
            }
        },
        404: {
            'description': 'Receta no encontrada en la colección del usuario',
            'examples': {
                'application/json': {
                    'error': 'Recipe not found in user collection',
                    'details': 'No se encontró una receta con ese título en tu colección',
                    'title_searched': 'Pasta carbonara casera',
                    'suggestion': 'Verifica el título exacto de la receta'
                }
            }
        },
        403: {
            'description': 'Sin permisos para eliminar esta receta',
            'examples': {
                'application/json': {
                    'error': 'Unauthorized to delete this recipe',
                    'details': 'No tienes permisos para eliminar esta receta'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno del servidor',
            'examples': {
                'application/json': {
                    'error': 'Database error',
                    'details': 'Error al eliminar la receta de la base de datos'
                }
            }
        }
    }
})
def delete_user_recipe():
    user_uid = get_jwt_identity()
    data = request.get_json()

    if not data or "title" not in data:
        raise InvalidRequestDataException(details={"title": "El campo 'title' es obligatorio."})

    title = data["title"]
    use_case = make_delete_user_recipe_use_case()

    use_case.execute(user_uid=user_uid, title=title)

    return jsonify({
        "message": f"Receta '{title}' eliminada exitosamente"
    }), 200


@recipes_bp.route("/generated/gallery", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Recipes'],
    'summary': 'Obtener galería completa de recetas generadas del usuario',
    'description': '''
Obtiene todas las recetas generadas por IA para el usuario con contenido completo e imágenes.

### Funcionalidades:
- **Contenido completo**: Incluye ingredientes, pasos, tiempos, dificultad
- **Imágenes**: URLs de imágenes generadas cuando están disponibles
- **Metadatos**: Información de generación, fechas, tipo
- **Filtros avanzados**: Por estado de imagen, tipo de generación, fecha
- **Paginación**: Para optimizar rendimiento con muchas recetas
- **Ordenamiento**: Por fecha de generación, nombre, dificultad

### Información Incluida por Receta:
- **Datos básicos**: Título, descripción, categoría, dificultad
- **Ingredientes completos**: Con cantidades y unidades
- **Pasos detallados**: Instrucciones paso a paso ordenadas
- **Tiempos**: Duración de preparación y cocción
- **Imagen**: URL cuando está disponible + estado de generación
- **Metadatos**: Fecha generación, tipo (inventory/custom), generación ID

### Casos de Uso:
- Mostrar historial completo de recetas generadas
- Galería visual de recetas con imágenes
- Búsqueda y filtrado en historial personal
- Exportar recetas generadas
- Análisis de patrones de generación del usuario
    ''',
    'parameters': [
        {
            'name': 'page',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 1,
            'description': 'Número de página para paginación'
        },
        {
            'name': 'per_page',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 20,
            'maximum': 50,
            'description': 'Recetas por página (máximo 50)'
        },
        {
            'name': 'image_status',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['ready', 'generating', 'failed', 'pending'],
            'description': 'Filtrar por estado de imagen'
        },
        {
            'name': 'generation_type',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['inventory', 'custom'],
            'description': 'Filtrar por tipo de generación'
        },
        {
            'name': 'category',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Filtrar por categoría de receta'
        },
        {
            'name': 'difficulty',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['Fácil', 'Intermedio', 'Difícil'],
            'description': 'Filtrar por nivel de dificultad'
        },
        {
            'name': 'search',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Búsqueda por texto en título o descripción'
        },
        {
            'name': 'sort_by',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['generated_at', 'title', 'difficulty', 'duration'],
            'default': 'generated_at',
            'description': 'Campo para ordenamiento'
        },
        {
            'name': 'sort_order',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['asc', 'desc'],
            'default': 'desc',
            'description': 'Orden ascendente o descendente'
        },
        {
            'name': 'date_from',
            'in': 'query',
            'type': 'string',
            'format': 'date',
            'required': False,
            'description': 'Filtrar desde fecha (YYYY-MM-DD)'
        },
        {
            'name': 'date_to',
            'in': 'query',
            'type': 'string',
            'format': 'date',
            'required': False,
            'description': 'Filtrar hasta fecha (YYYY-MM-DD)'
        },
        {
            'name': 'favorites_only',
            'in': 'query',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Mostrar solo recetas marcadas como favoritas'
        }
    ],
    'responses': {
        200: {
            'description': 'Galería de recetas generadas obtenida exitosamente',
            'examples': {
                'application/json': {
                    "generated_recipes": [
                        {
                            "recipe_uid": "recipe_gen_123456789",
                            "generation_id": "gen_abc123def456",
                            "title": "Pasta Carbonara con Tomates Cherry",
                            "description": "Deliciosa pasta italiana con tomates cherry frescos del inventario, cremosa salsa carbonara y hierbas aromáticas",
                            "category": "almuerzo",
                            "difficulty": "Intermedio",
                            "duration": "25 min",
                            "servings": 4,
                            "generation_type": "inventory",
                            "generated_at": "2024-01-16T15:30:00Z",
                            "image_path": "https://storage.googleapis.com/bucket/recipe-images/pasta-carbonara-123456789.jpg",
                            "image_status": "ready",
                            "ingredients": [
                                {
                                    "name": "Pasta",
                                    "quantity": 400,
                                    "type_unit": "gr"
                                },
                                {
                                    "name": "Tomates cherry",
                                    "quantity": 200,
                                    "type_unit": "gr"
                                },
                                {
                                    "name": "Huevos",
                                    "quantity": 3,
                                    "type_unit": "unidades"
                                },
                                {
                                    "name": "Queso parmesano",
                                    "quantity": 100,
                                    "type_unit": "gr"
                                }
                            ],
                            "steps": [
                                {
                                    "step_order": 1,
                                    "description": "Hervir agua con sal en una olla grande para la pasta"
                                },
                                {
                                    "step_order": 2,
                                    "description": "Cortar los tomates cherry por la mitad"
                                },
                                {
                                    "step_order": 3,
                                    "description": "Batir los huevos con el queso parmesano rallado"
                                },
                                {
                                    "step_order": 4,
                                    "description": "Cocinar la pasta según instrucciones del paquete hasta al dente"
                                },
                                {
                                    "step_order": 5,
                                    "description": "Saltear los tomates cherry en una sartén con aceite"
                                },
                                {
                                    "step_order": 6,
                                    "description": "Mezclar la pasta caliente con la mezcla de huevo y queso fuera del fuego"
                                },
                                {
                                    "step_order": 7,
                                    "description": "Agregar los tomates cherry salteados y servir inmediatamente"
                                }
                            ],
                            "footer": "Aprovecha los tomates cherry antes de que se estropeen y disfruta de esta deliciosa pasta italiana",
                            "nutritional_info": {
                                "calories_per_serving": 420,
                                "protein_g": 18,
                                "carbs_g": 55,
                                "fat_g": 14
                            },
                            "is_favorite": True,
                            "favorite_data": {
                                "favorite_uid": "fav_123456789",
                                "rating": 5,
                                "notes": "Mi receta favorita de pasta",
                                "favorited_at": "2024-01-15T18:30:00Z"
                            }
                        },
                        {
                            "recipe_uid": "recipe_gen_987654321",
                            "generation_id": "gen_xyz789abc123",
                            "title": "Ensalada Mediterránea de Aguacate",
                            "description": "Ensalada fresca y nutritiva con aguacate, perfecta para aprovechar vegetales del inventario",
                            "category": "ensalada",
                            "difficulty": "Fácil",
                            "duration": "15 min",
                            "servings": 2,
                            "generation_type": "custom",
                            "generated_at": "2024-01-15T12:45:00Z",
                            "image_path": "https://storage.googleapis.com/bucket/recipe-images/ensalada-mediterranea-987654321.jpg",
                            "image_status": "ready",
                            "ingredients": [
                                {
                                    "name": "Aguacate",
                                    "quantity": 2,
                                    "type_unit": "unidades"
                                },
                                {
                                    "name": "Tomate",
                                    "quantity": 300,
                                    "type_unit": "gr"
                                },
                                {
                                    "name": "Pepino",
                                    "quantity": 200,
                                    "type_unit": "gr"
                                },
                                {
                                    "name": "Aceitunas negras",
                                    "quantity": 50,
                                    "type_unit": "gr"
                                }
                            ],
                            "steps": [
                                {
                                    "step_order": 1,
                                    "description": "Cortar el aguacate en cubos medianos"
                                },
                                {
                                    "step_order": 2,
                                    "description": "Picar los tomates en cubos del mismo tamaño"
                                },
                                {
                                    "step_order": 3,
                                    "description": "Cortar el pepino en rodajas finas"
                                },
                                {
                                    "step_order": 4,
                                    "description": "Mezclar todos los ingredientes en un bowl grande"
                                },
                                {
                                    "step_order": 5,
                                    "description": "Aliñar con aceite de oliva, vinagre balsámico y sal"
                                },
                                {
                                    "step_order": 6,
                                    "description": "Servir fresco acompañado de pan pita"
                                }
                            ],
                            "footer": "Una ensalada nutritiva y refrescante que aprovecha al máximo los vegetales frescos",
                            "nutritional_info": {
                                "calories_per_serving": 280,
                                "protein_g": 6,
                                "carbs_g": 15,
                                "fat_g": 24
                            },
                            "is_favorite": False,
                            "favorite_data": None
                        }
                    ],
                    "pagination": {
                        "current_page": 1,
                        "per_page": 20,
                        "total_recipes": 47,
                        "total_pages": 3,
                        "has_next": True,
                        "has_previous": False
                    },
                    "gallery_stats": {
                        "total_generated_recipes": 47,
                        "recipes_with_images": 42,
                        "images_ready": 38,
                        "images_generating": 4,
                        "images_failed": 5,
                        "generation_types": {
                            "inventory": 28,
                            "custom": 19
                        },
                        "categories_distribution": {
                            "almuerzo": 18,
                            "cena": 15,
                            "desayuno": 8,
                            "ensalada": 6
                        },
                        "difficulty_distribution": {
                            "Fácil": 20,
                            "Intermedio": 22,
                            "Difícil": 5
                        },
                        "recent_generations": {
                            "last_7_days": 8,
                            "last_30_days": 23
                        }
                    },
                    "filters_applied": {
                        "image_status": None,
                        "generation_type": None,
                        "category": None,
                        "difficulty": None,
                        "search": None,
                        "date_from": None,
                        "date_to": None,
                        "favorites_only": False
                    },
                    "sort_applied": {
                        "sort_by": "generated_at",
                        "sort_order": "desc"
                    }
                }
            }
        },
        404: {
            'description': 'No se encontraron recetas generadas',
            'examples': {
                'application/json': {
                    'message': 'No generated recipes found',
                    'generated_recipes': [],
                    'gallery_stats': {
                        'total_generated_recipes': 0
                    }
                }
            }
        },
        400: {
            'description': 'Parámetros de filtros inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid filter parameters',
                    'details': {
                        'per_page': 'Debe ser un número entre 1 y 50',
                        'date_from': 'Formato de fecha inválido, use YYYY-MM-DD'
                    }
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno del servidor'
        }
    }
})
def get_generated_recipes_gallery():
    """
    🎨 GALERÍA DE RECETAS GENERADAS: Obtiene todas las recetas generadas del usuario con contenido e imágenes
    """
    user_uid = get_jwt_identity()
    print(f"🎨 [RECIPE GALLERY] Starting gallery request for user: {user_uid}")
    
    try:
        # Obtener parámetros de query
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        image_status = request.args.get('image_status')
        generation_type = request.args.get('generation_type')
        category = request.args.get('category')
        difficulty = request.args.get('difficulty')
        search = request.args.get('search')
        sort_by = request.args.get('sort_by', 'generated_at')
        sort_order = request.args.get('sort_order', 'desc')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        favorites_only = request.args.get('favorites_only', 'false').lower() == 'true'
        
        print(f"🎨 [RECIPE GALLERY] Filters: page={page}, per_page={per_page}, image_status={image_status}")
        
        from src.infrastructure.db.models.recipe_generated_orm import RecipeGeneratedORM
        from src.infrastructure.db.models.recipe_favorites_orm import RecipeFavoritesORM
        from src.infrastructure.db.base import db
        from sqlalchemy import desc, asc, and_, or_
        from datetime import datetime
        
        # Construir query base
        if favorites_only:
            # Si solo queremos favoritos, hacer JOIN con tabla de favoritos
            query = db.session.query(RecipeGeneratedORM).join(
                RecipeFavoritesORM, RecipeGeneratedORM.uid == RecipeFavoritesORM.recipe_uid
            ).filter(
                RecipeGeneratedORM.user_uid == user_uid,
                RecipeFavoritesORM.user_uid == user_uid
            )
        else:
            # Query normal para todas las recetas
            query = db.session.query(RecipeGeneratedORM).filter(
                RecipeGeneratedORM.user_uid == user_uid
            )
        
        # Aplicar filtros
        if image_status:
            query = query.filter(RecipeGeneratedORM.image_status == image_status)
        
        if generation_type:
            query = query.filter(RecipeGeneratedORM.generation_type == generation_type)
        
        if category:
            query = query.filter(RecipeGeneratedORM.category == category)
        
        if difficulty:
            query = query.filter(RecipeGeneratedORM.difficulty == difficulty)
        
        if search:
            search_filter = or_(
                RecipeGeneratedORM.title.contains(search),
                RecipeGeneratedORM.description.contains(search)
            )
            query = query.filter(search_filter)
        
        # Filtros de fecha
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(RecipeGeneratedORM.generated_at >= date_from_obj)
            except ValueError:
                return jsonify({
                    'error': 'Invalid date_from format, use YYYY-MM-DD'
                }), 400
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                query = query.filter(RecipeGeneratedORM.generated_at <= date_to_obj)
            except ValueError:
                return jsonify({
                    'error': 'Invalid date_to format, use YYYY-MM-DD'
                }), 400
        
        # Aplicar ordenamiento
        sort_column = getattr(RecipeGeneratedORM, sort_by, RecipeGeneratedORM.generated_at)
        if sort_order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Obtener conteo total
        total_count = query.count()
        print(f"🎨 [RECIPE GALLERY] Total recipes found: {total_count}")
        
        # Aplicar paginación
        offset = (page - 1) * per_page
        recipes_orm = query.offset(offset).limit(per_page).all()
        
        # Convertir a formato de respuesta
        generated_recipes = []
        
        # Obtener favoritos del usuario para incluir en la respuesta
        from src.infrastructure.db.models.recipe_favorites_orm import RecipeFavoritesORM
        recipe_uids = [recipe_orm.uid for recipe_orm in recipes_orm]
        favorites_query = db.session.query(RecipeFavoritesORM).filter(
            RecipeFavoritesORM.user_uid == user_uid,
            RecipeFavoritesORM.recipe_uid.in_(recipe_uids)
        ).all()
        favorites_map = {fav.recipe_uid: fav for fav in favorites_query}
        
        for recipe_orm in recipes_orm:
            recipe_data = recipe_orm.recipe_data if recipe_orm.recipe_data else {}
            favorite = favorites_map.get(recipe_orm.uid)
            
            recipe_response = {
                "recipe_uid": recipe_orm.uid,
                "generation_id": recipe_orm.generation_id,
                "title": recipe_orm.title,
                "description": recipe_orm.description,
                "category": recipe_orm.category,
                "difficulty": recipe_orm.difficulty,
                "duration": recipe_orm.duration,
                "servings": recipe_orm.servings,
                "generation_type": recipe_orm.generation_type,
                "generated_at": recipe_orm.generated_at.isoformat() if recipe_orm.generated_at else None,
                "image_path": recipe_orm.image_path,
                "image_status": recipe_orm.image_status,
                "ingredients": recipe_data.get('ingredients', []),
                "steps": recipe_data.get('steps', []),
                "footer": recipe_data.get('footer', ''),
                "nutritional_info": recipe_data.get('nutritional_info', {}),
                # Información de favoritos
                "is_favorite": favorite is not None,
                "favorite_data": {
                    "favorite_uid": favorite.uid if favorite else None,
                    "rating": favorite.rating if favorite else None,
                    "notes": favorite.notes if favorite else None,
                    "favorited_at": favorite.favorited_at.isoformat() if favorite else None
                } if favorite else None
            }
            generated_recipes.append(recipe_response)
        
        # Calcular estadísticas de galería
        from sqlalchemy import func
        stats_query = db.session.query(RecipeGeneratedORM).filter(
            RecipeGeneratedORM.user_uid == user_uid
        )
        
        gallery_stats = {
            "total_generated_recipes": total_count,
            "recipes_with_images": stats_query.filter(RecipeGeneratedORM.image_path.isnot(None)).count(),
            "images_ready": stats_query.filter(RecipeGeneratedORM.image_status == 'ready').count(),
            "images_generating": stats_query.filter(RecipeGeneratedORM.image_status == 'generating').count(),
            "images_failed": stats_query.filter(RecipeGeneratedORM.image_status == 'failed').count()
        }
        
        # Estadísticas adicionales
        generation_types = db.session.query(
            RecipeGeneratedORM.generation_type,
            func.count(RecipeGeneratedORM.generation_type)
        ).filter(RecipeGeneratedORM.user_uid == user_uid).group_by(RecipeGeneratedORM.generation_type).all()
        
        gallery_stats["generation_types"] = {gt[0]: gt[1] for gt in generation_types}
        
        # Paginación
        total_pages = (total_count + per_page - 1) // per_page
        pagination = {
            "current_page": page,
            "per_page": per_page,
            "total_recipes": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
        
        response = {
            "generated_recipes": generated_recipes,
            "pagination": pagination,
            "gallery_stats": gallery_stats,
            "filters_applied": {
                "image_status": image_status,
                "generation_type": generation_type,
                "category": category,
                "difficulty": difficulty,
                "search": search,
                "date_from": date_from,
                "date_to": date_to,
                "favorites_only": favorites_only
            },
            "sort_applied": {
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
        
        print(f"✅ [RECIPE GALLERY] Successfully retrieved {len(generated_recipes)} recipes")
        return jsonify(response), 200
        
    except Exception as e:

        
        error_details = {

        
            "error_type": type(e).__name__,

        
            "error_message": str(e),

        
            "traceback": str(e.__traceback__.tb_frame.f_code.co_filename) + ":" + str(e.__traceback__.tb_lineno) if e.__traceback__ else "No traceback"

        
        }

        
        

        
        # Log the detailed error

        
        print(f"ERROR: {error_details}")

        
        

        import traceback
        print(f"🚨 [RECIPE GALLERY] Error: {str(e)}")
        print(f"🚨 [RECIPE GALLERY] Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": "Failed to retrieve generated recipes gallery",
            "details": str(e),
            "error_type": type(e).__name__
        }), 500


@recipes_bp.route("/default", methods=["GET"])
@swag_from({
    'tags': ['Recipes'],
    'summary': 'Obtener recetas por defecto del sistema',
    'description': '''
Obtiene las recetas por defecto curadas que están disponibles para todos los usuarios.
Estas recetas están organizadas por categorías y no requieren autenticación.

### Categorías Disponibles:
- **Destacadas**: Las mejores recetas seleccionadas
- **Rápidas y Fáciles**: Recetas de preparación rápida
- **Vegetarianas**: Opciones sin carne
- **Postres**: Dulces y postres clásicos
- **Saludables**: Recetas nutritivas y balanceadas

### Características:
- **Sin autenticación**: Accesible sin login
- **Curadas**: Recetas seleccionadas y probadas
- **Completas**: Incluyen ingredientes, pasos, tiempos y dificultad
- **Categorizadas**: Organizadas para fácil navegación
- **Inspiración**: Perfectas para descubrir nuevas ideas

### Casos de Uso:
- Explorar recetas sin crear cuenta
- Obtener inspiración culinaria
- Acceder a recetas básicas y populares
- Navegar por categorías específicas
- Descubrir nuevas preparaciones
    ''',
    'parameters': [
        {
            'name': 'category',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['destacadas', 'rapidas_faciles', 'vegetarianas', 'postres', 'saludables'],
            'description': 'Filtrar por categoría específica',
            'example': 'destacadas'
        }
    ],
    'responses': {
        200: {
            'description': 'Recetas por defecto obtenidas exitosamente',
            'examples': {
                'application/json': {
                    "default_recipes": [
                        {
                            "uid": "default_recipe_001",
                            "title": "Pasta Carbonara Clásica",
                            "duration": "30 minutos",
                            "difficulty": "Intermedio",
                            "category": "almuerzo",
                            "description": "La auténtica receta italiana de carbonara con huevos, bacon y queso parmesano. Cremosa y deliciosa.",
                            "ingredients": [
                                {
                                    "name": "Pasta (espaguetis)",
                                    "quantity": 400,
                                    "type_unit": "gr"
                                },
                                {
                                    "name": "Huevos",
                                    "quantity": 4,
                                    "type_unit": "unidades"
                                },
                                {
                                    "name": "Bacon o panceta",
                                    "quantity": 200,
                                    "type_unit": "gr"
                                }
                            ],
                            "steps": [
                                {
                                    "step_order": 1,
                                    "description": "Cocinar la pasta en agua con sal hasta que esté al dente"
                                },
                                {
                                    "step_order": 2,
                                    "description": "Freír el bacon hasta que esté crujiente y reservar"
                                }
                            ],
                            "footer": "Un clásico italiano que nunca falla",
                            "generated_by_ai": False,
                            "image_status": "pending",
                            "saved_at": "2024-01-15T10:00:00Z"
                        }
                    ],
                    "categories_summary": {
                        "destacadas": 3,
                        "rapidas_faciles": 3,
                        "vegetarianas": 3,
                        "postres": 3,
                        "saludables": 2
                    },
                    "total_recipes": 14,
                    "filter_applied": {
                        "category": None
                    }
                }
            }
        },
        404: {
            'description': 'No se encontraron recetas por defecto',
            'examples': {
                'application/json': {
                    'message': 'No default recipes found',
                    'default_recipes': [],
                    'total_recipes': 0
                }
            }
        },
        500: {
            'description': 'Error interno del servidor'
        }
    }
})
def get_default_recipes():
    """
    Obtiene las recetas por defecto del sistema.
    No requiere autenticación ya que son recetas públicas.
    """
    from src.infrastructure.db.models.recipe_orm import RecipeORM
    from src.infrastructure.db.models.recipe_ingredient_orm import RecipeIngredientORM
    from src.infrastructure.db.models.recipe_step_orm import RecipeStepORM
    from src.infrastructure.db.base import db
    from sqlalchemy import select
    
    # UID especial para recetas del sistema
    SYSTEM_USER_UID = "SYSTEM_DEFAULT_RECIPES"
    
    try:
        # Obtener parámetro de categoría opcional
        category_filter = request.args.get('category')
        
        # Construir query base con eager loading para evitar N+1 queries
        query = select(RecipeORM).options(
            joinedload(RecipeORM.ingredients)
        ).where(RecipeORM.user_uid == SYSTEM_USER_UID)
        
        # Aplicar filtro de categoría si se especifica
        if category_filter:
            # Mapear categorías de query a categorías de base de datos
            category_mapping = {
                'destacadas': ['almuerzo', 'cena', 'ensalada'],
                'rapidas_faciles': ['almuerzo', 'desayuno'],
                'vegetarianas': ['cena', 'ensalada', 'almuerzo'],
                'postres': ['postre'],
                'saludables': ['almuerzo', 'cena']
            }
            
            if category_filter in category_mapping:
                db_categories = category_mapping[category_filter]
                query = query.where(RecipeORM.category.in_(db_categories))
        
        # Ejecutar query
        result = db.session.execute(query)
        recipes_orm = result.scalars().all()
        
        if not recipes_orm:
            return jsonify({
                "message": "No default recipes found",
                "default_recipes": [],
                "total_recipes": 0
            }), 404
        
        # Convertir a formato de respuesta
        default_recipes = []
        categories_count = {}
        
        for recipe_orm in recipes_orm:
            # Obtener ingredientes
            ingredients = []
            for ing in recipe_orm.ingredients:
                ingredients.append({
                    "name": ing.name,
                    "quantity": ing.quantity,
                    "type_unit": ing.type_unit
                })
            
            # Obtener pasos ordenados
            steps = []
            sorted_steps = sorted(recipe_orm.steps, key=lambda s: s.step_order)
            for step in sorted_steps:
                steps.append({
                    "step_order": step.step_order,
                    "description": step.description
                })
            
            # Construir objeto receta
            recipe_data = {
                "uid": recipe_orm.uid,
                "title": recipe_orm.title,
                "duration": recipe_orm.duration,
                "difficulty": recipe_orm.difficulty,
                "category": recipe_orm.category,
                "description": recipe_orm.description,
                "ingredients": ingredients,
                "steps": steps,
                "footer": recipe_orm.footer,
                "generated_by_ai": recipe_orm.generated_by_ai,
                "image_status": recipe_orm.image_status,
                "image_path": recipe_orm.image_path,
                "saved_at": recipe_orm.saved_at.isoformat() if recipe_orm.saved_at else None
            }
            
            default_recipes.append(recipe_data)
            
            # Contar categorías
            category = recipe_orm.category
            categories_count[category] = categories_count.get(category, 0) + 1
        
        return jsonify({
            "default_recipes": default_recipes,
            "categories_summary": categories_count,
            "total_recipes": len(default_recipes),
            "filter_applied": {
                "category": category_filter
            }
        }), 200
        
    except Exception as e:

        
        error_details = {

        
            "error_type": type(e).__name__,

        
            "error_message": str(e),

        
            "traceback": str(e.__traceback__.tb_frame.f_code.co_filename) + ":" + str(e.__traceback__.tb_lineno) if e.__traceback__ else "No traceback"

        
        }

        
        

        
        # Log the detailed error

        
        print(f"ERROR: {error_details}")

        
        

        print(f"❌ [DEFAULT RECIPES] Error: {str(e)}")
        return jsonify({
            "error": "Failed to fetch default recipes",
            "details": str(e)
        }), 500


@recipes_bp.route("/generated/<recipe_uid>/favorite", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Recipe Favorites'],
    'summary': 'Marcar receta generada como favorita',
    'description': '''
Marca una receta generada como favorita para el usuario autenticado.

### Funcionalidad:
- **Favoritos personales**: Cada usuario tiene sus propios favoritos
- **Prevención de duplicados**: No permite marcar la misma receta dos veces
- **Metadatos opcionales**: Permite agregar rating y notas personales
- **Validación de propiedad**: Solo se pueden marcar recetas del usuario actual

### Casos de Uso:
- Guardar recetas que te gustaron para acceso rápido
- Crear una colección personal de mejores recetas
- Organizar recetas por preferencias personales
- Facilitar la re-preparación de platos favoritos
    ''',
    'parameters': [
        {
            'name': 'recipe_uid',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'UID de la receta generada a marcar como favorita',
            'example': 'recipe_123456789'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': False,
            'schema': {
                'type': 'object',
                'properties': {
                    'rating': {
                        'type': 'integer',
                        'minimum': 1,
                        'maximum': 5,
                        'description': 'Rating personal de 1 a 5 estrellas',
                        'example': 4
                    },
                    'notes': {
                        'type': 'string',
                        'maxLength': 500,
                        'description': 'Notas personales sobre la receta',
                        'example': 'Deliciosa, la próxima vez agregaré más especias'
                    }
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Receta marcada como favorita exitosamente',
            'examples': {
                'application/json': {
                    "message": "Receta marcada como favorita",
                    "favorite": {
                        "uid": "fav_123456789",
                        "recipe_uid": "recipe_123456789",
                        "user_uid": "firebase_user_123",
                        "rating": 4,
                        "notes": "Deliciosa, la próxima vez agregaré más especias",
                        "favorited_at": "2024-01-16T10:30:00Z"
                    }
                }
            }
        },
        400: {
            'description': 'Datos inválidos o receta ya marcada como favorita',
            'examples': {
                'application/json': {
                    'error': 'Recipe already favorited',
                    'details': 'Esta receta ya está en tus favoritos'
                }
            }
        },
        404: {
            'description': 'Receta no encontrada',
            'examples': {
                'application/json': {
                    'error': 'Recipe not found',
                    'recipe_uid': 'recipe_invalid123'
                }
            }
        }
    }
})
def add_recipe_to_favorites(recipe_uid):
    from src.infrastructure.db.models.recipe_generated_orm import RecipeGeneratedORM
    from src.infrastructure.db.models.recipe_favorites_orm import RecipeFavoritesORM
    from src.infrastructure.db.base import db
    
    user_uid = get_jwt_identity()
    print(f"⭐ [ADD FAVORITE] User: {user_uid}, Recipe: {recipe_uid}")
    
    try:
        # Verificar que la receta existe y pertenece al usuario
        recipe = RecipeGeneratedORM.query.filter_by(
            uid=recipe_uid,
            user_uid=user_uid
        ).first()
        
        if not recipe:
            return jsonify({
                "error": "Recipe not found",
                "recipe_uid": recipe_uid
            }), 404
        
        # Verificar si ya está marcada como favorita
        existing_favorite = RecipeFavoritesORM.query.filter_by(
            user_uid=user_uid,
            recipe_uid=recipe_uid
        ).first()
        
        if existing_favorite:
            return jsonify({
                "error": "Recipe already favorited",
                "details": "Esta receta ya está en tus favoritos",
                "favorite_uid": existing_favorite.uid
            }), 400
        
        # Obtener datos opcionales del body
        data = request.get_json() or {}
        rating = data.get('rating')
        notes = data.get('notes')
        
        # Validar rating
        if rating is not None and (not isinstance(rating, int) or rating < 1 or rating > 5):
            return jsonify({
                "error": "Invalid rating",
                "details": "Rating debe ser un número entero entre 1 y 5"
            }), 400
        
        # Crear nuevo favorito
        new_favorite = RecipeFavoritesORM(
            uid=str(uuid.uuid4()),
            user_uid=user_uid,
            recipe_uid=recipe_uid,
            rating=rating,
            notes=notes,
            favorited_at=datetime.now(timezone.utc)
        )
        
        db.session.add(new_favorite)
        db.session.commit()
        
        return jsonify({
            "message": "Receta marcada como favorita",
            "favorite": {
                "uid": new_favorite.uid,
                "recipe_uid": recipe_uid,
                "user_uid": user_uid,
                "rating": rating,
                "notes": notes,
                "favorited_at": new_favorite.favorited_at.isoformat()
            }
        }), 201
        
    except Exception as e:

        
        error_details = {

        
            "error_type": type(e).__name__,

        
            "error_message": str(e),

        
            "traceback": str(e.__traceback__.tb_frame.f_code.co_filename) + ":" + str(e.__traceback__.tb_lineno) if e.__traceback__ else "No traceback"

        
        }

        
        

        
        # Log the detailed error

        
        print(f"ERROR: {error_details}")

        
        

        db.session.rollback()
        print(f"❌ [ADD FAVORITE] Error: {str(e)}")
        return jsonify({
            "error": "Failed to add favorite",
            "details": str(e)
        }), 500


@recipes_bp.route("/generated/<recipe_uid>/favorite", methods=["DELETE"])
@jwt_required()
@swag_from({
    'tags': ['Recipe Favorites'],
    'summary': 'Desmarcar receta como favorita',
    'description': '''
Elimina una receta de la lista de favoritos del usuario autenticado.

### Funcionalidad:
- **Eliminación segura**: Solo el usuario propietario puede desmarcar
- **Validación de existencia**: Verifica que el favorito existe antes de eliminar
- **Limpieza completa**: Elimina completamente el registro de favorito
- **Idempotente**: No genera error si la receta ya no está en favoritos

### Casos de Uso:
- Limpiar lista de favoritos de recetas que ya no interesan
- Reorganizar colección personal de recetas
- Corregir marcados accidentales como favoritos
- Mantenimiento de lista de favoritos actualizada
    ''',
    'parameters': [
        {
            'name': 'recipe_uid',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'UID de la receta a desmarcar como favorita',
            'example': 'recipe_123456789'
        }
    ],
    'responses': {
        200: {
            'description': 'Receta desmarcada exitosamente',
            'examples': {
                'application/json': {
                    "message": "Receta desmarcada de favoritos",
                    "recipe_uid": "recipe_123456789"
                }
            }
        },
        404: {
            'description': 'Favorito no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Favorite not found',
                    'details': 'Esta receta no está en tus favoritos'
                }
            }
        }
    }
})
def remove_recipe_from_favorites(recipe_uid):
    from src.infrastructure.db.models.recipe_favorites_orm import RecipeFavoritesORM
    from src.infrastructure.db.base import db
    
    user_uid = get_jwt_identity()
    print(f"❌ [REMOVE FAVORITE] User: {user_uid}, Recipe: {recipe_uid}")
    
    try:
        # Buscar el favorito
        favorite = RecipeFavoritesORM.query.filter_by(
            user_uid=user_uid,
            recipe_uid=recipe_uid
        ).first()
        
        if not favorite:
            return jsonify({
                "error": "Favorite not found",
                "details": "Esta receta no está en tus favoritos"
            }), 404
        
        # Eliminar favorito
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({
            "message": "Receta desmarcada de favoritos",
            "recipe_uid": recipe_uid
        }), 200
        
    except Exception as e:

        
        error_details = {

        
            "error_type": type(e).__name__,

        
            "error_message": str(e),

        
            "traceback": str(e.__traceback__.tb_frame.f_code.co_filename) + ":" + str(e.__traceback__.tb_lineno) if e.__traceback__ else "No traceback"

        
        }

        
        

        
        # Log the detailed error

        
        print(f"ERROR: {error_details}")

        
        

        db.session.rollback()
        print(f"❌ [REMOVE FAVORITE] Error: {str(e)}")
        return jsonify({
            "error": "Failed to remove favorite",
            "details": str(e)
        }), 500


@recipes_bp.route("/generated/favorites", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Recipe Favorites'],
    'summary': 'Obtener todas las recetas favoritas del usuario',
    'description': '''
Obtiene la lista completa de recetas marcadas como favoritas por el usuario autenticado.

### Funcionalidades de Listado:
- **Paginación**: Control de página y límite de resultados
- **Ordenamiento**: Por fecha de favorito, rating, nombre o dificultad
- **Filtros**: Por categoría, dificultad, rating mínimo, tipo de generación
- **Búsqueda**: Buscar por nombre de receta o ingredientes
- **Metadata completa**: Incluye datos del favorito (rating, notas, fecha)

### Datos Incluidos:
- **Receta completa**: Todos los datos de la receta (ingredientes, pasos, etc.)
- **Metadata de favorito**: Rating personal, notas, fecha de marcado
- **Estado de imágenes**: URLs e información de imágenes generadas
- **Estadísticas**: Resumen de favoritos por categoría y rating

### Casos de Uso:
- Mostrar colección personal de mejores recetas
- Búsqueda rápida en recetas que gustan al usuario
- Planificación de menús basada en favoritos
- Análisis de preferencias personales de cocina
    ''',
    'parameters': [
        {
            'name': 'page',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 1,
            'description': 'Número de página para paginación',
            'example': 1
        },
        {
            'name': 'limit',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 20,
            'minimum': 1,
            'maximum': 100,
            'description': 'Número de recetas por página',
            'example': 20
        },
        {
            'name': 'sort_by',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['favorited_at', 'rating', 'recipe_name', 'generated_at'],
            'default': 'favorited_at',
            'description': 'Campo para ordenamiento',
            'example': 'favorited_at'
        },
        {
            'name': 'sort_order',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['desc', 'asc'],
            'default': 'desc',
            'description': 'Orden de clasificación',
            'example': 'desc'
        },
        {
            'name': 'category',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Filtrar por categoría de receta',
            'example': 'almuerzo'
        },
        {
            'name': 'min_rating',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'minimum': 1,
            'maximum': 5,
            'description': 'Rating mínimo para filtrar',
            'example': 4
        },
        {
            'name': 'search',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Buscar en nombre de receta',
            'example': 'pasta'
        }
    ],
    'responses': {
        200: {
            'description': 'Lista de recetas favoritas obtenida exitosamente',
            'examples': {
                'application/json': {
                    "favorites": [
                        {
                            "favorite_uid": "fav_123456789",
                            "rating": 5,
                            "notes": "Mi receta favorita de pasta",
                            "favorited_at": "2024-01-16T10:30:00Z",
                            "recipe": {
                                "uid": "recipe_123456789",
                                "title": "Pasta Carbonara Gourmet",
                                "description": "Pasta cremosa con panceta y huevos",
                                "duration": "25 minutos",
                                "difficulty": "intermedio",
                                "servings": 4,
                                "category": "almuerzo",
                                "generated_at": "2024-01-15T14:20:00Z",
                                "image_path": "https://storage.googleapis.com/bucket/recipe_123.jpg",
                                "image_status": "ready",
                                "generation_type": "inventory",
                                "recipe_data": {
                                    "ingredients": [
                                        {
                                            "name": "pasta",
                                            "quantity": 400,
                                            "unit": "gr"
                                        },
                                        {
                                            "name": "panceta",
                                            "quantity": 150,
                                            "unit": "gr"
                                        }
                                    ],
                                    "steps": [
                                        "Hervir agua con sal para la pasta",
                                        "Cocinar la panceta hasta dorar",
                                        "Mezclar pasta con huevos y queso"
                                    ]
                                }
                            }
                        }
                    ],
                    "pagination": {
                        "current_page": 1,
                        "total_pages": 3,
                        "total_favorites": 45,
                        "favorites_per_page": 20,
                        "has_next": True,
                        "has_prev": False
                    },
                    "statistics": {
                        "total_favorites": 45,
                        "average_rating": 4.2,
                        "categories_count": {
                            "almuerzo": 18,
                            "cena": 15,
                            "desayuno": 8,
                            "postre": 4
                        },
                        "ratings_distribution": {
                            "5": 20,
                            "4": 15,
                            "3": 8,
                            "2": 2,
                            "1": 0
                        }
                    },
                    "filters_applied": {
                        "sort_by": "favorited_at",
                        "sort_order": "desc",
                        "category": None,
                        "min_rating": None,
                        "search": None
                    }
                }
            }
        }
    }
})
def get_user_favorite_recipes():
    from src.infrastructure.db.models.recipe_favorites_orm import RecipeFavoritesORM
    from src.infrastructure.db.models.recipe_generated_orm import RecipeGeneratedORM
    from src.infrastructure.db.base import db
    from sqlalchemy import desc, asc
    
    user_uid = get_jwt_identity()
    print(f"⭐ [GET FAVORITES] User: {user_uid}")
    
    try:
        # Parámetros de query
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)
        sort_by = request.args.get('sort_by', 'favorited_at')
        sort_order = request.args.get('sort_order', 'desc')
        category_filter = request.args.get('category')
        min_rating = request.args.get('min_rating')
        search = request.args.get('search')
        
        # Query base con JOIN
        query = db.session.query(RecipeFavoritesORM, RecipeGeneratedORM).join(
            RecipeGeneratedORM, RecipeFavoritesORM.recipe_uid == RecipeGeneratedORM.uid
        ).filter(RecipeFavoritesORM.user_uid == user_uid)
        
        # Aplicar filtros
        if category_filter:
            query = query.filter(RecipeGeneratedORM.category == category_filter)
        
        if min_rating:
            try:
                min_rating_int = int(min_rating)
                query = query.filter(RecipeFavoritesORM.rating >= min_rating_int)
            except ValueError:
                pass
        
        if search:
            query = query.filter(RecipeGeneratedORM.title.contains(search))
        
        # Aplicar ordenamiento
        if sort_by == 'favorited_at':
            sort_field = RecipeFavoritesORM.favorited_at
        elif sort_by == 'rating':
            sort_field = RecipeFavoritesORM.rating
        elif sort_by == 'recipe_name':
            sort_field = RecipeGeneratedORM.title
        elif sort_by == 'generated_at':
            sort_field = RecipeGeneratedORM.generated_at
        else:
            sort_field = RecipeFavoritesORM.favorited_at
        
        if sort_order == 'desc':
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))
        
        # Paginación
        offset = (page - 1) * limit
        total_query = query
        total_count = total_query.count()
        
        results = query.offset(offset).limit(limit).all()
        
        # Construir respuesta
        favorites_list = []
        categories_count = {}
        ratings_distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        total_rating = 0
        rated_count = 0
        
        for favorite, recipe in results:
            # Contar estadísticas
            category = recipe.category or "sin_categoria"
            categories_count[category] = categories_count.get(category, 0) + 1
            
            if favorite.rating:
                ratings_distribution[str(favorite.rating)] += 1
                total_rating += favorite.rating
                rated_count += 1
            
            # Construir objeto favorito
            favorite_data = {
                "favorite_uid": favorite.uid,
                "rating": favorite.rating,
                "notes": favorite.notes,
                "favorited_at": favorite.favorited_at.isoformat(),
                "recipe": {
                    "uid": recipe.uid,
                    "title": recipe.title,
                    "description": recipe.description,
                    "duration": recipe.duration,
                    "difficulty": recipe.difficulty,
                    "servings": recipe.servings,
                    "category": recipe.category,
                    "generated_at": recipe.generated_at.isoformat(),
                    "image_path": recipe.image_path,
                    "image_status": recipe.image_status,
                    "generation_type": recipe.generation_type,
                    "recipe_data": recipe.recipe_data
                }
            }
            
            favorites_list.append(favorite_data)
        
        # Calcular paginación
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        # Calcular estadísticas
        avg_rating = round(total_rating / rated_count, 1) if rated_count > 0 else 0
        
        return jsonify({
            "favorites": favorites_list,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_favorites": total_count,
                "favorites_per_page": limit,
                "has_next": has_next,
                "has_prev": has_prev
            },
            "statistics": {
                "total_favorites": total_count,
                "average_rating": avg_rating,
                "categories_count": categories_count,
                "ratings_distribution": ratings_distribution
            },
            "filters_applied": {
                "sort_by": sort_by,
                "sort_order": sort_order,
                "category": category_filter,
                "min_rating": min_rating,
                "search": search
            }
        }), 200
        
    except Exception as e:

        
        error_details = {

        
            "error_type": type(e).__name__,

        
            "error_message": str(e),

        
            "traceback": str(e.__traceback__.tb_frame.f_code.co_filename) + ":" + str(e.__traceback__.tb_lineno) if e.__traceback__ else "No traceback"

        
        }

        
        

        
        # Log the detailed error

        
        print(f"ERROR: {error_details}")

        
        

        print(f"❌ [GET FAVORITES] Error: {str(e)}")
        return jsonify({
            "error": "Failed to fetch favorites",
            "details": str(e)
        }), 500


@recipes_bp.route("/generated/<recipe_uid>/favorite", methods=["PUT"])
@jwt_required()
@swag_from({
    'tags': ['Recipe Favorites'],
    'summary': 'Actualizar rating y notas de receta favorita',
    'description': '''
Actualiza el rating personal y/o notas de una receta ya marcada como favorita.

### Funcionalidad:
- **Actualización parcial**: Permite actualizar solo rating o solo notas
- **Validación de existencia**: Verifica que la receta esté marcada como favorita
- **Validación de propiedad**: Solo el usuario propietario puede actualizar
- **Flexibilidad**: Acepta campos opcionales en el body

### Casos de Uso:
- Actualizar rating después de preparar la receta nuevamente
- Agregar notas con mejoras o variaciones probadas
- Corregir rating inicial después de más experiencia
- Documentar modificaciones exitosas a la receta original
    ''',
    'parameters': [
        {
            'name': 'recipe_uid',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'UID de la receta favorita a actualizar',
            'example': 'recipe_123456789'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'rating': {
                        'type': 'integer',
                        'minimum': 1,
                        'maximum': 5,
                        'description': 'Nuevo rating personal de 1 a 5 estrellas',
                        'example': 5
                    },
                    'notes': {
                        'type': 'string',
                        'maxLength': 500,
                        'description': 'Nuevas notas personales sobre la receta',
                        'example': 'Excelente! Agregué un poco más de ajo y quedó perfecta'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Favorito actualizado exitosamente',
            'examples': {
                'application/json': {
                    "message": "Favorito actualizado exitosamente",
                    "favorite": {
                        "uid": "fav_123456789",
                        "recipe_uid": "recipe_123456789",
                        "user_uid": "firebase_user_123",
                        "rating": 5,
                        "notes": "Excelente! Agregué un poco más de ajo y quedó perfecta",
                        "favorited_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-16T14:45:00Z"
                    }
                }
            }
        },
        400: {
            'description': 'Datos inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid rating',
                    'details': 'Rating debe ser un número entero entre 1 y 5'
                }
            }
        },
        404: {
            'description': 'Favorito no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Favorite not found',
                    'details': 'Esta receta no está en tus favoritos'
                }
            }
        }
    }
})
def update_recipe_favorite(recipe_uid):
    from src.infrastructure.db.models.recipe_favorites_orm import RecipeFavoritesORM
    from src.infrastructure.db.base import db
    
    user_uid = get_jwt_identity()
    print(f"✏️ [UPDATE FAVORITE] User: {user_uid}, Recipe: {recipe_uid}")
    
    try:
        # Buscar el favorito
        favorite = RecipeFavoritesORM.query.filter_by(
            user_uid=user_uid,
            recipe_uid=recipe_uid
        ).first()
        
        if not favorite:
            return jsonify({
                "error": "Favorite not found",
                "details": "Esta receta no está en tus favoritos"
            }), 404
        
        # Obtener datos del body
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "No data provided",
                "details": "Se requiere enviar al menos rating o notes"
            }), 400
        
        # Validar y actualizar campos
        if 'rating' in data:
            rating = data['rating']
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                return jsonify({
                    "error": "Invalid rating",
                    "details": "Rating debe ser un número entero entre 1 y 5"
                }), 400
            favorite.rating = rating
        
        if 'notes' in data:
            notes = data['notes']
            if isinstance(notes, str) and len(notes) <= 500:
                favorite.notes = notes
            elif isinstance(notes, str):
                return jsonify({
                    "error": "Notes too long",
                    "details": "Las notas no pueden exceder 500 caracteres"
                }), 400
        
        # Guardar cambios
        db.session.commit()
        
        return jsonify({
            "message": "Favorito actualizado exitosamente",
            "favorite": {
                "uid": favorite.uid,
                "recipe_uid": recipe_uid,
                "user_uid": user_uid,
                "rating": favorite.rating,
                "notes": favorite.notes,
                "favorited_at": favorite.favorited_at.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }), 200
        
    except Exception as e:

        
        error_details = {

        
            "error_type": type(e).__name__,

        
            "error_message": str(e),

        
            "traceback": str(e.__traceback__.tb_frame.f_code.co_filename) + ":" + str(e.__traceback__.tb_lineno) if e.__traceback__ else "No traceback"

        
        }

        
        

        
        # Log the detailed error

        
        print(f"ERROR: {error_details}")

        
        

        db.session.rollback()
        print(f"❌ [UPDATE FAVORITE] Error: {str(e)}")
        return jsonify({
            "error": "Failed to update favorite",
            "details": str(e)
        }), 500
