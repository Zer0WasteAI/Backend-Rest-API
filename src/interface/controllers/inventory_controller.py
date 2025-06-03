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
    schema = AddIngredientsBatchSchema()
    json_data = request.get_json()

    errors = schema.validate(json_data)
    if errors:
        raise InvalidRequestDataException(details=errors)

    ingredients_data = json_data.get("ingredients")

    use_case = make_add_ingredients_to_inventory_use_case(db)
    use_case.execute(user_uid=user_uid, ingredients_data=ingredients_data)

    return jsonify({"message": "Ingredientes agregados exitosamente"}), 201

@inventory_bp.route("", methods=["GET"])
@jwt_required()
def get_inventory():
    user_uid = get_jwt_identity()
    use_case = make_get_inventory_content_use_case(db)
    inventory = use_case.execute(user_uid)

    if not inventory:
        return jsonify({"message": "Inventario no encontrado"}), 404

    schema = InventorySchema()
    result = schema.dump({
        "ingredients": list(inventory.ingredients.values()),
        "food_items": []  # Futuro
    })

    return jsonify(result), 200

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

