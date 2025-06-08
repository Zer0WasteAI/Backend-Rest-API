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
def add_ingredients():
    user_uid = get_jwt_identity()
    json_data = request.get_json()
    
    print(f"📥 [INVENTORY POST] User: {user_uid}")
    print(f"📥 [INVENTORY POST] Request data: {json_data}")
    
    schema = AddIngredientsBatchSchema()
    errors = schema.validate(json_data)
    if errors:
        print(f"❌ [INVENTORY POST] Validation errors: {errors}")
        raise InvalidRequestDataException(details=errors)

    ingredients_data = json_data.get("ingredients")
    print(f"🥬 [INVENTORY POST] Processing {len(ingredients_data)} ingredients")
    
    for i, ingredient in enumerate(ingredients_data):
        print(f"   • Ingredient {i+1}: {ingredient.get('name')} - {ingredient.get('quantity')} {ingredient.get('type_unit')}")

    try:
        use_case = make_add_ingredients_to_inventory_use_case(db)
        use_case.execute(user_uid=user_uid, ingredients_data=ingredients_data)
        
        print(f"✅ [INVENTORY POST] Successfully added {len(ingredients_data)} ingredients for user {user_uid}")
        return jsonify({"message": "Ingredientes agregados exitosamente"}), 201
        
    except Exception as e:
        print(f"🚨 [INVENTORY POST] Error adding ingredients: {str(e)}")
        raise e

@inventory_bp.route("", methods=["GET"])
@jwt_required()
def get_inventory():
    user_uid = get_jwt_identity()
    
    print(f"📤 [INVENTORY GET] Fetching inventory for user: {user_uid}")
    
    try:
        use_case = make_get_inventory_content_use_case(db)
        inventory = use_case.execute(user_uid)

        if not inventory:
            print(f"❌ [INVENTORY GET] No inventory found for user: {user_uid}")
            return jsonify({"message": "Inventario no encontrado"}), 404

        print(f"📊 [INVENTORY GET] Found inventory with {len(inventory.ingredients)} ingredient types")
        
        # Log ingredient details
        total_stacks = 0
        for name, ingredient in inventory.ingredients.items():
            stack_count = len(ingredient.stacks)
            total_stacks += stack_count
            total_quantity = sum(stack.quantity for stack in ingredient.stacks)
            print(f"   • {name}: {stack_count} stacks, total quantity: {total_quantity} {ingredient.type_unit}")

        schema = InventorySchema()
        result = schema.dump({
            "ingredients": list(inventory.ingredients.values()),
            "food_items": []  # Futuro
        })
        
        print(f"✅ [INVENTORY GET] Successfully serialized inventory: {len(result['ingredients'])} ingredients, {total_stacks} total stacks")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"🚨 [INVENTORY GET] Error fetching inventory: {str(e)}")
        raise e

