import traceback
import json
from flasgger import swag_from # type: ignore
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.infrastructure.db.base import db
from src.application.factories.recognition_usecase_factory import (
    make_recognize_ingredients_use_case,
    make_recognize_foods_use_case,
    make_recognize_batch_use_case,
    make_recognize_ingredients_complete_use_case
)
from src.application.factories.auth_usecase_factory import make_firestore_profile_service
from src.infrastructure.async_tasks.async_task_service import async_task_service
from src.infrastructure.optimization.rate_limiter import smart_rate_limit
from src.infrastructure.optimization.cache_service import smart_cache, cache_user_data
from datetime import datetime, timezone, timedelta
import uuid

recognition_bp = Blueprint("recognition", __name__)

@recognition_bp.route("/ingredients", methods=["POST"])
@jwt_required()
@smart_rate_limit('ai_recognition')  # 🛡️ Rate limit: 5 requests/min for AI recognition
@swag_from({
    'tags': ['Recognition'],
    'summary': 'Reconocimiento de ingredientes por IA con imágenes',
    'description': '''
Reconoce automáticamente ingredientes en imágenes usando inteligencia artificial.

### Proceso de Reconocimiento:
1. **Análisis IA**: Procesa imágenes para identificar ingredientes
2. **Datos Completos**: Retorna información detallada inmediatamente
3. **Generación de Imágenes**: Crea imágenes de referencia en segundo plano
4. **Validación de Alergias**: Verifica ingredientes contra perfil del usuario

### Información Extraída:
- **Identificación**: Nombre específico del ingrediente
- **Cantidad Estimada**: Cantidad aproximada detectada
- **Unidades**: Unidad de medida apropiada
- **Almacenamiento**: Tipo de almacenamiento recomendado
- **Vencimiento**: Tiempo estimado hasta vencimiento
- **Consejos**: Recomendaciones de conservación

### Características Especiales:
- **Respuesta Inmediata**: Datos completos sin esperar imágenes
- **Imágenes Asíncronas**: Generación de imágenes en segundo plano
- **Detección de Alergias**: Alerta si detecta alérgenos del usuario
- **Cálculo Automático**: Fechas de vencimiento calculadas automáticamente

### Formatos de Imagen Soportados:
- JPG, PNG, WEBP, GIF
- Máximo 10MB por imagen
- Múltiples imágenes por request
    ''',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['images_paths'],
                'properties': {
                    'images_paths': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Lista de rutas de imágenes en Firebase Storage',
                        'example': [
                            'uploads/recognition/abc123-image1.jpg',
                            'uploads/recognition/def456-image2.jpg'
                        ]
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Ingredientes reconocidos exitosamente',
            'examples': {
                'application/json': {
                    "ingredients": [
                        {
                            "name": "Tomates cherry",
                            "quantity": 500,
                            "type_unit": "gr",
                            "storage_type": "refrigerador",
                            "expiration_time": 5,
                            "time_unit": "days",
                            "expiration_date": "2024-01-20T00:00:00Z",
                            "added_at": "2024-01-15T10:00:00Z",
                            "tips": "Mantener refrigerados para mayor duración",
                            "image_path": "https://via.placeholder.com/150x150/f0f0f0/666666?text=Generando...",
                            "image_status": "generating",
                            "confidence": 0.95,
                            "allergen_alert": False
                        },
                        {
                            "name": "Queso manchego",
                            "quantity": 200,
                            "type_unit": "gr",
                            "storage_type": "refrigerador",
                            "expiration_time": 3,
                            "time_unit": "weeks",
                            "expiration_date": "2024-02-05T00:00:00Z",
                            "added_at": "2024-01-15T10:00:00Z",
                            "tips": "Envolver en papel encerado",
                            "image_path": "https://via.placeholder.com/150x150/f0f0f0/666666?text=Generando...",
                            "image_status": "generating",
                            "confidence": 0.87,
                            "allergen_alert": True,
                            "allergen_details": ["lactose", "dairy"]
                        }
                    ],
                    "recognition_id": "rec_abc123def456",
                    "processed_images": 2,
                    "total_ingredients_found": 2,
                    "images_status": "generating",
                    "images_check_url": "/api/recognition/rec_abc123def456/images",
                    "message": "✅ Ingredientes reconocidos. Las imágenes se están generando y se actualizarán automáticamente.",
                    "allergen_warnings": [
                        {
                            "ingredient": "Queso manchego",
                            "allergens": ["lactose", "dairy"],
                            "message": "⚠️ Contiene lácteos - revisar alergias"
                        }
                    ]
                }
            }
        },
        400: {
            'description': 'Datos de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Debe proporcionar una lista válida en images_paths',
                    'details': 'images_paths debe ser un array con al menos una imagen'
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
            'description': 'Error en el reconocimiento por IA',
            'examples': {
                'application/json': {
                    'error': 'AI recognition failed',
                    'error_type': 'GoogleAIException',
                    'details': 'Unable to process images'
                }
            }
        }
    }
})
def recognize_ingredients():
    """
    🚀 RECONOCIMIENTO SIMPLIFICADO:
    - Respuesta inmediata con datos completos de IA (síncrono)
    - Generación de imágenes en segundo plano (asíncrono)
    - Frontend usa response inmediata + endpoint para verificar imágenes
    """
    user_uid = get_jwt_identity()
    images_paths = request.json.get("images_paths")
    
    print(f"🔍 [SIMPLE RECOGNITION] User: {user_uid}")
    print(f"🔍 [SIMPLE RECOGNITION] Images paths: {images_paths}")

    if not images_paths or not isinstance(images_paths, list):
        print("❌ [SIMPLE RECOGNITION] ERROR: Invalid images_paths")
        return jsonify({"error": "Debe proporcionar una lista válida en 'images_paths'"}), 400

    try:
        # 1. PASO SÍNCRONO: Reconocimiento AI inmediato CON datos completos
        print("🔍 [SIMPLE RECOGNITION] Loading images for AI recognition...")
        from src.application.factories.recognition_usecase_factory import (
            make_ai_service, make_recognition_repository, make_storage_adapter,
            make_ingredient_image_generator_service, make_calculator_service
        )
        
        ai_service = make_ai_service()
        recognition_repository = make_recognition_repository(db)
        storage_adapter = make_storage_adapter()
        calculator_service = make_calculator_service()
        
        # Cargar imágenes
        images_files = []
        for path in images_paths:
            file = storage_adapter.get_image(path)
            images_files.append(file)
        
        # Reconocimiento AI (síncrono)
        print("🤖 [SIMPLE RECOGNITION] Running AI recognition...")
        result = ai_service.recognize_ingredients(images_files)
        
        # Preparar datos completos inmediatamente
        current_time = datetime.now(timezone.utc)
        
        for ingredient in result["ingredients"]:
            # Imagen placeholder mientras se genera
            ingredient["image_path"] = "https://via.placeholder.com/150x150/f0f0f0/666666?text=Generando..."
            ingredient["image_status"] = "generating"
            ingredient["added_at"] = current_time.isoformat()
            
            # Calcular fecha de vencimiento
            try:
                # Verificar que expiration_time no sea None
                expiration_time = ingredient.get("expiration_time")
                time_unit = ingredient.get("time_unit", "Días")
                
                if expiration_time is not None and expiration_time > 0:
                    expiration_date = calculator_service.calculate_expiration_date(
                        added_at=current_time,
                        time_value=expiration_time,
                        time_unit=time_unit
                    )
                    ingredient["expiration_date"] = expiration_date.isoformat()
                else:
                    # Si expiration_time es None o 0, usar 7 días por defecto
                    print(f"⚠️ [SIMPLE RECOGNITION] expiration_time is None/0 for {ingredient.get('name', 'unknown')}, using 7 days default")
                    fallback_date = current_time + timedelta(days=7)
                    ingredient["expiration_date"] = fallback_date.isoformat()
                    ingredient["expiration_time"] = 7
                    ingredient["time_unit"] = "Días"
                    
            except Exception as e:
                print(f"🚨 [SIMPLE RECOGNITION] ERROR calculating expiration for {ingredient.get('name', 'unknown')}: {str(e)}")
                # Fallback seguro: usar 7 días por defecto
                fallback_date = current_time + timedelta(days=7)
                ingredient["expiration_date"] = fallback_date.isoformat()
                ingredient["expiration_time"] = 7
                ingredient["time_unit"] = "Días"
        
        # Guardar reconocimiento completo
        from src.domain.models.recognition import Recognition
        recognition = Recognition(
            uid=str(uuid.uuid4()),
            user_uid=user_uid,
            images_paths=images_paths,
            recognized_at=current_time,
            raw_result=result,
            is_validated=False,
            validated_at=None
        )
        recognition_repository.save(recognition)
        
        # Verificar alergias
        firestore_service = make_firestore_profile_service()
        user_profile = firestore_service.get_profile(user_uid)
        if user_profile:
            print("🔍 [SIMPLE RECOGNITION] Checking allergies...")
            result = _check_allergies_in_recognition(result, user_profile, "ingredients")
        
        # 2. RESPUESTA INMEDIATA con todos los datos
        response_data = {
            **result,
            "recognition_id": recognition.uid,
            "images_status": "generating",
            "images_check_url": f"/api/recognition/{recognition.uid}/images",
            "message": "✅ Ingredientes reconocidos. Las imágenes se están generando y se actualizarán automáticamente."
        }
        
        print("✅ [SIMPLE RECOGNITION] Immediate response sent")
        print(f"📤 [SIMPLE RECOGNITION] Recognition ID: {recognition.uid}")
        print(f"📤 [SIMPLE RECOGNITION] Ingredients count: {len(result.get('ingredients', []))}")
        
        # 3. GENERAR IMÁGENES EN BACKGROUND (sin task_id complejo)
        print("🎨 [SIMPLE RECOGNITION] Starting background image generation...")
        ingredient_image_generator_service = make_ingredient_image_generator_service()
        
        async_task_service.run_simple_image_generation(
            recognition_id=recognition.uid,
            user_uid=user_uid,
            ingredients=result['ingredients'],
            ingredient_image_generator_service=ingredient_image_generator_service,
            recognition_repository=recognition_repository
        )
        
        return jsonify(response_data), 200

    except Exception as e:
        # Log detallado del error
        error_msg = f"🚨 [SIMPLE RECOGNITION] ERROR: {str(e)}"
        error_traceback = f"🚨 [SIMPLE RECOGNITION] TRACEBACK: {traceback.format_exc()}"
        
        print(error_msg)
        print(error_traceback)
        
        return jsonify({
            "error": str(e), 
            "error_type": str(type(e).__name__),
            "traceback": traceback.format_exc()
        }), 500

