from flasgger import swag_from # type: ignore
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.application.factories.environmental_savings_factory import (
    make_estimate_savings_by_title_use_case,
    make_estimate_savings_by_uid_use_case,
    make_get_all_environmental_calculations_use_case,
    make_get_environmental_calculations_by_status_use_case,
make_sum_environmental_calculations_by_user
)
from src.shared.exceptions.custom import InvalidRequestDataException, RecipeNotFoundException

environmental_savings_bp = Blueprint("environmental_savings", __name__)


@environmental_savings_bp.route("/calculate/from-title", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Environmental'],
    'summary': 'Calcular ahorro ambiental por título de receta',
    'description': '''
Calcula el impacto ambiental positivo de preparar una receta específica basándose en su título.

### Cálculos Incluidos:
- **Reducción de CO2**: Emisiones evitadas vs. alternativas comerciales
- **Ahorro de agua**: Litros de agua conservados en producción
- **Reducción de desperdicios**: Alimentos salvados del desperdicio
- **Huella de carbono**: Impacto total de ingredientes utilizados

### Metodología:
- **Base de datos ambiental**: Factores de impacto por ingrediente
- **Comparación**: Cocinar en casa vs. comprar procesado
- **Aprovechamiento**: Uso de ingredientes del inventario
- **Sostenibilidad**: Priorización de ingredientes locales/estacionales

### Factores Considerados:
- Origen de ingredientes (local vs. importado)
- Tipo de procesamiento requerido
- Método de conservación y almacenamiento
- Transporte y packaging evitado
- Extensión de vida útil de alimentos

### Casos de Uso:
- Evaluar recetas por sostenibilidad  
- Motivar cocina casera
- Tracking de impacto ambiental personal
- Comparar opciones de menú
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
                        'description': 'Título exacto de la receta a analizar',
                        'example': 'Ensalada de Tomates Cherry con Queso Manchego',
                        'minLength': 3,
                        'maxLength': 200
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Cálculo de ahorro ambiental exitoso',
            'examples': {
                'application/json': {
                    "recipe_title": "Ensalada de Tomates Cherry con Queso Manchego",
                    "environmental_impact": {
                        "co2_reduction_kg": 0.85,
                        "water_saved_liters": 23.4,
                        "food_waste_reduced_kg": 0.5,
                        "carbon_footprint_kg": 0.45,
                        "sustainability_score": 8.2
                    },
                    "breakdown": {
                        "ingredients_impact": [
                            {
                                "ingredient": "Tomates cherry",
                                "co2_saved": 0.3,
                                "water_saved": 12.1,
                                "local_source": True,
                                "impact_category": "low"
                            },
                            {
                                "ingredient": "Queso manchego",
                                "co2_saved": 0.55,
                                "water_saved": 11.3,
                                "local_source": True,
                                "impact_category": "medium"
                            }
                        ],
                        "comparison_vs_processed": {
                            "co2_difference": 1.2,
                            "packaging_saved": True,
                            "transport_reduced": 0.3,
                            "freshness_factor": 1.4
                        }
                    },
                    "recommendations": [
                        "Usar tomates de producción local reduce 30% más el impacto",
                        "Preparar en temporada de tomates maximiza beneficios",
                        "Reutilizar agua de lavado para plantas"
                    ],
                    "calculation_metadata": {
                        "calculation_date": "2024-01-15T10:30:00Z",
                        "methodology_version": "2.1",
                        "data_sources": ["EU Environmental Database", "Local Agriculture Data"],
                        "confidence_level": 0.87
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
                        'title': ['El campo title es obligatorio']
                    }
                }
            }
        },
        404: {
            'description': 'Receta no encontrada',
            'examples': {
                'application/json': {
                    'error': 'Recipe not found',
                    'details': 'No se encontró una receta con ese título',
                    'suggestion': 'Verifica el título exacto de la receta'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error en cálculo ambiental',
            'examples': {
                'application/json': {
                    'error': 'Environmental calculation failed',
                    'details': 'Error accessing environmental database'
                }
            }
        }
    }
})
def calculate_savings_from_title():
    user_uid = get_jwt_identity()
    data = request.get_json()

    if not data or "title" not in data:
        raise InvalidRequestDataException(details={"title": "El campo 'title' es obligatorio."})

    use_case = make_estimate_savings_by_title_use_case()

    try:
        result = use_case.execute(user_uid=user_uid, recipe_title=data["title"])
        return jsonify(result), 200
    except RecipeNotFoundException as e:
        return jsonify({"error": str(e)}), 404


@environmental_savings_bp.route("/calculate/from-uid/<recipe_uid>", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Environmental Impact'],
    'summary': 'Calcular ahorro ambiental por UID de receta',
    'description': '''
Calcula el impacto ambiental positivo de preparar una receta específica identificada por su UID único.

### Ventajas vs. Cálculo por Título:
- **Identificación única**: Sin ambigüedad en la receta específica
- **Datos exactos**: Acceso directo a ingredientes y cantidades precisas
- **Historial vinculado**: Conecta con cálculos previos de la misma receta
- **Optimización**: Procesamiento más rápido al evitar búsquedas por texto

### Cálculos Incluidos:
- **Reducción de CO2**: Emisiones evitadas vs. alternativas comerciales
- **Ahorro de agua**: Litros de agua conservados en producción
- **Reducción de desperdicios**: Alimentos salvados del desperdicio
- **Huella de carbono**: Impacto total de ingredientes utilizados
- **Puntuación de sostenibilidad**: Evaluación integral (0-10)

### Metodología Avanzada:
- **Análisis por ingrediente**: Impacto individual y combinado
- **Factores estacionales**: Ajuste por disponibilidad temporal
- **Origen geográfico**: Consideración de transporte y producción local
- **Método de preparación**: Impacto energético de cocción
- **Aprovechamiento**: Uso eficiente de ingredientes disponibles

### Casos de Uso:
- Cálculo preciso para recetas guardadas
- Seguimiento de impacto de recetas favoritas
- Comparación entre diferentes versiones de una receta
- Análisis detallado para reportes de sostenibilidad
    ''',
    'parameters': [
        {
            'name': 'recipe_uid',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'UID único de la receta para calcular impacto ambiental',
            'example': 'recipe_abc123def456'
        }
    ],
    'responses': {
        200: {
            'description': 'Cálculo de ahorro ambiental por UID exitoso',
            'examples': {
                'application/json': {
                    "recipe_uid": "recipe_abc123def456",
                    "recipe_title": "Pasta Vegana con Verduras de Temporada",
                    "environmental_impact": {
                        "co2_reduction_kg": 2.3,
                        "water_saved_liters": 45.7,
                        "food_waste_reduced_kg": 0.8,
                        "carbon_footprint_kg": 0.6,
                        "sustainability_score": 9.1
                    },
                    "detailed_breakdown": {
                        "ingredients_analysis": [
                            {
                                "ingredient": "Pasta integral",
                                "quantity": 100,
                                "unit": "gr",
                                "co2_impact": 0.12,
                                "water_footprint": 8.5,
                                "sustainability_factor": 0.85,
                                "local_availability": True,
                                "seasonal_bonus": 0.1
                            },
                            {
                                "ingredient": "Tomates cherry",
                                "quantity": 200,
                                "unit": "gr",
                                "co2_impact": 0.08,
                                "water_footprint": 12.3,
                                "sustainability_factor": 0.92,
                                "local_availability": True,
                                "seasonal_bonus": 0.15
                            },
                            {
                                "ingredient": "Calabacín",
                                "quantity": 150,
                                "unit": "gr",
                                "co2_impact": 0.05,
                                "water_footprint": 9.1,
                                "sustainability_factor": 0.88,
                                "local_availability": True,
                                "seasonal_bonus": 0.12
                            }
                        ],
                        "cooking_method_impact": {
                            "energy_type": "gas_natural",
                            "cooking_time": 20,
                            "energy_consumption_kwh": 0.8,
                            "co2_from_cooking": 0.15,
                            "efficiency_rating": "high"
                        },
                        "comparison_baselines": {
                            "vs_restaurant_meal": {
                                "co2_saved": 1.8,
                                "water_saved": 25.4,
                                "packaging_avoided": True,
                                "transport_reduced": 0.4
                            },
                            "vs_processed_food": {
                                "co2_saved": 1.2,
                                "water_saved": 18.7,
                                "preservatives_avoided": True,
                                "freshness_gained": 1.3
                            }
                        }
                    },
                    "sustainability_insights": {
                        "seasonal_alignment": 0.95,
                        "local_sourcing_potential": 0.87,
                        "waste_minimization": 0.91,
                        "nutritional_density": 0.83,
                        "overall_eco_rating": "excellent"
                    },
                    "actionable_recommendations": [
                        "Ingredientes de temporada detectados - impacto óptimo",
                        "Considera usar pasta de producción local para 15% más ahorro",
                        "Receta ideal para compartir por su alto impacto positivo",
                        "Aprovecha agua de cocción para regar plantas"
                    ],
                    "calculation_metadata": {
                        "calculation_id": "calc_env_789012345",
                        "calculated_at": "2024-01-16T11:15:00Z",
                        "methodology_version": "3.1_advanced",
                        "data_sources": [
                            "Global Environmental Database",
                            "Local Agriculture Registry",
                            "Seasonal Availability Index",
                            "Carbon Footprint Database"
                        ],
                        "confidence_level": 0.94,
                        "processing_time": 2.8
                    }
                }
            }
        },
        404: {
            'description': 'Receta no encontrada',
            'examples': {
                'application/json': {
                    'error': 'Recipe not found',
                    'details': 'No se encontró una receta con el UID proporcionado',
                    'recipe_uid': 'recipe_invalid123',
                    'suggestion': 'Verifica que el UID de la receta sea correcto'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error en cálculo ambiental',
            'examples': {
                'application/json': {
                    'error': 'Environmental calculation failed',
                    'error_type': 'DatabaseConnectionException',
                    'details': 'Error accessing environmental impact database'
                }
            }
        }
    }
})
def calculate_savings_from_uid(recipe_uid):
    use_case = make_estimate_savings_by_uid_use_case()

    try:
        result = use_case.execute(recipe_uid=recipe_uid)
        return jsonify(result), 200
    except RecipeNotFoundException as e:
        return jsonify({"error": str(e)}), 404


@environmental_savings_bp.route("/calculations", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Environmental Impact'],
    'summary': 'Obtener todas las calculaciones ambientales del usuario',
    'description': '''
Obtiene el historial completo de todas las calculaciones de impacto ambiental realizadas por el usuario.

### Información Incluida:
- **Historial completo**: Todas las calculaciones realizadas históricamente
- **Detalles de recetas**: Información de las recetas analizadas
- **Métricas calculadas**: CO2 reducido, agua ahorrada, desperdicio evitado
- **Fechas de cálculo**: Cuándo se realizó cada análisis
- **Estado de ejecución**: Completadas, en proceso, con errores

### Ordenamiento y Filtrado:
- Por defecto ordenado por fecha (más reciente primero)
- Incluye tanto cálculos exitosos como fallidos
- Muestra progreso de cálculos asincrónicos
- Agrupa por período (día, semana, mes)

### Casos de Uso:
- Revisar historial de impacto ambiental personal
- Tracking de progreso en sostenibilidad
- Análisis de tendencias de impacto a largo plazo
- Identificación de recetas más eco-friendly
- Reportes de sostenibilidad personal
    ''',
    'responses': {
        200: {
            'description': 'Calculaciones ambientales obtenidas exitosamente',
            'examples': {
                'application/json': {
                    "calculations": [
                        {
                            "calculation_id": "calc_123456789",
                            "recipe_name": "Pasta vegana con verduras",
                            "recipe_uid": "recipe_vegan_pasta_001",
                            "calculated_at": "2024-01-16T10:30:00Z",
                            "status": "completed",
                            "environmental_impact": {
                                "co2_reduction": {
                                    "value": 2.5,
                                    "unit": "kg",
                                    "description": "CO2 evitado vs. receta con carne"
                                },
                                "water_savings": {
                                    "value": 850,
                                    "unit": "litros",
                                    "description": "Agua ahorrada vs. producción de carne"
                                },
                                "waste_reduction": {
                                    "value": 0.3,
                                    "unit": "kg",
                                    "description": "Desperdicio alimentario evitado"
                                }
                            },
                            "sustainability_score": 8.7,
                            "calculation_method": "ai_enhanced",
                            "processing_time": 3.2
                        },
                        {
                            "calculation_id": "calc_987654321",
                            "recipe_name": "Ensalada de quinoa",
                            "recipe_uid": "recipe_quinoa_salad_002",
                            "calculated_at": "2024-01-15T14:20:00Z",
                            "status": "completed",
                            "environmental_impact": {
                                "co2_reduction": {
                                    "value": 1.8,
                                    "unit": "kg",
                                    "description": "CO2 evitado vs. proteína animal"
                                },
                                "water_savings": {
                                    "value": 420,
                                    "unit": "litros",
                                    "description": "Agua ahorrada en producción"
                                },
                                "waste_reduction": {
                                    "value": 0.1,
                                    "unit": "kg",
                                    "description": "Desperdicio evitado por uso completo"
                                }
                            },
                            "sustainability_score": 7.3,
                            "calculation_method": "standard",
                            "processing_time": 1.8
                        }
                    ],
                    "summary": {
                        "total_calculations": 15,
                        "completed_calculations": 14,
                        "failed_calculations": 1,
                        "total_co2_saved": 28.5,
                        "total_water_saved": 6420,
                        "total_waste_reduced": 3.7,
                        "average_sustainability_score": 7.8,
                        "calculation_period": {
                            "start_date": "2024-01-01T00:00:00Z",
                            "end_date": "2024-01-16T23:59:59Z",
                            "period_days": 16
                        }
                    },
                    "environmental_trends": {
                        "weekly_co2_trend": "increasing",
                        "water_savings_consistency": "high",
                        "waste_reduction_improvement": 0.15,
                        "sustainability_score_trend": "stable"
                    },
                    "recommendations": [
                        "Continúa priorizando recetas veganas para maximizar impacto",
                        "Tus cálculos muestran excelente consistencia en sostenibilidad",
                        "Considera compartir recetas con alta puntuación ambiental"
                    ]
                }
            }
        },
        404: {
            'description': 'No se encontraron calculaciones para el usuario',
            'examples': {
                'application/json': {
                    'message': 'No calculations found for this user',
                    'calculations': [],
                    'summary': {
                        'total_calculations': 0
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
def get_all_calculations():
    user_uid = get_jwt_identity()
    use_case = make_get_all_environmental_calculations_use_case()
    result = use_case.execute(user_uid)
    return jsonify({"calculations": result, "count": len(result)}), 200


@environmental_savings_bp.route("/calculations/status", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Environmental Impact'],
    'summary': 'Obtener calculaciones ambientales filtradas por estado de receta',
    'description': '''
Obtiene calculaciones ambientales filtradas por el estado de preparación de las recetas (cocinadas o no cocinadas).

### Filtros Disponibles:
- **is_cooked=true**: Solo recetas que han sido preparadas/cocinadas
- **is_cooked=false**: Solo recetas planificadas pero no preparadas aún

### Información Incluida:
- **Cálculos filtrados**: Solo los que coinciden con el estado solicitado
- **Detalles de impacto**: Métricas ambientales completas
- **Estado de preparación**: Confirmación de si fueron cocinadas
- **Fechas relevantes**: Cuándo se calculó y cuándo se cocinó (si aplica)
- **Tendencias**: Comparación entre recetas cocinadas vs. planificadas

### Casos de Uso:
- Analizar impacto real vs. planificado
- Seguimiento de recetas efectivamente preparadas
- Identificar recetas planificadas pendientes de cocinar
- Calcular impacto ambiental real del usuario
- Generar reportes de sostenibilidad efectiva
    ''',
    'parameters': [
        {
            'name': 'is_cooked',
            'in': 'query',
            'type': 'string',
            'required': True,
            'enum': ['true', 'false'],
            'description': 'Filtrar por estado de preparación de la receta',
            'example': 'true'
        }
    ],
    'responses': {
        200: {
            'description': 'Calculaciones filtradas por estado obtenidas exitosamente',
            'examples': {
                'application/json': {
                    "calculations": [
                        {
                            "calculation_id": "calc_cooked_123456",
                            "recipe_name": "Ensalada mediterránea",
                            "recipe_uid": "recipe_mediterranean_salad_001",
                            "calculated_at": "2024-01-15T10:30:00Z",
                            "cooked_at": "2024-01-15T19:45:00Z",
                            "is_cooked": True,
                            "status": "completed",
                            "environmental_impact": {
                                "co2_reduction": {
                                    "value": 1.8,
                                    "unit": "kg",
                                    "description": "CO2 efectivamente ahorrado al cocinar"
                                },
                                "water_savings": {
                                    "value": 320,
                                    "unit": "litros",
                                    "description": "Agua realmente conservada"
                                },
                                "waste_reduction": {
                                    "value": 0.4,
                                    "unit": "kg",
                                    "description": "Desperdicio efectivamente evitado"
                                }
                            },
                            "real_vs_planned": {
                                "planned_impact": 1.8,
                                "actual_impact": 1.8,
                                "achievement_rate": 1.0,
                                "variance": 0.0
                            },
                            "sustainability_score": 8.5,
                            "cooking_confirmation": {
                                "confirmed_by": "user_action",
                                "confirmation_method": "meal_completion",
                                "ingredients_used": ["tomates", "pepino", "aceitunas", "queso feta"]
                            }
                        },
                        {
                            "calculation_id": "calc_cooked_789012",
                            "recipe_name": "Pasta con verduras",
                            "recipe_uid": "recipe_veggie_pasta_002",
                            "calculated_at": "2024-01-14T14:20:00Z",
                            "cooked_at": "2024-01-14T20:30:00Z",
                            "is_cooked": True,
                            "status": "completed",
                            "environmental_impact": {
                                "co2_reduction": {
                                    "value": 2.1,
                                    "unit": "kg",
                                    "description": "CO2 ahorrado mediante cocina casera"
                                },
                                "water_savings": {
                                    "value": 450,
                                    "unit": "litros",
                                    "description": "Agua conservada vs. alimentos procesados"
                                },
                                "waste_reduction": {
                                    "value": 0.6,
                                    "unit": "kg",
                                    "description": "Desperdicio evitado por uso completo"
                                }
                            },
                            "real_vs_planned": {
                                "planned_impact": 2.0,
                                "actual_impact": 2.1,
                                "achievement_rate": 1.05,
                                "variance": 0.1
                            },
                            "sustainability_score": 9.2,
                            "cooking_confirmation": {
                                "confirmed_by": "inventory_consumption",
                                "confirmation_method": "ingredient_tracking",
                                "ingredients_used": ["pasta", "calabacín", "tomates", "albahaca"]
                            }
                        }
                    ],
                    "filter_summary": {
                        "filter_applied": "is_cooked=true",
                        "total_results": 12,
                        "date_range": {
                            "earliest": "2024-01-01T00:00:00Z",
                            "latest": "2024-01-16T23:59:59Z"
                        },
                        "aggregate_impact": {
                            "total_co2_saved": 18.5,
                            "total_water_saved": 4200,
                            "total_waste_reduced": 5.2,
                            "average_sustainability_score": 8.7
                        }
                    },
                    "insights": {
                        "achievement_rate_average": 0.98,
                        "most_common_confirmation": "inventory_consumption",
                        "top_impact_recipe": "Pasta con verduras",
                        "consistency_score": 0.92
                    },
                    "recommendations": [
                        "Excelente tasa de cumplimiento en recetas planificadas",
                        "Continúa con el patrón de cocina casera sostenible",
                        "Considera documentar más recetas con alto impacto"
                    ]
                }
            }
        },
        400: {
            'description': 'Parámetro is_cooked inválido',
            'examples': {
                'application/json': {
                    'error': 'Invalid request data',
                    'details': {
                        'is_cooked': 'Debe ser true o false'
                    },
                    'received_value': 'maybe',
                    'valid_values': ['true', 'false']
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
def get_calculations_by_status():
    user_uid = get_jwt_identity()
    is_cooked_param = request.args.get("is_cooked")

    if is_cooked_param not in ["true", "false"]:
        raise InvalidRequestDataException(details={"is_cooked": "Debe ser 'true' o 'false'."})

    is_cooked = is_cooked_param == "true"
    use_case = make_get_environmental_calculations_by_status_use_case()
    result = use_case.execute(user_uid=user_uid, is_cooked=is_cooked)
    return jsonify({"calculations": result, "count": len(result)}), 200

@environmental_savings_bp.route("/summary", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Environmental Impact'],
    'summary': 'Obtener resumen consolidado de impacto ambiental del usuario',
    'description': '''
Proporciona un resumen ejecutivo y consolidado de todo el impacto ambiental positivo generado por el usuario.

### Métricas Consolidadas:
- **CO2 total ahorrado**: Suma de todas las reducciones de emisiones
- **Agua total conservada**: Litros de agua ahorrados acumulados
- **Desperdicio total evitado**: Kilogramos de alimentos salvados del desperdicio
- **Puntuación de sostenibilidad promedio**: Evaluación integral del comportamiento

### Análisis Temporal:
- **Tendencias mensuales**: Evolución del impacto a lo largo del tiempo
- **Comparaciones períodicas**: Mes actual vs. anterior, año actual vs. anterior
- **Proyecciones**: Estimación de impacto anual basado en tendencias
- **Hitos alcanzados**: Logros y metas de sostenibilidad cumplidas

### Información Contextual:
- **Equivalencias**: Impacto traducido a términos comprensibles
- **Ranking**: Posición relativa vs. otros usuarios (anonimizado)
- **Recomendaciones**: Sugerencias para maximizar impacto futuro
- **Certificaciones**: Logros ambientales desbloqueados

### Casos de Uso:
- Dashboard principal de sostenibilidad
- Reportes personales de impacto ambiental
- Motivación y gamificación ecológica
- Sharing en redes sociales de logros verdes
- Tracking de objetivos ambientales personales
    ''',
    'responses': {
        200: {
            'description': 'Resumen de impacto ambiental obtenido exitosamente',
            'examples': {
                'application/json': {
                    "user_environmental_summary": {
                        "user_uid": "firebase_user_123",
                        "summary_generated_at": "2024-01-16T12:00:00Z",
                        "reporting_period": {
                            "start_date": "2024-01-01T00:00:00Z",
                            "end_date": "2024-01-16T23:59:59Z",
                            "total_days": 16,
                            "active_cooking_days": 12
                        }
                    },
                    "consolidated_impact": {
                        "total_co2_saved": {
                            "value": 28.7,
                            "unit": "kg",
                            "equivalent_to": "Conducir 120 km menos en auto",
                            "trees_planted_equivalent": 1.2
                        },
                        "total_water_saved": {
                            "value": 6850,
                            "unit": "litros",
                            "equivalent_to": "45 duchas promedio",
                            "days_of_drinking_water": 3425
                        },
                        "total_waste_reduced": {
                            "value": 8.3,
                            "unit": "kg",
                            "equivalent_to": "16 comidas salvadas del desperdicio",
                            "meals_worth": 16
                        },
                        "average_sustainability_score": 8.4,
                        "total_recipes_analyzed": 23,
                        "recipes_actually_cooked": 18
                    },
                    "temporal_analysis": {
                        "monthly_trends": {
                            "january_2024": {
                                "co2_saved": 28.7,
                                "water_saved": 6850,
                                "waste_reduced": 8.3,
                                "trend_vs_previous": "first_month"
                            }
                        },
                        "weekly_breakdown": [
                            {
                                "week": "2024-W02",
                                "co2_saved": 12.5,
                                "water_saved": 2840,
                                "waste_reduced": 3.1,
                                "recipes_cooked": 8
                            },
                            {
                                "week": "2024-W03",
                                "co2_saved": 16.2,
                                "water_saved": 4010,
                                "waste_reduced": 5.2,
                                "recipes_cooked": 10
                            }
                        ],
                        "daily_average": {
                            "co2_per_day": 1.8,
                            "water_per_day": 428,
                            "waste_per_day": 0.52
                        }
                    },
                    "achievements_and_milestones": {
                        "badges_earned": [
                            {
                                "badge": "Eco Warrior",
                                "description": "Ahorrado más de 25kg CO2 en un mes",
                                "earned_at": "2024-01-15T10:30:00Z"
                            },
                            {
                                "badge": "Water Saver",
                                "description": "Conservado más de 5000L de agua",
                                "earned_at": "2024-01-14T14:20:00Z"
                            }
                        ],
                        "next_milestone": {
                            "target": "Climate Hero",
                            "description": "Ahorrar 50kg CO2 en un mes",
                            "progress": 0.57,
                            "remaining": "21.3 kg CO2"
                        },
                        "streak": {
                            "current_cooking_streak": 5,
                            "longest_cooking_streak": 8,
                            "current_sustainability_streak": 12
                        }
                    },
                    "comparative_insights": {
                        "vs_average_user": {
                            "co2_performance": 1.34,
                            "water_performance": 1.28,
                            "waste_performance": 1.45,
                            "overall_ranking_percentile": 78
                        },
                        "global_impact_context": {
                            "if_everyone_cooked_like_you": {
                                "annual_co2_saved": "2.1 million tons",
                                "annual_water_saved": "150 billion liters",
                                "equivalent_impact": "Eliminar 450,000 autos por un año"
                            }
                        }
                    },
                    "personalized_recommendations": [
                        "¡Excelente progreso! Estás en el top 25% de usuarios eco-friendly",
                        "Considera incorporar más recetas veganas para maximizar impacto CO2",
                        "Tu consistencia en cocina casera es ejemplar - sigue así",
                        "Próximo objetivo: Alcanzar el badge 'Climate Hero' en 2 semanas"
                    ],
                    "sharing_stats": {
                        "shareable_achievement": "He ahorrado 28.7kg de CO2 cocinando en casa este mes! 🌱",
                        "social_media_ready": {
                            "twitter": "🌱 Mi impacto ambiental este mes: 28.7kg CO2 ahorrado, 6850L agua conservada. ¡Cocinar en casa sí marca la diferencia! #ZeroWasteAI #CocinaEcológica",
                            "instagram": "🌿 Cocinando por el planeta: -28.7kg CO2, -6850L agua desperdiciada. Cada receta cuenta para nuestro futuro. #SustainableCooking"
                        }
                    }
                }
            }
        },
        404: {
            'description': 'No hay datos suficientes para generar resumen',
            'examples': {
                'application/json': {
                    'message': 'Insufficient data for environmental summary',
                    'details': 'No environmental calculations found for this user',
                    'suggestion': 'Cook some recipes and calculate their environmental impact first'
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
def get_environmental_summary():
    user_uid = get_jwt_identity()
    use_case = make_sum_environmental_calculations_by_user()
    result = use_case.execute(user_uid)
    return jsonify(result), 200

