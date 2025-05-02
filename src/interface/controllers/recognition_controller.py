from flask import Blueprint, request, jsonify
from PIL import Image
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.infrastructure.firebase.firebase_storage_adapter import get_image_from_firebase, get_images_from_firebase
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
    image_path = request.json.get("image_path")

    if not image_path:
        return jsonify({"error": "Falta image_path"}), 400

    try:
        image_file = get_image_from_firebase(image_path)
        Image.open(image_file)
        image_file.seek(0)
        use_case = make_recognize_ingredients_use_case(db)
        result = use_case.execute(user_uid=user_uid, image_file=image_file, image_path=image_path)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recognition_bp.route("/foods", methods=["POST"])
@jwt_required()
def recognize_foods():
    user_uid = get_jwt_identity()
    image_path = request.json.get("image_path")

    if not image_path:
        return jsonify({"error": "Not found image_path"}), 400

    try:
        image_file = get_image_from_firebase(image_path)
        Image.open(image_file)
        image_file.seek(0)
        use_case = make_recognize_foods_use_case(db)
        result = use_case.execute(user_uid=user_uid, image_file=image_file, image_path=image_path)
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
        images_files = []
        for path in images_paths:
            file = get_image_from_firebase(path)
            Image.open(file)  # Verifica que la imagen sea válida
            file.seek(0)  # Reinicia el puntero para futuras lecturas
            images_files.append(file)

        use_case = make_recognize_batch_use_case(db)
        result = use_case.execute(user_uid=user_uid, images_files=images_files, images_paths=images_paths)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500