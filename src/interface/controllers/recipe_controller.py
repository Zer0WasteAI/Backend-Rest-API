from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.interface.serializers.recipe_serializers import (
    CustomRecipeRequestSchema,
    SaveRecipeRequestSchema,
    RecipeSchema
)

from src.application.factories.recipe_usecase_factory import (
    make_generate_recipes_use_case,
    make_prepare_recipe_generation_data_use_case,
    make_generate_custom_recipe_use_case,
    make_save_recipe_use_case,
    make_get_saved_recipes_use_case,
    make_get_all_recipes_use_case,
    make_delete_user_recipe_use_case
)

from src.shared.exceptions.custom import InvalidRequestDataException

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

@recipes_bp.route("/generate-custom", methods=["POST"])
@jwt_required()
def generate_custom_recipes():
    user_uid = get_jwt_identity()
    schema = CustomRecipeRequestSchema()
    json_data = request.get_json()

    errors = schema.validate(json_data)
    if errors:
        raise InvalidRequestDataException(details=errors)

    use_case = make_generate_custom_recipe_use_case()
    result = use_case.execute(
        user_uid=user_uid,
        custom_ingredients=json_data["ingredients"],
        preferences=json_data.get("preferences", []),
        num_recipes=json_data.get("num_recipes", 2),
        recipe_categories=json_data.get("recipe_categories", [])
    )

    return jsonify(result), 200

@recipes_bp.route("/save", methods=["POST"])
@jwt_required()
def save_recipe():
    user_uid = get_jwt_identity()
    schema = SaveRecipeRequestSchema()
    json_data = request.get_json()

    errors = schema.validate(json_data)
    if errors:
        raise InvalidRequestDataException(details=errors)

    use_case = make_save_recipe_use_case()
    saved_recipe = use_case.execute(user_uid, json_data)

    recipe_schema = RecipeSchema()
    result = recipe_schema.dump(saved_recipe)

    return jsonify({
        "message": "Receta guardada exitosamente",
        "recipe": result
    }), 201

@recipes_bp.route("/saved", methods=["GET"])
@jwt_required()
def get_saved_recipes():
    user_uid = get_jwt_identity()
    
    use_case = make_get_saved_recipes_use_case()
    saved_recipes = use_case.execute(user_uid)

    recipe_schema = RecipeSchema()
    result = recipe_schema.dump(saved_recipes, many=True)

    return jsonify({
        "recipes": result,
        "count": len(result)
    }), 200


@recipes_bp.route("/all", methods=["GET"])
@jwt_required()
def get_all_recipes():

    use_case = make_get_all_recipes_use_case()
    all_recipes = use_case.execute()

    recipe_schema = RecipeSchema()
    result = recipe_schema.dump(all_recipes, many=True)

    return jsonify({
        "recipes": result,
        "count": len(result)
    }), 200

@recipes_bp.route("/delete", methods=["DELETE"])
@jwt_required()
def delete_user_recipe():
    user_uid = get_jwt_identity()
    data = request.get_json()

    if not data or "title" not in data:
        raise InvalidRequestDataException(details={"title": "El campo 'title' es obligatorio."})

    title = data["title"]
    use_case = make_delete_user_recipe_use_case()

    use_case.execute(user_uid=user_uid, title=title)

    return jsonify({
        "message": f"Receta '{title}' eliminada exitosamente"
    }), 200

