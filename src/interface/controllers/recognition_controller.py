from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.infrastructure.db.base import db
from src.application.factories.recognition_usecase_factory import (
    make_recognize_ingredients_use_case,
    make_recognize_foods_use_case,
    make_recognize_batch_use_case
)

recognition_bp = Blueprint("recognition", __name__)

@recognition_bp.route("/ingredients", methods=["POST"])
@jwt_required()
def recognize_ingredients():
    user_uid = get_jwt_identity()
    images_paths = request.json.get("images_paths")

    if not images_paths or not isinstance(images_paths, list):
        return jsonify({"error": "Debe proporcionar una lista válida en 'images_paths'"}), 400

    try:
        use_case = make_recognize_ingredients_use_case(db)
        result = use_case.execute(user_uid=user_uid, images_paths=images_paths)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recognition_bp.route("/foods", methods=["POST"])
@jwt_required()
def recognize_foods():
    user_uid = get_jwt_identity()
    images_paths = request.json.get("images_paths")

    if not images_paths or not isinstance(images_paths, list):
        return jsonify({"error": "Debe proporcionar una lista válida en 'images_paths'"}), 400

    try:
        use_case = make_recognize_foods_use_case(db)
        result = use_case.execute(user_uid=user_uid, images_paths=images_paths)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recognition_bp.route("/batch", methods=["POST"])
@jwt_required()
def recognize_batch():
    user_uid = get_jwt_identity()
    images_paths = request.json.get("images_paths")

    if not images_paths or not isinstance(images_paths, list):
        return jsonify({"error": "Debe proporcionar una lista válida en 'images_paths'"}), 400

    try:
        use_case = make_recognize_batch_use_case(db)
        result = use_case.execute(user_uid=user_uid, images_paths=images_paths)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500