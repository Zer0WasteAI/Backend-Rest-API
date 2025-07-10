from flasgger import swag_from # type: ignore
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
import uuid

from src.interface.serializers.planning_serializers import SaveMealPlanRequestSchema, MealPlanSchema
from src.application.factories.planning_usecase_factory import (
    make_save_meal_plan_use_case,
    make_update_meal_plan_use_case,
    make_delete_meal_plan_use_case,
    make_get_meal_plan_by_date_use_case,
    make_get_all_meal_plans_use_case,
    make_get_meal_plan_dates_use_case,
)
from src.application.factories.recipe_usecase_factory import make_recipe_image_generator_service
from src.infrastructure.async_tasks.async_task_service import async_task_service
from src.shared.exceptions.custom import InvalidRequestDataException

planning_bp = Blueprint("planning", __name__)

@planning_bp.route("/save", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Planning'],
    'summary': 'Guardar plan de comidas',
    'description': '''
Guarda un plan de comidas completo para una fecha específica del usuario.

### Funcionalidades:
- **Planificación por fecha**: Organiza comidas por día específico
- **Múltiples comidas**: Desayuno, almuerzo, cena, snacks
- **Recetas vinculadas**: Conecta con recetas generadas o guardadas
- **Flexibilidad**: Permite comidas personalizadas o desde inventario

### Estructura del Plan:
- **Fecha específica**: Una fecha por plan
- **Comidas organizadas**: Por tipo de comida (desayuno, almuerzo, etc.)
- **Detalles completos**: Nombre, descripción, ingredientes, tiempo
- **Vinculación**: Puede referenciar recetas existentes

### Casos de Uso:
- Planificar comidas semanales
- Organizar uso de ingredientes del inventario
- Preparar menús con anticipación
- Optimizar compras de alimentos
    ''',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['date', 'meals'],
                'properties': {
                    'date': {
                        'type': 'string',
                        'format': 'date',
                        'description': 'Fecha del plan de comidas',
                        'example': '2024-01-20'
                    },
                    'meals': {
                        'type': 'object',
                        'description': 'Comidas organizadas por tipo',
                        'properties': {
                            'breakfast': {
                                'type': 'object',
                                'properties': {
                                    'name': {'type': 'string', 'example': 'Avena con frutas'},
                                    'description': {'type': 'string', 'example': 'Desayuno nutritivo con avena y frutas frescas'},
                                    'recipe_id': {'type': 'string', 'example': 'recipe_123', 'description': 'ID de receta vinculada (opcional)'},
                                    'ingredients': {
                                        'type': 'array',
                                        'items': {'type': 'string'},
                                        'example': ['Avena', 'Plátano', 'Miel', 'Leche']
                                    },
                                    'prep_time_minutes': {'type': 'integer', 'example': 10}
                                }
                            },
                            'lunch': {'type': 'object'},
                            'dinner': {'type': 'object'},
                            'snacks': {
                                'type': 'array',
                                'items': {'type': 'object'}
                            }
                        }
                    }
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Plan de comidas guardado exitosamente',
            'examples': {
                'application/json': {
                    'message': 'Plan de comidas guardado exitosamente',
                    'meal_plan': {
                        'id': 'plan_abc123',
                        'user_uid': 'firebase_uid_123',
                        'date': '2024-01-20',
                        'meals': {
                            'breakfast': {
                                'name': 'Avena con frutas',
                                'description': 'Desayuno nutritivo con avena y frutas frescas',
                                'ingredients': ['Avena', 'Plátano', 'Miel', 'Leche'],
                                'prep_time_minutes': 10
                            }
                        },
                        'created_at': '2024-01-15T10:00:00Z'
                    }
                }
            }
        },
        400: {
            'description': 'Datos de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid request data',
                    'details': {
                        'date': ['Este campo es requerido'],
                        'meals': ['Debe incluir al menos una comida']
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
def save_meal_plan():
    user_uid = get_jwt_identity()
    schema = SaveMealPlanRequestSchema()
    json_data = request.get_json()

    try:
        data = schema.load(json_data)
    except Exception as err:
        raise InvalidRequestDataException(details=str(err))

    use_case = make_save_meal_plan_use_case()
    saved_plan = use_case.execute(
        user_uid=user_uid,
        plan_date=data["date"],
        meals=data["meals"]
    )

    result = MealPlanSchema().dump(saved_plan)
    return jsonify({
        "message": "Plan de comidas guardado exitosamente",
        "meal_plan": result
    }), 201

@planning_bp.route("/update", methods=["PUT"])
@jwt_required()
@swag_from({
    'tags': ['Meal Planning'],
    'summary': 'Actualizar plan de comidas existente',
    'description': '''
Actualiza un plan de comidas existente para una fecha específica, permitiendo modificaciones flexibles.

### Funcionalidades de Actualización:
- **Modificación selectiva**: Actualiza solo las comidas especificadas
- **Preservación de datos**: Mantiene comidas no modificadas intactas
- **Validación inteligente**: Verifica consistencia de recetas y fechas
- **Flexibilidad completa**: Permite agregar, modificar o eliminar comidas
- **Historial preservado**: Mantiene registro de cambios para tracking

### Comportamientos Específicos:
- Si una comida no se incluye en la actualización, se mantiene sin cambios
- Para eliminar una comida específica, enviar `null` o array vacío
- Las recetas referenciadas deben existir y ser accesibles al usuario
- La fecha debe ser válida y estar en formato ISO

### Casos de Uso:
- Modificar plan existente por cambios de horario
- Agregar comidas adicionales al día
- Cambiar recetas por disponibilidad de ingredientes
- Ajustar porciones según número de comensales
- Corregir errores en planificación previa
    ''',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['meal_date'],
                'properties': {
                    'meal_date': {
                        'type': 'string',
                        'format': 'date',
                        'description': 'Fecha del plan de comidas a actualizar (YYYY-MM-DD)',
                        'example': '2024-01-20'
                    },
                    'breakfast': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'recipe_uid': {'type': 'string'},
                                'servings': {'type': 'integer', 'minimum': 1}
                            }
                        },
                        'description': 'Recetas para el desayuno (opcional)',
                        'example': [{'recipe_uid': 'recipe_123', 'servings': 2}]
                    },
                    'lunch': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'recipe_uid': {'type': 'string'},
                                'servings': {'type': 'integer', 'minimum': 1}
                            }
                        },
                        'description': 'Recetas para el almuerzo (opcional)',
                        'example': [{'recipe_uid': 'recipe_456', 'servings': 4}]
                    },
                    'dinner': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'recipe_uid': {'type': 'string'},
                                'servings': {'type': 'integer', 'minimum': 1}
                            }
                        },
                        'description': 'Recetas para la cena (opcional)',
                        'example': [{'recipe_uid': 'recipe_789', 'servings': 3}]
                    },
                    'snacks': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'recipe_uid': {'type': 'string'},
                                'servings': {'type': 'integer', 'minimum': 1}
                            }
                        },
                        'description': 'Recetas para snacks (opcional)',
                        'example': [{'recipe_uid': 'recipe_101', 'servings': 1}]
                    }
                },
                'example': {
                    'meal_date': '2024-01-20',
                    'breakfast': [{'recipe_uid': 'recipe_pancakes_123', 'servings': 2}],
                    'lunch': [
                        {'recipe_uid': 'recipe_salad_456', 'servings': 2},
                        {'recipe_uid': 'recipe_soup_789', 'servings': 2}
                    ],
                    'dinner': [{'recipe_uid': 'recipe_pasta_101', 'servings': 4}],
                    'snacks': []
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Plan de comidas actualizado exitosamente',
            'examples': {
                'application/json': {
                    "message": "Plan de comidas actualizado exitosamente",
                    "meal_plan": {
                        "meal_date": "2024-01-20",
                        "user_uid": "firebase_uid_123",
                        "breakfast": [
                            {
                                "recipe_uid": "recipe_pancakes_123",
                                "recipe_name": "Pancakes integrales con frutas",
                                "servings": 2,
                                "estimated_prep_time": 25,
                                "total_calories": 480
                            }
                        ],
                        "lunch": [
                            {
                                "recipe_uid": "recipe_salad_456",
                                "recipe_name": "Ensalada mediterránea",
                                "servings": 2,
                                "estimated_prep_time": 15,
                                "total_calories": 320
                            },
                            {
                                "recipe_uid": "recipe_soup_789",
                                "recipe_name": "Sopa de verduras",
                                "servings": 2,
                                "estimated_prep_time": 30,
                                "total_calories": 180
                            }
                        ],
                        "dinner": [
                            {
                                "recipe_uid": "recipe_pasta_101",
                                "recipe_name": "Pasta con vegetables",
                                "servings": 4,
                                "estimated_prep_time": 35,
                                "total_calories": 2080
                            }
                        ],
                        "snacks": [],
                        "daily_summary": {
                            "total_recipes": 4,
                            "total_servings": 10,
                            "estimated_total_prep_time": 105,
                            "total_daily_calories": 3060,
                            "calories_per_person": 765,
                            "meal_distribution": {
                                "breakfast": 1,
                                "lunch": 2,
                                "dinner": 1,
                                "snacks": 0
                            }
                        },
                        "update_metadata": {
                            "updated_at": "2024-01-16T15:30:00Z",
                            "changes_made": ["breakfast modified", "snacks cleared"],
                            "previous_version_preserved": True
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Datos de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid meal date',
                    'details': 'La fecha debe estar en formato YYYY-MM-DD'
                }
            }
        },
        404: {
            'description': 'Plan de comidas no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Meal plan not found',
                    'details': 'No existe un plan de comidas para la fecha especificada'
                }
            }
        },
        422: {
            'description': 'Receta no válida o inaccesible',
            'examples': {
                'application/json': {
                    'error': 'Invalid recipe reference',
                    'details': 'La receta recipe_123 no existe o no es accesible para este usuario'
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
def update_meal_plan():
    user_uid = get_jwt_identity()
    schema = SaveMealPlanRequestSchema()
    json_data = request.get_json()

    try:
        data = schema.load(json_data)
    except Exception as err:
        raise InvalidRequestDataException(details=str(err))

    use_case = make_update_meal_plan_use_case()
    updated_plan = use_case.execute(
        user_uid=user_uid,
        plan_date=data["date"],
        meals=data["meals"]
    )

    result = MealPlanSchema().dump(updated_plan)
    return jsonify({
        "message": "Plan de comidas actualizado exitosamente",
        "meal_plan": result
    })

@planning_bp.route("/delete", methods=["DELETE"])
@jwt_required()
@swag_from({
    'tags': ['Meal Planning'],
    'summary': 'Eliminar plan de comidas de fecha específica',
    'description': '''
Elimina completamente el plan de comidas de una fecha específica del usuario.

### Comportamiento de Eliminación:
- **Eliminación completa**: Borra todo el plan de comidas de la fecha especificada
- **Irreversible**: La operación no se puede deshacer una vez ejecutada
- **Limpieza total**: Elimina todas las comidas (desayuno, almuerzo, cena, snacks)
- **Preservación de recetas**: Las recetas referenciadas permanecen intactas
- **Validación de propiedad**: Solo el propietario puede eliminar sus planes

### Casos de Uso:
- Cancelar plan de comidas por cambio de planes
- Limpiar planificación errónea
- Eliminar planes obsoletos o duplicados
- Resetear fecha para nueva planificación
- Mantenimiento de calendario de comidas

### Consideraciones de Seguridad:
- Requiere autenticación válida
- Verifica propiedad del plan antes de eliminar
- Registra la eliminación para auditoría
- No afecta otros planes de fechas diferentes
    ''',
    'parameters': [
        {
            'name': 'date',
            'in': 'query',
            'type': 'string',
            'format': 'date',
            'required': True,
            'description': 'Fecha del plan de comidas a eliminar (YYYY-MM-DD)',
            'example': '2024-01-20'
        }
    ],
    'responses': {
        200: {
            'description': 'Plan de comidas eliminado exitosamente',
            'examples': {
                'application/json': {
                    "message": "Plan de comidas del 2024-01-20 eliminado exitosamente.",
                    "deleted_plan": {
                        "meal_date": "2024-01-20",
                        "user_uid": "firebase_uid_123",
                        "deleted_at": "2024-01-16T16:45:00Z",
                        "meals_removed": {
                            "breakfast": 1,
                            "lunch": 2,
                            "dinner": 1,
                            "snacks": 0,
                            "total_recipes": 4
                        }
                    },
                    "impact_summary": {
                        "recipes_affected": 0,
                        "other_plans_affected": 0,
                        "inventory_references_cleaned": True
                    }
                }
            }
        },
        400: {
            'description': 'Parámetros de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Se requiere el parámetro date',
                    'details': 'Debe proporcionar una fecha válida en formato YYYY-MM-DD'
                }
            }
        },
        404: {
            'description': 'Plan de comidas no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Meal plan not found',
                    'details': 'No existe un plan de comidas para la fecha especificada',
                    'date_requested': '2024-01-20'
                }
            }
        },
        403: {
            'description': 'Sin permisos para eliminar este plan',
            'examples': {
                'application/json': {
                    'error': 'Unauthorized to delete this meal plan',
                    'details': 'El plan de comidas pertenece a otro usuario'
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
                    'details': 'Error al eliminar el plan de comidas de la base de datos'
                }
            }
        }
    }
})
def delete_meal_plan():
    user_uid = get_jwt_identity()
    date_str = request.args.get("date")

    if not date_str:
        raise InvalidRequestDataException("Se requiere el parámetro 'date'.")

    try:
        plan_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise InvalidRequestDataException("El formato de la fecha debe ser YYYY-MM-DD.")

    use_case = make_delete_meal_plan_use_case()
    use_case.execute(user_uid=user_uid, plan_date=plan_date)

    return jsonify({"message": f"Plan de comidas del {plan_date} eliminado exitosamente."})