@recognition_bp.route("/ingredients/complete", methods=["POST"])
@jwt_required()
@smart_rate_limit('ai_inventory_complete')  # 🛡️ Rate limit: 3 requests/min for expensive AI operations
@cache_user_data('ai_inventory_complete', timeout=3600)  # 🚀 Cache: 1 hour for expensive AI results
@swag_from({
    'tags': ['Recognition'],
    'summary': 'Reconocimiento completo de ingredientes con información detallada',
    'description': '''
Reconoce ingredientes en imagen y proporciona información completa incluyendo análisis nutricional, ambiental y sugerencias de uso.

### Funcionalidades Avanzadas:
- **Reconocimiento mejorado**: Utiliza modelos de IA más avanzados para mayor precisión
- **Información nutricional**: Análisis detallado de macronutrientes y vitaminas
- **Impacto ambiental**: Cálculo de huella de carbono y sostenibilidad
- **Sugerencias inteligentes**: Ideas de uso, recetas recomendadas y tips de conservación
- **Análisis de frescura**: Evaluación del estado y calidad del ingrediente
- **Categorización avanzada**: Clasificación detallada por tipo, origen y características

### Datos Adicionales Incluidos:
- **Información nutricional completa**: Calorías, proteínas, carbohidratos, grasas, vitaminas
- **Análisis de sostenibilidad**: Huella de carbono, uso de agua, estacionalidad
- **Recomendaciones de almacenamiento**: Condiciones óptimas y vida útil
- **Ideas de utilización**: Recetas sugeridas y combinaciones
- **Análisis de calidad**: Estado de frescura y consejos de selección

### Casos de Uso:
- Análisis detallado para planificación nutricional
- Educación sobre sostenibilidad alimentaria
- Optimización de compras y almacenamiento
- Planificación de menús balanceados
- Investigación de ingredientes desconocidos
    ''',
    'parameters': [
        {
            'name': 'image',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'Imagen de ingredientes para análisis completo (formatos: JPG, PNG, WEBP, GIF. Máximo: 10MB)',
        }
    ],
    'consumes': ['multipart/form-data'],
    'responses': {
        200: {
            'description': 'Reconocimiento completo de ingredientes exitoso',
            'examples': {
                'application/json': {
                    "ingredients": [
                        {
                            "name": "Tomates cherry",
                            "quantity": 500,
                            "type_unit": "gr",
                            "storage_type": "refrigerador",
                            "expiration_time": 7,
                            "time_unit": "Días",
                            "confidence_score": 0.95,
                            "freshness_analysis": {
                                "quality_score": 0.88,
                                "ripeness": "maduro_óptimo",
                                "visual_indicators": ["color rojo intenso", "piel firme", "sin manchas"],
                                "estimated_shelf_life": 7,
                                "quality_tips": "Excelente estado, consumir en los próximos 5-7 días"
                            },
                            "nutritional_info": {
                                "calories_per_100g": 18,
                                "macronutrients": {
                                    "proteins": 0.9,
                                    "carbs": 3.9,
                                    "fats": 0.2,
                                    "fiber": 1.2
                                },
                                "vitamins": {
                                    "vitamin_c": 13.7,
                                    "vitamin_k": 7.9,
                                    "folate": 15,
                                    "potassium": 237
                                },
                                "nutritional_highlights": [
                                    "Alto en vitamina C",
                                    "Rico en licopeno",
                                    "Bajo en calorías",
                                    "Antioxidantes naturales"
                                ]
                            },
                            "environmental_impact": {
                                "carbon_footprint": {
                                    "value": 0.4,
                                    "unit": "kg CO2 eq/kg",
                                    "rating": "bajo"
                                },
                                "water_footprint": {
                                    "value": 214,
                                    "unit": "litros/kg",
                                    "rating": "moderado"
                                },
                                "seasonality": {
                                    "peak_season": ["junio", "julio", "agosto", "septiembre"],
                                    "current_season_match": True,
                                    "local_availability": "alta"
                                },
                                "sustainability_score": 8.2,
                                "eco_tips": [
                                    "Compra tomates de temporada para menor huella",
                                    "Prefiere productores locales",
                                    "Aprovecha completamente, incluso la piel"
                                ]
                            },
                            "usage_suggestions": {
                                "recommended_recipes": [
                                    {
                                        "name": "Ensalada caprese",
                                        "prep_time": 10,
                                        "difficulty": "fácil"
                                    },
                                    {
                                        "name": "Salsa de tomate fresca",
                                        "prep_time": 20,
                                        "difficulty": "fácil"
                                    },
                                    {
                                        "name": "Bruschetta italiana",
                                        "prep_time": 15,
                                        "difficulty": "fácil"
                                    }
                                ],
                                "preparation_methods": [
                                    "consumo fresco",
                                    "asado al horno",
                                    "salteado",
                                    "en salsas"
                                ],
                                "pairing_suggestions": [
                                    "mozzarella",
                                    "albahaca",
                                    "aceite de oliva",
                                    "ajo"
                                ]
                            },
                            "storage_recommendations": {
                                "optimal_temperature": "12-15°C",
                                "humidity": "85-90%",
                                "container": "recipiente ventilado",
                                "tips": "No refrigerar hasta estar muy maduros. Almacenar con el tallo hacia abajo.",
                                "preservation_methods": [
                                    "conservación natural: 5-7 días",
                                    "refrigeración: 7-10 días",
                                    "congelado (procesado): 6 meses"
                                ]
                            },
                            "tips": "Mantener a temperatura ambiente hasta madurar completamente, luego refrigerar para prolongar frescura"
                        }
                    ],
                    "analysis_metadata": {
                        "recognition_model": "advanced_ingredient_analyzer_v3.2",
                        "processing_time": 4.8,
                        "confidence_average": 0.95,
                        "analysis_depth": "complete",
                        "data_sources": [
                            "visual_recognition",
                            "nutrition_database",
                            "environmental_data",
                            "culinary_knowledge_base"
                        ]
                    },
                    "overall_recommendations": [
                        "Excelente calidad detectada en todos los ingredientes",
                        "Ingredientes de temporada con bajo impacto ambiental",
                        "Perfectos para preparaciones mediterráneas frescas"
                    ]
                }
            }
        },
        400: {
            'description': 'Imagen inválida o faltante'
        },
        413: {
            'description': 'Archivo demasiado grande'
        },
        422: {
            'description': 'No se pudieron reconocer ingredientes en la imagen',
            'examples': {
                'application/json': {
                    'error': 'No ingredients detected',
                    'details': 'La imagen no contiene ingredientes reconocibles o la calidad es insuficiente'
                }
            }
        },
        429: {
            'description': 'Límite de velocidad excedido'
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno en el análisis completo'
        }
    }
})
def recognize_ingredients_complete():
    """
    Endpoint para reconocimiento completo de ingredientes con toda la información:
    - Datos básicos (nombre, cantidad, descripción, etc.)
    - Impacto ambiental (CO2, agua)
    - Ideas de aprovechamiento
    """
    user_uid = get_jwt_identity()
    images_paths = request.json.get("images_paths")
    
    print(f"🔍 RECOGNIZE INGREDIENTS COMPLETE - User: {user_uid}")
    print(f"🔍 Images paths: {images_paths}")

    if not images_paths or not isinstance(images_paths, list):
        print("❌ ERROR: Invalid images_paths")
        return jsonify({"error": "Debe proporcionar una lista válida en 'images_paths'"}), 400

    try:
        # Obtener preferencias del usuario
        print("🔍 Getting user profile from Firestore...")
        firestore_service = make_firestore_profile_service()
        user_profile = firestore_service.get_profile(user_uid)
        print(f"🔍 User profile: {user_profile is not None}")
        
        print("🔍 Creating complete recognition use case...")
        use_case = make_recognize_ingredients_complete_use_case(db)
        
        print("🔍 Executing complete recognition...")
        result = use_case.execute(user_uid=user_uid, images_paths=images_paths)
        print(f"🔍 Complete recognition result: {len(result.get('ingredients', []))} ingredients processed")
        
        # Verificar alergias en ingredientes reconocidos
        if user_profile:
            print("🔍 Checking allergies...")
            result = _check_allergies_in_recognition(result, user_profile, "ingredients")
        
        print("✅ Complete recognition successful")
        return jsonify(result), 200

    except Exception as e:
        # Log detallado del error
        error_msg = f"🚨 ERROR EN RECOGNIZE INGREDIENTS COMPLETE: {str(e)}"
        error_traceback = f"🚨 TRACEBACK: {traceback.format_exc()}"
        
        print(error_msg)
        print(error_traceback)
        
        return jsonify({
            "error": str(e), 
            "error_type": str(type(e).__name__),
            "traceback": traceback.format_exc()
        }), 500

