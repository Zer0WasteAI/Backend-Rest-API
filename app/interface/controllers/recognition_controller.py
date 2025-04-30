from flask import Blueprint, request, jsonify
from infrastructure.ai.gemini_adapter import GeminiAdapter
from use_cases.recognize_ingedient import recognize_ingredients_metadata
from use_cases.recognize_food import recognize_food_metadata
from use_cases.recognize_batch_metadata import recognize_batch_metadata
from utils.serialization_helper import serialize_pydantic_result

recognition_bp = Blueprint('recognition_bp', __name__)

@recognition_bp.route('/ingredients_metadata', methods=['GET'])
def ingredients_metadata():
    if 'img' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_file = request.files['img']
    recognizer = GeminiAdapter()
    result = recognize_ingredients_metadata(image_file, recognizer)
    #print("RESPONSE:", result)

    return jsonify(serialize_pydantic_result(result)), 200

@recognition_bp.route('/food_metadata', methods=['GET'])
def food_metadata():
    if 'img' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_file = request.files['img']
    recognizer = GeminiAdapter()
    result = recognize_food_metadata(image_file, recognizer)
    #print("RESPONSE:", result)

    return jsonify(serialize_pydantic_result(result)), 200

@recognition_bp.route('/batch_metadata', methods=['GET'])
def batch_metadata():
    if 'imgs' not in request.files:
        return jsonify({"error": "No images provided"}), 400
    
    image_files = request.files.getlist('imgs')
    recognizer = GeminiAdapter()
    result = recognize_batch_metadata(image_files, recognizer)

    return jsonify(serialize_pydantic_result(result)), 200