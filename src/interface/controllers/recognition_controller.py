import traceback
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.infrastructure.db.base import db
from src.application.factories.recognition_usecase_factory import (
    make_recognize_ingredients_use_case,
    make_recognize_foods_use_case,
    make_recognize_batch_use_case
)
from src.application.factories.auth_usecase_factory import make_firestore_profile_service

recognition_bp = Blueprint("recognition", __name__)

@recognition_bp.route("/ingredients", methods=["POST"])
@jwt_required()
def recognize_ingredients():
    user_uid = get_jwt_identity()
    images_paths = request.json.get("images_paths")
    
    print(f"🔍 RECOGNIZE INGREDIENTS - User: {user_uid}")
    print(f"🔍 Images paths: {images_paths}")

    if not images_paths or not isinstance(images_paths, list):
        print("❌ ERROR: Invalid images_paths")
        return jsonify({"error": "Debe proporcionar una lista válida en 'images_paths'"}), 400

    try:
        # Obtener preferencias del usuario
        print("🔍 Getting user profile from Firestore...")
        firestore_service = make_firestore_profile_service()
        user_profile = firestore_service.get_profile(user_uid)
        print(f"🔍 User profile: {user_profile is not None}")
        
        print("🔍 Creating use case...")
        use_case = make_recognize_ingredients_use_case(db)
        
        print("🔍 Executing recognition...")
        result = use_case.execute(user_uid=user_uid, images_paths=images_paths)
        print(f"🔍 Recognition result: {result}")
        
        # Verificar alergias en ingredientes reconocidos
        if user_profile:
            print("🔍 Checking allergies...")
            result = _check_allergies_in_recognition(result, user_profile, "ingredients")
        
        print("✅ Recognition successful")
        return jsonify(result), 200

    except Exception as e:
        # Log detallado del error
        error_msg = f"🚨 ERROR EN RECOGNIZE INGREDIENTS: {str(e)}"
        error_traceback = f"🚨 TRACEBACK: {traceback.format_exc()}"
        
        print(error_msg)
        print(error_traceback)
        
        return jsonify({
            "error": str(e), 
            "error_type": str(type(e).__name__),
            "traceback": traceback.format_exc()
        }), 500

@recognition_bp.route("/foods", methods=["POST"])
@jwt_required()
def recognize_foods():
    user_uid = get_jwt_identity()
    images_paths = request.json.get("images_paths")

    if not images_paths or not isinstance(images_paths, list):
        return jsonify({"error": "Debe proporcionar una lista válida en 'images_paths'"}), 400

    try:
        # Obtener preferencias del usuario
        firestore_service = make_firestore_profile_service()
        user_profile = firestore_service.get_profile(user_uid)
        
        use_case = make_recognize_foods_use_case(db)
        result = use_case.execute(user_uid=user_uid, images_paths=images_paths)
        
        # Verificar alergias en alimentos reconocidos
        if user_profile:
            result = _check_allergies_in_recognition(result, user_profile, "recognized_foods")
        
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
        # Obtener preferencias del usuario
        firestore_service = make_firestore_profile_service()
        user_profile = firestore_service.get_profile(user_uid)
        
        use_case = make_recognize_batch_use_case(db)
        result = use_case.execute(user_uid=user_uid, images_paths=images_paths)
        
        # Verificar alergias en resultados del lote
        if user_profile:
            result = _check_allergies_in_batch_recognition(result, user_profile)
        
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _check_allergies_in_recognition(result: dict, user_profile: dict, items_key: str) -> dict:
    """
    Verifica alergias en resultados de reconocimiento y agrega alertas
    """
    allergies = user_profile.get("allergies", [])
    allergy_items = user_profile.get("allergyItems", [])
    language = user_profile.get("language", "es")
    
    print(f"🔍 Allergies: {allergies}")
    print(f"🔍 Allergy items: {allergy_items}")
    
    if not allergies and not allergy_items:
        return result
    
    allergy_alerts = []
    items = result.get(items_key, [])
    
    for item in items:
        item_name = item.get("name", "").lower()
        detected_allergens = []
        
        # Verificar alergias generales
        for allergy in allergies:
            allergy_name = _extract_allergy_name(allergy)
            if allergy_name and allergy_name.lower() in item_name:
                detected_allergens.append(allergy_name)
        
        # Verificar items específicos de alergia
        for allergy_item in allergy_items:
            allergy_name = _extract_allergy_name(allergy_item)
            if allergy_name and allergy_name.lower() in item_name:
                detected_allergens.append(allergy_name)
        
        if detected_allergens:
            alert_message = _get_allergy_alert_message(detected_allergens, language)
            allergy_alerts.append({
                "item": item.get("name"),
                "allergens": detected_allergens,
                "message": alert_message,
                "confidence": item.get("confidence", 0)
            })
            
            # Marcar el item con alerta de alergia
            item["allergy_alert"] = True
            item["allergens"] = detected_allergens
    
    if allergy_alerts:
        result["allergy_alerts"] = allergy_alerts
        result["has_allergens"] = True
    
    return result

def _extract_allergy_name(allergy_data) -> str:
    """
    Extrae el nombre de la alergia desde diferentes formatos:
    - Si es string: retorna el string
    - Si es dict con 'name': retorna allergy_data['name']
    - Si es dict con 'value': retorna allergy_data['value']
    - Si es dict con 'label': retorna allergy_data['label']
    """
    if isinstance(allergy_data, str):
        return allergy_data
    elif isinstance(allergy_data, dict):
        # Intentar diferentes campos comunes
        for field in ['name', 'value', 'label', 'title']:
            if field in allergy_data and allergy_data[field]:
                return str(allergy_data[field])
        # Si no encuentra campos conocidos, usar el primer valor string encontrado
        for value in allergy_data.values():
            if isinstance(value, str) and value.strip():
                return value
    
    print(f"⚠️ Warning: Unable to extract allergy name from: {allergy_data}")
    return ""

def _check_allergies_in_batch_recognition(result: dict, user_profile: dict) -> dict:
    """
    Verifica alergias en resultados de reconocimiento por lotes
    """
    batch_results = result.get("batch_results", [])
    
    for batch_item in batch_results:
        detected_items = batch_item.get("detected_items", [])
        
        # Crear un resultado temporal para usar la función existente
        temp_result = {"recognized_items": detected_items}
        temp_result = _check_allergies_in_recognition(temp_result, user_profile, "recognized_items")
        
        # Transferir alertas de vuelta al batch
        if temp_result.get("allergy_alerts"):
            batch_item["allergy_alerts"] = temp_result["allergy_alerts"]
            batch_item["has_allergens"] = True
    
    return result

def _get_allergy_alert_message(allergens: list, language: str) -> str:
    """
    Genera mensaje de alerta de alergia según el idioma del usuario
    """
    allergens_str = ", ".join(allergens)
    
    if language == "en":
        if len(allergens) == 1:
            return f"⚠️ ALLERGY ALERT: This item contains {allergens_str}, which you are allergic to."
        else:
            return f"⚠️ ALLERGY ALERT: This item contains {allergens_str}, which you are allergic to."
    else:
        if len(allergens) == 1:
            return f"⚠️ ALERTA DE ALERGIA: Este elemento contiene {allergens_str}, al cual eres alérgico."
        else:
            return f"⚠️ ALERTA DE ALERGIA: Este elemento contiene {allergens_str}, a los cuales eres alérgico."