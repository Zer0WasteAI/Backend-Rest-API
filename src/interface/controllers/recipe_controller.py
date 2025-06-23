from flasgger import swag_from # type: ignore
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.application.factories.generation_usecase_factory import make_generation_repository
from src.domain.models.generation import Generation
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
    make_recipe_image_generator_service
)

from src.infrastructure.async_tasks.async_task_service import async_task_service
from src.shared.exceptions.custom import InvalidRequestDataException
from datetime import datetime, timezone
import uuid

recipes_bp = Blueprint("recipes", __name__)

@recipes_bp.route("/generate-from-inventory", methods=["POST"])
@jwt_required()
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

@recipes_bp.route("/save", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Recipes'],
    'summary': 'Guardar receta en favoritos del usuario',
    'description': '''
Guarda una receta generada o externa en la colección personal de recetas favoritas del usuario.

### Funcionalidades:
- **Guardado personalizado**: Almacena recetas con metadata del usuario
- **Categorización**: Organiza recetas por categorías personalizadas
- **Modificación permitida**: Permite editar la receta antes de guardarla
- **Búsqueda futura**: Indexa para búsquedas rápidas posteriores
- **Sincronización**: Mantiene consistencia entre dispositivos

### Tipos de Recetas Soportadas:
- **Generadas por IA**: Recetas creadas por el sistema
- **Importadas**: Recetas de fuentes externas
- **Modificadas**: Versiones editadas de recetas existentes
- **Originales**: Recetas creadas completamente por el usuario

### Datos Adicionales Almacenados:
- Fecha y hora de guardado
- Frecuencia de uso
- Valoraciones personales
- Notas y modificaciones del usuario
- Historial de preparación

### Casos de Uso:
- Guardar recetas generadas que gustaron
- Crear biblioteca personal de recetas
- Organizar recetas por ocasiones o dietas
- Compartir recetas favoritas con otros usuarios
- Tracking de recetas más utilizadas
    ''',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['recipe'],
                'properties': {
                    'recipe': {
                        'type': 'object',
                        'description': 'Datos completos de la receta a guardar',
                        'required': ['name', 'ingredients', 'instructions'],
                        'properties': {
                            'name': {
                                'type': 'string',
                                'description': 'Nombre de la receta',
                                'example': 'Pasta carbonara casera'
                            },
                            'description': {
                                'type': 'string',
                                'description': 'Descripción de la receta',
                                'example': 'Una deliciosa pasta italiana con huevos y bacon'
                            },
                            'ingredients': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'name': {'type': 'string'},
                                        'quantity': {'type': 'number'},
                                        'unit': {'type': 'string'}
                                    }
                                },
                                'description': 'Lista de ingredientes'
                            },
                            'instructions': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'step': {'type': 'integer'},
                                        'description': {'type': 'string'},
                                        'time': {'type': 'integer'},
                                        'temperature': {'type': 'string'}
                                    }
                                },
                                'description': 'Pasos de preparación'
                            },
                            'prep_time': {
                                'type': 'integer',
                                'description': 'Tiempo de preparación en minutos'
                            },
                            'servings': {
                                'type': 'integer',
                                'description': 'Número de porciones'
                            },
                            'difficulty': {
                                'type': 'string',
                                'enum': ['fácil', 'intermedio', 'avanzado'],
                                'description': 'Nivel de dificultad'
                            },
                            'cuisine_type': {
                                'type': 'string',
                                'description': 'Tipo de cocina'
                            },
                            'tags': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'description': 'Etiquetas personalizadas'
                            }
                        }
                    },
                    'user_notes': {
                        'type': 'string',
                        'description': 'Notas personales sobre la receta (opcional)',
                        'example': 'Receta favorita para domingos familiares'
                    },
                    'rating': {
                        'type': 'integer',
                        'minimum': 1,
                        'maximum': 5,
                        'description': 'Valoración personal (1-5 estrellas)',
                        'example': 5
                    },
                    'custom_category': {
                        'type': 'string',
                        'description': 'Categoría personalizada del usuario',
                        'example': 'Comidas familiares'
                    }
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Receta guardada exitosamente',
            'examples': {
                'application/json': {
                    "message": "Receta guardada exitosamente en tu colección",
                    "recipe_uid": "user_recipe_123456789",
                    "saved_recipe": {
                        "name": "Pasta carbonara casera",
                        "description": "Una deliciosa pasta italiana con huevos y bacon",
                        "recipe_uid": "user_recipe_123456789",
                        "user_uid": "firebase_uid_123",
                        "saved_at": "2024-01-16T16:00:00Z",
                        "prep_time": 30,
                        "servings": 4,
                        "difficulty": "intermedio",
                        "cuisine_type": "italiana",
                        "user_rating": 5,
                        "user_notes": "Receta favorita para domingos familiares",
                        "custom_category": "Comidas familiares",
                        "tags": ["pasta", "italiana", "familiar", "rápida"],
                        "usage_stats": {
                            "times_prepared": 0,
                            "last_prepared": None,
                            "favorite": True
                        }
                    },
                    "collection_stats": {
                        "total_saved_recipes": 25,
                        "recipes_in_category": 6,
                        "average_rating": 4.3
                    }
                }
            }
        },
        400: {
            'description': 'Datos de receta inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid recipe data',
                    'details': 'La receta debe incluir nombre, ingredientes e instrucciones'
                }
            }
        },
        409: {
            'description': 'Receta ya existe en la colección',
            'examples': {
                'application/json': {
                    'error': 'Recipe already saved',
                    'details': 'Ya tienes una receta con el mismo nombre en tu colección',
                    'existing_recipe_uid': 'user_recipe_987654321'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno al guardar la receta'
        }
    }
})
def save_recipe():
    user_uid = get_jwt_identity()
    schema = SaveRecipeRequestSchema()
    json_data = request.get_json()

    errors = schema.validate(json_data)
    if errors:
        raise InvalidRequestDataException(details=errors)

    use_case = make_save_recipe_use_case()
    saved_recipe = use_case.execute(user_uid, json_data)

    recipe_schema = RecipeSchema()
    result = recipe_schema.dump(saved_recipe)

    return jsonify({
        "message": "Receta guardada exitosamente",
        "recipe": result
    }), 201

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
        
        # Construir query base
        query = select(RecipeORM).where(RecipeORM.user_uid == SYSTEM_USER_UID)
        
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
        print(f"❌ [DEFAULT RECIPES] Error: {str(e)}")
        return jsonify({
            "error": "Failed to fetch default recipes",
            "details": str(e)
        }), 500
