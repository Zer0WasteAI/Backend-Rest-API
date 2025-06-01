from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.application.factories.recipe_usecase_factory import (
    make_generate_recipes_use_case,
    make_prepare_recipe_generation_data_use_case
)

recipes_bp = Blueprint("recipes", __name__)

@recipes_bp.route("/generate-from-inventory", methods=["POST"])
@jwt_required()
def generate_recipes():
    user_uid = get_jwt_identity()

    # Preparar datos desde inventario
    prepare_use_case = make_prepare_recipe_generation_data_use_case()
    structured_data = prepare_use_case.execute(user_uid)

    # Generar recetas
    generate_use_case = make_generate_recipes_use_case()
    result = generate_use_case.execute(structured_data)

    return jsonify(result), 200
