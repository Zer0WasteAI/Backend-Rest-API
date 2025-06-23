from flasgger import swag_from # type: ignore
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.infrastructure.db.base import db

from src.interface.serializers.inventory_serializers import (
AddIngredientsBatchSchema,
InventorySchema,
UpdateIngredientSchema,
UpdateIngredientQuantitySchema,
UpdateFoodQuantitySchema
)

from src.interface.serializers.add_item_serializer import AddItemToInventorySchema, AddItemResponseSchema
from src.interface.serializers.mark_consumed_serializer import (
    MarkIngredientConsumedSchema, 
    MarkFoodConsumedSchema, 
    ConsumedResponseSchema
)

from src.application.factories.inventory_usecase_factory import (
make_add_food_items_to_inventory_use_case,
make_add_ingredients_and_foods_to_inventory_use_case,
make_add_ingredients_to_inventory_use_case,
make_add_item_to_inventory_use_case,
make_delete_food_item_use_case,
make_delete_ingredient_stack_use_case,
make_delete_ingredient_complete_use_case,
make_get_ingredient_detail_use_case,
make_get_food_detail_use_case,
make_get_ingredients_list_use_case,
make_get_foods_list_use_case,
make_get_expiring_soon_use_case,
make_get_inventory_content_use_case,
make_update_food_item_use_case,
make_update_ingredient_stack_use_case,
make_update_ingredient_quantity_use_case,
make_update_food_quantity_use_case,
make_mark_ingredient_stack_consumed_use_case,
make_mark_food_item_consumed_use_case
)

from src.application.factories.inventory_image_upload_factory import make_upload_inventory_image_use_case