@recognition_bp.route("/foods", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Recognition'],
    'summary': 'Reconocimiento de alimentos preparados',
    'description': '''
Reconoce alimentos preparados o comidas completas usando inteligencia artificial avanzada.

### Capacidades del Sistema:
- **Análisis de platos**: Identifica comidas preparadas y platillos completos
- **Detección de ingredientes**: Extrae ingredientes principales de platos complejos
- **Análisis nutricional**: Calcula información nutricional aproximada
- **Categorización**: Clasifica por tipo de comida (desayuno, almuerzo, cena, snack)
- **Origen cultural**: Identifica origen o estilo culinario del plato

### Proceso de Reconocimiento:
1. **Análisis de imagen**: Procesamiento con IA especializada en alimentos
2. **Identificación de componentes**: Detección de ingredientes visibles
3. **Estimación de porciones**: Cálculo aproximado de cantidades
4. **Análisis nutricional**: Estimación de calorías, proteínas, carbohidratos, grasas
5. **Generación de metadatos**: Tips de conservación y consumo

### Casos de Uso:
- Análisis de comidas preparadas caseras
- Tracking nutricional de platos complejos
- Identificación de ingredientes en recetas desconocidas
- Planificación de dietas basada en comidas preparadas
    ''',
    'parameters': [
        {
            'name': 'image',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'Imagen del alimento preparado (formatos: JPG, PNG, WEBP, GIF. Máximo: 10MB)',
        }
    ],
    'consumes': ['multipart/form-data'],
    'responses': {
        200: {
            'description': 'Reconocimiento de alimentos preparados exitoso',
            'examples': {
                'application/json': {
                    "foods": [
                        {
                            "name": "Pasta carbonara",
                            "category": "pasta",
                            "cuisine_type": "italiana",
                            "meal_type": "almuerzo",
                            "estimated_calories": 650,
                            "estimated_servings": 1,
                            "main_ingredients": [
                                {
                                    "name": "Pasta",
                                    "estimated_quantity": 100,
                                    "unit": "gr"
                                },
                                {
                                    "name": "Bacon",
                                    "estimated_quantity": 50,
                                    "unit": "gr"
                                },
                                {
                                    "name": "Queso parmesano",
                                    "estimated_quantity": 30,
                                    "unit": "gr"
                                },
                                {
                                    "name": "Huevos",
                                    "estimated_quantity": 2,
                                    "unit": "unidades"
                                }
                            ],
                            "nutritional_info": {
                                "calories": 650,
                                "proteins": 28,
                                "carbs": 55,
                                "fats": 35,
                                "fiber": 3
                            },
                            "preparation_time": "15-20 min",
                            "difficulty": "fácil",
                            "storage_tips": "Consumir inmediatamente, no se conserva bien",
                            "confidence_score": 0.89
                        }
                    ],
                    "total_foods": 1,
                    "analysis_metadata": {
                        "processing_time": 2.8,
                        "confidence_average": 0.89,
                        "analysis_date": "2024-01-16T10:30:00Z",
                        "model_version": "food_recognition_v2.1"
                    },
                    "recommendations": [
                        "Plato rico en proteínas, ideal para almuerzo",
                        "Combina bien con ensalada verde",
                        "Considerar reducir el bacon para versión más saludable"
                    ]
                }
            }
        },
        400: {
            'description': 'Imagen inválida o faltante',
            'examples': {
                'application/json': {
                    'error': 'Invalid image format',
                    'details': 'El archivo debe ser una imagen válida (JPG, PNG, WEBP, GIF)'
                }
            }
        },
        413: {
            'description': 'Archivo demasiado grande',
            'examples': {
                'application/json': {
                    'error': 'File too large',
                    'details': 'El archivo no puede exceder 10MB'
                }
            }
        },
        429: {
            'description': 'Límite de velocidad excedido',
            'examples': {
                'application/json': {
                    'error': 'Rate limit exceeded',
                    'details': 'Máximo 10 reconocimientos por minuto'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno del servidor o en el procesamiento de IA'
        }
    }
})
def recognize_foods():
    """
    🍽️ RECONOCIMIENTO SIMPLIFICADO DE COMIDAS:
    - Respuesta inmediata con datos de IA (síncrono)
    - Generación de imágenes en segundo plano automática (asíncrono)
    - Sin polling complejo - similar al flujo de ingredientes
    """
    user_uid = get_jwt_identity()
    images_paths = request.json.get("images_paths")
    
    print(f"🍽️ [SIMPLE FOOD RECOGNITION] User: {user_uid}")
    print(f"🍽️ [SIMPLE FOOD RECOGNITION] Images paths: {images_paths}")

    if not images_paths or not isinstance(images_paths, list):
        print("❌ [SIMPLE FOOD RECOGNITION] ERROR: Invalid images_paths")
        return jsonify({"error": "Debe proporcionar una lista válida en 'images_paths'"}), 400

    try:
        # 1. PASO SÍNCRONO: Reconocimiento AI inmediato
        print("🔍 [SIMPLE FOOD RECOGNITION] Loading images for AI recognition...")
        from src.application.factories.recognition_usecase_factory import (
            make_ai_service, make_recognition_repository, make_storage_adapter,
            make_food_image_generator_service, make_calculator_service
        )
        
        ai_service = make_ai_service()
        recognition_repository = make_recognition_repository(db)
        storage_adapter = make_storage_adapter()
        
        # Cargar imágenes
        images_files = []
        for path in images_paths:
            file = storage_adapter.get_image(path)
            images_files.append(file)
        
        # Reconocimiento AI de comidas (síncrono)
        print("🤖 [SIMPLE FOOD RECOGNITION] Running AI food recognition...")
        result = ai_service.recognize_foods(images_files)
        
        # Guardar reconocimiento básico
        from src.domain.models.recognition import Recognition
        recognition = Recognition(
            uid=str(uuid.uuid4()),
            user_uid=user_uid,
            images_paths=images_paths,
            recognized_at=datetime.now(timezone.utc),
            raw_result=result,
            is_validated=False,
            validated_at=None
        )
        recognition_repository.save(recognition)
        
        # 2. PREPARAR DATOS DE RESPUESTA INMEDIATA
        current_time = datetime.now(timezone.utc)
        calculator_service = make_calculator_service()
        
        # Procesar cada comida reconocida
        for food in result["foods"]:
            food["image_path"] = None  # Se agregará cuando esté lista
            food["added_at"] = current_time.isoformat()
            
            # Calcular fecha de vencimiento
            try:
                expiration_date = calculator_service.calculate_expiration_date(
                    added_at=current_time,
                    time_value=food.get("expiration_time", 3),
                    time_unit=food.get("time_unit", "days")
                )
                food["expiration_date"] = expiration_date.isoformat()
            except Exception as e:
                from datetime import timedelta
                fallback_date = current_time + timedelta(days=food.get("expiration_time", 3))
                food["expiration_date"] = fallback_date.isoformat()
        
        # 3. VERIFICAR ALERGIAS
        firestore_service = make_firestore_profile_service()
        user_profile = firestore_service.get_profile(user_uid)
        if user_profile:
            print("🔍 [SIMPLE FOOD RECOGNITION] Checking allergies...")
            result = _check_allergies_in_recognition(result, user_profile, "foods")
        
        # 4. LANZAR GENERACIÓN DE IMÁGENES EN BACKGROUND (sin task tracking)
        print("🎨 [SIMPLE FOOD RECOGNITION] Starting simple background image generation...")
        food_image_generator_service = make_food_image_generator_service()
        
        async_task_service.run_simple_food_image_generation(
            recognition_id=recognition.uid,
            user_uid=user_uid,
            foods=result['foods'],
            food_image_generator_service=food_image_generator_service,
            recognition_repository=recognition_repository
        )
        
        # 5. RESPUESTA INMEDIATA CON DATOS COMPLETOS
        response_data = {
            **result,
            "recognition_id": recognition.uid,
            "message": "✅ Comidas reconocidas exitosamente. Las imágenes se están generando automáticamente.",
            "images_status": "generating_in_background"
        }
        
        print("✅ [SIMPLE FOOD RECOGNITION] Recognition successful - immediate response sent")
        print(f"📤 [SIMPLE FOOD RECOGNITION] Recognition ID: {recognition.uid}")
        print(f"📤 [SIMPLE FOOD RECOGNITION] Foods count: {len(result.get('foods', []))}")
        return jsonify(response_data), 200

    except Exception as e:
        print(f"🚨 [SIMPLE FOOD RECOGNITION] ERROR: {str(e)}")
        import traceback
        print(f"🚨 [SIMPLE FOOD RECOGNITION] TRACEBACK: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@recognition_bp.route("/batch", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Recognition'],
    'summary': 'Reconocimiento en lote de múltiples imágenes',
    'description': '''
Procesa múltiples imágenes de alimentos simultáneamente, optimizado para eficiencia y velocidad.

### Capacidades Avanzadas:
- **Procesamiento paralelo**: Analiza hasta 10 imágenes simultáneamente
- **Reconocimiento mixto**: Combina ingredientes y alimentos preparados
- **Optimización inteligente**: Agrupa resultados similares automáticamente
- **Análisis comparativo**: Identifica duplicados y variaciones
- **Procesamiento asíncrono**: Devuelve task_id para seguimiento del progreso

### Ventajas del Procesamiento en Lote:
- **Eficiencia**: Reduce tiempo total de procesamiento
- **Consistencia**: Análisis coherente entre múltiples imágenes
- **Optimización**: Mejor uso de recursos computacionales
- **Agregación**: Combina resultados relacionados automáticamente

### Límites del Sistema:
- Máximo 10 imágenes por solicitud
- Tamaño máximo por imagen: 10MB
- Tiempo máximo de procesamiento: 5 minutos
- Formatos soportados: JPG, PNG, WEBP, GIF

### Casos de Uso:
- Procesar fotos de compras completas
- Análisis de inventario completo por imágenes
- Reconocimiento de múltiples ingredientes en cocina
- Documentación rápida de inventario alimentario
    ''',
    'parameters': [
        {
            'name': 'images',
            'in': 'formData',
            'type': 'array',
            'items': {'type': 'file'},
            'required': True,
            'description': 'Array de imágenes para procesar (máximo 10 imágenes, 10MB cada una)',
        }
    ],
    'consumes': ['multipart/form-data'],
    'responses': {
        202: {
            'description': 'Procesamiento en lote iniciado - modo asíncrono',
            'examples': {
                'application/json': {
                    "task_id": "batch_recognition_123456789",
                    "status": "processing",
                    "images_count": 5,
                    "estimated_completion": "2024-01-16T10:35:00Z",
                    "progress_url": "/api/recognition/status/batch_recognition_123456789",
                    "message": "Procesamiento iniciado. Use el task_id para verificar el progreso."
                }
            }
        },
        200: {
            'description': 'Procesamiento en lote completado - modo síncrono (pocas imágenes)',
            'examples': {
                'application/json': {
                    "batch_results": {
                        "total_images": 3,
                        "successful_recognitions": 3,
                        "failed_recognitions": 0,
                        "processing_time": 12.5,
                        "aggregated_results": {
                            "total_ingredients": 8,
                            "total_foods": 2,
                            "unique_items": 10,
                            "duplicates_found": 0
                        }
                    },
                    "results_by_image": [
                        {
                            "image_index": 0,
                            "image_name": "vegetables.jpg",
                            "recognition_type": "ingredients",
                            "items_found": 4,
                            "processing_time": 3.2,
                            "ingredients": [
                                {
                                    "name": "Tomates cherry",
                                    "quantity": 500,
                                    "type_unit": "gr",
                                    "confidence_score": 0.95
                                }
                            ]
                        }
                    ],
                    "aggregated_inventory": {
                        "ingredients": [
                            {
                                "name": "Tomates cherry",
                                "total_quantity": 1000,
                                "type_unit": "gr",
                                "sources": ["vegetables.jpg", "tomatoes_close.jpg"],
                                "average_confidence": 0.93
                            }
                        ],
                        "foods": []
                    },
                    "recommendations": [
                        "Se detectaron tomates en múltiples imágenes - considera combinar en un solo stack",
                        "Gran variedad de verduras detectada - ideal para recetas variadas"
                    ]
                }
            }
        },
        400: {
            'description': 'Datos de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid batch request',
                    'details': 'Máximo 10 imágenes permitidas por lote'
                }
            }
        },
        413: {
            'description': 'Archivos demasiado grandes',
            'examples': {
                'application/json': {
                    'error': 'Files too large',
                    'details': 'Una o más imágenes exceden el límite de 10MB'
                }
            }
        },
        429: {
            'description': 'Límite de velocidad excedido',
            'examples': {
                'application/json': {
                    'error': 'Rate limit exceeded',
                    'details': 'Máximo 2 lotes por minuto'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno en el procesamiento del lote'
        }
    }
})
def recognize_batch():
    user_uid = get_jwt_identity()
    images_paths = request.json.get("images_paths")

    if not images_paths or not isinstance(images_paths, list):
        return jsonify({"error": "Debe proporcionar una lista válida en 'images_paths'"}), 400

    try:
        # Obtener preferencias del usuario
        firestore_service = make_firestore_profile_service()
        user_profile = firestore_service.get_profile(user_uid)
        
        use_case = make_recognize_batch_use_case(db)
        result = use_case.execute(user_uid=user_uid, images_paths=images_paths)
        
        # Verificar alergias en resultados del lote
        if user_profile:
            result = _check_allergies_in_batch_recognition(result, user_profile)
        
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _check_allergies_in_recognition(result: dict, user_profile: dict, items_key: str) -> dict:
    """
    Verifica alergias en resultados de reconocimiento y agrega alertas
    """
    allergies = user_profile.get("allergies", [])
    allergy_items = user_profile.get("allergyItems", [])
    language = user_profile.get("language", "es")
    
    print(f"🔍 Allergies: {allergies}")
    print(f"🔍 Allergy items: {allergy_items}")
    
    if not allergies and not allergy_items:
        return result
    
    allergy_alerts = []
    items = result.get(items_key, [])
    
    for item in items:
        item_name = item.get("name", "").lower()
        detected_allergens = []
        
        # Verificar alergias generales
        for allergy in allergies:
            allergy_name = _extract_allergy_name(allergy)
            if allergy_name and allergy_name.lower() in item_name:
                detected_allergens.append(allergy_name)
        
        # Verificar items específicos de alergia
        for allergy_item in allergy_items:
            allergy_name = _extract_allergy_name(allergy_item)
            if allergy_name and allergy_name.lower() in item_name:
                detected_allergens.append(allergy_name)
        
        if detected_allergens:
            alert_message = _get_allergy_alert_message(detected_allergens, language)
            allergy_alerts.append({
                "item": item.get("name"),
                "allergens": detected_allergens,
                "message": alert_message,
                "confidence": item.get("confidence", 0)
            })
            
            # Marcar el item con alerta de alergia
            item["allergy_alert"] = True
            item["allergens"] = detected_allergens
    
    if allergy_alerts:
        result["allergy_alerts"] = allergy_alerts
        result["has_allergens"] = True
    
    return result

