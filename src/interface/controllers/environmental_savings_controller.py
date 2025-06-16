from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.application.factories.environmental_savings_factory import (
    make_estimate_savings_by_title_use_case,
    make_estimate_savings_by_uid_use_case,
    make_get_all_environmental_calculations_use_case,
    make_get_environmental_calculations_by_status_use_case
)
from src.shared.exceptions.custom import InvalidRequestDataException, RecipeNotFoundException

environmental_savings_bp = Blueprint("environmental_savings", __name__)


@environmental_savings_bp.route("/calculate/from-title", methods=["POST"])
@jwt_required()
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
def calculate_savings_from_uid(recipe_uid):
    use_case = make_estimate_savings_by_uid_use_case()

    try:
        result = use_case.execute(recipe_uid=recipe_uid)
        return jsonify(result), 200
    except RecipeNotFoundException as e:
        return jsonify({"error": str(e)}), 404


@environmental_savings_bp.route("/calculations", methods=["GET"])
@jwt_required()
def get_all_calculations():
    user_uid = get_jwt_identity()
    use_case = make_get_all_environmental_calculations_use_case()
    result = use_case.execute(user_uid)
    return jsonify({"calculations": result, "count": len(result)}), 200


@environmental_savings_bp.route("/calculations/status", methods=["GET"])
@jwt_required()
def get_calculations_by_status():
    user_uid = get_jwt_identity()
    is_cooked_param = request.args.get("is_cooked")

    if is_cooked_param not in ["true", "false"]:
        raise InvalidRequestDataException(details={"is_cooked": "Debe ser 'true' o 'false'."})

    is_cooked = is_cooked_param == "true"
    use_case = make_get_environmental_calculations_by_status_use_case()
    result = use_case.execute(user_uid=user_uid, is_cooked=is_cooked)
    return jsonify({"calculations": result, "count": len(result)}), 200