from src.shared.exceptions.custom import InvalidRequestDataException

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route("/ingredients", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Agregar ingredientes al inventario por lotes',
    'description': '''
Agrega múltiples ingredientes al inventario del usuario en una sola operación.

### Funcionalidades:
- **Agregar por lotes**: Múltiples ingredientes en una sola request
- **Cálculo automático**: Fechas de vencimiento basadas en tiempo estimado
- **Validación completa**: Todos los campos son validados antes de guardar
- **Organización**: Agrupa por tipo de almacenamiento y categoría

### Campos Requeridos por Ingrediente:
- `name`: Nombre del ingrediente
- `quantity`: Cantidad numérica
- `type_unit`: Unidad de medida (gr, ml, piezas, etc.)
- `storage_type`: Tipo de almacenamiento (refrigerador, congelador, despensa)
- `expiration_time`: Tiempo estimado hasta vencimiento
- `time_unit`: Unidad de tiempo (días, semanas, meses)

### Campos Opcionales:
- `tips`: Consejos de almacenamiento
- `image_path`: URL de imagen del ingrediente
- `expiration_date`: Fecha específica de vencimiento (sobrescribe cálculo automático)

### Validaciones:
- Quantity debe ser mayor a 0
- Storage_type debe ser válido
- Time_unit debe ser válido (days, weeks, months)
- Name no puede estar vacío
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
                            'required': ['name', 'quantity', 'type_unit', 'storage_type', 'expiration_time', 'time_unit'],
                            'properties': {
                                'name': {'type': 'string', 'example': 'Tomates cherry'},
                                'quantity': {'type': 'number', 'example': 500},
                                'type_unit': {'type': 'string', 'example': 'gr'},
                                'storage_type': {'type': 'string', 'enum': ['refrigerador', 'congelador', 'despensa'], 'example': 'refrigerador'},
                                'expiration_time': {'type': 'integer', 'example': 5},
                                'time_unit': {'type': 'string', 'enum': ['days', 'weeks', 'months'], 'example': 'days'},
                                'tips': {'type': 'string', 'example': 'Mantener en lugar fresco y seco'},
                                'image_path': {'type': 'string', 'example': 'https://storage.googleapis.com/...'},
                                'expiration_date': {'type': 'string', 'format': 'date-time', 'example': '2024-01-20T00:00:00Z'}
                            }
                        },
                        'example': [
                            {
                                'name': 'Tomates cherry',
                                'quantity': 500,
                                'type_unit': 'gr',
                                'storage_type': 'refrigerador',
                                'expiration_time': 5,
                                'time_unit': 'days',
                                'tips': 'Mantener refrigerados para mayor duración',
                                'image_path': 'https://storage.googleapis.com/bucket/tomatoes.jpg'
                            },
                            {
                                'name': 'Arroz integral',
                                'quantity': 1,
                                'type_unit': 'kg',
                                'storage_type': 'despensa',
                                'expiration_time': 6,
                                'time_unit': 'months',
                                'tips': 'Almacenar en recipiente hermético'
                            }
                        ]
                    }
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Ingredientes agregados exitosamente',
            'examples': {
                'application/json': {
                    'message': 'Ingredientes agregados exitosamente'
                }
            }
        },
        400: {
            'description': 'Datos de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid JSON data',
                    'details': {
                        'ingredients': ['Este campo es requerido'],
                        'ingredients.0.name': ['Campo requerido'],
                        'ingredients.0.quantity': ['Debe ser mayor a 0']
                    }
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
            'description': 'Error interno del servidor',
            'examples': {
                'application/json': {
                    'error': 'Internal server error',
                    'details': 'Database connection failed'
                }
            }
        }
    }
})
def add_ingredients():
    user_uid = get_jwt_identity()
    
    print(f"📥 [INVENTORY POST] ===== REQUEST DETAILS =====")
    print(f"📥 [INVENTORY POST] User: {user_uid}")
    print(f"📥 [INVENTORY POST] Method: {request.method}")
    print(f"📥 [INVENTORY POST] URL: {request.url}")
    print(f"📥 [INVENTORY POST] Content-Type: {request.content_type}")
    print(f"📥 [INVENTORY POST] Content-Length: {request.content_length}")
    
    # Log headers (sin datos sensibles)
    print(f"📥 [INVENTORY POST] Headers:")
    for header_name, header_value in request.headers:
        if header_name.lower() not in ['authorization', 'cookie']:
            print(f"📥 [INVENTORY POST]   {header_name}: {header_value}")
    
    # Obtener y validar JSON
    try:
        json_data = request.get_json()
        print(f"📥 [INVENTORY POST] Raw JSON received: {json_data}")
        
        if not json_data:
            print(f"❌ [INVENTORY POST] ERROR: No JSON data received")
            return jsonify({"error": "No JSON data provided"}), 400
            
        print(f"📥 [INVENTORY POST] JSON keys: {list(json_data.keys()) if json_data else 'None'}")
        
    except Exception as json_error:
        print(f"❌ [INVENTORY POST] JSON parsing error: {str(json_error)}")
        print(f"❌ [INVENTORY POST] Raw data: {request.data}")
        return jsonify({"error": "Invalid JSON data", "details": str(json_error)}), 400
    
    # Validación con schema
    print(f"📥 [INVENTORY POST] ===== SCHEMA VALIDATION =====")
    schema = AddIngredientsBatchSchema()
    errors = schema.validate(json_data)
    if errors:
        print(f"❌ [INVENTORY POST] Schema validation errors: {errors}")
        print(f"❌ [INVENTORY POST] Failed fields: {list(errors.keys())}")
        raise InvalidRequestDataException(details=errors)
    
    print(f"✅ [INVENTORY POST] Schema validation passed")

    # Procesar ingredientes
    ingredients_data = json_data.get("ingredients")
    print(f"🥬 [INVENTORY POST] ===== INGREDIENTS PROCESSING =====")
    print(f"🥬 [INVENTORY POST] Total ingredients to process: {len(ingredients_data) if ingredients_data else 0}")
    
    if not ingredients_data:
        print(f"❌ [INVENTORY POST] ERROR: No ingredients data found")
        return jsonify({"error": "No ingredients provided"}), 400
    
    # Log detallado de cada ingrediente
    for i, ingredient in enumerate(ingredients_data):
        print(f"📦 [INVENTORY POST] Ingredient {i+1}/{len(ingredients_data)}:")
        print(f"   └─ Name: {ingredient.get('name', 'MISSING')}")
        print(f"   └─ Quantity: {ingredient.get('quantity', 'MISSING')}")
        print(f"   └─ Unit: {ingredient.get('type_unit', 'MISSING')}")
        print(f"   └─ Storage: {ingredient.get('storage_type', 'MISSING')}")
        print(f"   └─ Tips: {ingredient.get('tips', 'MISSING')}")
        print(f"   └─ Image: {ingredient.get('image_path', 'MISSING')[:50]}..." if ingredient.get('image_path') else "   └─ Image: MISSING")
        print(f"   └─ Has expiration_date: {'YES' if ingredient.get('expiration_date') else 'NO'}")
        print(f"   └─ Has expiration_time: {'YES' if ingredient.get('expiration_time') else 'NO'}")
        print(f"   └─ All keys: {list(ingredient.keys())}")

    print(f"🥬 [INVENTORY POST] ===== STARTING USE CASE EXECUTION =====")
    try:
        use_case = make_add_ingredients_to_inventory_use_case(db)
        print(f"🥬 [INVENTORY POST] Use case factory created successfully")
        
        print(f"🥬 [INVENTORY POST] Calling use_case.execute()...")
        use_case.execute(user_uid=user_uid, ingredients_data=ingredients_data)
        print(f"🥬 [INVENTORY POST] Use case execution completed successfully")
        
        print(f"✅ [INVENTORY POST] ===== SUCCESS =====")
        print(f"✅ [INVENTORY POST] Successfully added {len(ingredients_data)} ingredients for user {user_uid}")
        print(f"✅ [INVENTORY POST] Returning 201 response")
        return jsonify({"message": "Ingredientes agregados exitosamente"}), 201
        
    except Exception as e:
        print(f"🚨 [INVENTORY POST] ===== ERROR DETAILS =====")
        print(f"🚨 [INVENTORY POST] Error type: {type(e).__name__}")
        print(f"🚨 [INVENTORY POST] Error message: {str(e)}")
        print(f"🚨 [INVENTORY POST] User: {user_uid}")
        print(f"🚨 [INVENTORY POST] Ingredients count: {len(ingredients_data)}")
        
        # Log stack trace para debugging
        import traceback
        print(f"🚨 [INVENTORY POST] FULL STACK TRACE:")
        print(traceback.format_exc())
        print(f"🚨 [INVENTORY POST] ===== END ERROR =====")
        raise e

@inventory_bp.route("", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Obtener inventario completo del usuario',
    'description': '''
Obtiene el inventario completo del usuario con todos los ingredientes y alimentos organizados.

### Estructura del Inventario:
- **Ingredientes**: Agrupados por nombre con múltiples "stacks" (lotes)
- **Alimentos**: Lista de alimentos individuales 
- **Información detallada**: Fechas de vencimiento, cantidades, ubicación de almacenamiento

### Organización de Datos:
- Los ingredientes del mismo tipo se agrupan automáticamente
- Cada "stack" representa un lote con fecha específica de agregado
- Se incluyen imágenes, consejos de almacenamiento y fechas de vencimiento

### Datos Incluidos:
- **Por Ingrediente**: Nombre, stacks, cantidad total, unidad, tipo de almacenamiento
- **Por Stack**: Cantidad individual, fecha agregada, fecha vencimiento, consejos
- **Metadatos**: Totales, conteos, análisis de vencimientos próximos

### Casos de Uso:
- Ver todo el inventario disponible
- Planificar recetas basadas en ingredientes disponibles
- Revisar fechas de vencimiento
- Gestionar organización del almacenamiento
    ''',
    'responses': {
        200: {
            'description': 'Inventario obtenido exitosamente',
            'examples': {
                'application/json': {
                    "user_uid": "firebase_uid_123",
                    "ingredients": {
                        "Tomates cherry": {
                            "name": "Tomates cherry",
                            "type_unit": "gr",
                            "storage_type": "refrigerador",
                            "image_path": "https://storage.googleapis.com/bucket/tomatoes.jpg",
                            "stacks": [
                                {
                                    "quantity": 500,
                                    "added_at": "2024-01-15T10:00:00Z",
                                    "expiration_date": "2024-01-20T00:00:00Z",
                                    "tips": "Mantener refrigerados",
                                    "days_until_expiration": 5
                                }
                            ]
                        },
                        "Arroz integral": {
                            "name": "Arroz integral", 
                            "type_unit": "kg",
                            "storage_type": "despensa",
                            "stacks": [
                                {
                                    "quantity": 1,
                                    "added_at": "2024-01-15T10:00:00Z",
                                    "expiration_date": "2024-07-15T00:00:00Z",
                                    "tips": "Almacenar en recipiente hermético",
                                    "days_until_expiration": 180
                                }
                            ]
                        }
                    },
                    "foods": [],
                    "summary": {
                        "total_ingredient_types": 2,
                        "total_food_items": 0,
                        "expiring_soon_count": 1,
                        "storage_distribution": {
                            "refrigerador": 1,
                            "despensa": 1,
                            "congelador": 0
                        }
                    }
                }
            }
        },
        404: {
            'description': 'Inventario no encontrado para el usuario',
            'examples': {
                'application/json': {
                    'message': 'Inventario no encontrado'
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
            'description': 'Error interno del servidor',
            'examples': {
                'application/json': {
                    'error': 'Internal server error',
                    'details': 'Database query failed'
                }
            }
        }
    }
})
def get_inventory():
    user_uid = get_jwt_identity()
    
    print(f"📤 [INVENTORY GET] ===== REQUEST DETAILS =====")
    print(f"📤 [INVENTORY GET] User: {user_uid}")
    print(f"📤 [INVENTORY GET] Method: {request.method}")
    print(f"📤 [INVENTORY GET] URL: {request.url}")
    print(f"📤 [INVENTORY GET] User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    # Log query parameters if any
    if request.args:
        print(f"📤 [INVENTORY GET] Query params: {dict(request.args)}")
    else:
        print(f"📤 [INVENTORY GET] No query parameters")
    
    print(f"📤 [INVENTORY GET] ===== STARTING USE CASE EXECUTION =====")
    try:
        print(f"📤 [INVENTORY GET] Creating use case...")
        use_case = make_get_inventory_content_use_case(db)
        print(f"📤 [INVENTORY GET] Use case created successfully")
        
        print(f"📤 [INVENTORY GET] Calling use_case.execute()...")
        inventory = use_case.execute(user_uid)
        print(f"📤 [INVENTORY GET] Use case execution completed")

        print(f"📤 [INVENTORY GET] ===== INVENTORY ANALYSIS =====")
        if not inventory:
            print(f"❌ [INVENTORY GET] No inventory found for user: {user_uid}")
            print(f"❌ [INVENTORY GET] Returning 404 response")
            return jsonify({"message": "Inventario no encontrado"}), 404

        print(f"📤 [INVENTORY GET] Inventory object type: {type(inventory)}")
        print(f"📤 [INVENTORY GET] Inventory user_uid: {inventory.user_uid}")
        print(f"📤 [INVENTORY GET] Total ingredient types: {len(inventory.ingredients)}")
        
        # Log ingredient details (máximo 10 para no saturar)
        total_stacks = 0
        ingredient_details = []
        
        for i, (name, ingredient) in enumerate(inventory.ingredients.items()):
            stack_count = len(ingredient.stacks)
            total_stacks += stack_count
            total_quantity = sum(stack.quantity for stack in ingredient.stacks)
            
            detail = {
                'name': name,
                'stacks': stack_count,
                'quantity': total_quantity,
                'unit': ingredient.type_unit,
                'storage': ingredient.storage_type,
                'has_image': bool(ingredient.image_path)
            }
            ingredient_details.append(detail)
            
            if i < 10:  # Log solo los primeros 10
                print(f"📤 [INVENTORY GET]   • {name}: {stack_count} stacks, {total_quantity} {ingredient.type_unit}, storage: {ingredient.storage_type}")
        
        if len(inventory.ingredients) > 10:
            print(f"📤 [INVENTORY GET]   ... and {len(inventory.ingredients) - 10} more ingredients")
        
        print(f"📤 [INVENTORY GET] Total stacks across all ingredients: {total_stacks}")

        print(f"📤 [INVENTORY GET] ===== SERIALIZATION =====")
        try:
            schema = InventorySchema()
            print(f"📤 [INVENTORY GET] Schema created successfully")
            
            inventory_data = {
                "ingredients": list(inventory.ingredients.values()),
                "food_items": []  # Futuro
            }
            print(f"📤 [INVENTORY GET] Data structure prepared for serialization")
            print(f"📤 [INVENTORY GET] Serializing {len(inventory_data['ingredients'])} ingredients...")
            
            result = schema.dump(inventory_data)
            print(f"📤 [INVENTORY GET] Serialization completed successfully")
            print(f"📤 [INVENTORY GET] Result type: {type(result)}")
            print(f"📤 [INVENTORY GET] Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict) and 'ingredients' in result:
                print(f"📤 [INVENTORY GET] Serialized ingredients count: {len(result['ingredients'])}")
            
            response_size = len(str(result))
            print(f"📤 [INVENTORY GET] Response size: ~{response_size} characters")
            
        except Exception as serialization_error:
            print(f"🚨 [INVENTORY GET] Serialization error: {str(serialization_error)}")
            print(f"🚨 [INVENTORY GET] Serialization error type: {type(serialization_error).__name__}")
            raise serialization_error
        
        print(f"✅ [INVENTORY GET] ===== SUCCESS =====")
        print(f"✅ [INVENTORY GET] Successfully processed inventory:")
        print(f"✅ [INVENTORY GET]   - {len(result['ingredients'])} ingredients serialized")
        print(f"✅ [INVENTORY GET]   - {total_stacks} total stacks")
        print(f"✅ [INVENTORY GET]   - User: {user_uid}")
        print(f"✅ [INVENTORY GET] Returning 200 response")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"🚨 [INVENTORY GET] ===== ERROR DETAILS =====")
        print(f"🚨 [INVENTORY GET] Error type: {type(e).__name__}")
        print(f"🚨 [INVENTORY GET] Error message: {str(e)}")
        print(f"🚨 [INVENTORY GET] User: {user_uid}")
        
        # Log stack trace para debugging
        import traceback
        print(f"🚨 [INVENTORY GET] FULL STACK TRACE:")
        print(traceback.format_exc())
        print(f"🚨 [INVENTORY GET] ===== END ERROR =====")
        raise e

@inventory_bp.route("/complete", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Obtener inventario completo con análisis IA enriquecido',
    'description': '''
Obtiene el inventario completo del usuario con información enriquecida por IA incluyendo impacto ambiental y sugerencias de uso.

### Información Enriquecida Incluida:
- **Análisis ambiental**: Huella de carbono, uso de agua, sostenibilidad
- **Ideas de aprovechamiento**: Sugerencias creativas de uso
- **Información nutricional**: Análisis detallado de nutrientes
- **Tips de conservación**: Recomendaciones específicas por ingrediente
- **Estado de frescura**: Evaluación del estado actual

### Diferencias vs Inventario Básico:
- **Inventario básico**: Solo datos almacenados del usuario
- **Inventario completo**: Datos + análisis IA + recomendaciones
- **Procesamiento**: Requiere más tiempo pero proporciona valor agregado
- **Casos de uso**: Planificación avanzada, educación, sostenibilidad

### Funcionalidades IA:
- Análisis de impacto ambiental por ingrediente
- Generación de ideas de aprovechamiento personalizadas
- Evaluación de sostenibilidad y recomendaciones eco-friendly
- Sugerencias de uso basadas en cantidad y estado
- Tips de conservación optimizados

### Casos de Uso:
- Dashboard principal con insights inteligentes
- Planificación de menús sostenibles
- Educación sobre impacto ambiental
- Optimización de uso de ingredientes
- Reducción de desperdicio alimentario
    ''',
    'responses': {
        200: {
            'description': 'Inventario completo con análisis IA obtenido exitosamente',
            'examples': {
                'application/json': {
                    "ingredients": [
                        {
                            "name": "Tomates cherry",
                            "quantity": 500,
                            "type_unit": "gr",
                            "storage_type": "refrigerador",
                            "expiration_date": "2024-01-25T00:00:00Z",
                            "expiration_time": 8,
                            "time_unit": "Días",
                            "added_at": "2024-01-17T10:00:00Z",
                            "tips": "Mantener refrigerados para mayor frescura",
                            "environmental_impact": {
                                "carbon_footprint": {
                                    "value": 0.4,
                                    "unit": "kg CO2 eq",
                                    "description": "Huella de carbono por kg"
                                },
                                "water_footprint": {
                                    "value": 214,
                                    "unit": "litros",
                                    "description": "Agua utilizada en producción"
                                },
                                "sustainability_message": "Ingrediente de temporada con bajo impacto ambiental. Prefiere productores locales."
                            },
                            "utilization_ideas": [
                                {
                                    "title": "Ensalada mediterránea fresca",
                                    "description": "Combina con mozzarella, albahaca y aceite de oliva para una ensalada caprese clásica.",
                                    "type": "receta"
                                },
                                {
                                    "title": "Salsa de tomate casera",
                                    "description": "Procesa con ajo y hierbas para crear una salsa fresca para pasta.",
                                    "type": "preparación"
                                },
                                {
                                    "title": "Conservación óptima",
                                    "description": "Almacena con el tallo hacia abajo para prolongar frescura.",
                                    "type": "conservación"
                                }
                            ]
                        },
                        {
                            "name": "Queso manchego",
                            "quantity": 250,
                            "type_unit": "gr",
                            "storage_type": "refrigerador",
                            "expiration_date": "2024-02-15T00:00:00Z",
                            "expiration_time": 29,
                            "time_unit": "Días",
                            "added_at": "2024-01-16T15:30:00Z",
                            "tips": "Envolver en papel encerado para mantener textura",
                            "environmental_impact": {
                                "carbon_footprint": {
                                    "value": 8.2,
                                    "unit": "kg CO2 eq",
                                    "description": "Impacto por kg de queso curado"
                                },
                                "water_footprint": {
                                    "value": 3178,
                                    "unit": "litros",
                                    "description": "Agua requerida en producción láctea"
                                },
                                "sustainability_message": "Producto lácteo con mayor impacto. Consume moderadamente y aprovecha completamente."
                            },
                            "utilization_ideas": [
                                {
                                    "title": "Tabla de quesos gourmet",
                                    "description": "Presenta con membrillo, nueces y vino para una experiencia completa.",
                                    "type": "presentación"
                                },
                                {
                                    "title": "Gratinado de verduras",
                                    "description": "Ralla sobre verduras al horno para un toque cremoso y sabroso.",
                                    "type": "técnica"
                                }
                            ]
                        }
                    ],
                    "food_items": [],
                    "total_ingredients": 2,
                    "enriched_with": ["environmental_impact", "utilization_ideas"],
                    "analysis_summary": {
                        "total_carbon_footprint": 2.6,
                        "total_water_usage": 1696,
                        "sustainability_score": 7.3,
                        "recommendations": [
                            "Prioriza consumo de tomates por menor impacto ambiental",
                            "Aprovecha completamente el queso para maximizar valor",
                            "Considera recetas que combinen ambos ingredientes"
                        ]
                    },
                    "processing_metadata": {
                        "ai_analysis_time": 3.2,
                        "enrichment_success_rate": 1.0,
                        "data_sources": ["environmental_db", "culinary_knowledge", "nutrition_data"]
                    }
                }
            }
        },
        404: {
            'description': 'Inventario vacío',
            'examples': {
                'application/json': {
                    'message': 'No items found in inventory',
                    'ingredients': [],
                    'food_items': [],
                    'total_ingredients': 0
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error en análisis IA o procesamiento'
        }
    }
})
def get_inventory_complete():
    """
    Endpoint para obtener el inventario completo con toda la información:
    - Datos básicos del inventario
    - Impacto ambiental de cada ingrediente
    - Ideas de aprovechamiento para cada ingrediente
    """
    user_uid = get_jwt_identity()
    
    print(f"📤 [INVENTORY GET COMPLETE] Fetching complete inventory for user: {user_uid}")
    
    try:
        use_case = make_get_inventory_content_use_case(db)
        inventory = use_case.execute(user_uid)

        if not inventory:
            print(f"❌ [INVENTORY GET COMPLETE] No inventory found for user: {user_uid}")
            return jsonify({"message": "Inventario no encontrado"}), 404

        print(f"📊 [INVENTORY GET COMPLETE] Found inventory with {len(inventory.ingredients)} ingredient types")
        
        # Enriquecer con información completa usando el servicio AI
        from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
        ai_service = GeminiAdapterService()
        
        enriched_ingredients = []
        
        for name, ingredient in inventory.ingredients.items():
            print(f"🔍 [INVENTORY GET COMPLETE] Enriching ingredient: {name}")
            
            # Serializar la información básica del ingrediente
            basic_ingredient_data = {
                "name": ingredient.name,
                "type_unit": ingredient.type_unit,
                "storage_type": ingredient.storage_type,
                "tips": ingredient.tips,
                "image_path": ingredient.image_path,
                "stacks": [
                    {
                        "quantity": stack.quantity,
                        "type_unit": ingredient.type_unit,
                        "expiration_date": stack.expiration_date.isoformat(),
                        "added_at": stack.added_at.isoformat()
                    }
                    for stack in ingredient.stacks
                ]
            }
            
            try:
                # Obtener impacto ambiental
                environmental_data = ai_service.analyze_environmental_impact(ingredient.name)
                basic_ingredient_data.update(environmental_data)
                
                # Obtener ideas de aprovechamiento (usar tips como descripción)
                utilization_data = ai_service.generate_utilization_ideas(ingredient.name, ingredient.tips)
                basic_ingredient_data.update(utilization_data)
                
                print(f"✅ [INVENTORY GET COMPLETE] Enriched {ingredient.name} with complete data")
                
            except Exception as e:
                print(f"⚠️ [INVENTORY GET COMPLETE] Error enriching {ingredient.name}: {str(e)}")
                # Agregar datos por defecto en caso de error
                basic_ingredient_data["environmental_impact"] = {
                    "carbon_footprint": {"value": 0.0, "unit": "kg", "description": "CO2"},
                    "water_footprint": {"value": 0, "unit": "l", "description": "agua"},
                    "sustainability_message": "Consume de manera responsable y evita el desperdicio."
                }
                basic_ingredient_data["utilization_ideas"] = [
                    {
                        "title": "Consume fresco",
                        "description": "Utiliza el ingrediente lo antes posible para aprovechar sus nutrientes.",
                        "type": "conservación"
                    }
                ]
            
            enriched_ingredients.append(basic_ingredient_data)
        
        result = {
            "ingredients": enriched_ingredients,
            "food_items": [],  # Futuro
            "total_ingredients": len(enriched_ingredients),
            "enriched_with": ["environmental_impact", "utilization_ideas"]
        }
        
        print(f"✅ [INVENTORY GET COMPLETE] Successfully enriched and serialized complete inventory")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"🚨 [INVENTORY GET COMPLETE] Error fetching complete inventory: {str(e)}")
        raise e

@inventory_bp.route("/ingredients/<ingredient_name>/<added_at>", methods=["PUT"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Actualizar información completa de un stack de ingrediente',
    'description': '''
Actualiza la información completa de un stack específico de ingrediente en el inventario.

### Campos Actualizables:
- **Cantidad**: Nueva cantidad del ingrediente
- **Fecha de vencimiento**: Cambiar fecha de expiración
- **Tipo de almacenamiento**: Mover entre refrigerador, congelador, despensa
- **Tips de conservación**: Actualizar consejos de almacenamiento
- **Imagen**: Cambiar URL de imagen asociada

### Validaciones Incluidas:
- Verificación de propiedad del ingrediente por usuario
- Validación de cantidad mayor a 0
- Confirmación de tipos de almacenamiento válidos
- Validación de formato de fecha ISO
- Prevención de actualizaciones inconsistentes

### Comportamiento:
- **Actualización selectiva**: Solo actualiza campos proporcionados
- **Preservación de datos**: Mantiene campos no especificados
- **Validación completa**: Verifica consistencia de todos los datos
- **Historial**: Registra cambios para auditoría

### Casos de Uso:
- Corrección de errores de entrada
- Actualización de fechas de vencimiento
- Cambio de ubicación de almacenamiento
- Modificación de cantidades por conteo físico
- Actualización de tips de conservación
    ''',
    'parameters': [
        {
            'name': 'ingredient_name',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Nombre exacto del ingrediente',
            'example': 'Tomates cherry'
        },
        {
            'name': 'added_at',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Timestamp exacto de cuando se agregó el stack (formato ISO)',
            'example': '2024-01-15T10:00:00Z'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'quantity': {
                        'type': 'number',
                        'description': 'Nueva cantidad del ingrediente',
                        'example': 400,
                        'minimum': 0.01
                    },
                    'expiration_date': {
                        'type': 'string',
                        'format': 'date-time',
                        'description': 'Nueva fecha de vencimiento (formato ISO)',
                        'example': '2024-01-25T00:00:00Z'
                    },
                    'storage_type': {
                        'type': 'string',
                        'enum': ['refrigerador', 'congelador', 'despensa'],
                        'description': 'Nuevo tipo de almacenamiento',
                        'example': 'congelador'
                    },
                    'tips': {
                        'type': 'string',
                        'description': 'Nuevos consejos de conservación',
                        'example': 'Congelar en porciones pequeñas para facilitar uso',
                        'maxLength': 500
                    },
                    'image_path': {
                        'type': 'string',
                        'format': 'uri',
                        'description': 'Nueva URL de imagen del ingrediente',
                        'example': 'https://storage.googleapis.com/bucket/updated_tomatoes.jpg'
                    }
                },
                'example': {
                    'quantity': 350,
                    'expiration_date': '2024-01-28T00:00:00Z',
                    'storage_type': 'refrigerador',
                    'tips': 'Mantener en cajón de verduras para mayor frescura',
                    'image_path': 'https://storage.googleapis.com/bucket/fresh_tomatoes.jpg'
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Ingrediente actualizado exitosamente',
            'examples': {
                'application/json': {
                    "message": "Ingrediente actualizado exitosamente",
                    "update_details": {
                        "ingredient_name": "Tomates cherry",
                        "stack_identifier": {
                            "added_at": "2024-01-15T10:00:00Z",
                            "updated_at": "2024-01-17T16:30:00Z"
                        },
                        "changes_applied": {
                            "quantity": {
                                "old_value": 500,
                                "new_value": 350,
                                "change_type": "decreased"
                            },
                            "expiration_date": {
                                "old_value": "2024-01-22T00:00:00Z",
                                "new_value": "2024-01-28T00:00:00Z",
                                "change_type": "extended"
                            },
                            "storage_type": {
                                "old_value": "despensa",
                                "new_value": "refrigerador",
                                "change_type": "relocated"
                            },
                            "tips": {
                                "old_value": "Mantener en lugar fresco",
                                "new_value": "Mantener en cajón de verduras para mayor frescura",
                                "change_type": "updated"
                            }
                        },
                        "fields_unchanged": ["type_unit", "image_path"]
                    },
                    "inventory_impact": {
                        "total_ingredient_quantity_change": -150,
                        "storage_reorganization": {
                            "moved_from": "despensa",
                            "moved_to": "refrigerador"
                        },
                        "expiration_impact": {
                            "days_extended": 6,
                            "new_expiration_priority": "medium"
                        }
                    },
                    "validation_results": {
                        "quantity_valid": True,
                        "expiration_date_valid": True,
                        "storage_type_valid": True,
                        "tips_length_valid": True,
                        "overall_consistency": True
                    }
                }
            }
        },
        400: {
            'description': 'Datos de actualización inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid update data',
                    'details': {
                        'quantity': ['La cantidad debe ser mayor a 0'],
                        'expiration_date': ['Formato de fecha inválido'],
                        'storage_type': ['Tipo de almacenamiento no válido']
                    },
                    'valid_storage_types': ['refrigerador', 'congelador', 'despensa']
                }
            }
        },
        404: {
            'description': 'Stack de ingrediente no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Ingredient stack not found',
                    'details': 'No se encontró el stack específico del ingrediente para actualizar'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno del servidor durante la actualización'
        }
    }
})
def update_ingredient(ingredient_name, added_at):
    from urllib.parse import unquote
    
    # Decodificar el nombre del ingrediente URL-encoded
    ingredient_name = unquote(ingredient_name)
    
    # Restaurar caracteres especiales que fueron reemplazados para ser URL-safe
    ingredient_name = ingredient_name.replace('_SLASH_', '/')
    
    user_uid = get_jwt_identity()
    schema = UpdateIngredientSchema()
    json_data = request.get_json()

    errors = schema.validate(json_data)
    if errors:
        raise InvalidRequestDataException(details=errors)

    use_case = make_update_ingredient_stack_use_case(db)
    use_case.execute(
        user_uid=user_uid,
        ingredient_name=ingredient_name,
        added_at=added_at,
        updated_data=json_data
    )

    return jsonify({"message": "Ingrediente actualizado exitosamente"}), 200

@inventory_bp.route("/ingredients/<ingredient_name>/<added_at>", methods=["DELETE"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Eliminar stack específico de ingrediente',
    'description': '''
Elimina un stack específico de un ingrediente identificado por nombre y timestamp de agregado.

### Funcionamiento del Sistema de Stacks:
- **Stack**: Lote individual de un ingrediente agregado en un momento específico
- **Identificación única**: Nombre + timestamp exacto de agregado
- **Eliminación selectiva**: Solo elimina el stack específico, no todo el ingrediente
- **Auto-limpieza**: Si es el último stack, elimina el ingrediente completo

### Validaciones de Seguridad:
- Verificación de propiedad del ingrediente por usuario
- Confirmación de existencia del stack específico
- Validación de formato de timestamp ISO
- Prevención de eliminación accidental

### Impacto de la Eliminación:
- **Inmediato**: Stack eliminado permanentemente
- **Inventario**: Cantidad total del ingrediente se reduce
- **Historial**: Se mantiene registro de la eliminación
- **Irreversible**: No se puede deshacer la operación
- **Limpieza automática**: Si es el último stack, se elimina el ingrediente completo

### Casos de Uso:
- Corrección de errores de entrada
- Eliminación de ingredientes vencidos específicos
- Gestión granular de lotes con diferentes calidades
- Limpieza de inventario por fechas específicas
- Gestión de ingredientes con múltiples compras
    ''',
    'parameters': [
        {
            'name': 'ingredient_name',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Nombre exacto del ingrediente',
            'example': 'Tomates cherry'
        },
        {
            'name': 'added_at',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Timestamp exacto de cuando se agregó el stack (formato ISO)',
            'example': '2024-01-15T10:00:00Z'
        }
    ],
    'responses': {
        200: {
            'description': 'Stack eliminado exitosamente',
            'examples': {
                'application/json': {
                    "message": "Stack de ingrediente eliminado exitosamente",
                    "ingredient": "Tomates cherry",
                    "deleted_stack_added_at": "2024-01-15T10:00:00Z",
                    "note": "Si era el último stack, el ingrediente fue eliminado completamente",
                    "deletion_details": {
                        "stack_info": {
                            "ingredient_name": "Tomates cherry",
                            "quantity_removed": 300,
                            "type_unit": "gr",
                            "storage_type": "refrigerador",
                            "expiration_date": "2024-01-22T00:00:00Z",
                            "was_last_stack": False
                        },
                        "remaining_inventory": {
                            "ingredient_still_exists": True,
                            "remaining_stacks": 1,
                            "total_quantity_remaining": 450,
                            "next_expiration": "2024-01-25T00:00:00Z"
                        },
                        "operation_metadata": {
                            "deleted_at": "2024-01-17T15:30:00Z",
                            "user_id": "user123",
                            "operation_type": "stack_deletion"
                        }
                    }
                }
            }
        },
        404: {
            'description': 'Stack no encontrado',
            'examples': {
                'application/json': {
                    'error': "Error eliminando stack del ingrediente 'Tomates cherry': Stack not found",
                    'details': {
                        'ingredient_name': 'Tomates cherry',
                        'timestamp_searched': '2024-01-15T10:00:00Z',
                        'possible_causes': [
                            'Timestamp incorrecto',
                            'Stack ya eliminado previamente',
                            'Ingrediente no existe para este usuario'
                        ],
                        'available_stacks': [
                            {
                                'added_at': '2024-01-16T14:30:00Z',
                                'quantity': 200,
                                'expiration_date': '2024-01-23T00:00:00Z'
                            }
                        ]
                    }
                }
            }
        },
        400: {
            'description': 'Formato de timestamp inválido',
            'examples': {
                'application/json': {
                    'error': 'Invalid timestamp format',
                    'details': 'El timestamp debe estar en formato ISO (YYYY-MM-DDTHH:MM:SSZ)',
                    'provided_timestamp': '15-01-2024 10:00:00',
                    'expected_format': '2024-01-15T10:00:00Z'
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
def delete_ingredient(ingredient_name, added_at):
    """
    Elimina un stack específico de ingrediente del inventario.
    Si es el último stack, elimina también el ingrediente completo.
    
    URL: DELETE /api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z
    """
    from urllib.parse import unquote
    
    # Decodificar el nombre del ingrediente URL-encoded
    ingredient_name = unquote(ingredient_name)
    
    # Restaurar caracteres especiales que fueron reemplazados para ser URL-safe
    ingredient_name = ingredient_name.replace('_SLASH_', '/')
    
    user_uid = get_jwt_identity()
    
    print(f"🗑️ [DELETE INGREDIENT STACK] User: {user_uid}")
    print(f"   └─ Ingredient: {ingredient_name}")
    print(f"   └─ Stack added at: {added_at}")

    try:
        use_case = make_delete_ingredient_stack_use_case(db)
        use_case.execute(user_uid, ingredient_name, added_at)

        print(f"✅ [DELETE INGREDIENT STACK] Successfully deleted stack for: {ingredient_name}")
        return jsonify({
            "message": "Stack de ingrediente eliminado exitosamente",
            "ingredient": ingredient_name,
            "deleted_stack_added_at": added_at,
            "note": "Si era el último stack, el ingrediente fue eliminado completamente"
        }), 200

    except Exception as e:
        print(f"❌ [DELETE INGREDIENT STACK] Error: {str(e)}")
        return jsonify({
            "error": f"Error eliminando stack del ingrediente '{ingredient_name}': {str(e)}"
        }), 404

@inventory_bp.route("/expiring", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Obtener elementos próximos a vencer',
    'description': '''
Obtiene una lista de todos los elementos del inventario que están próximos a vencer según el número de días especificado.

### Funcionalidades:
- **Filtro por días**: Elementos que vencen en X días (por defecto 3 días)
- **Alertas tempranas**: Identificar alimentos antes de que se desperdicien
- **Priorización**: Lista organizada por urgencia de consumo
- **Información completa**: Incluye cantidad, ubicación y días restantes

### Casos de Uso:
- Planificar recetas con ingredientes próximos a vencer
- Alertas de vencimiento para el usuario
- Reducir desperdicio alimentario
- Priorizar consumo por fecha de vencimiento

### Algoritmo de Filtrado:
- Calcula días restantes hasta vencimiento
- Filtra elementos dentro del rango especificado
- Ordena por proximidad al vencimiento
- Incluye elementos ya vencidos (días negativos)
    ''',
    'parameters': [
        {
            'name': 'days',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 3,
            'description': 'Número de días para filtrar elementos próximos a vencer',
            'example': 7
        }
    ],
    'responses': {
        200: {
            'description': 'Lista de elementos próximos a vencer obtenida exitosamente',
            'examples': {
                'application/json': {
                    "expiring_items": [
                        {
                            "type": "ingredient",
                            "name": "Tomates cherry",
                            "quantity": 500,
                            "unit": "gr",
                            "storage_type": "refrigerador",
                            "expiration_date": "2024-01-18T00:00:00Z",
                            "days_until_expiration": 2,
                            "added_at": "2024-01-15T10:00:00Z",
                            "urgency_level": "high",
                            "tips": "Usar para ensalada o cocinar pronto"
                        },
                        {
                            "type": "ingredient", 
                            "name": "Queso manchego",
                            "quantity": 200,
                            "unit": "gr",
                            "storage_type": "refrigerador",
                            "expiration_date": "2024-01-20T00:00:00Z",
                            "days_until_expiration": 4,
                            "added_at": "2024-01-15T10:00:00Z",
                            "urgency_level": "medium",
                            "tips": "Mantener bien envuelto en refrigerador"
                        }
                    ],
                    "within_days": 7,
                    "count": 2,
                    "urgency_breakdown": {
                        "expired": 0,
                        "urgent": 1,
                        "soon": 1,
                        "moderate": 0
                    },
                    "recommendations": [
                        "Usa los tomates cherry en los próximos 2 días",
                        "Considera hacer recetas que usen varios ingredientes próximos a vencer"
                    ]
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
def get_expiring_items():
    user_uid = get_jwt_identity()
    within_days = request.args.get('days', 3, type=int)
    
    use_case = make_get_expiring_soon_use_case(db)
    expiring_items = use_case.execute(user_uid, within_days)

    return jsonify({
        "expiring_items": expiring_items,
        "within_days": within_days,
        "count": len(expiring_items)
    }), 200

@inventory_bp.route("/ingredients/from-recognition", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Agregar ingredientes desde reconocimiento IA con enriquecimiento automático',
    'description': '''
Agrega ingredientes al inventario directamente desde el resultado de reconocimiento de IA con enriquecimiento automático de datos.

### Características Avanzadas:
- **Integración directa**: Acepta estructura completa del response de reconocimiento
- **Enriquecimiento IA**: Genera automáticamente datos adicionales con inteligencia artificial
- **Procesamiento paralelo**: Enriquece múltiples ingredientes simultáneamente
- **Datos completos**: Combina reconocimiento + análisis ambiental + consejos de consumo
- **Fallback inteligente**: Imágenes por defecto si no están disponibles

### Datos Generados Automáticamente:
- **Impacto ambiental**: Huella de carbono, uso de agua, mensajes de sostenibilidad
- **Consejos de consumo**: Recomendaciones óptimas de preparación y consumo
- **Consejos pre-consumo**: Verificaciones de calidad y seguridad alimentaria
- **Ideas de utilización**: Sugerencias creativas de uso y recetas

### Estructura de Entrada:
Debe contener el campo `ingredients` con la estructura completa del reconocimiento:
- Datos básicos: name, quantity, type_unit, storage_type, expiration_time, time_unit, tips
- Datos opcionales: image_path, description
- Validación automática de campos requeridos

### Procesamiento:
1. **Validación**: Verifica estructura y campos requeridos
2. **Enriquecimiento**: Genera datos adicionales con IA en paralelo
3. **Almacenamiento**: Guarda ingredientes con datos completos
4. **Respuesta**: Confirma agregado con metadatos de enriquecimiento

### Casos de Uso:
- Flujo automático después de reconocimiento de imágenes
- Importación masiva de ingredientes con IA
- Migración desde sistemas de reconocimiento externos
- Agregado inteligente con mínima intervención del usuario
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
                        'description': 'Array de ingredientes desde reconocimiento con estructura completa',
                        'items': {
                            'type': 'object',
                            'required': ['name', 'quantity', 'type_unit', 'storage_type', 'expiration_time', 'time_unit', 'tips'],
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Nombre del ingrediente reconocido',
                                    'example': 'Tomates cherry'
                                },
                                'quantity': {
                                    'type': 'number',
                                    'description': 'Cantidad estimada por reconocimiento',
                                    'example': 400
                                },
                                'type_unit': {
                                    'type': 'string',
                                    'description': 'Unidad de medida detectada',
                                    'example': 'gr'
                                },
                                'storage_type': {
                                    'type': 'string',
                                    'description': 'Tipo de almacenamiento recomendado',
                                    'example': 'refrigerador'
                                },
                                'expiration_time': {
                                    'type': 'integer',
                                    'description': 'Tiempo estimado hasta vencimiento',
                                    'example': 7
                                },
                                'time_unit': {
                                    'type': 'string',
                                    'description': 'Unidad de tiempo para vencimiento',
                                    'example': 'days'
                                },
                                'tips': {
                                    'type': 'string',
                                    'description': 'Tips básicos de conservación',
                                    'example': 'Mantener refrigerados para mayor duración'
                                },
                                'image_path': {
                                    'type': 'string',
                                    'description': 'URL de imagen del reconocimiento (opcional)',
                                    'example': 'https://storage.googleapis.com/bucket/recognized_tomatoes.jpg'
                                },
                                'description': {
                                    'type': 'string',
                                    'description': 'Descripción adicional del reconocimiento (opcional)',
                                    'example': 'Tomates cherry frescos de color rojo intenso'
                                }
                            }
                        },
                        'example': [
                            {
                                'name': 'Tomates cherry',
                                'quantity': 400,
                                'type_unit': 'gr',
                                'storage_type': 'refrigerador',
                                'expiration_time': 7,
                                'time_unit': 'days',
                                'tips': 'Mantener refrigerados para mayor duración',
                                'image_path': 'https://storage.googleapis.com/bucket/tomatoes_recognition.jpg',
                                'description': 'Tomates cherry frescos detectados por IA'
                            },
                            {
                                'name': 'Lechuga romana',
                                'quantity': 1,
                                'type_unit': 'unidades',
                                'storage_type': 'refrigerador',
                                'expiration_time': 5,
                                'time_unit': 'days',
                                'tips': 'Mantener en cajón de verduras con humedad',
                                'image_path': 'https://storage.googleapis.com/bucket/lettuce_recognition.jpg',
                                'description': 'Lechuga romana fresca identificada'
                            }
                        ]
                    }
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Ingredientes agregados exitosamente con enriquecimiento IA',
            'examples': {
                'application/json': {
                    "message": "Ingredientes agregados exitosamente desde reconocimiento con datos enriquecidos",
                    "ingredients_count": 2,
                    "source": "recognition",
                    "enhanced_data": [
                        "environmental_impact",
                        "consumption_advice", 
                        "before_consumption_advice",
                        "utilization_ideas"
                    ],
                    "processing_summary": {
                        "total_ingredients": 2,
                        "enrichment_success_rate": 1.0,
                        "ai_processing_time": 4.7,
                        "fallback_images_applied": 0,
                        "parallel_processing": True
                    },
                    "ingredients_added": [
                        {
                            "name": "Tomates cherry",
                            "quantity": 400,
                            "unit": "gr",
                            "enriched_with": [
                                "environmental_impact",
                                "consumption_advice",
                                "before_consumption_advice",
                                "utilization_ideas"
                            ],
                            "ai_confidence": 0.94
                        },
                        {
                            "name": "Lechuga romana",
                            "quantity": 1,
                            "unit": "unidades",
                            "enriched_with": [
                                "environmental_impact",
                                "consumption_advice",
                                "before_consumption_advice",
                                "utilization_ideas"
                            ],
                            "ai_confidence": 0.89
                        }
                    ],
                    "enrichment_details": {
                        "environmental_analysis": "completed",
                        "consumption_advice_generated": "completed",
                        "utilization_ideas_created": "completed",
                        "safety_recommendations_added": "completed"
                    }
                }
            }
        },
        400: {
            'description': 'Estructura de datos inválida o campos faltantes',
            'examples': {
                'application/json': {
                    'error': 'Se requiere el campo "ingredients" con la estructura de reconocimiento',
                    'details': {
                        'missing_field': 'ingredients',
                        'expected_structure': 'Array de objetos con campos requeridos del reconocimiento'
                    }
                }
            }
        },
        400: {
            'description': 'Ingrediente con campos faltantes',
            'examples': {
                'application/json': {
                    'error': 'Ingrediente 1 (Tomates cherry) carece de campos requeridos: ["expiration_time", "time_unit"]',
                    'required_fields': [
                        'name',
                        'quantity', 
                        'type_unit',
                        'storage_type',
                        'expiration_time',
                        'time_unit',
                        'tips'
                    ],
                    'ingredient_index': 1,
                    'ingredient_name': 'Tomates cherry'
                }
            }
        },
        422: {
            'description': 'Error en enriquecimiento con IA',
            'examples': {
                'application/json': {
                    'error': 'Partial AI enrichment failure',
                    'details': 'Algunos ingredientes se agregaron con datos básicos debido a errores de IA',
                    'ingredients_added': 1,
                    'ingredients_with_ai_errors': 1,
                    'fallback_applied': True
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno del servidor durante el procesamiento'
        }
    }
})
def add_ingredients_from_recognition():
    """
    🌱 Endpoint específico para agregar ingredientes directamente desde el response de reconocimiento.
    Genera automáticamente:
    - Impacto ambiental (CO2, agua, sostenibilidad)
    - Consejos de consumo
    - Consejos antes de consumir
    """
    user_uid = get_jwt_identity()
    json_data = request.get_json()
    
    print(f"📥 [INVENTORY FROM RECOGNITION ENHANCED] User: {user_uid}")
    print(f"📥 [INVENTORY FROM RECOGNITION ENHANCED] Request data keys: {list(json_data.keys()) if json_data else 'None'}")
    print(f"📥 [INVENTORY FROM RECOGNITION ENHANCED] Request data size: {len(str(json_data)) if json_data else 0} characters")
    
    # Log específico para ingredients
    if json_data and "ingredients" in json_data:
        ingredients = json_data["ingredients"]
        print(f"📥 [INVENTORY FROM RECOGNITION ENHANCED] Ingredients array length: {len(ingredients)}")
        for i, ing in enumerate(ingredients[:3]):  # Solo los primeros 3 para no saturar
            print(f"📥 [INVENTORY FROM RECOGNITION ENHANCED] Ingredient {i+1} keys: {list(ing.keys())}")
            print(f"📥 [INVENTORY FROM RECOGNITION ENHANCED] Ingredient {i+1} name: {ing.get('name', 'MISSING')}")
            print(f"📥 [INVENTORY FROM RECOGNITION ENHANCED] Ingredient {i+1} has image_path: {'image_path' in ing}")
        if len(ingredients) > 3:
            print(f"📥 [INVENTORY FROM RECOGNITION ENHANCED] ... and {len(ingredients) - 3} more ingredients")
    else:
        print(f"📥 [INVENTORY FROM RECOGNITION ENHANCED] No 'ingredients' field in request data")
    
    # Validar que tenga la estructura del response de reconocimiento
    if not json_data or "ingredients" not in json_data:
        print(f"❌ [INVENTORY FROM RECOGNITION ENHANCED] Missing 'ingredients' field")
        return jsonify({"error": "Se requiere el campo 'ingredients' con la estructura de reconocimiento"}), 400
    
    ingredients_data = json_data["ingredients"]
    
    # Validar que cada ingrediente tenga los campos necesarios
    required_fields = ["name", "quantity", "type_unit", "storage_type", "expiration_time", "time_unit", "tips"]
    for i, ingredient in enumerate(ingredients_data):
        missing_fields = [field for field in required_fields if field not in ingredient]
        if missing_fields:
            print(f"❌ [INVENTORY FROM RECOGNITION ENHANCED] Ingredient {i+1} missing fields: {missing_fields}")
            return jsonify({
                "error": f"Ingrediente {i+1} ({ingredient.get('name', 'unknown')}) carece de campos requeridos: {missing_fields}"
            }), 400
        
        # 🔍 LOG DETALLADO DEL IMAGE_PATH
        print(f"🔍 [IMAGE_PATH DEBUG] Ingredient {i+1}: {ingredient['name']}")
        print(f"🔍 [IMAGE_PATH DEBUG]   - Has 'image_path' key: {'image_path' in ingredient}")
        if 'image_path' in ingredient:
            image_path = ingredient['image_path']
            print(f"🔍 [IMAGE_PATH DEBUG]   - image_path value: '{image_path}'")
            print(f"🔍 [IMAGE_PATH DEBUG]   - image_path length: {len(image_path) if image_path else 0}")
            print(f"🔍 [IMAGE_PATH DEBUG]   - image_path is empty: {not image_path or image_path.strip() == ''}")
        else:
            print(f"🔍 [IMAGE_PATH DEBUG]   - image_path key missing")
        
        # Mejorar la lógica del fallback para ser más específica
        if "image_path" not in ingredient or not ingredient.get("image_path") or ingredient.get("image_path").strip() == "":
            print(f"⚠️ [INVENTORY FROM RECOGNITION ENHANCED] Adding fallback image_path for: {ingredient['name']}")
            print(f"⚠️ [INVENTORY FROM RECOGNITION ENHANCED] Reason: image_path is missing or empty")
            ingredient["image_path"] = "https://via.placeholder.com/150x150/cccccc/666666?text=No+Image"
        else:
            print(f"✅ [INVENTORY FROM RECOGNITION ENHANCED] Using existing image_path for: {ingredient['name']}")
            print(f"✅ [INVENTORY FROM RECOGNITION ENHANCED] Image path: {ingredient['image_path'][:100]}..." if len(ingredient['image_path']) > 100 else f"✅ [INVENTORY FROM RECOGNITION ENHANCED] Image path: {ingredient['image_path']}")
    
    print(f"🥬 [INVENTORY FROM RECOGNITION ENHANCED] Processing {len(ingredients_data)} ingredients from recognition")
    
    for i, ingredient in enumerate(ingredients_data):
        print(f"   • Ingredient {i+1}: {ingredient.get('name')} - {ingredient.get('quantity')} {ingredient.get('type_unit')}")
        print(f"     └─ Has image_path: {'✅' if ingredient.get('image_path') else '❌'}")

    try:
        # 🌱 NUEVA FUNCIONALIDAD: Generar datos enriquecidos automáticamente
        print(f"🌱 [ENHANCED ENRICHMENT] Generating enhanced data for {len(ingredients_data)} ingredients...")
        
        from src.application.factories.recognition_usecase_factory import make_ai_service
        ai_service = make_ai_service()
        
        # Enriquecer con impacto ambiental, consejos de consumo y consejos antes de consumir
        _enrich_ingredients_with_enhanced_data(ingredients_data, ai_service)
        
        # Usar el use case con AI habilitado para el enriquecimiento adicional
        use_case = make_add_ingredients_to_inventory_use_case(db)
        use_case.execute(user_uid=user_uid, ingredients_data=ingredients_data)
        
        print(f"✅ [INVENTORY FROM RECOGNITION ENHANCED] Successfully added {len(ingredients_data)} enhanced ingredients for user {user_uid}")
        return jsonify({
            "message": "Ingredientes agregados exitosamente desde reconocimiento con datos enriquecidos",
            "ingredients_count": len(ingredients_data),
            "source": "recognition",
            "enhanced_data": [
                "environmental_impact",
                "consumption_advice", 
                "before_consumption_advice",
                "utilization_ideas"
            ]
        }), 201
        
    except Exception as e:
        print(f"🚨 [INVENTORY FROM RECOGNITION ENHANCED] Error adding enhanced ingredients: {str(e)}")
        raise e

