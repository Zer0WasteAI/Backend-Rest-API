from flask import Blueprint, request, jsonify
from infrastructure.ai.gemini_adapter import GeminiAdapter
from use_cases.recognize_ingedient import recognize_ingredients_metadata

recognition_bp = Blueprint('recognition_bp', __name__)

@recognition_bp.route('/ingredients_metadata', methods=['GET'])
def ingredients_metadata():
    if 'img' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_file = request.files['img']
    recognizer = GeminiAdapter()
    result = recognize_ingredients_metadata(image_file, recognizer)
    print("RESPONSE:", result)

    return jsonify(result), 200