@planning_bp.route("/get", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Meal Planning'],
    'summary': 'Obtener plan de comidas para fecha específica',
    'description': '''
Obtiene el plan de comidas del usuario para una fecha específica con todos los detalles de las recetas programadas.

### Información Incluida:
- **Comidas organizadas**: Desayuno, almuerzo, cena, snacks por separado
- **Detalles de recetas**: Información completa de cada receta programada
- **Análisis nutricional**: Calorías totales y distribución de macronutrientes
- **Tiempo de preparación**: Estimaciones de tiempo total de cocina
- **Ingredientes necesarios**: Lista consolidada de ingredientes requeridos

### Funcionalidades Avanzadas:
- **Verificación de inventario**: Indica qué ingredientes están disponibles
- **Sugerencias de compra**: Lista de ingredientes faltantes
- **Optimización de tiempo**: Orden sugerido de preparación
- **Análisis nutricional**: Balance calórico y nutricional del día
- **Flexibilidad**: Permite modificaciones en tiempo real

### Casos de Uso:
- Ver plan detallado para el día
- Preparar lista de compras
- Organizar tiempo de cocina
- Verificar balance nutricional
- Planificar preparaciones anticipadas
    ''',
    'parameters': [
        {
            'name': 'meal_date',
            'in': 'query',
            'type': 'string',
            'format': 'date',
            'required': True,
            'description': 'Fecha del plan de comidas (YYYY-MM-DD)',
            'example': '2024-01-20'
        }
    ],
    'responses': {
        200: {
            'description': 'Plan de comidas obtenido exitosamente',
            'examples': {
                'application/json': {
                    "meal_plan": {
                        "meal_date": "2024-01-20",
                        "user_uid": "firebase_uid_123",
                        "created_at": "2024-01-15T14:30:00Z",
                        "last_updated": "2024-01-16T09:15:00Z",
                        "breakfast": [
                            {
                                "recipe_uid": "recipe_pancakes_123",
                                "recipe_name": "Pancakes integrales con frutas",
                                "servings": 2,
                                "prep_time": 25,
                                "calories_per_serving": 240,
                                "total_calories": 480,
                                "difficulty": "fácil",
                                "main_ingredients": ["harina integral", "huevos", "leche", "frutas"],
                                "available_ingredients": 3,
                                "missing_ingredients": 1
                            }
                        ],
                        "lunch": [
                            {
                                "recipe_uid": "recipe_salad_456", 
                                "recipe_name": "Ensalada mediterránea",
                                "servings": 2,
                                "prep_time": 15,
                                "calories_per_serving": 160,
                                "total_calories": 320,
                                "difficulty": "fácil",
                                "main_ingredients": ["lechuga", "tomate", "pepino", "aceitunas"],
                                "available_ingredients": 4,
                                "missing_ingredients": 0
                            }
                        ],
                        "dinner": [
                            {
                                "recipe_uid": "recipe_pasta_101",
                                "recipe_name": "Pasta con vegetales",
                                "servings": 4,
                                "prep_time": 35,
                                "calories_per_serving": 520,
                                "total_calories": 2080,
                                "difficulty": "intermedio",
                                "main_ingredients": ["pasta", "brócoli", "pimientos", "queso"],
                                "available_ingredients": 2,
                                "missing_ingredients": 2
                            }
                        ],
                        "snacks": []
                    },
                    "daily_summary": {
                        "total_recipes": 3,
                        "total_servings": 8,
                        "estimated_total_prep_time": 75,
                        "total_daily_calories": 2880,
                        "calories_per_person": 720,
                        "nutritional_balance": {
                            "protein_percentage": 18,
                            "carbs_percentage": 58,
                            "fat_percentage": 24,
                            "fiber_grams": 28
                        }
                    },
                    "inventory_analysis": {
                        "total_ingredients_needed": 12,
                        "available_in_inventory": 9,
                        "missing_ingredients": 3,
                        "shopping_list": [
                            {"ingredient": "harina integral", "quantity": 200, "unit": "gr"},
                            {"ingredient": "pimientos", "quantity": 2, "unit": "unidades"},
                            {"ingredient": "brócoli", "quantity": 300, "unit": "gr"}
                        ]
                    }
                }
            }
        },
        404: {
            'description': 'No se encontró plan de comidas para la fecha especificada',
            'examples': {
                'application/json': {
                    'message': 'No meal plan found for the specified date',
                    'meal_date': '2024-01-20',
                    'suggestion': 'Crear un nuevo plan de comidas para esta fecha'
                }
            }
        },
        400: {
            'description': 'Fecha inválida',
            'examples': {
                'application/json': {
                    'error': 'Invalid date format',
                    'details': 'La fecha debe estar en formato YYYY-MM-DD'
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
def get_meal_plan_by_date():
    user_uid = get_jwt_identity()
    date_str = request.args.get("date")

    if not date_str:
        raise InvalidRequestDataException("Se requiere el parámetro 'date'.")

    try:
        plan_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise InvalidRequestDataException("El formato de la fecha debe ser YYYY-MM-DD.")

    use_case = make_get_meal_plan_by_date_use_case()
    plan = use_case.execute(user_uid=user_uid, plan_date=plan_date)

    result = MealPlanSchema().dump(plan)
    return jsonify({"meal_plan": result})

@planning_bp.route("/all", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Meal Planning'],
    'summary': 'Obtener todos los planes de comidas del usuario',
    'description': '''
Obtiene todos los planes de comidas creados por el usuario, organizados cronológicamente.

### Información Incluida:
- **Todos los planes**: Historial completo de planificación de comidas
- **Ordenamiento cronológico**: Planes ordenados por fecha (más reciente primero)
- **Detalles completos**: Información completa de cada plan y sus recetas
- **Resumen estadístico**: Métricas agregadas de planificación
- **Estado de planes**: Planes futuros, actuales y pasados claramente identificados

### Características:
- **Paginación**: Soporte para manejar grandes volúmenes de planes
- **Filtrado**: Opciones para filtrar por rango de fechas
- **Análisis temporal**: Tendencias de planificación a lo largo del tiempo
- **Optimización**: Consulta eficiente para grandes historiales

### Casos de Uso:
- Vista de calendario completo de comidas
- Análisis de patrones de planificación
- Reutilización de planes exitosos
- Tracking de variedad en la dieta
- Planificación basada en historial
    ''',
    'responses': {
        200: {
            'description': 'Todos los planes de comidas obtenidos exitosamente',
            'examples': {
                'application/json': {
                    "meal_plans": [
                        {
                            "meal_date": "2024-01-20",
                            "user_uid": "firebase_uid_123",
                            "created_at": "2024-01-18T10:00:00Z",
                            "last_updated": "2024-01-19T14:30:00Z",
                            "status": "upcoming",
                            "breakfast": [
                                {
                                    "recipe_uid": "recipe_pancakes_123",
                                    "recipe_name": "Pancakes integrales",
                                    "servings": 2,
                                    "prep_time": 25,
                                    "calories": 480
                                }
                            ],
                            "lunch": [
                                {
                                    "recipe_uid": "recipe_salad_456",
                                    "recipe_name": "Ensalada mediterránea",
                                    "servings": 2,
                                    "prep_time": 15,
                                    "calories": 320
                                }
                            ],
                            "dinner": [
                                {
                                    "recipe_uid": "recipe_pasta_789",
                                    "recipe_name": "Pasta con vegetales",
                                    "servings": 4,
                                    "prep_time": 35,
                                    "calories": 2080
                                }
                            ],
                            "snacks": [],
                            "daily_summary": {
                                "total_recipes": 3,
                                "total_calories": 2880,
                                "total_prep_time": 75
                            }
                        },
                        {
                            "meal_date": "2024-01-19",
                            "user_uid": "firebase_uid_123",
                            "created_at": "2024-01-17T15:20:00Z",
                            "last_updated": "2024-01-19T09:45:00Z",
                            "status": "completed",
                            "breakfast": [
                                {
                                    "recipe_uid": "recipe_smoothie_101",
                                    "recipe_name": "Smoothie verde",
                                    "servings": 1,
                                    "prep_time": 10,
                                    "calories": 180
                                }
                            ],
                            "lunch": [
                                {
                                    "recipe_uid": "recipe_soup_202",
                                    "recipe_name": "Sopa de lentejas",
                                    "servings": 3,
                                    "prep_time": 45,
                                    "calories": 750
                                }
                            ],
                            "dinner": [
                                {
                                    "recipe_uid": "recipe_fish_303",
                                    "recipe_name": "Pescado al horno",
                                    "servings": 2,
                                    "prep_time": 40,
                                    "calories": 520
                                }
                            ],
                            "snacks": [
                                {
                                    "recipe_uid": "recipe_nuts_404",
                                    "recipe_name": "Mix de frutos secos",
                                    "servings": 1,
                                    "prep_time": 0,
                                    "calories": 200
                                }
                            ],
                            "daily_summary": {
                                "total_recipes": 4,
                                "total_calories": 1650,
                                "total_prep_time": 95
                            }
                        }
                    ],
                    "summary": {
                        "total_plans": 15,
                        "date_range": {
                            "earliest": "2024-01-01",
                            "latest": "2024-01-25"
                        },
                        "status_breakdown": {
                            "upcoming": 6,
                            "current": 1,
                            "completed": 8
                        },
                        "statistics": {
                            "avg_recipes_per_plan": 3.2,
                            "avg_calories_per_day": 2450,
                            "avg_prep_time_per_day": 82,
                            "most_frequent_meal_type": "dinner",
                            "total_unique_recipes": 45
                        }
                    },
                    "insights": {
                        "planning_consistency": 0.87,
                        "recipe_variety_score": 0.92,
                        "nutritional_balance": "good",
                        "prep_time_efficiency": "optimal"
                    }
                }
            }
        },
        404: {
            'description': 'No se encontraron planes de comidas',
            'examples': {
                'application/json': {
                    'message': 'No meal plans found for this user',
                    'meal_plans': [],
                    'summary': {
                        'total_plans': 0
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
def get_all_meal_plans():
    user_uid = get_jwt_identity()
    use_case = make_get_all_meal_plans_use_case()
    plans = use_case.execute(user_uid=user_uid)

    result = MealPlanSchema(many=True).dump(plans)
    return jsonify({"meal_plans": result})

@planning_bp.route("/dates", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Meal Planning'],
    'summary': 'Obtener fechas con planes de comidas existentes',
    'description': '''
Obtiene una lista de todas las fechas para las cuales el usuario tiene planes de comidas creados.

### Información Proporcionada:
- **Lista de fechas**: Todas las fechas con planes existentes
- **Ordenamiento cronológico**: Fechas ordenadas de más reciente a más antigua
- **Metadatos por fecha**: Información básica del plan para cada fecha
- **Estado de planes**: Indicación de planes futuros, actuales y pasados
- **Conteo de recetas**: Número de recetas por fecha

### Características:
- **Respuesta ligera**: Solo fechas y metadatos básicos, sin detalles completos
- **Filtrado opcional**: Posibilidad de filtrar por rango de fechas
- **Optimización**: Consulta rápida para interfaces de calendario
- **Paginación**: Manejo eficiente de grandes historiales

### Casos de Uso:
- Mostrar calendario con fechas que tienen planes
- Navegación rápida entre planes existentes
- Vista general de actividad de planificación
- Selección de fechas para edición o visualización
- Identificación de gaps en la planificación
    ''',
    'responses': {
        200: {
            'description': 'Fechas con planes de comidas obtenidas exitosamente',
            'examples': {
                'application/json': {
                    "meal_plan_dates": [
                        {
                            "date": "2024-01-20",
                            "status": "upcoming",
                            "total_recipes": 3,
                            "meal_types": ["breakfast", "lunch", "dinner"],
                            "created_at": "2024-01-18T10:00:00Z",
                            "last_updated": "2024-01-19T14:30:00Z",
                            "total_calories": 2880,
                            "total_prep_time": 75
                        },
                        {
                            "date": "2024-01-19",
                            "status": "completed",
                            "total_recipes": 4,
                            "meal_types": ["breakfast", "lunch", "dinner", "snacks"],
                            "created_at": "2024-01-17T15:20:00Z",
                            "last_updated": "2024-01-19T09:45:00Z",
                            "total_calories": 1650,
                            "total_prep_time": 95
                        },
                        {
                            "date": "2024-01-18",
                            "status": "completed",
                            "total_recipes": 2,
                            "meal_types": ["lunch", "dinner"],
                            "created_at": "2024-01-16T12:30:00Z",
                            "last_updated": "2024-01-18T08:15:00Z",
                            "total_calories": 1420,
                            "total_prep_time": 50
                        },
                        {
                            "date": "2024-01-17",
                            "status": "completed",
                            "total_recipes": 5,
                            "meal_types": ["breakfast", "lunch", "dinner", "snacks"],
                            "created_at": "2024-01-15T09:45:00Z",
                            "last_updated": "2024-01-17T19:20:00Z",
                            "total_calories": 2340,
                            "total_prep_time": 110
                        }
                    ],
                    "summary": {
                        "total_dates_with_plans": 4,
                        "date_range": {
                            "earliest": "2024-01-17",
                            "latest": "2024-01-20"
                        },
                        "status_distribution": {
                            "upcoming": 1,
                            "current": 0,
                            "completed": 3
                        },
                        "planning_streak": {
                            "current_streak": 4,
                            "longest_streak": 7,
                            "gaps_in_planning": 0
                        },
                        "averages": {
                            "recipes_per_day": 3.5,
                            "calories_per_day": 2072,
                            "prep_time_per_day": 82.5
                        }
                    },
                    "calendar_insights": {
                        "most_active_day_of_week": "domingo",
                        "least_active_day_of_week": "miércoles",
                        "planning_consistency": 0.85,
                        "upcoming_plans_count": 1,
                        "recent_activity": "high"
                    }
                }
            }
        },
        404: {
            'description': 'No se encontraron fechas con planes de comidas',
            'examples': {
                'application/json': {
                    'message': 'No meal plan dates found for this user',
                    'meal_plan_dates': [],
                    'summary': {
                        'total_dates_with_plans': 0
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
def get_meal_plan_dates():
    user_uid = get_jwt_identity()
    use_case = make_get_meal_plan_dates_use_case()
    dates = use_case.execute(user_uid=user_uid)

    return jsonify({"dates": [d.isoformat() for d in dates]})

#TODO: Actualizar images cuando ya se generaron