def _enrich_ingredients_with_enhanced_data(ingredients_data: list[dict], ai_service):
    """
    🌱 Enriquece los ingredientes con datos adicionales:
    - Impacto ambiental (CO2, agua, sostenibilidad)
    - Consejos de consumo
    - Consejos antes de consumir
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    print(f"🌱 [ENHANCED ENRICHMENT] Starting enhanced data generation for {len(ingredients_data)} ingredients")
    
    def enrich_single_ingredient(ingredient_data):
        ingredient_name = ingredient_data["name"]
        ingredient_description = ingredient_data.get("description", "")
        
        print(f"   🌱 [ENHANCED] Processing: {ingredient_name}")
        
        try:
            # 1. Generar impacto ambiental
            environmental_impact = ai_service.analyze_environmental_impact(ingredient_name)
            
            # 2. Generar consejos de consumo (incluye before_consumption_advice)
            consumption_data = ai_service.generate_consumption_advice(ingredient_name, ingredient_description)
            
            # 3. Generar ideas de utilización (ya existía)
            utilization_ideas = ai_service.generate_utilization_ideas(ingredient_name, ingredient_description)
            
            print(f"   ✅ [ENHANCED] Successfully enriched: {ingredient_name}")
            
            return {
                "name": ingredient_name,
                "environmental_impact": environmental_impact,
                "consumption_advice": consumption_data.get("consumption_advice", {}),
                "before_consumption_advice": consumption_data.get("before_consumption_advice", {}),
                "utilization_ideas": utilization_ideas
            }
            
        except Exception as e:
            print(f"   ⚠️ [ENHANCED] Error enriching {ingredient_name}: {str(e)}")
            # Datos por defecto en caso de error
            return {
                "name": ingredient_name,
                "environmental_impact": {
                    "carbon_footprint": {"value": 0.5, "unit": "kg", "description": "CO2 estimado"},
                    "water_footprint": {"value": 100, "unit": "l", "description": "agua estimada"},
                    "sustainability_message": "Consume de manera responsable y evita el desperdicio."
                },
                "consumption_advice": {
                    "optimal_consumption": "Consume fresco para aprovechar al máximo sus nutrientes.",
                    "preparation_tips": "Lava bien antes de consumir y mantén refrigerado.",
                    "nutritional_benefits": "Rico en vitaminas y minerales esenciales.",
                    "recommended_portions": "Consume en porciones moderadas."
                },
                "before_consumption_advice": {
                    "quality_check": "Verifica que esté fresco y sin signos de deterioro.",
                    "safety_tips": "Lava con agua corriente antes de consumir.",
                    "preparation_notes": "Consume preferiblemente en los próximos días.",
                    "special_considerations": "Mantener en condiciones adecuadas de almacenamiento."
                },
                "utilization_ideas": [
                    {
                        "title": "Consume fresco",
                        "description": "Utiliza el ingrediente lo antes posible para aprovechar sus nutrientes.",
                        "type": "conservación"
                    }
                ]
            }
    
    # Generar datos enriquecidos en paralelo
    enriched_results = {}
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_ingredient = {
            executor.submit(enrich_single_ingredient, ingredient): ingredient["name"] 
            for ingredient in ingredients_data
        }
        
        for future in as_completed(future_to_ingredient):
            try:
                result = future.result()
                enriched_results[result["name"]] = result
            except Exception as e:
                ingredient_name = future_to_ingredient[future]
                print(f"   🚨 [ENHANCED] Error in thread for {ingredient_name}: {str(e)}")
    
    # Aplicar los datos enriquecidos a cada ingrediente
    for ingredient in ingredients_data:
        ingredient_name = ingredient["name"]
        if ingredient_name in enriched_results:
            enriched_data = enriched_results[ingredient_name]
            ingredient["environmental_impact"] = enriched_data["environmental_impact"]
            ingredient["consumption_advice"] = enriched_data["consumption_advice"] 
            ingredient["before_consumption_advice"] = enriched_data["before_consumption_advice"]
            ingredient["utilization_ideas"] = enriched_data["utilization_ideas"]
            print(f"   💚 [ENHANCED] Added all enhanced data to {ingredient_name}")
    
    print(f"🎯 [ENHANCED ENRICHMENT] Completed enhanced enrichment for all {len(ingredients_data)} ingredients!")

@inventory_bp.route("/simple", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Obtener inventario simplificado sin análisis IA',
    'description': '''
Obtiene el inventario básico del usuario sin procesamiento adicional de IA, optimizado para respuestas rápidas.

### Características:
- **Respuesta rápida**: Sin procesamiento IA adicional
- **Datos básicos**: Solo información almacenada por el usuario
- **Optimizado**: Para aplicaciones que requieren velocidad
- **Ligero**: Menor uso de recursos y ancho de banda
- **Confiable**: Sin dependencia de servicios externos de IA

### Diferencias vs Inventario Completo:
- **Simple**: Solo datos del usuario + tips básicos
- **Completo**: Datos + análisis IA + impacto ambiental + sugerencias
- **Velocidad**: ~10x más rápido que el completo
- **Uso de datos**: Menor consumo de ancho de banda

### Casos de Uso:
- Listados rápidos para móviles
- Verificación de disponibilidad de ingredientes
- Interfaces que priorizan velocidad
- Aplicaciones con conectividad limitada
- Operaciones CRUD básicas de inventario
    ''',
    'responses': {
        200: {
            'description': 'Inventario simple obtenido exitosamente',
            'examples': {
                'application/json': {
                    "ingredients": [
                        {
                            "name": "Tomates cherry",
                            "quantity": 500,
                            "type_unit": "gr",
                            "storage_type": "refrigerador",
                            "expiration_date": "2024-01-25T00:00:00Z",
                            "expiration_time": 8,
                            "time_unit": "Días",
                            "added_at": "2024-01-17T10:00:00Z",
                            "tips": "Mantener refrigerados para mayor frescura"
                        },
                        {
                            "name": "Queso manchego", 
                            "quantity": 250,
                            "type_unit": "gr",
                            "storage_type": "refrigerador",
                            "expiration_date": "2024-02-15T00:00:00Z",
                            "expiration_time": 29,
                            "time_unit": "Días",
                            "added_at": "2024-01-16T15:30:00Z",
                            "tips": "Envolver en papel encerado para mantener textura"
                        }
                    ],
                    "food_items": [],
                    "total_ingredients": 2,
                    "response_type": "simple",
                    "processing_time": 0.05
                }
            }
        },
        404: {
            'description': 'Inventario vacío',
            'examples': {
                'application/json': {
                    'message': 'No items found in inventory',
                    'ingredients': [],
                    'food_items': [],
                    'total_ingredients': 0
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
def get_inventory_simple():
    """
    Retorna el inventario en formato plano similar al response de reconocimiento.
    Útil para compatibilidad con interfaces que esperan formato de reconocimiento.
    """
    user_uid = get_jwt_identity()
    
    print(f"📤 [INVENTORY SIMPLE GET] Fetching simple inventory for user: {user_uid}")
    
    try:
        use_case = make_get_inventory_content_use_case(db)
        inventory = use_case.execute(user_uid)

        if not inventory:
            print(f"❌ [INVENTORY SIMPLE GET] No inventory found for user: {user_uid}")
            return jsonify({"message": "Inventario no encontrado"}), 404

        print(f"📊 [INVENTORY SIMPLE GET] Found inventory with {len(inventory.ingredients)} ingredient types")
        
        # Convertir a formato plano (como reconocimiento)
        simple_ingredients = []
        total_items = 0
        
        for name, ingredient in inventory.ingredients.items():
            # Para cada stack, crear un "ingrediente" separado
            for stack in ingredient.stacks:
                # Calcular días restantes hasta vencimiento
                from datetime import datetime
                days_to_expire = (stack.expiration_date - datetime.now()).days
                
                simple_ingredient = {
                    "name": ingredient.name,
                    "quantity": stack.quantity,
                    "type_unit": ingredient.type_unit,
                    "storage_type": ingredient.storage_type,
                    "expiration_time": max(days_to_expire, 0),  # No negativos
                    "time_unit": "Días",
                    "tips": ingredient.tips,
                    "image_path": ingredient.image_path,
                    # Campos adicionales para tracking
                    "added_at": stack.added_at.isoformat(),
                    "expiration_date": stack.expiration_date.isoformat(),
                    "is_expired": days_to_expire < 0
                }
                simple_ingredients.append(simple_ingredient)
                total_items += 1
                
                print(f"   • {name}: {stack.quantity} {ingredient.type_unit}, expires in {days_to_expire} days")

        result = {
            "ingredients": simple_ingredients,
            "total_items": total_items,
            "format": "recognition_compatible"
        }
        
        print(f"✅ [INVENTORY SIMPLE GET] Successfully returned {total_items} ingredient stacks in simple format")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"🚨 [INVENTORY SIMPLE GET] Error fetching simple inventory: {str(e)}")
        raise e

# ===============================================================================
# 🔧 NUEVOS ENDPOINTS PARA ACTUALIZACIÓN SIMPLE DE CANTIDADES
# ===============================================================================

@inventory_bp.route("/ingredients/<ingredient_name>/<added_at>/quantity", methods=["PATCH"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Actualizar cantidad de ingrediente específico',
    'description': '''
Actualiza únicamente la cantidad de un stack específico de ingrediente, manteniendo todos los demás datos intactos.

### Funcionalidades:
- **Actualización precisa**: Modifica solo la cantidad del stack específico
- **Preservación de datos**: Mantiene fecha de vencimiento, tips y otros metadatos
- **Validación**: Verifica que la nueva cantidad sea válida (>0)
- **Identificación única**: Usa nombre del ingrediente + timestamp de agregado
- **Atomicidad**: Operación completamente exitosa o completamente fallida

### Casos de Uso:
- Corregir errores de cantidad al agregar ingredientes
- Ajustar cantidades después de mediciones más precisas
- Reducir cantidad por consumo parcial medido
- Actualizar inventario después de verificación física
- Sincronizar con sistemas externos de inventario

### Identificación del Stack:
- **ingredient_name**: Nombre exacto como aparece en el inventario
- **added_at**: Timestamp exacto de cuando se agregó el stack (ISO format)
- Ambos parámetros deben coincidir exactamente con un stack existente
    ''',
    'parameters': [
        {
            'name': 'ingredient_name',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Nombre exacto del ingrediente',
            'example': 'Tomates cherry'
        },
        {
            'name': 'added_at',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Timestamp de cuando se agregó el stack (ISO format)',
            'example': '2024-01-15T10:00:00Z'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['quantity'],
                'properties': {
                    'quantity': {
                        'type': 'number',
                        'description': 'Nueva cantidad para el stack',
                        'example': 750,
                        'minimum': 0.01
                    }
                },
                'example': {
                    'quantity': 750
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Cantidad actualizada exitosamente',
            'examples': {
                'application/json': {
                    "message": "Cantidad de ingrediente actualizada exitosamente",
                    "ingredient_update": {
                        "ingredient_name": "Tomates cherry",
                        "stack_identifier": {
                            "added_at": "2024-01-15T10:00:00Z",
                            "original_quantity": 500,
                            "new_quantity": 750
                        },
                        "quantity_change": {
                            "difference": 250,
                            "change_type": "increase",
                            "percentage_change": 50.0
                        },
                        "stack_details": {
                            "type_unit": "gr",
                            "storage_type": "refrigerador",
                            "expiration_date": "2024-01-20T00:00:00Z",
                            "days_until_expiration": 4,
                            "tips": "Mantener refrigerados para mayor frescura"
                        },
                        "updated_at": "2024-01-16T14:30:00Z"
                    },
                    "inventory_impact": {
                        "total_ingredient_quantity": 1250,
                        "total_stacks_for_ingredient": 2,
                        "average_expiration_days": 6
                    }
                }
            }
        },
        400: {
            'description': 'Datos de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid quantity',
                    'details': 'La cantidad debe ser un número positivo mayor a 0'
                }
            }
        },
        404: {
            'description': 'Stack de ingrediente no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Ingredient stack not found',
                    'details': 'No se encontró un stack con el nombre y timestamp especificados'
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
def update_ingredient_quantity(ingredient_name, added_at):
    """
    Actualiza únicamente la cantidad de un stack específico de ingrediente.
    Mantiene todos los demás datos intactos.
    
    Body: { "quantity": 2.5 }
    """
    from urllib.parse import unquote
    
    # Decodificar el nombre del ingrediente URL-encoded
    ingredient_name = unquote(ingredient_name)
    
    # Restaurar caracteres especiales que fueron reemplazados para ser URL-safe
    ingredient_name = ingredient_name.replace('_SLASH_', '/')
    
    user_uid = get_jwt_identity()
    
    print(f"📦 [UPDATE INGREDIENT QUANTITY] ===== REQUEST DETAILS =====")
    print(f"📦 [UPDATE INGREDIENT QUANTITY] User: {user_uid}")
    print(f"📦 [UPDATE INGREDIENT QUANTITY] Ingredient: '{ingredient_name}'")
    print(f"📦 [UPDATE INGREDIENT QUANTITY] Added at: '{added_at}'")
    print(f"📦 [UPDATE INGREDIENT QUANTITY] Method: {request.method}")
    print(f"📦 [UPDATE INGREDIENT QUANTITY] URL: {request.url}")
    print(f"📦 [UPDATE INGREDIENT QUANTITY] Content-Type: {request.content_type}")

    # Validar parámetros de URL
    print(f"📦 [UPDATE INGREDIENT QUANTITY] ===== PARAMETER VALIDATION =====")
    if not ingredient_name or ingredient_name.strip() == '':
        print(f"❌ [UPDATE INGREDIENT QUANTITY] ERROR: Empty ingredient name")
        return jsonify({"error": "Ingredient name is required"}), 400
    
    if not added_at or added_at.strip() == '':
        print(f"❌ [UPDATE INGREDIENT QUANTITY] ERROR: Empty added_at timestamp")
        return jsonify({"error": "Added at timestamp is required"}), 400

    ingredient_name = ingredient_name.strip()
    added_at = added_at.strip()
    print(f"📦 [UPDATE INGREDIENT QUANTITY] Cleaned ingredient: '{ingredient_name}'")
    print(f"📦 [UPDATE INGREDIENT QUANTITY] Cleaned timestamp: '{added_at}'")

    # Obtener y validar JSON
    print(f"📦 [UPDATE INGREDIENT QUANTITY] ===== JSON VALIDATION =====")
    try:
        json_data = request.get_json()
        print(f"📦 [UPDATE INGREDIENT QUANTITY] Raw JSON: {json_data}")
        
        if not json_data:
            print(f"❌ [UPDATE INGREDIENT QUANTITY] ERROR: No JSON data provided")
            return jsonify({"error": "JSON data is required"}), 400
            
        print(f"📦 [UPDATE INGREDIENT QUANTITY] JSON keys: {list(json_data.keys())}")
    except Exception as json_error:
        print(f"❌ [UPDATE INGREDIENT QUANTITY] JSON parsing error: {str(json_error)}")
        return jsonify({"error": "Invalid JSON data"}), 400

    # Validar datos con schema
    schema = UpdateIngredientQuantitySchema()
    errors = schema.validate(json_data)
    if errors:
        print(f"❌ [UPDATE INGREDIENT QUANTITY] ===== SCHEMA VALIDATION ERRORS =====")
        print(f"❌ [UPDATE INGREDIENT QUANTITY] Validation errors: {errors}")
        print(f"❌ [UPDATE INGREDIENT QUANTITY] Failed fields: {list(errors.keys())}")
        raise InvalidRequestDataException(details=errors)
    
    print(f"✅ [UPDATE INGREDIENT QUANTITY] Schema validation passed")
    
    new_quantity = json_data["quantity"]
    print(f"📦 [UPDATE INGREDIENT QUANTITY] New quantity: {new_quantity}")
    print(f"📦 [UPDATE INGREDIENT QUANTITY] Quantity type: {type(new_quantity)}")

    print(f"📦 [UPDATE INGREDIENT QUANTITY] ===== STARTING USE CASE EXECUTION =====")
    try:
        print(f"📦 [UPDATE INGREDIENT QUANTITY] Creating use case...")
        use_case = make_update_ingredient_quantity_use_case(db)
        print(f"📦 [UPDATE INGREDIENT QUANTITY] Use case created successfully")

        print(f"📦 [UPDATE INGREDIENT QUANTITY] Calling use_case.execute()...")
        print(f"📦 [UPDATE INGREDIENT QUANTITY] Parameters:")
        print(f"📦 [UPDATE INGREDIENT QUANTITY]   - user_uid: '{user_uid}'")
        print(f"📦 [UPDATE INGREDIENT QUANTITY]   - ingredient_name: '{ingredient_name}'")
        print(f"📦 [UPDATE INGREDIENT QUANTITY]   - added_at: '{added_at}'")
        print(f"📦 [UPDATE INGREDIENT QUANTITY]   - new_quantity: {new_quantity}")
        
        result = use_case.execute(
            user_uid=user_uid,
            ingredient_name=ingredient_name,
            added_at=added_at,
            new_quantity=new_quantity
        )
        print(f"📦 [UPDATE INGREDIENT QUANTITY] Use case execution completed")

        print(f"📦 [UPDATE INGREDIENT QUANTITY] ===== RESULT ANALYSIS =====")
        print(f"📦 [UPDATE INGREDIENT QUANTITY] Result type: {type(result)}")
        print(f"📦 [UPDATE INGREDIENT QUANTITY] Result content: {result}")

        print(f"✅ [UPDATE INGREDIENT QUANTITY] ===== SUCCESS =====")
        print(f"✅ [UPDATE INGREDIENT QUANTITY] Successfully updated quantity for {ingredient_name}")
        print(f"✅ [UPDATE INGREDIENT QUANTITY] User: {user_uid}")
        print(f"✅ [UPDATE INGREDIENT QUANTITY] New quantity: {new_quantity}")
        print(f"✅ [UPDATE INGREDIENT QUANTITY] Returning 200 response")
        
        return jsonify({
            "message": "Cantidad de ingrediente actualizada exitosamente",
            "ingredient": ingredient_name,
            "new_quantity": new_quantity
        }), 200

    except ValueError as e:
        print(f"❌ [UPDATE INGREDIENT QUANTITY] ===== STACK NOT FOUND =====")
        print(f"❌ [UPDATE INGREDIENT QUANTITY] ValueError: {str(e)}")
        print(f"❌ [UPDATE INGREDIENT QUANTITY] User: {user_uid}")
        print(f"❌ [UPDATE INGREDIENT QUANTITY] Ingredient: '{ingredient_name}'")
        print(f"❌ [UPDATE INGREDIENT QUANTITY] Added at: '{added_at}'")
        print(f"❌ [UPDATE INGREDIENT QUANTITY] New quantity: {new_quantity}")
        print(f"❌ [UPDATE INGREDIENT QUANTITY] Returning 404 response")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"🚨 [UPDATE INGREDIENT QUANTITY] ===== ERROR DETAILS =====")
        print(f"🚨 [UPDATE INGREDIENT QUANTITY] Error type: {type(e).__name__}")
        print(f"🚨 [UPDATE INGREDIENT QUANTITY] Error message: {str(e)}")
        print(f"🚨 [UPDATE INGREDIENT QUANTITY] User: {user_uid}")
        print(f"🚨 [UPDATE INGREDIENT QUANTITY] Ingredient: '{ingredient_name}'")
        print(f"🚨 [UPDATE INGREDIENT QUANTITY] Added at: '{added_at}'")
        print(f"🚨 [UPDATE INGREDIENT QUANTITY] New quantity: {new_quantity}")
        
        # Log stack trace para debugging
        import traceback
        print(f"🚨 [UPDATE INGREDIENT QUANTITY] FULL STACK TRACE:")
        print(traceback.format_exc())
        print(f"🚨 [UPDATE INGREDIENT QUANTITY] ===== END ERROR =====")
        raise e

@inventory_bp.route("/foods/<food_name>/<added_at>/quantity", methods=["PATCH"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Actualizar cantidad de porciones de alimento preparado',
    'description': '''
Actualiza únicamente la cantidad de porciones de un alimento preparado específico, manteniendo todos los demás datos intactos.

### Funcionalidades:
- **Actualización precisa**: Modifica solo la cantidad de porciones del alimento específico
- **Preservación de datos**: Mantiene fecha de vencimiento, tips y otros metadatos
- **Validación**: Verifica que la nueva cantidad sea válida (>0)
- **Identificación única**: Usa nombre del alimento + timestamp de agregado
- **Atomicidad**: Operación completamente exitosa o completamente fallida

### Diferencias vs Ingredientes:
- **Alimentos**: Se mide en porciones/servings
- **Ingredientes**: Se mide en unidades de peso/volumen
- **Gestión**: Diferentes lógicas de conservación y vencimiento
- **Uso**: Alimentos listos para consumir vs ingredientes para cocinar

### Casos de Uso:
- Ajustar porciones después de consumo parcial
- Corregir errores de cantidad al agregar alimentos
- Actualizar después de redistribución de porciones
- Sincronizar con sistemas de meal prep
- Gestión de sobras y batch cooking

### Identificación del Alimento:
- **food_name**: Nombre exacto como aparece en el inventario
- **added_at**: Timestamp exacto de cuando se agregó el alimento (ISO format)
- Ambos parámetros deben coincidir exactamente con un alimento existente
    ''',
    'parameters': [
        {
            'name': 'food_name',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Nombre exacto del alimento preparado',
            'example': 'Lasaña de verduras'
        },
        {
            'name': 'added_at',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Timestamp de cuando se agregó el alimento (ISO format)',
            'example': '2024-01-17T19:30:00Z'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['serving_quantity'],
                'properties': {
                    'serving_quantity': {
                        'type': 'number',
                        'description': 'Nueva cantidad de porciones disponibles',
                        'example': 3,
                        'minimum': 0.5
                    }
                },
                'example': {
                    'serving_quantity': 3
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Cantidad de porciones actualizada exitosamente',
            'examples': {
                'application/json': {
                    "message": "Cantidad de comida actualizada exitosamente",
                    "food_update": {
                        "food_name": "Lasaña de verduras",
                        "food_identifier": {
                            "added_at": "2024-01-17T19:30:00Z",
                            "original_serving_quantity": 4,
                            "new_serving_quantity": 3
                        },
                        "quantity_change": {
                            "difference": -1,
                            "change_type": "decrease",
                            "percentage_change": -25.0
                        },
                        "food_details": {
                            "serving_unit": "porciones",
                            "storage_type": "refrigerador",
                            "expiration_date": "2024-01-19T00:00:00Z",
                            "days_until_expiration": 2,
                            "tips": "Recalentar en horno a 180°C por 15 minutos",
                            "main_ingredients": ["pasta", "espinacas", "ricotta", "salsa de tomate"],
                            "meal_type": "almuerzo_cena"
                        },
                        "updated_at": "2024-01-17T21:15:00Z"
                    },
                    "inventory_impact": {
                        "total_servings_available": 3,
                        "estimated_people_served": 3,
                        "remaining_meal_value": "alto"
                    },
                    "consumption_tracking": {
                        "servings_consumed": 1,
                        "consumption_rate": "normal",
                        "projected_finish_date": "2024-01-19T00:00:00Z"
                    }
                }
            }
        },
        400: {
            'description': 'Datos de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid serving quantity',
                    'details': 'La cantidad de porciones debe ser un número positivo mayor a 0.5'
                }
            }
        },
        404: {
            'description': 'Alimento preparado no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Food item not found',
                    'details': 'No se encontró un alimento con el nombre y timestamp especificados'
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
def update_food_quantity(food_name, added_at):
    """
    Actualiza únicamente la cantidad de porciones de un food item específico.
    Mantiene todos los demás datos intactos.
    
    Body: { "serving_quantity": 3 }
    """
    from urllib.parse import unquote
    
    # Decodificar el nombre del food URL-encoded
    food_name = unquote(food_name)
    
    # Restaurar caracteres especiales que fueron reemplazados para ser URL-safe
    food_name = food_name.replace('_SLASH_', '/')
    
    user_uid = get_jwt_identity()
    schema = UpdateFoodQuantitySchema()
    json_data = request.get_json()

    print(f"🍽️ [UPDATE FOOD QUANTITY] User: {user_uid}")
    print(f"   └─ Food: {food_name}")
    print(f"   └─ Added at: {added_at}")
    print(f"   └─ Request data: {json_data}")

    errors = schema.validate(json_data)
    if errors:
        print(f"❌ [UPDATE FOOD QUANTITY] Validation errors: {errors}")
        raise InvalidRequestDataException(details=errors)

    try:
        use_case = make_update_food_quantity_use_case(db)
        use_case.execute(
            user_uid=user_uid,
            food_name=food_name,
            added_at=added_at,
            new_quantity=json_data["serving_quantity"]
        )

        print(f"✅ [UPDATE FOOD QUANTITY] Successfully updated quantity for {food_name}")
        return jsonify({
            "message": "Cantidad de comida actualizada exitosamente",
            "food": food_name,
            "new_serving_quantity": json_data["serving_quantity"]
        }), 200

    except ValueError as e:
        print(f"❌ [UPDATE FOOD QUANTITY] Food item not found: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"🚨 [UPDATE FOOD QUANTITY] Unexpected error: {str(e)}")
        raise e

# ===============================================================================
# 🗑️ ENDPOINTS PARA ELIMINACIÓN DE ITEMS DEL INVENTARIO
# ===============================================================================

@inventory_bp.route("/ingredients/<ingredient_name>", methods=["DELETE"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Eliminar ingrediente completo del inventario',
    'description': '''
Elimina un ingrediente completo del inventario del usuario, incluyendo todos sus stacks asociados.

### Funcionalidades:
- **Eliminación completa**: Remueve todos los stacks del ingrediente especificado
- **Operación irreversible**: La eliminación es permanente y no se puede deshacer
- **Validación de permisos**: Solo el propietario puede eliminar sus ingredientes
- **Limpieza automática**: Elimina referencias asociadas y metadatos
- **Confirmación detallada**: Proporciona información de lo que se eliminó

### Comportamiento:
- Elimina todos los stacks del ingrediente independientemente de la cantidad
- Remueve imágenes asociadas si existen
- Actualiza contadores globales del inventario
- Registra la acción para auditoría

### Casos de Uso:
- Limpiar ingredientes que ya no se usan
- Corregir errores de agregado masivo
- Mantener inventario organizado y actualizado
- Eliminación por vencimiento o deterioro completo
- Reorganización del inventario

### ⚠️ Advertencia:
Esta operación es **IRREVERSIBLE**. Una vez eliminado, el ingrediente y todos sus stacks no se pueden recuperar.
    ''',
    'parameters': [
        {
            'name': 'ingredient_name',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Nombre exacto del ingrediente a eliminar completamente',
            'example': 'Tomates cherry'
        }
    ],
    'responses': {
        200: {
            'description': 'Ingrediente eliminado exitosamente',
            'examples': {
                'application/json': {
                    "message": "Ingrediente eliminado completamente del inventario",
                    "deletion_details": {
                        "ingredient_name": "Tomates cherry",
                        "stacks_deleted": 3,
                        "total_quantity_removed": 1500,
                        "unit": "gr",
                        "storage_type": "refrigerador",
                        "stacks_details": [
                            {
                                "quantity": 500,
                                "added_at": "2024-01-15T10:00:00Z",
                                "expiration_date": "2024-01-20T00:00:00Z"
                            },
                            {
                                "quantity": 400,
                                "added_at": "2024-01-14T15:30:00Z",
                                "expiration_date": "2024-01-19T00:00:00Z"
                            },
                            {
                                "quantity": 600,
                                "added_at": "2024-01-16T08:00:00Z",
                                "expiration_date": "2024-01-21T00:00:00Z"
                            }
                        ],
                        "deleted_at": "2024-01-16T14:45:00Z"
                    },
                    "inventory_impact": {
                        "remaining_ingredient_types": 15,
                        "total_inventory_reduction": {
                            "quantity": 1500,
                            "unit": "gr"
                        },
                        "storage_space_freed": "refrigerador"
                    },
                    "cleanup_actions": {
                        "images_removed": 1,
                        "references_updated": True,
                        "audit_log_created": True
                    }
                }
            }
        },
        404: {
            'description': 'Ingrediente no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Ingredient not found',
                    'details': 'No se encontró un ingrediente con el nombre especificado en el inventario del usuario'
                }
            }
        },
        400: {
            'description': 'Nombre de ingrediente inválido',
            'examples': {
                'application/json': {
                    'error': 'Invalid ingredient name',
                    'details': 'El nombre del ingrediente no puede estar vacío'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno del servidor durante la eliminación'
        }
    }
})
def delete_ingredient_complete(ingredient_name):
    """
    Elimina un ingrediente completo del inventario (todos sus stacks).
    
    URL: DELETE /api/inventory/ingredients/Tomate
    """
    user_uid = get_jwt_identity()

    print(f"🗑️ [DELETE INGREDIENT COMPLETE] ===== REQUEST DETAILS =====")
    print(f"🗑️ [DELETE INGREDIENT COMPLETE] User: {user_uid}")
    print(f"🗑️ [DELETE INGREDIENT COMPLETE] Ingredient name: '{ingredient_name}'")
    print(f"🗑️ [DELETE INGREDIENT COMPLETE] Method: {request.method}")
    print(f"🗑️ [DELETE INGREDIENT COMPLETE] URL: {request.url}")
    print(f"🗑️ [DELETE INGREDIENT COMPLETE] User-Agent: {request.headers.get('User-Agent', 'Unknown')}")

    # Validar parámetros
    print(f"🗑️ [DELETE INGREDIENT COMPLETE] ===== PARAMETER VALIDATION =====")
    if not ingredient_name or ingredient_name.strip() == '':
        print(f"❌ [DELETE INGREDIENT COMPLETE] ERROR: Empty or invalid ingredient name")
        return jsonify({"error": "Ingredient name is required"}), 400

    ingredient_name = ingredient_name.strip()
    print(f"🗑️ [DELETE INGREDIENT COMPLETE] Cleaned ingredient name: '{ingredient_name}'")
    print(f"🗑️ [DELETE INGREDIENT COMPLETE] Name length: {len(ingredient_name)} characters")

    print(f"🗑️ [DELETE INGREDIENT COMPLETE] ===== STARTING USE CASE EXECUTION =====")
    try:
        print(f"🗑️ [DELETE INGREDIENT COMPLETE] Creating use case...")
        use_case = make_delete_ingredient_complete_use_case(db)
        print(f"🗑️ [DELETE INGREDIENT COMPLETE] Use case created successfully")

        print(f"🗑️ [DELETE INGREDIENT COMPLETE] Calling use_case.execute()...")
        print(f"🗑️ [DELETE INGREDIENT COMPLETE] Parameters: user_uid='{user_uid}', ingredient_name='{ingredient_name}'")
        
        result = use_case.execute(user_uid=user_uid, ingredient_name=ingredient_name)
        print(f"🗑️ [DELETE INGREDIENT COMPLETE] Use case execution completed")

        print(f"🗑️ [DELETE INGREDIENT COMPLETE] ===== RESULT ANALYSIS =====")
        print(f"🗑️ [DELETE INGREDIENT COMPLETE] Result type: {type(result)}")
        print(f"🗑️ [DELETE INGREDIENT COMPLETE] Result content: {result}")

        print(f"✅ [DELETE INGREDIENT COMPLETE] ===== SUCCESS =====")
        print(f"✅ [DELETE INGREDIENT COMPLETE] Successfully deleted complete ingredient: {ingredient_name}")
        print(f"✅ [DELETE INGREDIENT COMPLETE] User: {user_uid}")
        print(f"✅ [DELETE INGREDIENT COMPLETE] Returning 200 response")
        
        return jsonify({
            "message": "Ingrediente eliminado completamente del inventario",
            "ingredient": ingredient_name,
            "deleted": "all_stacks"
        }), 200

    except ValueError as e:
        print(f"❌ [DELETE INGREDIENT COMPLETE] ===== INGREDIENT NOT FOUND =====")
        print(f"❌ [DELETE INGREDIENT COMPLETE] ValueError: {str(e)}")
        print(f"❌ [DELETE INGREDIENT COMPLETE] User: {user_uid}")
        print(f"❌ [DELETE INGREDIENT COMPLETE] Ingredient: '{ingredient_name}'")
        print(f"❌ [DELETE INGREDIENT COMPLETE] Returning 404 response")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"🚨 [DELETE INGREDIENT COMPLETE] ===== ERROR DETAILS =====")
        print(f"🚨 [DELETE INGREDIENT COMPLETE] Error type: {type(e).__name__}")
        print(f"🚨 [DELETE INGREDIENT COMPLETE] Error message: {str(e)}")
        print(f"🚨 [DELETE INGREDIENT COMPLETE] User: {user_uid}")
        print(f"🚨 [DELETE INGREDIENT COMPLETE] Ingredient: '{ingredient_name}'")
        
        # Log stack trace para debugging
        import traceback
        print(f"🚨 [DELETE INGREDIENT COMPLETE] FULL STACK TRACE:")
        print(traceback.format_exc())
        print(f"🚨 [DELETE INGREDIENT COMPLETE] ===== END ERROR =====")
        raise e



@inventory_bp.route("/foods/<food_name>/<added_at>", methods=["DELETE"])
@jwt_required()
def delete_food_item(food_name, added_at):
    """
    Elimina un food item específico del inventario.
    
    URL: DELETE /api/inventory/foods/Pasta con Tomate/2025-01-01T10:00:00Z
    """
    from urllib.parse import unquote
    
    # Decodificar el nombre del food URL-encoded
    food_name = unquote(food_name)
    
    # Restaurar caracteres especiales que fueron reemplazados para ser URL-safe
    food_name = food_name.replace('_SLASH_', '/')
    
    user_uid = get_jwt_identity()

    print(f"🗑️ [DELETE FOOD ITEM] User: {user_uid}")
    print(f"   └─ Food: {food_name}")
    print(f"   └─ Added at: {added_at}")

    try:
        use_case = make_delete_food_item_use_case(db)
        use_case.execute(user_uid, food_name, added_at)

        print(f"✅ [DELETE FOOD ITEM] Successfully deleted food item: {food_name}")
        return jsonify({
            "message": "Comida eliminada exitosamente del inventario",
            "food": food_name,
            "deleted_added_at": added_at
        }), 200

    except ValueError as e:
        print(f"❌ [DELETE FOOD ITEM] Food item not found: {str(e)}")
        return jsonify({"error": f"Food item not found for '{food_name}' added at '{added_at}'"}), 404
    except Exception as e:
        print(f"🚨 [DELETE FOOD ITEM] Unexpected error: {str(e)}")
        raise e


# ===============================================================================
# 🍽️ ENDPOINTS PARA MARCAR COMO CONSUMIDO
# ===============================================================================

@inventory_bp.route("/ingredients/<ingredient_name>/<added_at>/consume", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Marcar ingrediente como consumido',
    'description': '''
Marca un stack específico de ingrediente como consumido, reduciendo su cantidad o eliminándolo completamente.

### Funcionalidades:
- **Consumo parcial**: Reduce cantidad específica del stack
- **Consumo total**: Elimina el stack completo si no se especifica cantidad
- **Tracking**: Registra el consumo para estadísticas
- **Validación**: Verifica que la cantidad consumida no exceda la disponible

### Comportamiento:
- Si `consumed_quantity` no se especifica: consume todo el stack
- Si `consumed_quantity` < cantidad total: reduce la cantidad
- Si `consumed_quantity` = cantidad total: elimina el stack
- Registra fecha y hora del consumo para tracking

### Casos de Uso:
- Marcar ingredientes usados en recetas
- Registrar consumo directo de alimentos
- Tracking de desperdicio vs. consumo real
- Mantener inventario actualizado automáticamente
    ''',
    'parameters': [
        {
            'name': 'ingredient_name',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Nombre exacto del ingrediente a consumir',
            'example': 'Tomates cherry'
        },
        {
            'name': 'added_at',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Timestamp de cuando se agregó el stack (ISO format)',
            'example': '2024-01-15T10:00:00Z'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': False,
            'schema': {
                'type': 'object',
                'properties': {
                    'consumed_quantity': {
                        'type': 'number',
                        'description': 'Cantidad específica a consumir (opcional - por defecto consume todo)',
                        'example': 250,
                        'minimum': 0.01
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Ingrediente marcado como consumido exitosamente',
            'examples': {
                'application/json': {
                    "message": "Ingrediente marcado como consumido exitosamente",
                    "consumption_details": {
                        "ingredient_name": "Tomates cherry",
                        "consumed_quantity": 250,
                        "unit": "gr",
                        "consumed_at": "2024-01-16T14:30:00Z",
                        "remaining_quantity": 250,
                        "stack_status": "partially_consumed",
                        "original_quantity": 500
                    },
                    "inventory_impact": {
                        "stack_removed": False,
                        "quantity_updated": True,
                        "new_expiration_date": "2024-01-20T00:00:00Z"
                    },
                    "sustainability_impact": {
                        "food_waste_avoided": True,
                        "consumption_efficiency": 0.5
                    }
                }
            }
        },
        400: {
            'description': 'Datos de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid consumed quantity',
                    'details': 'La cantidad consumida no puede ser mayor a la disponible'
                }
            }
        },
        404: {
            'description': 'Ingrediente o stack no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Ingredient stack not found',
                    'details': 'No se encontró el stack específico del ingrediente'
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
def mark_ingredient_stack_consumed(ingredient_name, added_at):
    """
    Marca un stack específico de ingrediente como consumido.
    Puede ser consumo parcial o total.
    
    URL: POST /api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume
    Body: { "consumed_quantity": 2.5 } (opcional - por defecto consume todo)
    """
    from urllib.parse import unquote
    
    # Decodificar el nombre del ingrediente URL-encoded
    ingredient_name = unquote(ingredient_name)
    
    # Restaurar caracteres especiales que fueron reemplazados para ser URL-safe
    ingredient_name = ingredient_name.replace('_SLASH_', '/')
    
    user_uid = get_jwt_identity()

    print(f"🍽️ [MARK INGREDIENT CONSUMED] ===== REQUEST DETAILS =====")
    print(f"🍽️ [MARK INGREDIENT CONSUMED] User: {user_uid}")
    print(f"🍽️ [MARK INGREDIENT CONSUMED] Ingredient: '{ingredient_name}'")
    print(f"🍽️ [MARK INGREDIENT CONSUMED] Added at: '{added_at}'")
    print(f"🍽️ [MARK INGREDIENT CONSUMED] Method: {request.method}")
    print(f"🍽️ [MARK INGREDIENT CONSUMED] URL: {request.url}")
    print(f"🍽️ [MARK INGREDIENT CONSUMED] Content-Type: {request.content_type}")

    # Validar parámetros de URL
    print(f"🍽️ [MARK INGREDIENT CONSUMED] ===== PARAMETER VALIDATION =====")
    if not ingredient_name or ingredient_name.strip() == '':
        print(f"❌ [MARK INGREDIENT CONSUMED] ERROR: Empty ingredient name")
        return jsonify({"error": "Ingredient name is required"}), 400
    
    if not added_at or added_at.strip() == '':
        print(f"❌ [MARK INGREDIENT CONSUMED] ERROR: Empty added_at timestamp")
        return jsonify({"error": "Added at timestamp is required"}), 400

    ingredient_name = ingredient_name.strip()
    added_at = added_at.strip()
    print(f"🍽️ [MARK INGREDIENT CONSUMED] Cleaned ingredient: '{ingredient_name}'")
    print(f"🍽️ [MARK INGREDIENT CONSUMED] Cleaned timestamp: '{added_at}'")

    # Obtener y validar JSON
    print(f"🍽️ [MARK INGREDIENT CONSUMED] ===== JSON VALIDATION =====")
    try:
        json_data = request.get_json() or {}
        print(f"🍽️ [MARK INGREDIENT CONSUMED] Raw JSON: {json_data}")
        print(f"🍽️ [MARK INGREDIENT CONSUMED] JSON keys: {list(json_data.keys())}")
    except Exception as json_error:
        print(f"❌ [MARK INGREDIENT CONSUMED] JSON parsing error: {str(json_error)}")
        return jsonify({"error": "Invalid JSON data"}), 400

    # Validar datos de entrada con schema
    schema = MarkIngredientConsumedSchema()
    try:
        validated_data = schema.load(json_data)
        print(f"🍽️ [MARK INGREDIENT CONSUMED] Schema validation passed")
        print(f"🍽️ [MARK INGREDIENT CONSUMED] Validated data: {validated_data}")
    except Exception as e:
        print(f"❌ [MARK INGREDIENT CONSUMED] Schema validation error: {str(e)}")
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400

    consumed_quantity = validated_data.get('consumed_quantity')
    print(f"🍽️ [MARK INGREDIENT CONSUMED] Consumed quantity: {consumed_quantity or 'ALL (complete stack)'}")

    print(f"🍽️ [MARK INGREDIENT CONSUMED] ===== STARTING USE CASE EXECUTION =====")
    try:
        print(f"🍽️ [MARK INGREDIENT CONSUMED] Creating use case...")
        use_case = make_mark_ingredient_stack_consumed_use_case(db)
        print(f"🍽️ [MARK INGREDIENT CONSUMED] Use case created successfully")

        print(f"🍽️ [MARK INGREDIENT CONSUMED] Calling use_case.execute()...")
        print(f"🍽️ [MARK INGREDIENT CONSUMED] Parameters:")
        print(f"🍽️ [MARK INGREDIENT CONSUMED]   - user_uid: '{user_uid}'")
        print(f"🍽️ [MARK INGREDIENT CONSUMED]   - ingredient_name: '{ingredient_name}'")
        print(f"🍽️ [MARK INGREDIENT CONSUMED]   - added_at: '{added_at}'")
        print(f"🍽️ [MARK INGREDIENT CONSUMED]   - consumed_quantity: {consumed_quantity}")
        
        result = use_case.execute(
            user_uid=user_uid,
            ingredient_name=ingredient_name,
            added_at=added_at,
            consumed_quantity=consumed_quantity
        )
        print(f"🍽️ [MARK INGREDIENT CONSUMED] Use case execution completed")

        print(f"🍽️ [MARK INGREDIENT CONSUMED] ===== RESULT ANALYSIS =====")
        print(f"🍽️ [MARK INGREDIENT CONSUMED] Result type: {type(result)}")
        print(f"🍽️ [MARK INGREDIENT CONSUMED] Result content: {result}")
        
        if isinstance(result, dict):
            action = result.get('action', 'unknown')
            print(f"🍽️ [MARK INGREDIENT CONSUMED] Action performed: {action}")
        
        print(f"🍽️ [MARK INGREDIENT CONSUMED] ===== SERIALIZATION =====")
        # Serializar response
        response_schema = ConsumedResponseSchema()
        response_data = response_schema.dump(result)
        print(f"🍽️ [MARK INGREDIENT CONSUMED] Serialization completed")
        print(f"🍽️ [MARK INGREDIENT CONSUMED] Response data: {response_data}")

        print(f"✅ [MARK INGREDIENT CONSUMED] ===== SUCCESS =====")
        print(f"✅ [MARK INGREDIENT CONSUMED] Success: {result.get('action', 'completed')}")
        print(f"✅ [MARK INGREDIENT CONSUMED] User: {user_uid}")
        print(f"✅ [MARK INGREDIENT CONSUMED] Ingredient: '{ingredient_name}'")
        print(f"✅ [MARK INGREDIENT CONSUMED] Returning 200 response")
        
        return jsonify(response_data), 200

    except ValueError as e:
        print(f"❌ [MARK INGREDIENT CONSUMED] ===== VALIDATION ERROR =====")
        print(f"❌ [MARK INGREDIENT CONSUMED] ValueError: {str(e)}")
        print(f"❌ [MARK INGREDIENT CONSUMED] User: {user_uid}")
        print(f"❌ [MARK INGREDIENT CONSUMED] Ingredient: '{ingredient_name}'")
        print(f"❌ [MARK INGREDIENT CONSUMED] Added at: '{added_at}'")
        print(f"❌ [MARK INGREDIENT CONSUMED] Returning 404 response")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"🚨 [MARK INGREDIENT CONSUMED] ===== ERROR DETAILS =====")
        print(f"🚨 [MARK INGREDIENT CONSUMED] Error type: {type(e).__name__}")
        print(f"🚨 [MARK INGREDIENT CONSUMED] Error message: {str(e)}")
        print(f"🚨 [MARK INGREDIENT CONSUMED] User: {user_uid}")
        print(f"🚨 [MARK INGREDIENT CONSUMED] Ingredient: '{ingredient_name}'")
        print(f"🚨 [MARK INGREDIENT CONSUMED] Added at: '{added_at}'")
        
        # Log stack trace para debugging
        import traceback
        print(f"🚨 [MARK INGREDIENT CONSUMED] FULL STACK TRACE:")
        print(traceback.format_exc())
        print(f"🚨 [MARK INGREDIENT CONSUMED] ===== END ERROR =====")
        raise e


@inventory_bp.route("/foods/<food_name>/<added_at>/consume", methods=["POST"])
@jwt_required()
def mark_food_item_consumed(food_name, added_at):
    """
    Marca un food item como consumido.
    Puede ser consumo parcial o total.
    
    URL: POST /api/inventory/foods/Pasta con Tomate/2025-01-01T10:00:00Z/consume
    Body: { "consumed_portions": 1.5 } (opcional - por defecto consume todo)
    """
    from urllib.parse import unquote
    
    # Decodificar el nombre del food URL-encoded
    food_name = unquote(food_name)
    
    # Restaurar caracteres especiales que fueron reemplazados para ser URL-safe
    food_name = food_name.replace('_SLASH_', '/')
    
    user_uid = get_jwt_identity()

    print(f"🍽️ [MARK FOOD CONSUMED] User: {user_uid}")
    print(f"   └─ Food: {food_name}")
    print(f"   └─ Added at: {added_at}")

    # Validar datos de entrada
    schema = MarkFoodConsumedSchema()
    try:
        validated_data = schema.load(request.get_json() or {})
    except Exception as e:
        print(f"❌ [MARK FOOD CONSUMED] Validation error: {str(e)}")
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400

    consumed_portions = validated_data.get('consumed_portions')
    print(f"   └─ Consumed portions: {consumed_portions or 'ALL'}")

    try:
        use_case = make_mark_food_item_consumed_use_case(db)
        result = use_case.execute(
            user_uid=user_uid,
            food_name=food_name,
            added_at=added_at,
            consumed_portions=consumed_portions
        )

        print(f"✅ [MARK FOOD CONSUMED] Success: {result['action']}")
        
        # Serializar response
        response_schema = ConsumedResponseSchema()
        response_data = response_schema.dump(result)

        return jsonify(response_data), 200

    except ValueError as e:
        print(f"❌ [MARK FOOD CONSUMED] Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"🚨 [MARK FOOD CONSUMED] Unexpected error: {str(e)}")
        raise e

# ===============================================================================
# 🔍 ENDPOINTS PARA OBTENER DETALLES INDIVIDUALES DE ITEMS
# ===============================================================================

@inventory_bp.route("/ingredients/<ingredient_name>/detail", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Obtener detalles completos de un ingrediente específico',
    'description': '''
Obtiene información detallada de todos los stacks de un ingrediente específico en el inventario.

### Información Detallada Incluida:
- **Todos los stacks**: Cada lote agregado por separado
- **Análisis temporal**: Historial de agregado y consumo
- **Predicciones de vencimiento**: Estimaciones precisas por stack
- **Recomendaciones de uso**: Orden sugerido de consumo
- **Estadísticas de uso**: Frecuencia y patrones de consumo

### Datos por Stack:
- Cantidad actual y original
- Fecha de agregado y vencimiento
- Condiciones de almacenamiento
- Tips específicos de conservación
- Estado de frescura actual
- Historial de modificaciones

### Casos de Uso:
- Gestión detallada de ingredientes específicos
- Planificación de uso por orden de vencimiento
- Análisis de patrones de consumo
- Optimización de compras futuras
- Control de calidad y frescura
    ''',
    'parameters': [
        {
            'name': 'ingredient_name',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Nombre exacto del ingrediente',
            'example': 'Tomates cherry'
        }
    ],
    'responses': {
        200: {
            'description': 'Detalles del ingrediente obtenidos exitosamente',
            'examples': {
                'application/json': {
                    "ingredient_name": "Tomates cherry",
                    "stacks": [
                        {
                            "stack_id": "stack_001",
                            "quantity": 300,
                            "original_quantity": 500,
                            "type_unit": "gr",
                            "storage_type": "refrigerador",
                            "expiration_date": "2024-01-22T00:00:00Z",
                            "expiration_time": 5,
                            "time_unit": "Días",
                            "added_at": "2024-01-17T10:00:00Z",
                            "tips": "Mantener refrigerados para mayor frescura",
                            "freshness_status": "muy_fresco",
                            "consumption_history": [
                                {
                                    "consumed_quantity": 200,
                                    "consumed_at": "2024-01-18T19:00:00Z",
                                    "reason": "Preparación ensalada"
                                }
                            ],
                            "quality_indicators": {
                                "color": "rojo intenso",
                                "firmness": "firme",
                                "estimated_shelf_life": 5
                            }
                        },
                        {
                            "stack_id": "stack_002",
                            "quantity": 450,
                            "original_quantity": 450,
                            "type_unit": "gr",
                            "storage_type": "refrigerador",
                            "expiration_date": "2024-01-25T00:00:00Z",
                            "expiration_time": 8,
                            "time_unit": "Días",
                            "added_at": "2024-01-15T14:00:00Z",
                            "tips": "Mantener refrigerados para mayor frescura",
                            "freshness_status": "fresco",
                            "consumption_history": [],
                            "quality_indicators": {
                                "color": "rojo brillante",
                                "firmness": "muy firme",
                                "estimated_shelf_life": 8
                            }
                        }
                    ],
                    "summary": {
                        "total_quantity": 750,
                        "total_stacks": 2,
                        "total_original_quantity": 950,
                        "total_consumed": 200,
                        "consumption_rate": 21.05,
                        "next_expiration": "2024-01-22T00:00:00Z",
                        "days_until_next_expiration": 5,
                        "average_freshness": "muy_fresco",
                        "storage_recommendation": "refrigerador"
                    },
                    "usage_recommendations": {
                        "consumption_order": [
                            {
                                "stack_id": "stack_001",
                                "priority": 1,
                                "reason": "Vence primero (5 días)",
                                "suggested_use": "Ensalada fresca o consumo directo"
                            },
                            {
                                "stack_id": "stack_002", 
                                "priority": 2,
                                "reason": "Vence después (8 días)",
                                "suggested_use": "Reservar para cocción o salsas"
                            }
                        ],
                        "recipe_suggestions": [
                            "Ensalada caprese",
                            "Bruschetta italiana",
                            "Salsa de tomate fresca"
                        ]
                    },
                    "analytics": {
                        "consumption_pattern": "regular",
                        "average_days_to_consume": 3.2,
                        "waste_risk": "bajo",
                        "purchase_frequency": "semanal"
                    }
                }
            }
        },
        404: {
            'description': 'Ingrediente no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Ingredient not found',
                    'details': 'No se encontró un ingrediente con ese nombre en el inventario'
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
def get_ingredient_detail(ingredient_name):
    """
    Obtiene todos los detalles de un ingrediente específico del inventario,
    incluyendo todos sus stacks, imagen, impacto ambiental, ideas de aprovechamiento y más.
    
    URL: GET /api/inventory/ingredients/Tomate/detail
    """
    user_uid = get_jwt_identity()

    print(f"🔍 [GET INGREDIENT DETAIL] User: {user_uid}")
    print(f"   └─ Ingredient: {ingredient_name}")

    try:
        use_case = make_get_ingredient_detail_use_case(db)
        ingredient_detail = use_case.execute(user_uid=user_uid, ingredient_name=ingredient_name)

        print(f"✅ [GET INGREDIENT DETAIL] Successfully fetched details for: {ingredient_name}")
        return jsonify(ingredient_detail), 200

    except ValueError as e:
        print(f"❌ [GET INGREDIENT DETAIL] Ingredient not found: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"🚨 [GET INGREDIENT DETAIL] Unexpected error: {str(e)}")
        return jsonify({"error": f"Error fetching ingredient details: {str(e)}"}), 500

@inventory_bp.route("/foods/<food_name>/<added_at>/detail", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Obtener detalles completos de un alimento preparado específico',
    'description': '''
Obtiene información detallada de un alimento preparado específico en el inventario.

### Información Detallada Incluida:
- **Datos de preparación**: Fecha, método, tiempo de cocción
- **Análisis nutricional**: Calorías, macronutrientes, micronutrientes
- **Ingredientes identificados**: Lista de componentes principales
- **Recomendaciones de consumo**: Orden de consumo, porciones sugeridas
- **Tips de conservación**: Almacenamiento óptimo y recalentamiento

### Datos Específicos de Alimentos:
- Información de porciones y servings
- Fecha de preparación vs fecha de vencimiento
- Métodos de recalentamiento recomendados
- Análisis de frescura y calidad
- Compatibilidad con congelación
- Historial de consumo parcial

### Diferencias vs Detalles de Ingredientes:
- **Ingredientes**: Productos crudos con múltiples stacks
- **Alimentos**: Comidas preparadas con porciones
- **Gestión**: Diferentes métricas (porciones vs cantidad)
- **Vencimiento**: Tiempos más cortos para alimentos preparados

### Casos de Uso:
- Gestión detallada de meal prep
- Control de calidad de alimentos preparados
- Planificación de consumo de sobras
- Análisis nutricional de comidas caseras
- Optimización de almacenamiento de alimentos
    ''',
    'parameters': [
        {
            'name': 'food_name',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Nombre exacto del alimento preparado',
            'example': 'Lasaña de verduras'
        },
        {
            'name': 'added_at',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Timestamp exacto de cuando se agregó el alimento (formato ISO)',
            'example': '2024-01-17T19:30:00Z'
        }
    ],
    'responses': {
        200: {
            'description': 'Detalles del alimento obtenidos exitosamente',
            'examples': {
                'application/json': {
                    "food_details": {
                        "name": "Lasaña de verduras",
                        "serving_quantity": 4,
                        "original_serving_quantity": 6,
                        "serving_unit": "porciones",
                        "storage_type": "refrigerador",
                        "expiration_date": "2024-01-19T00:00:00Z",
                        "expiration_time": 2,
                        "time_unit": "Días",
                        "added_at": "2024-01-17T19:30:00Z",
                        "preparation_date": "2024-01-17T19:30:00Z",
                        "tips": "Recalentar en horno a 180°C por 15 minutos. Cubrir con papel aluminio para evitar que se seque.",
                        "freshness_status": "muy_fresco"
                    },
                    "nutritional_analysis": {
                        "per_serving": {
                            "calories": 320,
                            "protein": 18.5,
                            "carbohydrates": 35.0,
                            "fat": 12.0,
                            "fiber": 8.2,
                            "sodium": 450
                        },
                        "total_remaining": {
                            "calories": 1280,
                            "protein": 74.0,
                            "carbohydrates": 140.0,
                            "fat": 48.0
                        },
                        "nutritional_highlights": [
                            "Alto en proteínas vegetales",
                            "Rica en fibra",
                            "Fuente de calcio por el queso ricotta",
                            "Vitaminas A y K por las espinacas"
                        ]
                    },
                    "ingredient_breakdown": {
                        "main_ingredients": [
                            {
                                "name": "pasta para lasaña",
                                "category": "carbohidratos",
                                "estimated_quantity": "300gr"
                            },
                            {
                                "name": "espinacas",
                                "category": "verduras",
                                "estimated_quantity": "400gr"
                            },
                            {
                                "name": "ricotta",
                                "category": "lácteos",
                                "estimated_quantity": "250gr"
                            },
                            {
                                "name": "salsa de tomate",
                                "category": "salsas",
                                "estimated_quantity": "200ml"
                            }
                        ],
                        "secondary_ingredients": [
                            "mozzarella",
                            "parmesano",
                            "ajo",
                            "cebolla",
                            "aceite de oliva"
                        ]
                    },
                    "consumption_history": [
                        {
                            "consumed_servings": 2,
                            "consumed_at": "2024-01-18T13:00:00Z",
                            "occasion": "almuerzo",
                            "rating": 4.5,
                            "notes": "Excelente sabor, se recalentó perfectamente"
                        }
                    ],
                    "storage_recommendations": {
                        "current_storage": "refrigerador",
                        "optimal_temperature": "2-4°C",
                        "max_refrigerator_days": 3,
                        "freezer_compatible": True,
                        "max_freezer_months": 2,
                        "reheating_methods": [
                            {
                                "method": "horno",
                                "temperature": "180°C",
                                "time": "15-20 minutos",
                                "notes": "Cubrir con papel aluminio, destaparlo los últimos 5 minutos"
                            },
                            {
                                "method": "microondas",
                                "power": "70%",
                                "time": "2-3 minutos por porción",
                                "notes": "Añadir una cucharada de agua, cubrir con papel apto para microondas"
                            }
                        ]
                    },
                    "quality_indicators": {
                        "visual_appearance": "excelente",
                        "aroma": "fresco",
                        "texture_expected": "firme",
                        "color_preservation": "buena",
                        "overall_quality_score": 9.2
                    },
                    "usage_recommendations": {
                        "best_consumption_order": "Consumir en los próximos 2 días para máxima calidad",
                        "portion_suggestions": [
                            "1 porción como almuerzo principal",
                            "0.5 porción como acompañamiento",
                            "1.5 porciones para cena abundante"
                        ],
                        "pairing_suggestions": [
                            "Ensalada verde fresca",
                            "Pan de ajo",
                            "Vino tinto ligero"
                        ]
                    },
                    "meal_context": {
                        "meal_type": "almuerzo_cena",
                        "cuisine_type": "italiana",
                        "difficulty_level": "intermedio",
                        "preparation_time_original": "90 minutos",
                        "cooking_method": "horneado"
                    }
                }
            }
        },
        404: {
            'description': 'Alimento no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Food item not found',
                    'details': 'No se encontró un alimento con ese nombre y fecha en el inventario'
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
def get_food_detail(food_name, added_at):
    """
    Obtiene todos los detalles de un food item específico del inventario,
    incluyendo información nutricional, consejos de consumo, ideas de acompañamiento y más.
    
    URL: GET /api/inventory/foods/Pasta con Tomate/2025-01-01T10:00:00Z/detail
    """
    from urllib.parse import unquote
    
    # Decodificar el nombre del food URL-encoded
    food_name = unquote(food_name)
    
    # Restaurar caracteres especiales que fueron reemplazados para ser URL-safe
    food_name = food_name.replace('_SLASH_', '/')
    
    user_uid = get_jwt_identity()

    print(f"🍽️ [GET FOOD DETAIL] User: {user_uid}")
    print(f"   └─ Food: {food_name}")
    print(f"   └─ Added at: {added_at}")

    try:
        use_case = make_get_food_detail_use_case(db)
        food_detail = use_case.execute(user_uid=user_uid, food_name=food_name, added_at=added_at)

        print(f"✅ [GET FOOD DETAIL] Successfully fetched details for: {food_name}")
        return jsonify(food_detail), 200

    except ValueError as e:
        print(f"❌ [GET FOOD DETAIL] Food item not found: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"🚨 [GET FOOD DETAIL] Unexpected error: {str(e)}")
        return jsonify({"error": f"Error fetching food details: {str(e)}"}), 500

# ===============================================================================
# 📋 ENDPOINTS PARA LISTAR TIPOS ESPECÍFICOS DE ITEMS
# ===============================================================================

@inventory_bp.route("/ingredients/list", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Obtener lista específica de ingredientes',
    'description': '''
Obtiene únicamente la lista de ingredientes del inventario, excluyendo alimentos preparados.

### Características:
- **Filtrado específico**: Solo ingredientes, no alimentos preparados
- **Datos completos**: Información detallada de cada ingrediente
- **Organización por stacks**: Agrupa ingredientes por fecha de agregado
- **Información de vencimiento**: Prioriza por proximidad de vencimiento
- **Metadatos incluidos**: Tips, cantidades, almacenamiento

### Información por Ingrediente:
- Nombre y cantidad actual
- Tipo de unidad y almacenamiento
- Fecha de vencimiento y días restantes
- Tips de conservación específicos
- Fecha de agregado al inventario
- Estado de frescura estimado

### Casos de Uso:
- Verificar ingredientes disponibles para recetas
- Planificación de compras de ingredientes
- Gestión específica de ingredientes frescos
- Análisis de rotación de ingredientes
- Interfaces especializadas en ingredientes crudos
    ''',
    'responses': {
        200: {
            'description': 'Lista de ingredientes obtenida exitosamente',
            'examples': {
                'application/json': {
                    "ingredients": [
                        {
                            "name": "Tomates cherry",
                            "stacks": [
                                {
                                    "quantity": 300,
                                    "type_unit": "gr",
                                    "storage_type": "refrigerador",
                                    "expiration_date": "2024-01-22T00:00:00Z",
                                    "expiration_time": 5,
                                    "time_unit": "Días",
                                    "added_at": "2024-01-17T10:00:00Z",
                                    "tips": "Mantener refrigerados para mayor frescura",
                                    "freshness_status": "muy_fresco"
                                },
                                {
                                    "quantity": 200,
                                    "type_unit": "gr", 
                                    "storage_type": "refrigerador",
                                    "expiration_date": "2024-01-25T00:00:00Z",
                                    "expiration_time": 8,
                                    "time_unit": "Días",
                                    "added_at": "2024-01-15T14:00:00Z",
                                    "tips": "Mantener refrigerados para mayor frescura",
                                    "freshness_status": "fresco"
                                }
                            ],
                            "total_quantity": 500,
                            "total_stacks": 2,
                            "next_expiration": "2024-01-22T00:00:00Z",
                            "days_until_next_expiration": 5
                        },
                        {
                            "name": "Queso manchego",
                            "stacks": [
                                {
                                    "quantity": 250,
                                    "type_unit": "gr",
                                    "storage_type": "refrigerador", 
                                    "expiration_date": "2024-02-15T00:00:00Z",
                                    "expiration_time": 29,
                                    "time_unit": "Días",
                                    "added_at": "2024-01-16T15:30:00Z",
                                    "tips": "Envolver en papel encerado para mantener textura",
                                    "freshness_status": "excelente"
                                }
                            ],
                            "total_quantity": 250,
                            "total_stacks": 1,
                            "next_expiration": "2024-02-15T00:00:00Z",
                            "days_until_next_expiration": 29
                        }
                    ],
                    "summary": {
                        "total_ingredient_types": 2,
                        "total_stacks": 3,
                        "total_quantity_all": 750,
                        "expiring_soon_count": 0,
                        "excellent_condition_count": 2,
                        "next_expiration_ingredient": "Tomates cherry",
                        "next_expiration_date": "2024-01-22T00:00:00Z"
                    }
                }
            }
        },
        404: {
            'description': 'No se encontraron ingredientes',
            'examples': {
                'application/json': {
                    'message': 'No ingredients found in inventory',
                    'ingredients': [],
                    'summary': {
                        'total_ingredient_types': 0,
                        'total_stacks': 0
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
def get_ingredients_list():
    """
    Obtiene únicamente la lista de ingredientes del inventario del usuario.
    No incluye food items.
    
    URL: GET /api/inventory/ingredients/list
    """
    user_uid = get_jwt_identity()

    print(f"📋 [GET INGREDIENTS LIST] ===== REQUEST DETAILS =====")
    print(f"📋 [GET INGREDIENTS LIST] User: {user_uid}")
    print(f"📋 [GET INGREDIENTS LIST] Method: {request.method}")
    print(f"📋 [GET INGREDIENTS LIST] URL: {request.url}")
    print(f"📋 [GET INGREDIENTS LIST] User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    # Log query parameters if any
    if request.args:
        print(f"📋 [GET INGREDIENTS LIST] Query params: {dict(request.args)}")
    else:
        print(f"📋 [GET INGREDIENTS LIST] No query parameters")

    print(f"📋 [GET INGREDIENTS LIST] ===== STARTING USE CASE EXECUTION =====")
    try:
        print(f"📋 [GET INGREDIENTS LIST] Creating use case...")
        use_case = make_get_ingredients_list_use_case(db)
        print(f"📋 [GET INGREDIENTS LIST] Use case created successfully")
        
        print(f"📋 [GET INGREDIENTS LIST] Calling use_case.execute()...")
        ingredients_result = use_case.execute(user_uid=user_uid)
        print(f"📋 [GET INGREDIENTS LIST] Use case execution completed")
        
        print(f"📋 [GET INGREDIENTS LIST] ===== RESULT ANALYSIS =====")
        print(f"📋 [GET INGREDIENTS LIST] Result type: {type(ingredients_result)}")
        print(f"📋 [GET INGREDIENTS LIST] Result keys: {list(ingredients_result.keys()) if isinstance(ingredients_result, dict) else 'Not a dict'}")
        
        total_ingredients = ingredients_result.get('total_ingredients', 0)
        total_stacks = ingredients_result.get('total_stacks', 0)
        ingredients_list = ingredients_result.get('ingredients', [])
        
        print(f"📋 [GET INGREDIENTS LIST] Total ingredients: {total_ingredients}")
        print(f"📋 [GET INGREDIENTS LIST] Total stacks: {total_stacks}")
        print(f"📋 [GET INGREDIENTS LIST] Ingredients list length: {len(ingredients_list)}")
        
        # Log detalles de algunos ingredientes (máximo 5 para no saturar)
        for i, ingredient in enumerate(ingredients_list[:5]):
            print(f"📋 [GET INGREDIENTS LIST] Ingredient {i+1}: {ingredient.get('name', 'Unknown')} ({ingredient.get('stack_count', 0)} stacks)")
        
        if len(ingredients_list) > 5:
            print(f"📋 [GET INGREDIENTS LIST] ... and {len(ingredients_list) - 5} more ingredients")
        
        print(f"📋 [GET INGREDIENTS LIST] ===== SERIALIZATION =====")
        response_size = len(str(ingredients_result))
        print(f"📋 [GET INGREDIENTS LIST] Response size: ~{response_size} characters")
        
        print(f"✅ [GET INGREDIENTS LIST] ===== SUCCESS =====")
        print(f"✅ [GET INGREDIENTS LIST] Successfully fetched {total_ingredients} ingredients")
        print(f"✅ [GET INGREDIENTS LIST] Returning 200 response")
        return jsonify(ingredients_result), 200

    except Exception as e:
        print(f"🚨 [GET INGREDIENTS LIST] ===== ERROR DETAILS =====")
        print(f"🚨 [GET INGREDIENTS LIST] Error type: {type(e).__name__}")
        print(f"🚨 [GET INGREDIENTS LIST] Error message: {str(e)}")
        print(f"🚨 [GET INGREDIENTS LIST] User: {user_uid}")
        
        # Log stack trace para debugging
        import traceback
        print(f"🚨 [GET INGREDIENTS LIST] FULL STACK TRACE:")
        print(traceback.format_exc())
        print(f"🚨 [GET INGREDIENTS LIST] ===== END ERROR =====")
        
        return jsonify({"error": f"Error fetching ingredients list: {str(e)}"}), 500

@inventory_bp.route("/foods/list", methods=["GET"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Obtener lista específica de alimentos preparados',
    'description': '''
Obtiene únicamente la lista de alimentos preparados del inventario, excluyendo ingredientes crudos.

### Características:
- **Filtrado específico**: Solo alimentos preparados, no ingredientes crudos
- **Datos completos**: Información detallada de cada alimento
- **Información nutricional**: Calorías, porciones, ingredientes principales
- **Gestión de vencimiento**: Fechas de caducidad y frescura
- **Metadatos incluidos**: Tips de conservación y recalentamiento

### Información por Alimento:
- Nombre y descripción del plato
- Cantidad de porciones disponibles
- Fecha de preparación y vencimiento
- Ingredientes principales identificados
- Tips de conservación y recalentamiento
- Estado de frescura estimado

### Diferencias vs Lista de Ingredientes:
- **Ingredientes**: Productos crudos para cocinar
- **Alimentos**: Comidas ya preparadas listas para consumir
- **Gestión**: Diferentes tiempos de conservación y métodos
- **Uso**: Alimentos para consumo directo, ingredientes para cocinar

### Casos de Uso:
- Verificar comidas preparadas disponibles
- Planificación de menús con sobras
- Gestión de meal prep y batch cooking
- Control de alimentos preparados en cocinas comerciales
- Interfaces especializadas en comida lista
    ''',
    'responses': {
        200: {
            'description': 'Lista de alimentos preparados obtenida exitosamente',
            'examples': {
                'application/json': {
                    "foods": [
                        {
                            "name": "Lasaña de verduras",
                            "serving_quantity": 4,
                            "serving_unit": "porciones",
                            "storage_type": "refrigerador",
                            "expiration_date": "2024-01-19T00:00:00Z",
                            "expiration_time": 2,
                            "time_unit": "Días",
                            "added_at": "2024-01-17T19:30:00Z",
                            "preparation_date": "2024-01-17T19:30:00Z",
                            "tips": "Recalentar en horno a 180°C por 15 minutos. Cubrir con papel aluminio.",
                            "freshness_status": "muy_fresco",
                            "main_ingredients": [
                                "pasta",
                                "espinacas",
                                "ricotta",
                                "salsa de tomate"
                            ],
                            "nutritional_info": {
                                "calories_per_serving": 320,
                                "protein": "alto",
                                "carbs": "medio",
                                "fat": "medio"
                            },
                            "meal_type": "almuerzo_cena",
                            "cuisine_type": "italiana"
                        },
                        {
                            "name": "Sopa de lentejas",
                            "serving_quantity": 6,
                            "serving_unit": "porciones",
                            "storage_type": "refrigerador",
                            "expiration_date": "2024-01-20T00:00:00Z",
                            "expiration_time": 3,
                            "time_unit": "Días",
                            "added_at": "2024-01-17T14:00:00Z",
                            "preparation_date": "2024-01-17T14:00:00Z",
                            "tips": "Se puede congelar hasta 3 meses. Recalentar a fuego lento agregando un poco de agua si es necesario.",
                            "freshness_status": "fresco",
                            "main_ingredients": [
                                "lentejas",
                                "zanahoria",
                                "cebolla",
                                "apio"
                            ],
                            "nutritional_info": {
                                "calories_per_serving": 280,
                                "protein": "alto",
                                "carbs": "alto",
                                "fat": "bajo"
                            },
                            "meal_type": "almuerzo_cena",
                            "cuisine_type": "mediterránea"
                        }
                    ],
                    "summary": {
                        "total_food_items": 2,
                        "total_servings_available": 10,
                        "expiring_soon_count": 1,
                        "fresh_condition_count": 2,
                        "storage_distribution": {
                            "refrigerador": 2,
                            "congelador": 0,
                            "temperatura_ambiente": 0
                        },
                        "meal_type_distribution": {
                            "almuerzo_cena": 2,
                            "desayuno": 0,
                            "snack": 0
                        },
                        "next_expiration_food": "Lasaña de verduras",
                        "next_expiration_date": "2024-01-19T00:00:00Z"
                    }
                }
            }
        },
        404: {
            'description': 'No se encontraron alimentos preparados',
            'examples': {
                'application/json': {
                    'message': 'No prepared foods found in inventory',
                    'foods': [],
                    'summary': {
                        'total_food_items': 0,
                        "total_servings_available": 0
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
def get_foods_list():
    """
    Obtiene únicamente la lista de food items del inventario del usuario.
    No incluye ingredientes.
    
    URL: GET /api/inventory/foods/list
    """
    user_uid = get_jwt_identity()

    print(f"🍽️ [GET FOODS LIST] User: {user_uid}")

    try:
        use_case = make_get_foods_list_use_case(db)
        foods_result = use_case.execute(user_uid=user_uid)

        print(f"✅ [GET FOODS LIST] Successfully fetched {foods_result['total_foods']} food items")
        return jsonify(foods_result), 200

    except Exception as e:
        print(f"🚨 [GET FOODS LIST] Unexpected error: {str(e)}")
        return jsonify({"error": f"Error fetching foods list: {str(e)}"}), 500

# ===============================================================================
# 📤 ENDPOINT PARA UPLOAD DE IMÁGENES DEL INVENTARIO
# ===============================================================================

@inventory_bp.route("/upload_image", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Subir imagen específica del inventario',
    'description': '''
Sube una imagen específica para el inventario del usuario con organización automática por categorías.

### Tipos de Upload Soportados:
- **recognition**: Imágenes para reconocimiento automático
- **ingredient**: Fotos de ingredientes específicos
- **food**: Imágenes de alimentos preparados
- **inventory_general**: Fotos generales del inventario

### Organización Automática:
- **Estructura de carpetas**: `uploads/{user_uid}/{upload_type}/`
- **Nomenclatura inteligente**: Basada en contenido y timestamp
- **Compresión automática**: Optimización para almacenamiento
- **Metadatos**: Extracción automática de información relevante

### Validaciones Incluidas:
- Formatos soportados: JPG, PNG, WEBP, GIF
- Tamaño máximo: 10MB por imagen
- Resolución mínima: 200x200 pixels
- Validación de contenido alimentario

### Casos de Uso:
- Documentar ingredientes para referencia futura
- Crear base de datos visual del inventario
- Facilitar reconocimiento automático mejorado
- Compartir inventario con otros usuarios
- Backup visual de productos perecederos
    ''',
    'consumes': ['multipart/form-data'],
    'parameters': [
        {
            'name': 'image',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'Archivo de imagen (JPG, PNG, WEBP, GIF, máximo 10MB)'
        },
        {
            'name': 'upload_type',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'enum': ['recognition', 'ingredient', 'food', 'inventory_general'],
            'description': 'Tipo de uso de la imagen'
        },
        {
            'name': 'item_name',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'Nombre del item en la imagen (opcional para algunos tipos)',
            'example': 'Tomates cherry'
        },
        {
            'name': 'description',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'Descripción adicional de la imagen',
            'example': 'Estado fresco, recién comprados'
        }
    ],
    'responses': {
        201: {
            'description': 'Imagen subida exitosamente',
            'examples': {
                'application/json': {
                    "message": "Imagen subida exitosamente",
                    "upload_details": {
                        "image_id": "img_inv_123456789",
                        "original_filename": "tomates_cherry.jpg",
                        "upload_type": "ingredient",
                        "item_name": "Tomates cherry",
                        "file_size": 2457600,
                        "dimensions": {
                            "width": 1920,
                            "height": 1080
                        },
                        "format": "JPEG"
                    },
                    "storage_info": {
                        "storage_path": "uploads/user123/ingredient/img_inv_123456789.jpg",
                        "public_url": "https://storage.googleapis.com/bucket/uploads/user123/ingredient/img_inv_123456789.jpg",
                        "folder_structure": "uploads/{user_uid}/ingredient/",
                        "compression_applied": True,
                        "optimized_size": 1843200
                    },
                    "processing_results": {
                        "content_validation": "passed",
                        "food_content_detected": True,
                        "quality_score": 0.92,
                        "metadata_extracted": {
                            "camera_model": "iPhone 13",
                            "capture_date": "2024-01-17T10:30:00Z",
                            "location_data": "removed_for_privacy"
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Archivo inválido o parámetros faltantes',
            'examples': {
                'application/json': {
                    'error': 'Invalid file or parameters',
                    'details': {
                        'image': ['Archivo de imagen requerido'],
                        'upload_type': ['Tipo de upload requerido'],
                        'file_validation': 'Formato no soportado o archivo corrupto'
                    }
                }
            }
        },
        413: {
            'description': 'Archivo demasiado grande',
            'examples': {
                'application/json': {
                    'error': 'File too large',
                    'details': 'El archivo excede el límite de 10MB',
                    'max_size': '10MB',
                    'received_size': '15MB'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error en el servidor durante la subida'
        }
    }
})
def upload_inventory_image():
    """
    Sube una imagen específica para el inventario del usuario.
    Organiza las imágenes en carpetas específicas según el tipo de uso.
    
    Estructura de carpetas:
    - uploads/{user_uid}/recognitions/  - Imágenes para reconocimiento
    - uploads/{user_uid}/items/         - Imágenes de ingredientes y comidas manuales
    
    URL: POST /api/inventory/upload_image
    Form Data:
    - image: archivo de imagen (required)
    - upload_type: 'recognition', 'ingredient', 'food' (required)
    - item_name: nombre del item (optional, para algunos tipos)
    """
    user_uid = get_jwt_identity()
    
    print(f"📤 [UPLOAD INVENTORY IMAGE] ===== REQUEST DETAILS =====")
    print(f"📤 [UPLOAD INVENTORY IMAGE] User: {user_uid}")
    print(f"📤 [UPLOAD INVENTORY IMAGE] Method: {request.method}")
    print(f"📤 [UPLOAD INVENTORY IMAGE] URL: {request.url}")
    print(f"📤 [UPLOAD INVENTORY IMAGE] Content-Type: {request.content_type}")
    print(f"📤 [UPLOAD INVENTORY IMAGE] Content-Length: {request.content_length}")
    
    print(f"📤 [UPLOAD INVENTORY IMAGE] ===== FORM DATA ANALYSIS =====")
    # Analizar archivos
    if request.files:
        print(f"📤 [UPLOAD INVENTORY IMAGE] Files in request:")
        for key, file in request.files.items():
            print(f"📤 [UPLOAD INVENTORY IMAGE]   - {key}: {file.filename} (size: {file.content_length if hasattr(file, 'content_length') else 'unknown'})")
    else:
        print(f"📤 [UPLOAD INVENTORY IMAGE] No files in request")
    
    # Analizar form data
    if request.form:
        print(f"📤 [UPLOAD INVENTORY IMAGE] Form data:")
        for key, value in request.form.items():
            print(f"📤 [UPLOAD INVENTORY IMAGE]   - {key}: '{value}'")
    else:
        print(f"📤 [UPLOAD INVENTORY IMAGE] No form data")
    
    print(f"📤 [UPLOAD INVENTORY IMAGE] ===== DATA EXTRACTION =====")
    try:
        # Obtener datos del formulario
        image_file = request.files.get('image')
        upload_type = request.form.get('upload_type', '').strip()
        item_name = request.form.get('item_name', '').strip() or None
        
        print(f"📤 [UPLOAD INVENTORY IMAGE] Extracted data:")
        print(f"📤 [UPLOAD INVENTORY IMAGE]   - Upload type: '{upload_type}'")
        print(f"📤 [UPLOAD INVENTORY IMAGE]   - Item name: '{item_name or 'N/A'}'")
        print(f"📤 [UPLOAD INVENTORY IMAGE]   - Image file: {image_file.filename if image_file else 'None'}")
        
        if image_file:
            print(f"📤 [UPLOAD INVENTORY IMAGE]   - File size: {len(image_file.read())} bytes")
            image_file.seek(0)  # Reset file pointer
            print(f"📤 [UPLOAD INVENTORY IMAGE]   - File mimetype: {image_file.mimetype}")
            print(f"📤 [UPLOAD INVENTORY IMAGE]   - File content type: {image_file.content_type}")
        
    except Exception as extraction_error:
        print(f"❌ [UPLOAD INVENTORY IMAGE] Data extraction error: {str(extraction_error)}")
        return jsonify({"error": "Failed to extract form data"}), 400
    
    print(f"📤 [UPLOAD INVENTORY IMAGE] ===== VALIDATION =====")
    # Validaciones básicas
    if not image_file:
        print(f"❌ [UPLOAD INVENTORY IMAGE] ERROR: No image file provided")
        return jsonify({"error": "No image file provided"}), 400
    
    if not upload_type:
        print(f"❌ [UPLOAD INVENTORY IMAGE] ERROR: No upload_type provided")
        return jsonify({"error": "upload_type is required"}), 400
    
    valid_upload_types = ['recognition', 'ingredient', 'food']
    if upload_type not in valid_upload_types:
        print(f"❌ [UPLOAD INVENTORY IMAGE] ERROR: Invalid upload_type '{upload_type}'. Valid types: {valid_upload_types}")
        return jsonify({"error": f"Invalid upload_type. Must be one of: {valid_upload_types}"}), 400
    
    print(f"✅ [UPLOAD INVENTORY IMAGE] Validation passed")
    
    print(f"📤 [UPLOAD INVENTORY IMAGE] ===== STARTING USE CASE EXECUTION =====")
    try:
        print(f"📤 [UPLOAD INVENTORY IMAGE] Creating use case...")
        use_case = make_upload_inventory_image_use_case()
        print(f"📤 [UPLOAD INVENTORY IMAGE] Use case created successfully")
        
        print(f"📤 [UPLOAD INVENTORY IMAGE] Calling use_case.execute()...")
        print(f"📤 [UPLOAD INVENTORY IMAGE] Parameters:")
        print(f"📤 [UPLOAD INVENTORY IMAGE]   - user_uid: '{user_uid}'")
        print(f"📤 [UPLOAD INVENTORY IMAGE]   - upload_type: '{upload_type}'")
        print(f"📤 [UPLOAD INVENTORY IMAGE]   - item_name: '{item_name}'")
        print(f"📤 [UPLOAD INVENTORY IMAGE]   - file: {image_file.filename}")
        
        result = use_case.execute(
            file=image_file,
            upload_type=upload_type,
            user_uid=user_uid,
            item_name=item_name
        )
        print(f"📤 [UPLOAD INVENTORY IMAGE] Use case execution completed")
        
        print(f"📤 [UPLOAD INVENTORY IMAGE] ===== RESULT ANALYSIS =====")
        print(f"📤 [UPLOAD INVENTORY IMAGE] Result type: {type(result)}")
        print(f"📤 [UPLOAD INVENTORY IMAGE] Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict) and 'upload_info' in result:
            upload_info = result['upload_info']
            print(f"📤 [UPLOAD INVENTORY IMAGE] Upload info:")
            print(f"📤 [UPLOAD INVENTORY IMAGE]   - Folder: {upload_info.get('folder', 'unknown')}")
            print(f"📤 [UPLOAD INVENTORY IMAGE]   - Filename: {upload_info.get('filename', 'unknown')}")
            print(f"📤 [UPLOAD INVENTORY IMAGE]   - Path: {upload_info.get('path', 'unknown')}")
        
        print(f"✅ [UPLOAD INVENTORY IMAGE] ===== SUCCESS =====")
        print(f"✅ [UPLOAD INVENTORY IMAGE] Successfully uploaded image")
        print(f"✅ [UPLOAD INVENTORY IMAGE] User: {user_uid}")
        print(f"✅ [UPLOAD INVENTORY IMAGE] Type: {upload_type}")
        print(f"✅ [UPLOAD INVENTORY IMAGE] Item: {item_name or 'N/A'}")
        print(f"✅ [UPLOAD INVENTORY IMAGE] File: {image_file.filename}")
        if isinstance(result, dict) and 'upload_info' in result:
            print(f"✅ [UPLOAD INVENTORY IMAGE] Uploaded to: {result['upload_info'].get('folder', 'unknown')}")
        print(f"✅ [UPLOAD INVENTORY IMAGE] Returning 201 response")
        
        return jsonify(result), 201
        
    except ValueError as e:
        print(f"❌ [UPLOAD INVENTORY IMAGE] ===== VALIDATION ERROR =====")
        print(f"❌ [UPLOAD INVENTORY IMAGE] ValueError: {str(e)}")
        print(f"❌ [UPLOAD INVENTORY IMAGE] User: {user_uid}")
        print(f"❌ [UPLOAD INVENTORY IMAGE] Upload type: '{upload_type}'")
        print(f"❌ [UPLOAD INVENTORY IMAGE] Item name: '{item_name}'")
        print(f"❌ [UPLOAD INVENTORY IMAGE] File: {image_file.filename if image_file else 'None'}")
        print(f"❌ [UPLOAD INVENTORY IMAGE] Returning 400 response")
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        print(f"🚨 [UPLOAD INVENTORY IMAGE] ===== ERROR DETAILS =====")
        print(f"🚨 [UPLOAD INVENTORY IMAGE] Error type: {type(e).__name__}")
        print(f"🚨 [UPLOAD INVENTORY IMAGE] Error message: {str(e)}")
        print(f"🚨 [UPLOAD INVENTORY IMAGE] User: {user_uid}")
        print(f"🚨 [UPLOAD INVENTORY IMAGE] Upload type: '{upload_type}'")
        print(f"🚨 [UPLOAD INVENTORY IMAGE] Item name: '{item_name}'")
        print(f"🚨 [UPLOAD INVENTORY IMAGE] File: {image_file.filename if image_file else 'None'}")
        
        # Log stack trace para debugging
        import traceback
        print(f"🚨 [UPLOAD INVENTORY IMAGE] FULL STACK TRACE:")
        print(traceback.format_exc())
        print(f"🚨 [UPLOAD INVENTORY IMAGE] ===== END ERROR =====")
        
        return jsonify({
            "error": "Failed to upload inventory image",
            "details": str(e)
        }), 500

# ===============================================================================
# 🎯 ENDPOINT PARA AGREGAR ITEM AL INVENTARIO (UNIFICADO)
# ===============================================================================

@inventory_bp.route("/add_item", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Inventory'],
    'summary': 'Agregar item al inventario con generación IA',
    'description': '''
Agrega un item (ingrediente o comida) al inventario con datos básicos del usuario y completado automático con IA.

### Características Avanzadas:
- **Generación con IA**: Completa automáticamente datos faltantes usando inteligencia artificial
- **Flexibilidad de entrada**: Solo requiere datos básicos del usuario
- **Enriquecimiento automático**: Tips, fechas de vencimiento, categorías, etc.
- **Validación inteligente**: Verifica consistencia de datos con IA
- **Doble funcionalidad**: Soporta tanto ingredientes como alimentos preparados

### Datos Generados Automáticamente:
**Para Ingredientes:**
- Tips de almacenamiento y conservación
- Tiempo de vencimiento estimado basado en tipo y almacenamiento
- Categoría nutricional y propiedades
- Impacto ambiental y sostenibilidad
- Ideas de utilización y recetas sugeridas

**Para Alimentos:**
- Ingredientes principales estimados
- Información nutricional aproximada
- Categoría de comida y ocasión de consumo
- Tips de conservación y recalentamiento
- Análisis de frescura y vida útil

### Casos de Uso:
- Agregar items de forma rápida sin datos técnicos
- Captura desde aplicaciones móviles simplificadas
- Usuarios que no conocen detalles técnicos de conservación
- Migración desde otros sistemas de inventario
- Creación masiva de inventario inicial
    ''',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['name', 'quantity', 'unit', 'storage_type', 'category'],
                'properties': {
                    'name': {
                        'type': 'string',
                        'description': 'Nombre del item a agregar',
                        'example': 'Queso manchego',
                        'minLength': 2,
                        'maxLength': 100
                    },
                    'quantity': {
                        'type': 'number',
                        'description': 'Cantidad del item',
                        'example': 250,
                        'minimum': 0.01
                    },
                    'unit': {
                        'type': 'string',
                        'description': 'Unidad de medida',
                        'example': 'gr',
                        'enum': ['gr', 'kg', 'ml', 'l', 'unidades', 'piezas', 'tazas', 'cucharadas']
                    },
                    'storage_type': {
                        'type': 'string',
                        'description': 'Tipo de almacenamiento',
                        'example': 'refrigerador',
                        'enum': ['refrigerador', 'congelador', 'despensa', 'temperatura_ambiente']
                    },
                    'category': {
                        'type': 'string',
                        'description': 'Categoría del item',
                        'example': 'ingredient',
                        'enum': ['ingredient', 'food']
                    },
                    'image_url': {
                        'type': 'string',
                        'description': 'URL de imagen del item (opcional)',
                        'example': 'https://storage.googleapis.com/bucket/cheese.jpg',
                        'format': 'uri'
                    }
                },
                'example': {
                    'name': 'Queso manchego',
                    'quantity': 250,
                    'unit': 'gr',
                    'storage_type': 'refrigerador',
                    'category': 'ingredient',
                    'image_url': 'https://storage.googleapis.com/bucket/manchego_cheese.jpg'
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Item agregado exitosamente con enriquecimiento de IA',
            'examples': {
                'application/json': {
                    "message": "Item agregado al inventario exitosamente",
                    "item_type": "ingredient",
                    "item_details": {
                        "name": "Queso manchego",
                        "quantity": 250,
                        "type_unit": "gr",
                        "storage_type": "refrigerador",
                        "added_at": "2024-01-16T15:00:00Z",
                        "expiration_date": "2024-02-16T00:00:00Z",
                        "expiration_time": 31,
                        "time_unit": "Días"
                    },
                    "ai_generated_data": {
                        "tips": "Mantener envuelto en papel encerado o film plástico. Sacar del refrigerador 30 minutos antes de consumir para mejor sabor.",
                        "category": "lácteos",
                        "subcategory": "quesos curados",
                        "nutritional_highlights": ["alto en proteínas", "rico en calcio", "vitamina B12"],
                        "storage_recommendations": {
                            "temperature": "2-8°C",
                            "humidity": "80-85%",
                            "container": "envoltorio transpirable"
                        },
                        "usage_suggestions": [
                            "Perfecto para tablas de quesos",
                            "Excelente para gratinar",
                            "Combina bien con membrillo",
                            "Ideal para bocadillos gourmet"
                        ]
                    },
                    "environmental_impact": {
                        "carbon_footprint": {
                            "value": 1.2,
                            "unit": "kg CO2 eq",
                            "description": "Huella de carbono por 250gr de queso"
                        },
                        "sustainability_tips": [
                            "Compra quesos locales para reducir transporte",
                            "Aprovecha la corteza para caldos",
                            "Conserva adecuadamente para evitar desperdicio"
                        ]
                    },
                    "generation_metadata": {
                        "ai_confidence": 0.92,
                        "data_sources": ["nutrition_db", "storage_guidelines", "culinary_knowledge"],
                        "processing_time": 2.3,
                        "model_version": "food_ai_v3.1"
                    }
                }
            }
        },
        400: {
            'description': 'Datos de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Validation failed',
                    'details': {
                        'name': ['El nombre es requerido'],
                        'quantity': ['La cantidad debe ser mayor a 0'],
                        'category': ['Categoría debe ser "ingredient" o "food"']
                    }
                }
            }
        },
        422: {
            'description': 'Error en generación con IA',
            'examples': {
                'application/json': {
                    'error': 'AI generation failed',
                    'details': 'No se pudo generar información adicional para el item especificado',
                    'fallback_data': {
                        'tips': 'Almacenar según tipo de producto',
                        'expiration_time': 7,
                        'time_unit': 'Días'
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
def add_item_to_inventory():
    """
    Agrega un item (ingrediente o comida) al inventario del usuario.
    Los datos básicos vienen del frontend y los faltantes se generan con IA.
    
    URL: POST /api/inventory/add_item
    Body JSON:
    - name: nombre del item (required)
    - quantity: cantidad (required) 
    - unit: unidad de cantidad (required)
    - storage_type: tipo de almacenamiento (required)
    - category: 'ingredient' o 'food' (required)
    - image_url: URL de imagen (optional, nullable)
    
    Los campos generados automáticamente con IA:
    - Para ingredientes: tips, tiempo de vencimiento, impacto ambiental, ideas de uso
    - Para comidas: ingredientes principales, categoría, calorías, descripción, tips, análisis nutricional
    """
    user_uid = get_jwt_identity()
    
    print(f"🎯 [ADD ITEM] User: {user_uid}")
    
    try:
        # Validar datos de entrada
        json_data = request.get_json()
        
        if not json_data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        print(f"   └─ Request data: {json_data}")
        
        schema = AddItemToInventorySchema()
        errors = schema.validate(json_data)
        if errors:
            print(f"❌ [ADD ITEM] Validation errors: {errors}")
            return jsonify({"error": "Validation failed", "details": errors}), 400
        
        # Ejecutar caso de uso
        use_case = make_add_item_to_inventory_use_case(db)
        result = use_case.execute(
            user_uid=user_uid,
            item_data=json_data
        )
        
        print(f"✅ [ADD ITEM] Successfully added {result['item_type']}: {json_data.get('name')}")
        return jsonify(result), 201
        
    except ValueError as e:
        print(f"❌ [ADD ITEM] Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        print(f"🚨 [ADD ITEM] Unexpected error: {str(e)}")
        return jsonify({
            "error": "Failed to add item to inventory",
            "details": str(e)
        }), 500