def _extract_allergy_name(allergy_data) -> str:
    """
    Extrae el nombre de la alergia desde diferentes formatos:
    - Si es string: retorna el string
    - Si es dict con 'name': retorna allergy_data['name']
    - Si es dict con 'value': retorna allergy_data['value']
    - Si es dict con 'label': retorna allergy_data['label']
    """
    if isinstance(allergy_data, str):
        return allergy_data
    elif isinstance(allergy_data, dict):
        # Intentar diferentes campos comunes
        for field in ['name', 'value', 'label', 'title']:
            if field in allergy_data and allergy_data[field]:
                return str(allergy_data[field])
        # Si no encuentra campos conocidos, usar el primer valor string encontrado
        for value in allergy_data.values():
            if isinstance(value, str) and value.strip():
                return value
    
    print(f"⚠️ Warning: Unable to extract allergy name from: {allergy_data}")
    return ""

def _check_allergies_in_batch_recognition(result: dict, user_profile: dict) -> dict:
    """
    Verifica alergias en resultados de reconocimiento por lotes
    """
    batch_results = result.get("batch_results", [])
    
    for batch_item in batch_results:
        detected_items = batch_item.get("detected_items", [])
        
        # Crear un resultado temporal para usar la función existente
        temp_result = {"recognized_items": detected_items}
        temp_result = _check_allergies_in_recognition(temp_result, user_profile, "recognized_items")
        
        # Transferir alertas de vuelta al batch
        if temp_result.get("allergy_alerts"):
            batch_item["allergy_alerts"] = temp_result["allergy_alerts"]
            batch_item["has_allergens"] = True
    
    return result

def _get_allergy_alert_message(allergens: list, language: str) -> str:
    """
    Genera mensaje de alerta de alergia según el idioma del usuario
    """
    allergens_str = ", ".join(allergens)
    
    if language == "en":
        if len(allergens) == 1:
            return f"⚠️ ALLERGY ALERT: This item contains {allergens_str}, which you are allergic to."
        else:
            return f"⚠️ ALLERGY ALERT: This item contains {allergens_str}, which you are allergic to."
    else:
        if len(allergens) == 1:
            return f"⚠️ ALERTA DE ALERGIA: Este elemento contiene {allergens_str}, al cual eres alérgico."
        else:
            return f"⚠️ ALERTA DE ALERGIA: Este elemento contiene {allergens_str}, a los cuales eres alérgico."

