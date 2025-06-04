from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.infrastructure.db.base import db

from src.interface.serializers.inventory_serializers import (
AddIngredientsBatchSchema,
InventorySchema,
UpdateIngredientSchema
)

from src.application.factories.inventory_usecase_factory import (
make_add_food_items_to_inventory_use_case,
make_add_ingredients_and_foods_to_inventory_use_case,
make_add_ingredients_to_inventory_use_case,
make_delete_food_item_use_case,
make_delete_ingredient_stack_use_case,
make_get_expiring_soon_use_case,
make_get_inventory_content_use_case,
make_update_food_item_use_case,
make_update_ingredient_stack_use_case
)

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
    user_uid = get_jwt_identity()
    
    use_case = make_delete_ingredient_stack_use_case(db)
    use_case.execute(user_uid, ingredient_name, added_at)

    return jsonify({"message": "Ingrediente eliminado exitosamente"}), 200

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
    Endpoint específico para agregar ingredientes directamente desde el response de reconocimiento.
    Evita que el cliente tenga que reformatear los datos.
    """
    user_uid = get_jwt_identity()
    json_data = request.get_json()
    
    print(f"📥 [INVENTORY FROM RECOGNITION] User: {user_uid}")
    print(f"📥 [INVENTORY FROM RECOGNITION] Request data: {json_data}")
    
    # Validar que tenga la estructura del response de reconocimiento
    if not json_data or "ingredients" not in json_data:
        print(f"❌ [INVENTORY FROM RECOGNITION] Missing 'ingredients' field")
        return jsonify({"error": "Se requiere el campo 'ingredients' con la estructura de reconocimiento"}), 400
    
    ingredients_data = json_data["ingredients"]
    
    # Validar que cada ingrediente tenga los campos necesarios
    required_fields = ["name", "quantity", "type_unit", "storage_type", "expiration_time", "time_unit", "tips"]
    for i, ingredient in enumerate(ingredients_data):
        missing_fields = [field for field in required_fields if field not in ingredient]
        if missing_fields:
            print(f"❌ [INVENTORY FROM RECOGNITION] Ingredient {i+1} missing fields: {missing_fields}")
            return jsonify({
                "error": f"Ingrediente {i+1} ({ingredient.get('name', 'unknown')}) carece de campos requeridos: {missing_fields}"
            }), 400
        
        # Agregar image_path si no existe (fallback)
        if "image_path" not in ingredient:
            print(f"⚠️ [INVENTORY FROM RECOGNITION] Adding fallback image_path for: {ingredient['name']}")
            ingredient["image_path"] = "https://via.placeholder.com/150x150/cccccc/666666?text=No+Image"
    
    print(f"🥬 [INVENTORY FROM RECOGNITION] Processing {len(ingredients_data)} ingredients from recognition")
    
    for i, ingredient in enumerate(ingredients_data):
        print(f"   • Ingredient {i+1}: {ingredient.get('name')} - {ingredient.get('quantity')} {ingredient.get('type_unit')}")
        print(f"     └─ Has image_path: {'✅' if ingredient.get('image_path') else '❌'}")

    try:
        # Usar el mismo use case que el endpoint normal
        use_case = make_add_ingredients_to_inventory_use_case(db)
        use_case.execute(user_uid=user_uid, ingredients_data=ingredients_data)
        
        print(f"✅ [INVENTORY FROM RECOGNITION] Successfully added {len(ingredients_data)} ingredients for user {user_uid}")
        return jsonify({
            "message": "Ingredientes agregados exitosamente desde reconocimiento",
            "ingredients_count": len(ingredients_data),
            "source": "recognition"
        }), 201
        
    except Exception as e:
        print(f"🚨 [INVENTORY FROM RECOGNITION] Error adding ingredients: {str(e)}")
        raise e

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

