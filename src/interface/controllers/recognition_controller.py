from flask import Blueprint, request, jsonify
from PIL import Image
from io import BytesIO
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.infrastructure.firebase.firebase_storage_adapter import get_image_from_firebase
from src.application.use_cases.recognition.recognize_ingredients_use_case import RecognizeIngredientsUseCase
from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
from src.infrastructure.db.recognition_repository_impl import RecognitionRepositoryImpl
from src.infrastructure.db.base import db

recognition_bp = Blueprint("recognition", __name__)
ai_service = GeminiAdapterService()
repository = RecognitionRepositoryImpl(db)
use_case = RecognizeIngredientsUseCase(ai_service, repository)

@recognition_bp.route("/ingredients", methods=["POST"])
@jwt_required()
def recognize_ingredients():
    user_uid = get_jwt_identity()
    image_path = request.json.get("image_path")
    print("Image_path exists")

    if not image_path:
        return jsonify({"error": "Falta image_path"}), 400

    try:
        image_file = get_image_from_firebase(image_path)
        print("Image exists")
        Image.open(image_file)
        print("Image oppened")
        image_file.seek(0)

        result = use_case.execute(user_uid=user_uid, image_file=image_file, image_path=image_path)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