@recognition_bp.route("/ingredients/async", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Recognition'],
    'summary': 'Reconocimiento asíncrono de ingredientes en segundo plano',
    'description': '''
Inicia el reconocimiento de ingredientes en modo asíncrono, ideal para procesar múltiples imágenes sin bloquear la interfaz.

### Características del Procesamiento Asíncrono:
- **Respuesta inmediata**: Retorna task_id sin esperar el procesamiento completo
- **Procesamiento en segundo plano**: La IA procesa las imágenes mientras el usuario continúa usando la app
- **Seguimiento de progreso**: Permite consultar el estado del procesamiento con el task_id
- **Optimización de recursos**: Mejor manejo de recursos del servidor para múltiples usuarios
- **Timeout inteligente**: Procesamiento con límites de tiempo razonables

### Flujo de Trabajo:
1. **Envío de imágenes**: Cliente envía rutas de imágenes en Firebase Storage
2. **Creación de tarea**: Sistema crea task_id y responde inmediatamente
3. **Procesamiento en background**: IA procesa imágenes sin bloquear cliente
4. **Consulta de estado**: Cliente verifica progreso con `/status/{task_id}`
5. **Obtención de resultados**: Una vez completado, resultados disponibles vía task_id

### Ventajas vs. Procesamiento Síncrono:
- **Mejor UX**: No bloquea la interfaz durante procesamiento largo
- **Escalabilidad**: Maneja mejor múltiples usuarios simultáneos
- **Confiabilidad**: Menos timeouts en conexiones lentas
- **Flexibilidad**: Usuario puede continuar usando la app mientras procesa

### Casos de Uso Ideales:
- Procesamiento de muchas imágenes (5+ fotos)
- Conexiones lentas o inestables
- Aplicaciones móviles con limitaciones de tiempo
- Procesamiento de inventario completo
- Usuarios que prefieren no esperar
    ''',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['images_paths'],
                'properties': {
                    'images_paths': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Lista de rutas de imágenes en Firebase Storage para procesamiento asíncrono',
                        'example': [
                            'uploads/recognition/user123/img_001.jpg',
                            'uploads/recognition/user123/img_002.jpg',
                            'uploads/recognition/user123/img_003.jpg'
                        ],
                        'minItems': 1,
                        'maxItems': 10
                    }
                }
            }
        }
    ],
    'responses': {
        202: {
            'description': 'Tarea de reconocimiento asíncrono creada exitosamente',
            'examples': {
                'application/json': {
                    "message": "🚀 Estamos procesando tu imagen en segundo plano",
                    "task_id": "async_recognition_abc123def456",
                    "status": "pending",
                    "progress_percentage": 0,
                    "estimated_time": "30-60 segundos",
                    "check_status_url": "/api/recognition/status/async_recognition_abc123def456",
                    "task_details": {
                        "images_count": 3,
                        "user_uid": "firebase_user_123",
                        "created_at": "2024-01-16T10:30:00Z",
                        "estimated_completion": "2024-01-16T10:31:00Z"
                    },
                    "instructions": {
                        "next_steps": [
                            "Guarda el task_id para consultar el progreso",
                            "Usa check_status_url para verificar el estado",
                            "Los resultados estarán disponibles cuando status sea 'completed'"
                        ],
                        "status_codes": {
                            "pending": "Tarea en cola, esperando procesamiento",
                            "processing": "IA analizando imágenes actualmente",
                            "completed": "Procesamiento completado, resultados disponibles",
                            "failed": "Error en el procesamiento"
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Datos de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Debe proporcionar una lista válida en images_paths',
                    'details': 'images_paths debe ser un array con al menos una imagen',
                    'received_type': 'null',
                    'expected_format': {
                        'images_paths': ['ruta1.jpg', 'ruta2.jpg']
                    }
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        429: {
            'description': 'Límite de tareas asíncronas excedido',
            'examples': {
                'application/json': {
                    'error': 'Too many async tasks',
                    'details': 'Máximo 3 tareas asíncronas simultáneas por usuario',
                    'active_tasks': 3,
                    'retry_after': 30
                }
            }
        },
        500: {
            'description': 'Error interno al crear la tarea asíncrona',
            'examples': {
                'application/json': {
                    'error': 'Failed to create async task',
                    'error_type': 'TaskCreationException',
                    'details': 'Unable to initialize background processing'
                }
            }
        }
    }
})
def recognize_ingredients_async():
    """
    🚀 ENDPOINT ASÍNCRONO: Reconocimiento de ingredientes en background
    
    - Respuesta inmediata con task_id
    - Procesamiento en segundo plano
    - Generación de imágenes asíncrona
    - Consultar progreso con /status/{task_id}
    """
    user_uid = get_jwt_identity()
    
    # 🔍 LOGGING DETALLADO - INFORMACIÓN DE REQUEST
    print(f"🚀 [ASYNC RECOGNITION] ===== REQUEST DETAILS =====")
    print(f"🚀 [ASYNC RECOGNITION] User: {user_uid}")
    print(f"🚀 [ASYNC RECOGNITION] Method: {request.method}")
    print(f"🚀 [ASYNC RECOGNITION] URL: {request.url}")
    print(f"🚀 [ASYNC RECOGNITION] Content-Type: {request.content_type}")
    print(f"🚀 [ASYNC RECOGNITION] Content-Length: {request.content_length}")
    
    # 🔍 LOGGING DE HEADERS
    print(f"🚀 [ASYNC RECOGNITION] Headers:")
    for header_name, header_value in request.headers:
        if header_name.lower() not in ['authorization', 'cookie']:  # No loggear datos sensibles
            print(f"🚀 [ASYNC RECOGNITION]   {header_name}: {header_value}")
    
    # 🔍 VERIFICAR SI HAY CONTENIDO JSON
    try:
        if request.is_json:
            print(f"🚀 [ASYNC RECOGNITION] JSON detected: True")
            json_data = request.get_json()
            print(f"🚀 [ASYNC RECOGNITION] JSON content: {json_data}")
            images_paths = json_data.get("images_paths") if json_data else None
        else:
            print(f"🚀 [ASYNC RECOGNITION] JSON detected: False")
            print(f"🚀 [ASYNC RECOGNITION] Raw data preview: {str(request.data)[:200]}...")
            
            # Verificar si viene como FormData por error
            if request.form:
                print(f"🚀 [ASYNC RECOGNITION] FormData detected: {dict(request.form)}")
            if request.files:
                print(f"🚀 [ASYNC RECOGNITION] Files detected: {list(request.files.keys())}")
            
            images_paths = None
            
    except Exception as json_error:
        print(f"🚨 [ASYNC RECOGNITION] Error parsing JSON: {str(json_error)}")
        print(f"🚨 [ASYNC RECOGNITION] Request data type: {type(request.data)}")
        print(f"🚨 [ASYNC RECOGNITION] Request data: {request.data}")
        return jsonify({
            "error": "Error parsing JSON data",
            "details": str(json_error),
            "content_type_received": request.content_type,
            "expected": "application/json"
        }), 400

    print(f"🚀 [ASYNC RECOGNITION] Images paths extracted: {images_paths}")
    print(f"🚀 [ASYNC RECOGNITION] Images count: {len(images_paths) if images_paths else 0}")

    # 🔍 VALIDACIÓN DETALLADA
    if not images_paths:
        print("❌ [ASYNC RECOGNITION] images_paths is None or empty")
        return jsonify({
            "error": "Debe proporcionar una lista válida en 'images_paths'",
            "received": images_paths,
            "content_type": request.content_type,
            "is_json": request.is_json
        }), 400
        
    if not isinstance(images_paths, list):
        print(f"❌ [ASYNC RECOGNITION] images_paths is not a list. Type: {type(images_paths)}")
        return jsonify({
            "error": "images_paths debe ser una lista",
            "received_type": str(type(images_paths)),
            "received_value": images_paths
        }), 400
        
    if len(images_paths) == 0:
        print("❌ [ASYNC RECOGNITION] images_paths is empty list")
        return jsonify({
            "error": "La lista images_paths no puede estar vacía",
            "received": images_paths
        }), 400

    # 🔍 VALIDAR CADA PATH
    print(f"🚀 [ASYNC RECOGNITION] Validating image paths...")
    for i, path in enumerate(images_paths):
        print(f"🚀 [ASYNC RECOGNITION]   Path {i+1}: {path}")
        if not isinstance(path, str):
            print(f"❌ [ASYNC RECOGNITION] Path {i+1} is not string: {type(path)}")
            return jsonify({
                "error": f"Todas las rutas deben ser strings. Path {i+1} es {type(path)}",
                "invalid_path_index": i,
                "invalid_path_value": path,
                "invalid_path_type": str(type(path))
            }), 400

    try:
        print(f"🚀 [ASYNC RECOGNITION] Creating async task...")
        
        # Crear tarea asíncrona
        task_id = async_task_service.create_task(
            user_uid=user_uid,
            task_type='ingredient_recognition',
            input_data={'images_paths': images_paths}
        )
        
        print(f"✅ [ASYNC RECOGNITION] Task created successfully: {task_id}")
        
        # Lanzar procesamiento en background
        print(f"🚀 [ASYNC RECOGNITION] Loading factories and services...")
        
        from src.application.factories.recognition_usecase_factory import (
            make_ai_service, make_recognition_repository, make_storage_adapter,
            make_ingredient_image_generator_service, make_calculator_service
        )
        
        ai_service = make_ai_service()
        recognition_repository = make_recognition_repository(db)
        storage_adapter = make_storage_adapter()
        ingredient_image_generator_service = make_ingredient_image_generator_service()
        calculator_service = make_calculator_service()
        
        print(f"✅ [ASYNC RECOGNITION] All services loaded successfully")
        print(f"🚀 [ASYNC RECOGNITION] Starting background processing...")
        
        async_task_service.run_async_recognition(
            task_id=task_id,
            ai_service=ai_service,
            recognition_repository=recognition_repository,
            storage_adapter=storage_adapter,
            ingredient_image_generator_service=ingredient_image_generator_service,
            calculator_service=calculator_service,
            user_uid=user_uid,
            images_paths=images_paths
        )
        
        print(f"🎯 [ASYNC RECOGNITION] Task {task_id} queued successfully")
        print(f"🚀 [ASYNC RECOGNITION] ===== REQUEST COMPLETED =====")
        
        # Respuesta inmediata
        return jsonify({
            "message": "🚀 Estamos procesando tu imagen en segundo plano",
            "task_id": task_id,
            "status": "pending",
            "progress_percentage": 0,
            "estimated_time": "30-60 segundos",
            "check_status_url": f"/api/recognition/status/{task_id}",
            "debug_info": {
                "images_count": len(images_paths),
                "user_uid": user_uid,
                "content_type_received": request.content_type
            }
        }), 202  # 202 Accepted

    except Exception as e:
        import traceback
        error_msg = f"🚨 ERROR EN ASYNC RECOGNITION: {str(e)}"
        print(error_msg)
        print(f"🚨 [ASYNC RECOGNITION] Exception type: {type(e).__name__}")
        print(f"🚨 [ASYNC RECOGNITION] Exception args: {e.args}")
        print(f"🚨 [ASYNC RECOGNITION] FULL TRACEBACK:")
        print(traceback.format_exc())
        
        # Información adicional del contexto
        print(f"🚨 [ASYNC RECOGNITION] Context info:")
        print(f"🚨 [ASYNC RECOGNITION]   User UID: {user_uid}")
        print(f"🚨 [ASYNC RECOGNITION]   Images paths: {images_paths}")
        print(f"🚨 [ASYNC RECOGNITION]   Task ID: {locals().get('task_id', 'Not created yet')}")
        
        return jsonify({
            "error": str(e), 
            "error_type": str(type(e).__name__),
            "error_details": {
                "user_uid": user_uid,
                "images_paths": images_paths,
                "images_count": len(images_paths) if images_paths else 0,
                "content_type": request.content_type,
                "is_json": request.is_json,
                "task_id": locals().get('task_id', 'Not created yet')
            },
            "traceback": traceback.format_exc().split('\n')[-10:]  # Últimas 10 líneas del traceback
        }), 500

@recognition_bp.route("/status/<task_id>", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Recognition'],
    'summary': 'Consultar estado y progreso de tarea asíncrona de reconocimiento',
    'description': '''
Obtiene el estado actual, progreso y resultados de una tarea de reconocimiento asíncrono.

### Estados Posibles de la Tarea:
- **pending**: Tarea en cola, esperando procesamiento
- **processing**: IA analizando imágenes actualmente
- **completed**: Procesamiento completado, resultados disponibles
- **failed**: Error en el procesamiento

### Información de Progreso:
- **Porcentaje de completado**: Progreso actual de 0-100%
- **Tiempo estimado restante**: Estimación basada en carga del servidor
- **Detalles del procesamiento**: Número de imágenes procesadas vs. total
- **Metadatos de la tarea**: Información sobre el tipo y parámetros

### Resultados Incluidos (cuando status = completed):
- **Ingredientes reconocidos**: Lista completa con datos enriquecidos
- **Verificación de alergias**: Alertas basadas en perfil del usuario
- **Imágenes generadas**: URLs de imágenes de referencia creadas por IA
- **Estadísticas de procesamiento**: Tiempos, confianza promedio, errores

### Casos de Uso:
- Polling para actualizar UI con progreso en tiempo real
- Verificar si el procesamiento ha terminado antes de mostrar resultados
- Debugging y monitoreo de tareas largas
- Implementación de notificaciones push cuando se complete
    ''',
    'parameters': [
        {
            'name': 'task_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'ID único de la tarea asíncrona de reconocimiento',
            'example': 'async_recognition_abc123def456'
        }
    ],
    'responses': {
        200: {
            'description': 'Estado de la tarea obtenido exitosamente',
            'examples': {
                'application/json': {
                    "task_id": "async_recognition_abc123def456",
                    "status": "completed",
                    "progress_percentage": 100,
                    "created_at": "2024-01-16T10:30:00Z",
                    "updated_at": "2024-01-16T10:30:45Z",
                    "completed_at": "2024-01-16T10:30:45Z",
                    "processing_time": 45.2,
                    "task_metadata": {
                        "task_type": "ingredient_recognition",
                        "images_count": 3,
                        "user_uid": "firebase_user_123"
                    },
                    "result_data": {
                        "ingredients": [
                            {
                                "name": "Tomates cherry",
                                "quantity": 500,
                                "type_unit": "gr",
                                "storage_type": "refrigerador",
                                "expiration_time": 7,
                                "time_unit": "days",
                                "expiration_date": "2024-01-23T00:00:00Z",
                                "added_at": "2024-01-16T10:30:00Z",
                                "tips": "Mantener refrigerados para mayor duración",
                                "image_path": "https://storage.googleapis.com/generated-images/tomatoes-cherry-abc123.jpg",
                                "image_status": "completed",
                                "confidence": 0.95,
                                "allergen_alert": False
                            },
                            {
                                "name": "Queso manchego",
                                "quantity": 200,
                                "type_unit": "gr",
                                "storage_type": "refrigerador",
                                "expiration_time": 3,
                                "time_unit": "weeks",
                                "expiration_date": "2024-02-06T00:00:00Z",
                                "added_at": "2024-01-16T10:30:00Z",
                                "tips": "Envolver en papel encerado",
                                "image_path": "https://storage.googleapis.com/generated-images/queso-manchego-def456.jpg",
                                "image_status": "completed",
                                "confidence": 0.87,
                                "allergen_alert": True,
                                "allergen_details": ["lactose", "dairy"]
                            }
                        ],
                        "recognition_summary": {
                            "total_ingredients_found": 2,
                            "processed_images": 3,
                            "average_confidence": 0.91,
                            "processing_time": 45.2,
                            "images_generated": 2,
                            "allergen_warnings_count": 1
                        },
                        "allergen_warnings": [
                            {
                                "ingredient": "Queso manchego",
                                "allergens": ["lactose", "dairy"],
                                "message": "⚠️ Contiene lácteos - revisar alergias"
                            }
                        ]
                    },
                    "next_actions": [
                        "Los ingredientes están listos para agregar al inventario",
                        "Revisar alertas de alergias antes de consumir",
                        "Las imágenes han sido generadas y están disponibles"
                    ]
                }
            }
        },
        200: {
            'description': 'Tarea en progreso',
            'examples': {
                'application/json': {
                    "task_id": "async_recognition_abc123def456",
                    "status": "processing",
                    "progress_percentage": 65,
                    "created_at": "2024-01-16T10:30:00Z",
                    "updated_at": "2024-01-16T10:30:30Z",
                    "estimated_completion": "2024-01-16T10:31:00Z",
                    "processing_details": {
                        "current_step": "Generando imágenes de referencia",
                        "images_processed": 2,
                        "images_total": 3,
                        "ingredients_found_so_far": 4
                    },
                    "task_metadata": {
                        "task_type": "ingredient_recognition",
                        "images_count": 3,
                        "user_uid": "firebase_user_123"
                    },
                    "partial_results": {
                        "ingredients_count": 4,
                        "average_confidence_so_far": 0.89
                    }
                }
            }
        },
        404: {
            'description': 'Tarea no encontrada',
            'examples': {
                'application/json': {
                    'error': 'Tarea no encontrada',
                    'task_id': 'async_recognition_invalid123'
                }
            }
        },
        403: {
            'description': 'Sin permisos para ver esta tarea',
            'examples': {
                'application/json': {
                    'error': 'No tienes permiso para ver esta tarea',
                    'details': 'La tarea pertenece a otro usuario'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno al consultar el estado',
            'examples': {
                'application/json': {
                    'error': 'Database connection failed',
                    'error_type': 'DatabaseException'
                }
            }
        }
    }
})
def get_recognition_status(task_id):
    """
    📊 CONSULTAR ESTADO: Obtiene el progreso y resultado de una tarea asíncrona
    """
    user_uid = get_jwt_identity()
    
    print(f"📊 [STATUS CHECK] Task: {task_id}, User: {user_uid}")
    
    try:
        task_status = async_task_service.get_task_status(task_id)
        
        if not task_status:
            print(f"❌ [STATUS CHECK] Task {task_id} not found")
            return jsonify({"error": "Tarea no encontrada"}), 404
        
        # Verificar que la tarea pertenece al usuario
        from src.infrastructure.db.models.async_task_orm import AsyncTaskORM
        task = AsyncTaskORM.query.filter_by(task_id=task_id).first()
        if not task or task.user_uid != user_uid:
            print(f"❌ [STATUS CHECK] Task {task_id} unauthorized for user {user_uid}")
            return jsonify({"error": "No tienes permiso para ver esta tarea"}), 403
        
        print(f"📊 [STATUS CHECK] Task {task_id}: {task_status['status']} - {task_status['progress_percentage']}%")
        
        # Si está completada, incluir verificación de alergias
        if task_status['status'] == 'completed' and task_status['result_data']:
            try:
                print(f"🔍 [STATUS CHECK] Raw result_data type: {type(task_status['result_data'])}")
                print(f"🔍 [STATUS CHECK] Raw result_data keys: {task_status['result_data'].keys() if isinstance(task_status['result_data'], dict) else 'Not a dict'}")
                
                if isinstance(task_status['result_data'], dict) and 'ingredients' in task_status['result_data']:
                    print(f"🔍 [STATUS CHECK] Found {len(task_status['result_data']['ingredients'])} ingredients in result")
                    for i, ingredient in enumerate(task_status['result_data']['ingredients'][:3]):  # Solo los primeros 3
                        print(f"🔍 [STATUS CHECK] Ingredient {i+1}: {ingredient.get('name', 'No name')} - Image: {ingredient.get('image_path', 'No image')}")
                
                # Obtener preferencias del usuario para verificar alergias
                firestore_service = make_firestore_profile_service()
                user_profile = firestore_service.get_profile(user_uid)
                
                if user_profile:
                    print("🔍 [STATUS CHECK] Checking allergies in completed result...")
                    result_with_allergies = _check_allergies_in_recognition(
                        task_status['result_data'], 
                        user_profile, 
                        "ingredients"
                    )
                    task_status['result_data'] = result_with_allergies
                    print(f"🔍 [STATUS CHECK] After allergy check - ingredients count: {len(task_status['result_data'].get('ingredients', []))}")
                    
            except Exception as e:
                print(f"⚠️ [STATUS CHECK] Error checking allergies: {str(e)}")
                import traceback
                print(f"⚠️ [STATUS CHECK] Error traceback: {traceback.format_exc()}")
                # No fallar la respuesta por esto
        
        # Log final response details
        print(f"📤 [STATUS CHECK] Final response status: {task_status['status']}")
        if task_status['status'] == 'completed' and task_status['result_data']:
            ingredients_count = len(task_status['result_data'].get('ingredients', [])) if isinstance(task_status['result_data'], dict) else 0
            print(f"📤 [STATUS CHECK] Final response ingredients count: {ingredients_count}")
            print(f"📤 [STATUS CHECK] First ingredient example: {task_status['result_data'].get('ingredients', [{}])[0] if ingredients_count > 0 else 'None'}")
        
        return jsonify(task_status), 200

    except Exception as e:
        error_msg = f"🚨 ERROR EN STATUS CHECK: {str(e)}"
        print(error_msg)
        
        return jsonify({
            "error": str(e),
            "error_type": str(type(e).__name__)
        }), 500

@recognition_bp.route("/images/status/<task_id>", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Recognition'],
    'summary': 'Consultar estado de generación de imágenes para reconocimiento',
    'description': '''
Obtiene el estado actual y progreso de la generación de imágenes de referencia para elementos reconocidos.

### Funcionalidades:
- **Seguimiento en tiempo real**: Progreso de generación de imágenes
- **Estado detallado**: Información completa del proceso
- **Validación de propiedad**: Solo el propietario puede consultar sus tareas
- **Metadatos incluidos**: Información del proceso y tiempos

### Estados Posibles:
- **pending**: Tarea en cola, esperando procesamiento
- **processing**: Generando imágenes actualmente  
- **completed**: Todas las imágenes generadas exitosamente
- **failed**: Error en la generación de imágenes

### Casos de Uso:
- Verificar progreso de generación de imágenes
- Obtener URLs de imágenes generadas cuando estén listas
- Debugging de problemas en generación
- Implementar polling para actualizaciones en tiempo real
    ''',
    'parameters': [
        {
            'name': 'task_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'ID único de la tarea de generación de imágenes',
            'example': 'task_img_abc123def456'
        }
    ],
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Estado de generación de imágenes obtenido exitosamente',
            'examples': {
                'application/json': {
                    "task_id": "task_img_abc123def456",
                    "status": "completed", 
                    "progress_percentage": 100,
                    "current_step": "Imágenes generadas exitosamente",
                    "created_at": "2024-01-16T10:30:00Z",
                    "started_at": "2024-01-16T10:30:05Z",
                    "completed_at": "2024-01-16T10:30:45Z",
                    "images_data": {
                        "generated_images": [
                            {
                                "item_name": "Tomates cherry",
                                "image_url": "https://storage.googleapis.com/generated/tomatoes-abc123.jpg",
                                "generation_time": 12.5,
                                "quality_score": 0.92
                            },
                            {
                                "item_name": "Queso manchego", 
                                "image_url": "https://storage.googleapis.com/generated/cheese-def456.jpg",
                                "generation_time": 15.2,
                                "quality_score": 0.88
                            }
                        ],
                        "total_images": 2,
                        "successful_generations": 2,
                        "failed_generations": 0,
                        "average_quality": 0.90
                    },
                    "message": "🎉 Imágenes generadas exitosamente"
                }
            }
        },
        200: {
            'description': 'Generación en progreso',
            'examples': {
                'application/json': {
                    "task_id": "task_img_abc123def456",
                    "status": "processing",
                    "progress_percentage": 65,
                    "current_step": "Generando imagen 2 de 3",
                    "created_at": "2024-01-16T10:30:00Z",
                    "started_at": "2024-01-16T10:30:05Z",
                    "completed_at": None,
                    "message": "🎨 Generando imágenes... 65%"
                }
            }
        },
        404: {
            'description': 'Tarea de generación no encontrada',
            'examples': {
                'application/json': {
                    'error': 'Tarea de imágenes no encontrada',
                    'task_id': 'task_img_invalid123'
                }
            }
        },
        403: {
            'description': 'Sin permisos para ver esta tarea',
            'examples': {
                'application/json': {
                    'error': 'No tienes permiso para ver esta tarea',
                    'details': 'La tarea pertenece a otro usuario'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno al consultar estado de imágenes',
            'examples': {
                'application/json': {
                    'error': 'Database connection failed',
                    'error_type': 'DatabaseException'
                }
            }
        }
    }
})
def get_images_status(task_id):
    """
    🎨 CONSULTAR IMÁGENES: Obtiene el progreso y resultado de la generación de imágenes
    """
    user_uid = get_jwt_identity()
    
    print(f"🎨 [IMAGES STATUS] Task: {task_id}, User: {user_uid}")
    
    try:
        task_status = async_task_service.get_task_status(task_id)
        
        if not task_status:
            print(f"❌ [IMAGES STATUS] Task {task_id} not found")
            return jsonify({"error": "Tarea de imágenes no encontrada"}), 404
        
        # Verificar que la tarea pertenece al usuario
        from src.infrastructure.db.models.async_task_orm import AsyncTaskORM
        task = AsyncTaskORM.query.filter_by(task_id=task_id).first()
        if not task or task.user_uid != user_uid:
            print(f"❌ [IMAGES STATUS] Task {task_id} unauthorized for user {user_uid}")
            return jsonify({"error": "No tienes permiso para ver esta tarea"}), 403
        
        print(f"🎨 [IMAGES STATUS] Task {task_id}: {task_status['status']} - {task_status['progress_percentage']}%")
        
        # Formatear respuesta específica para imágenes
        response = {
            "task_id": task_id,
            "status": task_status['status'],
            "progress_percentage": task_status['progress_percentage'],
            "current_step": task_status['current_step'],
            "created_at": task_status['created_at'],
            "started_at": task_status['started_at'],
            "completed_at": task_status['completed_at']
        }
        
        if task_status['status'] == 'completed' and task_status['result_data']:
            response['images_data'] = task_status['result_data']
            response['message'] = "🎉 Imágenes generadas exitosamente"
        elif task_status['status'] == 'failed':
            response['error'] = task_status['error_message']
            response['message'] = "🚨 Error generando imágenes"
        elif task_status['status'] == 'processing':
            response['message'] = f"🎨 Generando imágenes... {task_status['progress_percentage']}%"
        else:
            response['message'] = "⏳ Esperando para procesar imágenes..."
        
        return jsonify(response), 200

    except Exception as e:
        error_msg = f"🚨 ERROR EN IMAGES STATUS: {str(e)}"
        print(error_msg)
        
        return jsonify({
            "error": str(e),
            "error_type": str(type(e).__name__)
        }), 500

@recognition_bp.route("/recognition/<recognition_id>/images", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Recognition'],
    'summary': 'Verificar estado de imágenes generadas para reconocimiento específico',
    'description': '''
Verifica el estado de las imágenes generadas para un reconocimiento específico y devuelve el estado actual.

### Funcionalidades:
- **Verificación de estado**: Consulta si las imágenes están listas
- **Soporte multi-tipo**: Funciona con reconocimiento de ingredientes y alimentos
- **Información detallada**: Progreso y metadatos de generación
- **Validación de propiedad**: Solo el propietario puede consultar sus reconocimientos

### Tipos de Reconocimiento Soportados:
- **Ingredientes**: Reconocimiento simple de ingredientes
- **Alimentos**: Reconocimiento de comidas preparadas  
- **Mixto**: Reconocimiento combinado (batch)
- **Vacío**: Reconocimientos sin elementos detectados

### Estados de Imágenes:
- **ready**: Imagen generada y disponible
- **generating**: Imagen en proceso de generación
- **failed**: Error en la generación
- **pending**: Esperando procesamiento

### Casos de Uso:
- Verificar si las imágenes están listas después del reconocimiento
- Obtener URLs de imágenes generadas automáticamente
- Implementar polling para actualizaciones de UI
- Debugging de problemas en generación de imágenes
    ''',
    'parameters': [
        {
            'name': 'recognition_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'ID único del reconocimiento cuyas imágenes se quieren verificar',
            'example': 'rec_abc123def456'
        }
    ],
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Estado de imágenes del reconocimiento obtenido exitosamente',
            'examples': {
                'application/json': {
                    "recognition_id": "rec_abc123def456",
                    "recognition_type": "ingredients",
                    "images_status": "ready",
                    "images_ready": 3,
                    "images_generating": 0,
                    "total_items": 3,
                    "progress_percentage": 100,
                    "last_updated": "2024-01-16T10:30:45Z",
                    "ingredients": [
                        {
                            "name": "Tomates cherry",
                            "quantity": 500,
                            "type_unit": "gr",
                            "image_path": "https://storage.googleapis.com/generated/tomatoes-abc123.jpg",
                            "image_status": "ready",
                            "confidence": 0.95
                        },
                        {
                            "name": "Queso manchego",
                            "quantity": 200,
                            "type_unit": "gr", 
                            "image_path": "https://storage.googleapis.com/generated/cheese-def456.jpg",
                            "image_status": "ready",
                            "confidence": 0.87
                        },
                        {
                            "name": "Aceite de oliva",
                            "quantity": 250,
                            "type_unit": "ml",
                            "image_path": "https://storage.googleapis.com/generated/oil-ghi789.jpg",
                            "image_status": "ready",
                            "confidence": 0.91
                        }
                    ],
                    "total_ingredients": 3,
                    "message": "✅ Todas las imágenes están listas (ingredients)"
                }
            }
        },
        200: {
            'description': 'Imágenes en proceso de generación',
            'examples': {
                'application/json': {
                    "recognition_id": "rec_abc123def456",
                    "recognition_type": "foods",
                    "images_status": "generating",
                    "images_ready": 1,
                    "images_generating": 1,
                    "total_items": 2,
                    "progress_percentage": 50,
                    "last_updated": "2024-01-16T10:30:30Z",
                    "foods": [
                        {
                            "name": "Pasta carbonara",
                            "image_path": "https://storage.googleapis.com/generated/pasta-jkl012.jpg",
                            "image_status": "ready"
                        },
                        {
                            "name": "Ensalada mixta",
                            "image_path": "https://via.placeholder.com/150x150/f0f0f0/666666?text=Generando...",
                            "image_status": "generating"
                        }
                    ],
                    "total_foods": 2,
                    "message": "🎨 Generando imágenes... 1/2 listas (foods)"
                }
            }
        },
        200: {
            'description': 'Reconocimiento mixto con ingredientes y alimentos',
            'examples': {
                'application/json': {
                    "recognition_id": "rec_abc123def456",
                    "recognition_type": "mixed",
                    "images_status": "ready",
                    "images_ready": 4,
                    "images_generating": 0,
                    "total_items": 4,
                    "progress_percentage": 100,
                    "ingredients": [
                        {
                            "name": "Tomates",
                            "image_status": "ready"
                        }
                    ],
                    "foods": [
                        {
                            "name": "Pizza margherita",
                            "image_status": "ready"
                        }
                    ],
                    "total_ingredients": 1,
                    "total_foods": 1,
                    "message": "✅ Todas las imágenes están listas (mixed)"
                }
            }
        },
        404: {
            'description': 'Reconocimiento no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Reconocimiento no encontrado',
                    'recognition_id': 'rec_invalid123'
                }
            }
        },
        403: {
            'description': 'Sin permisos para ver este reconocimiento',
            'examples': {
                'application/json': {
                    'error': 'No tienes permiso para ver este reconocimiento',
                    'details': 'El reconocimiento pertenece a otro usuario'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno al consultar imágenes del reconocimiento',
            'examples': {
                'application/json': {
                    'error': 'Database connection failed',
                    'error_type': 'DatabaseException'
                }
            }
        }
    }
})
def get_recognition_images(recognition_id):
    """
    🖼️ VERIFICAR IMÁGENES: Verifica si las imágenes están listas y devuelve el estado actual
    Soporta tanto reconocimiento de ingredientes como de alimentos preparados
    """
    user_uid = get_jwt_identity()
    
    print(f"🖼️ [CHECK IMAGES] Recognition: {recognition_id}, User: {user_uid}")
    
    try:
        # Obtener el reconocimiento de la base de datos
        from src.application.factories.recognition_usecase_factory import make_recognition_repository
        recognition_repository = make_recognition_repository(db)
        recognition = recognition_repository.find_by_uid(recognition_id)
        
        if not recognition:
            print(f"❌ [CHECK IMAGES] Recognition {recognition_id} not found")
            return jsonify({"error": "Reconocimiento no encontrado"}), 404
        
        # Verificar que pertenece al usuario
        if recognition.user_uid != user_uid:
            print(f"❌ [CHECK IMAGES] Recognition {recognition_id} unauthorized for user {user_uid}")
            return jsonify({"error": "No tienes permiso para ver este reconocimiento"}), 403
        
        # Determinar el tipo de reconocimiento y obtener los elementos correspondientes
        raw_result = recognition.raw_result
        ingredients = raw_result.get('ingredients', [])
        foods = raw_result.get('foods', [])
        
        # Determinar qué tipo de reconocimiento es
        if ingredients and not foods:
            # Reconocimiento de ingredientes
            items = ingredients
            item_type = "ingredients"
            print(f"🖼️ [CHECK IMAGES] Detected ingredients recognition with {len(items)} items")
        elif foods and not ingredients:
            # Reconocimiento de alimentos preparados
            items = foods
            item_type = "foods"
            print(f"🖼️ [CHECK IMAGES] Detected foods recognition with {len(items)} items")
        elif ingredients and foods:
            # Reconocimiento mixto (batch) - combinar ambos
            items = ingredients + foods
            item_type = "mixed"
            print(f"🖼️ [CHECK IMAGES] Detected mixed recognition with {len(ingredients)} ingredients and {len(foods)} foods")
        else:
            # Sin elementos reconocidos
            items = []
            item_type = "empty"
            print(f"🖼️ [CHECK IMAGES] No items found in recognition")
        
        # Verificar estado de las imágenes
        images_ready = 0
        images_generating = 0
        
        for item in items:
            image_status = item.get('image_status', 'unknown')
            if image_status == 'ready':
                images_ready += 1
            elif image_status == 'generating':
                images_generating += 1
        
        all_images_ready = images_ready == len(items) if items else True
        
        # Preparar respuesta adaptada al tipo de reconocimiento
        response = {
            "recognition_id": recognition_id,
            "recognition_type": item_type,
            "images_status": "ready" if all_images_ready else "generating",
            "images_ready": images_ready,
            "images_generating": images_generating,
            "total_items": len(items),
            "progress_percentage": int((images_ready / len(items)) * 100) if items else 100,
            "last_updated": recognition.recognized_at.isoformat()
        }
        
        # Incluir los elementos según el tipo
        if item_type == "ingredients":
            response["ingredients"] = items
            response["total_ingredients"] = len(items)
        elif item_type == "foods":
            response["foods"] = items
            response["total_foods"] = len(items)
        elif item_type == "mixed":
            response["ingredients"] = ingredients
            response["foods"] = foods
            response["total_ingredients"] = len(ingredients)
            response["total_foods"] = len(foods)
        else:
            response["items"] = []
        
        if all_images_ready:
            response['message'] = f"✅ Todas las imágenes están listas ({item_type})"
            print(f"✅ [CHECK IMAGES] All {images_ready} images ready for {item_type} recognition {recognition_id}")
        else:
            response['message'] = f"🎨 Generando imágenes... {images_ready}/{len(items)} listas ({item_type})"
            print(f"🎨 [CHECK IMAGES] Images progress: {images_ready}/{len(items)} ready for {item_type}")
        
        return jsonify(response), 200

    except Exception as e:
        error_msg = f"🚨 [CHECK IMAGES] ERROR: {str(e)}"
        print(error_msg)
        
        return jsonify({
            "error": str(e),
            "error_type": str(type(e).__name__)
        }), 500