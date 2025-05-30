from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.infrastructure.db.base import db

from src.interface.serializers.food_item_input_serializer import FoodItemInputSchema
from src.interface.serializers.expiring_soon_output_serializer import ExpiringSoonOutputSchema
from src.interface.serializers.ingredient_stack_input_serializer import IngredientStackInputSchema, IngredientInputSchema
from src.interface.serializers.inventory_public_serializer import InventoryPublicSchema

from src.application.factories.inventory_usecase_factory import (
make_add_food_item_to_inventory_use_case,
make_add_ingredient_to_inventory_use_case,
make_get_inventory_use_case,
make_get_expiring_soon_use_case
)

from src.shared.exceptions.custom import InvalidRequestDataException

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route("/ingredients", methods=["POST"])
@jwt_required()
def add_ingredient():
    json_data = request.get_json()
    errors = IngredientInputSchema().validate(json_data)
    if errors:
        raise InvalidRequestDataException(details=errors)
    user_uid = get_jwt_identity()
    user_case = make_add_ingredient_to_inventory_use_case(db)
    user_case.execute(user_uid=user_uid, ingredient_data=json_data)

    return jsonify({"message": "Ingrediente agregado correctamente"}), 201

@inventory_bp.route("/foods", methods=["POST"])
@jwt_required()
def add_food():
    json_data = request.get_json()
    errors = FoodItemInputSchema().validate(json_data)
    if errors:
        raise InvalidRequestDataException(details=errors)

    user_uid = get_jwt_identity()
    use_case = make_add_food_item_to_inventory_use_case(db)
    use_case.execute(user_uid=user_uid, food_item_data=json_data)

    return jsonify({"message": "Plato agregado correctamente"}), 201

@inventory_bp.route("", methods=["GET"])
@jwt_required()
def get_inventory():
    user_uid = get_jwt_identity()
    use_case = make_get_inventory_use_case(db)
    inventory = use_case.execute(user_uid=user_uid)
    serialized = InventoryPublicSchema().dump(inventory)
    return jsonify(serialized), 200

@inventory_bp.route("/expiring_soon", methods=["GET"])
@jwt_required()
def get_expiring_soon():
    days = int(request.args.get("days", 3))
    user_uid = get_jwt_identity()
    use_case = make_get_expiring_soon_use_case(db)
    items = use_case.execute(user_uid=user_uid, within_days=days)
    serialized = ExpiringSoonOutputSchema(many=True).dump(items)
    return jsonify(serialized), 200