@inventory_bp.route("/complete", methods=["GET"])
@jwt_required()
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
def update_ingredient(ingredient_name, added_at):
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
def delete_ingredient(ingredient_name, added_at):
    """
    Elimina un stack específico de ingrediente del inventario.
    Si es el último stack, elimina también el ingrediente completo.
    
    URL: DELETE /api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z
    """
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
    print(f"📥 [INVENTORY FROM RECOGNITION ENHANCED] Request data: {json_data}")
    
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
        
        # Agregar image_path si no existe (fallback)
        if "image_path" not in ingredient:
            print(f"⚠️ [INVENTORY FROM RECOGNITION ENHANCED] Adding fallback image_path for: {ingredient['name']}")
            ingredient["image_path"] = "https://via.placeholder.com/150x150/cccccc/666666?text=No+Image"
    
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
def update_ingredient_quantity(ingredient_name, added_at):
    """
    Actualiza únicamente la cantidad de un stack específico de ingrediente.
    Mantiene todos los demás datos intactos.
    
    Body: { "quantity": 2.5 }
    """
    user_uid = get_jwt_identity()
    schema = UpdateIngredientQuantitySchema()
    json_data = request.get_json()

    print(f"📦 [UPDATE INGREDIENT QUANTITY] User: {user_uid}")
    print(f"   └─ Ingredient: {ingredient_name}")
    print(f"   └─ Added at: {added_at}")
    print(f"   └─ Request data: {json_data}")

    errors = schema.validate(json_data)
    if errors:
        print(f"❌ [UPDATE INGREDIENT QUANTITY] Validation errors: {errors}")
        raise InvalidRequestDataException(details=errors)

    try:
        use_case = make_update_ingredient_quantity_use_case(db)
        use_case.execute(
            user_uid=user_uid,
            ingredient_name=ingredient_name,
            added_at=added_at,
            new_quantity=json_data["quantity"]
        )

        print(f"✅ [UPDATE INGREDIENT QUANTITY] Successfully updated quantity for {ingredient_name}")
        return jsonify({
            "message": "Cantidad de ingrediente actualizada exitosamente",
            "ingredient": ingredient_name,
            "new_quantity": json_data["quantity"]
        }), 200

    except ValueError as e:
        print(f"❌ [UPDATE INGREDIENT QUANTITY] Stack not found: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"🚨 [UPDATE INGREDIENT QUANTITY] Unexpected error: {str(e)}")
        raise e

@inventory_bp.route("/foods/<food_name>/<added_at>/quantity", methods=["PATCH"])
@jwt_required()
def update_food_quantity(food_name, added_at):
    """
    Actualiza únicamente la cantidad de porciones de un food item específico.
    Mantiene todos los demás datos intactos.
    
    Body: { "serving_quantity": 3 }
    """
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
def delete_ingredient_complete(ingredient_name):
    """
    Elimina un ingrediente completo del inventario (todos sus stacks).
    
    URL: DELETE /api/inventory/ingredients/Tomate
    """
    user_uid = get_jwt_identity()

    print(f"🗑️ [DELETE INGREDIENT COMPLETE] User: {user_uid}")
    print(f"   └─ Ingredient to delete: {ingredient_name}")

    try:
        use_case = make_delete_ingredient_complete_use_case(db)
        use_case.execute(user_uid=user_uid, ingredient_name=ingredient_name)

        print(f"✅ [DELETE INGREDIENT COMPLETE] Successfully deleted complete ingredient: {ingredient_name}")
        return jsonify({
            "message": "Ingrediente eliminado completamente del inventario",
            "ingredient": ingredient_name,
            "deleted": "all_stacks"
        }), 200

    except ValueError as e:
        print(f"❌ [DELETE INGREDIENT COMPLETE] Ingredient not found: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"🚨 [DELETE INGREDIENT COMPLETE] Unexpected error: {str(e)}")
        raise e



@inventory_bp.route("/foods/<food_name>/<added_at>", methods=["DELETE"])
@jwt_required()
def delete_food_item(food_name, added_at):
    """
    Elimina un food item específico del inventario.
    
    URL: DELETE /api/inventory/foods/Pasta con Tomate/2025-01-01T10:00:00Z
    """
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
def mark_ingredient_stack_consumed(ingredient_name, added_at):
    """
    Marca un stack específico de ingrediente como consumido.
    Puede ser consumo parcial o total.
    
    URL: POST /api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume
    Body: { "consumed_quantity": 2.5 } (opcional - por defecto consume todo)
    """
    user_uid = get_jwt_identity()

    print(f"🍽️ [MARK INGREDIENT CONSUMED] User: {user_uid}")
    print(f"   └─ Ingredient: {ingredient_name}")
    print(f"   └─ Stack added at: {added_at}")

    # Validar datos de entrada
    schema = MarkIngredientConsumedSchema()
    try:
        validated_data = schema.load(request.get_json() or {})
    except Exception as e:
        print(f"❌ [MARK INGREDIENT CONSUMED] Validation error: {str(e)}")
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400

    consumed_quantity = validated_data.get('consumed_quantity')
    print(f"   └─ Consumed quantity: {consumed_quantity or 'ALL'}")

    try:
        use_case = make_mark_ingredient_stack_consumed_use_case(db)
        result = use_case.execute(
            user_uid=user_uid,
            ingredient_name=ingredient_name,
            added_at=added_at,
            consumed_quantity=consumed_quantity
        )

        print(f"✅ [MARK INGREDIENT CONSUMED] Success: {result['action']}")
        
        # Serializar response
        response_schema = ConsumedResponseSchema()
        response_data = response_schema.dump(result)

        return jsonify(response_data), 200

    except ValueError as e:
        print(f"❌ [MARK INGREDIENT CONSUMED] Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"🚨 [MARK INGREDIENT CONSUMED] Unexpected error: {str(e)}")
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
def get_food_detail(food_name, added_at):
    """
    Obtiene todos los detalles de un food item específico del inventario,
    incluyendo información nutricional, consejos de consumo, ideas de acompañamiento y más.
    
    URL: GET /api/inventory/foods/Pasta con Tomate/2025-01-01T10:00:00Z/detail
    """
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
def get_ingredients_list():
    """
    Obtiene únicamente la lista de ingredientes del inventario del usuario.
    No incluye food items.
    
    URL: GET /api/inventory/ingredients/list
    """
    user_uid = get_jwt_identity()

    print(f"📋 [GET INGREDIENTS LIST] User: {user_uid}")

    try:
        use_case = make_get_ingredients_list_use_case(db)
        ingredients_result = use_case.execute(user_uid=user_uid)

        print(f"✅ [GET INGREDIENTS LIST] Successfully fetched {ingredients_result['total_ingredients']} ingredients")
        return jsonify(ingredients_result), 200

    except Exception as e:
        print(f"🚨 [GET INGREDIENTS LIST] Unexpected error: {str(e)}")
        return jsonify({"error": f"Error fetching ingredients list: {str(e)}"}), 500

@inventory_bp.route("/foods/list", methods=["GET"])
@jwt_required()
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
    
    print(f"📤 [UPLOAD INVENTORY IMAGE] User: {user_uid}")
    
    try:
        # Obtener datos del formulario
        image_file = request.files.get('image')
        upload_type = request.form.get('upload_type', '').strip()
        item_name = request.form.get('item_name', '').strip() or None
        
        print(f"   └─ Upload type: {upload_type}")
        print(f"   └─ Item name: {item_name or 'N/A'}")
        print(f"   └─ File: {image_file.filename if image_file else 'None'}")
        
        # Validaciones básicas
        if not image_file:
            return jsonify({"error": "No image file provided"}), 400
        
        if not upload_type:
            return jsonify({"error": "upload_type is required"}), 400
        
        # Ejecutar caso de uso
        use_case = make_upload_inventory_image_use_case()
        result = use_case.execute(
            file=image_file,
            upload_type=upload_type,
            user_uid=user_uid,
            item_name=item_name
        )
        
        print(f"✅ [UPLOAD INVENTORY IMAGE] Successfully uploaded to: {result['upload_info']['folder']}")
        return jsonify(result), 201
        
    except ValueError as e:
        print(f"❌ [UPLOAD INVENTORY IMAGE] Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        print(f"🚨 [UPLOAD INVENTORY IMAGE] Unexpected error: {str(e)}")
        return jsonify({
            "error": "Failed to upload inventory image",
            "details": str(e)
        }), 500

# ===============================================================================
# 🎯 ENDPOINT PARA AGREGAR ITEM AL INVENTARIO (UNIFICADO)
# ===============================================================================

@inventory_bp.route("/add_item", methods=["POST"])
@jwt_required()
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

