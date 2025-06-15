from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.application.factories.generation_usecase_factory import make_generation_repository
from src.domain.models.generation import Generation
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
    make_delete_user_recipe_use_case,
    make_recipe_image_generator_service
)

from src.infrastructure.async_tasks.async_task_service import async_task_service
from src.shared.exceptions.custom import InvalidRequestDataException
from datetime import datetime, timezone
import uuid

recipes_bp = Blueprint("recipes", __name__)

@recipes_bp.route("/generate-from-inventory", methods=["POST"])
@jwt_required()
def generate_recipes():
    user_uid = get_jwt_identity()

    prepare_use_case = make_prepare_recipe_generation_data_use_case()
    structured_data = prepare_use_case.execute(user_uid)

    generate_use_case = make_generate_recipes_use_case()
    result = generate_use_case.execute(structured_data)

    generation_id = str(uuid.uuid4())

    # Guardar Generation
    generation_repository = make_generation_repository()
    generation = Generation(
        uid=generation_id,
        user_uid=user_uid,
        generated_at=datetime.now(timezone.utc),
        raw_result=result,
        generation_type="inventory",
        recipes_ids=None
    )
    generation_repository.save(generation)

    # Crear tarea de imagen
    image_task_id = async_task_service.create_task(
        user_uid=user_uid,
        task_type='recipe_images',
        input_data={
            'generation_id': generation_id,
            'recipes': result["generated_recipes"]
        }
    )

    recipe_image_generator_service = make_recipe_image_generator_service()

    async_task_service.run_async_recipe_image_generation(
        task_id=image_task_id,
        user_uid=user_uid,
        recipes=result["generated_recipes"],
        recipe_image_generator_service=recipe_image_generator_service,
        generation_repository=generation_repository,
        generation_id=generation_id
    )
    current_time = datetime.now(timezone.utc)
    for recipe in result["generated_recipes"]:
        recipe["image_path"] = None
        recipe["image_status"] = "generating"
        recipe["generated_at"] = current_time.isoformat()

    result["images"] = {
        "status": "generating",
        "task_id": image_task_id,
        "check_images_url": f"/api/generation/images/status/{image_task_id}",
        "estimated_time": "15-30 segundos"
    }

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

    generation_id = str(uuid.uuid4())

    generation_repository = make_generation_repository()
    generation = Generation(
        uid=generation_id,
        user_uid=user_uid,
        generated_at=datetime.now(timezone.utc),
        raw_result=result,
        generation_type="custom",
        recipes_ids=None
    )
    generation_repository.save(generation)

    image_task_id = async_task_service.create_task(
        user_uid=user_uid,
        task_type='recipe_images',
        input_data={
            'generation_id': generation_id,
            'recipes': result["generated_recipes"]
        }
    )

    recipe_image_generator_service = make_recipe_image_generator_service()

    async_task_service.run_async_recipe_image_generation(
        task_id=image_task_id,
        user_uid=user_uid,
        recipes=result["generated_recipes"],
        recipe_image_generator_service=recipe_image_generator_service,
        generation_repository=generation_repository,
        generation_id=generation_id
    )

    current_time = datetime.now(timezone.utc)
    for recipe in result["generated_recipes"]:
        recipe["image_path"] = None
        recipe["image_status"] = "generating"
        recipe["generated_at"] = current_time.isoformat()

    result["images"] = {
        "status": "generating",
        "task_id": image_task_id,
        "check_images_url": f"/api/generation/images/status/{image_task_id}",
        "estimated_time": "15-30 segundos"
    }

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
