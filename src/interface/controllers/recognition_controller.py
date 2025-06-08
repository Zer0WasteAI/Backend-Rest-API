import traceback
import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.infrastructure.db.base import db
from src.application.factories.recognition_usecase_factory import (
    make_recognize_ingredients_use_case,
    make_recognize_foods_use_case,
    make_recognize_batch_use_case,
    make_recognize_ingredients_complete_use_case
)
from src.application.factories.auth_usecase_factory import make_firestore_profile_service
from src.infrastructure.async_tasks.async_task_service import async_task_service
from datetime import datetime, timezone
import uuid

recognition_bp = Blueprint("recognition", __name__)

@recognition_bp.route("/ingredients", methods=["POST"])
@jwt_required()
def recognize_ingredients():
    """
    🚀 RECONOCIMIENTO HÍBRIDO:
    - Respuesta inmediata con datos de IA (síncrono)
    - Generación de imágenes en segundo plano (asíncrono)
    """
    user_uid = get_jwt_identity()
    images_paths = request.json.get("images_paths")
    
    print(f"🔍 HYBRID RECOGNITION - User: {user_uid}")
    print(f"🔍 Images paths: {images_paths}")

    if not images_paths or not isinstance(images_paths, list):
        print("❌ ERROR: Invalid images_paths")
        return jsonify({"error": "Debe proporcionar una lista válida en 'images_paths'"}), 400

    try:
        # 1. PASO SÍNCRONO: Reconocimiento AI inmediato
        print("🔍 Loading images for AI recognition...")
        from src.application.factories.recognition_usecase_factory import make_ai_service, make_recognition_repository, make_storage_adapter
        
        ai_service = make_ai_service()
        recognition_repository = make_recognition_repository(db)
        storage_adapter = make_storage_adapter()
        
        # Cargar imágenes
        images_files = []
        for path in images_paths:
            file = storage_adapter.get_image(path)
            images_files.append(file)
        
        # Reconocimiento AI (síncrono)
        print("🤖 Running AI recognition...")
        result = ai_service.recognize_ingredients(images_files)
        
        # Guardar reconocimiento básico
        from src.domain.models.recognition import Recognition
        recognition = Recognition(
            uid=str(uuid.uuid4()),
            user_uid=user_uid,
            images_paths=images_paths,
            recognized_at=datetime.now(timezone.utc),
            raw_result=result,
            is_validated=False,
            validated_at=None
        )
        recognition_repository.save(recognition)
        
        # 2. PASO ASÍNCRONO: Crear tarea para generar imágenes
        print("🎨 Queuing image generation task...")
        image_task_id = async_task_service.create_task(
            user_uid=user_uid,
            task_type='ingredient_images',
            input_data={
                'recognition_id': recognition.uid,
                'ingredients': result['ingredients']
            }
        )
        
        # Lanzar generación de imágenes en background
        from src.application.factories.recognition_usecase_factory import make_ingredient_image_generator_service, make_calculator_service
        ingredient_image_generator_service = make_ingredient_image_generator_service()
        calculator_service = make_calculator_service()
        
        async_task_service.run_async_image_generation(
            task_id=image_task_id,
            user_uid=user_uid,
            ingredients=result['ingredients'],
            ingredient_image_generator_service=ingredient_image_generator_service,
            calculator_service=calculator_service,
            recognition_repository=recognition_repository,
            recognition_id=recognition.uid
        )
        
        # 3. RESPUESTA INMEDIATA: Datos sin imágenes + task_id para imágenes
        current_time = datetime.now(timezone.utc)
        
        # Agregar placeholders de imagen y datos básicos
        for ingredient in result["ingredients"]:
            ingredient["image_path"] = None  # Se agregará cuando esté lista
            ingredient["image_status"] = "generating"
            ingredient["added_at"] = current_time.isoformat()
            
            # Calcular fecha de vencimiento básica
            try:
                from src.application.factories.recognition_usecase_factory import make_calculator_service
                calculator_service = make_calculator_service()
                expiration_date = calculator_service.calculate_expiration_date(
                    added_at=current_time,
                    time_value=ingredient["expiration_time"],
                    time_unit=ingredient["time_unit"]
                )
                ingredient["expiration_date"] = expiration_date.isoformat()
            except Exception as e:
                from datetime import timedelta
                fallback_date = current_time + timedelta(days=ingredient.get("expiration_time", 7))
                ingredient["expiration_date"] = fallback_date.isoformat()
        
        # Verificar alergias
        firestore_service = make_firestore_profile_service()
        user_profile = firestore_service.get_profile(user_uid)
        if user_profile:
            print("🔍 Checking allergies...")
            result = _check_allergies_in_recognition(result, user_profile, "ingredients")
        
        # Respuesta con datos inmediatos + info de tarea de imágenes
        response_data = {
            **result,
            "recognition_id": recognition.uid,
            "images": {
                "status": "generating",
                "task_id": image_task_id,
                "check_images_url": f"/api/recognition/images/status/{image_task_id}",
                "estimated_time": "20-40 segundos"
            },
            "message": "✅ Ingredientes reconocidos. Las imágenes se están generando en segundo plano."
        }
        
        print("✅ Hybrid recognition successful - immediate response sent")
        print(f"📤 [HYBRID RESPONSE] Recognition ID: {recognition.uid}")
        print(f"📤 [HYBRID RESPONSE] Images Task ID: {image_task_id}")
        print(f"📤 [HYBRID RESPONSE] Ingredients count: {len(result.get('ingredients', []))}")
        print(f"📤 [HYBRID RESPONSE] Complete response:")
        print(f"📄 {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        return jsonify(response_data), 200

    except Exception as e:
        # Log detallado del error
        error_msg = f"🚨 ERROR EN HYBRID RECOGNITION: {str(e)}"
        error_traceback = f"🚨 TRACEBACK: {traceback.format_exc()}"
        
        print(error_msg)
        print(error_traceback)
        
        return jsonify({
            "error": str(e), 
            "error_type": str(type(e).__name__),
            "traceback": traceback.format_exc()
        }), 500

@recognition_bp.route("/ingredients/complete", methods=["POST"])
@jwt_required()
def recognize_ingredients_complete():
    """
    Endpoint para reconocimiento completo de ingredientes con toda la información:
    - Datos básicos (nombre, cantidad, descripción, etc.)
    - Impacto ambiental (CO2, agua)
    - Ideas de aprovechamiento
    """
    user_uid = get_jwt_identity()
    images_paths = request.json.get("images_paths")
    
    print(f"🔍 RECOGNIZE INGREDIENTS COMPLETE - User: {user_uid}")
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
        
        print("🔍 Creating complete recognition use case...")
        use_case = make_recognize_ingredients_complete_use_case(db)
        
        print("🔍 Executing complete recognition...")
        result = use_case.execute(user_uid=user_uid, images_paths=images_paths)
        print(f"🔍 Complete recognition result: {len(result.get('ingredients', []))} ingredients processed")
        
        # Verificar alergias en ingredientes reconocidos
        if user_profile:
            print("🔍 Checking allergies...")
            result = _check_allergies_in_recognition(result, user_profile, "ingredients")
        
        print("✅ Complete recognition successful")
        return jsonify(result), 200

    except Exception as e:
        # Log detallado del error
        error_msg = f"🚨 ERROR EN RECOGNIZE INGREDIENTS COMPLETE: {str(e)}"
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
    """
    🍽️ RECONOCIMIENTO HÍBRIDO DE COMIDA:
    - Respuesta inmediata con datos de IA (síncrono)
    - Generación de imágenes en segundo plano (asíncrono)
    """
    user_uid = get_jwt_identity()
    images_paths = request.json.get("images_paths")
    
    print(f"🍽️ HYBRID FOOD RECOGNITION - User: {user_uid}")
    print(f"🍽️ Images paths: {images_paths}")

    if not images_paths or not isinstance(images_paths, list):
        print("❌ ERROR: Invalid images_paths")
        return jsonify({"error": "Debe proporcionar una lista válida en 'images_paths'"}), 400

    try:
        # 1. PASO SÍNCRONO: Reconocimiento AI inmediato de platos
        print("🔍 Loading images for AI food recognition...")
        from src.application.factories.recognition_usecase_factory import make_ai_service, make_recognition_repository, make_storage_adapter
        
        ai_service = make_ai_service()
        recognition_repository = make_recognition_repository(db)
        storage_adapter = make_storage_adapter()
        
        # Cargar imágenes
        images_files = []
        for path in images_paths:
            file = storage_adapter.get_image(path)
            images_files.append(file)
        
        # Reconocimiento AI de platos (síncrono)
        print("🤖 Running AI food recognition...")
        result = ai_service.recognize_foods(images_files)
        
        # Guardar reconocimiento básico
        from src.domain.models.recognition import Recognition
        recognition = Recognition(
            uid=str(uuid.uuid4()),
            user_uid=user_uid,
            images_paths=images_paths,
            recognized_at=datetime.now(timezone.utc),
            raw_result=result,
            is_validated=False,
            validated_at=None
        )
        recognition_repository.save(recognition)
        
        # 2. PASO ASÍNCRONO: Crear tarea para generar imágenes de platos
        print("🎨 Queuing food image generation task...")
        image_task_id = async_task_service.create_task(
            user_uid=user_uid,
            task_type='food_images',
            input_data={
                'recognition_id': recognition.uid,
                'foods': result['foods']
            }
        )
        
        # Lanzar generación de imágenes de platos en background
        from src.application.factories.recognition_usecase_factory import make_food_image_generator_service, make_calculator_service
        food_image_generator_service = make_food_image_generator_service()
        calculator_service = make_calculator_service()
        
        async_task_service.run_async_food_image_generation(
            task_id=image_task_id,
            user_uid=user_uid,
            foods=result['foods'],
            food_image_generator_service=food_image_generator_service,
            calculator_service=calculator_service,
            recognition_repository=recognition_repository,
            recognition_id=recognition.uid
        )
        
        # 3. RESPUESTA INMEDIATA: Datos sin imágenes + task_id para imágenes
        current_time = datetime.now(timezone.utc)
        
        # Agregar placeholders de imagen y datos básicos
        for food in result["foods"]:
            food["image_path"] = None  # Se agregará cuando esté lista
            food["image_status"] = "generating"
            food["added_at"] = current_time.isoformat()
            
            # Calcular fecha de vencimiento básica
            try:
                expiration_date = calculator_service.calculate_expiration_date(
                    added_at=current_time,
                    time_value=food["expiration_time"],
                    time_unit=food["time_unit"]
                )
                food["expiration_date"] = expiration_date.isoformat()
            except Exception as e:
                from datetime import timedelta
                fallback_date = current_time + timedelta(days=food.get("expiration_time", 3))
                food["expiration_date"] = fallback_date.isoformat()
        
        # Verificar alergias
        firestore_service = make_firestore_profile_service()
        user_profile = firestore_service.get_profile(user_uid)
        if user_profile:
            result = _check_allergies_in_recognition(result, user_profile, "foods")
        
        # Respuesta con datos inmediatos + info de tarea de imágenes
        response_data = {
            **result,
            "recognition_id": recognition.uid,
            "images": {
                "status": "generating",
                "task_id": image_task_id,
                "check_images_url": f"/api/recognition/images/status/{image_task_id}",
                "estimated_time": "15-30 segundos"
            },
            "message": "✅ Platos reconocidos. Las imágenes se están generando en segundo plano."
        }
        
        print("✅ Hybrid food recognition successful - immediate response sent")
        print(f"📤 [HYBRID FOOD RESPONSE] Recognition ID: {recognition.uid}")
        print(f"📤 [HYBRID FOOD RESPONSE] Images Task ID: {image_task_id}")
        print(f"📤 [HYBRID FOOD RESPONSE] Foods count: {len(result.get('foods', []))}")
        print(f"📤 [HYBRID FOOD RESPONSE] Complete response:")
        print(f"📄 {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        return jsonify(response_data), 200

    except Exception as e:
        print(f"🚨 HYBRID FOOD RECOGNITION ERROR: {str(e)}")
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

@recognition_bp.route("/ingredients/async", methods=["POST"])
@jwt_required()
def recognize_ingredients_async():
    """
    🚀 ENDPOINT ASÍNCRONO: Reconocimiento de ingredientes en background
    
    - Respuesta inmediata con task_id
    - Procesamiento en segundo plano
    - Generación de imágenes asíncrona
    - Consultar progreso con /status/{task_id}
    """
    user_uid = get_jwt_identity()
    images_paths = request.json.get("images_paths")
    
    print(f"🚀 [ASYNC RECOGNITION] User: {user_uid}")
    print(f"🚀 [ASYNC RECOGNITION] Images: {len(images_paths) if images_paths else 0}")

    if not images_paths or not isinstance(images_paths, list):
        print("❌ [ASYNC RECOGNITION] Invalid images_paths")
        return jsonify({"error": "Debe proporcionar una lista válida en 'images_paths'"}), 400

    try:
        # Crear tarea asíncrona
        task_id = async_task_service.create_task(
            user_uid=user_uid,
            task_type='ingredient_recognition',
            input_data={'images_paths': images_paths}
        )
        
        # Lanzar procesamiento en background
        from src.application.factories.recognition_usecase_factory import (
            make_ai_service, make_recognition_repository, make_storage_adapter,
            make_ingredient_image_generator_service, make_calculator_service
        )
        
        ai_service = make_ai_service()
        recognition_repository = make_recognition_repository(db)
        storage_adapter = make_storage_adapter()
        ingredient_image_generator_service = make_ingredient_image_generator_service()
        calculator_service = make_calculator_service()
        
        async_task_service.run_async_recognition(
            task_id=task_id,
            ai_service=ai_service,
            recognition_repository=recognition_repository,
            storage_adapter=storage_adapter,
            ingredient_image_generator_service=ingredient_image_generator_service,
            calculator_service=calculator_service,
            user_uid=user_uid,
            images_paths=images_paths
        )
        
        print(f"🎯 [ASYNC RECOGNITION] Task {task_id} queued successfully")
        
        # Respuesta inmediata
        return jsonify({
            "message": "🚀 Estamos procesando tu imagen en segundo plano",
            "task_id": task_id,
            "status": "pending",
            "progress_percentage": 0,
            "estimated_time": "30-60 segundos",
            "check_status_url": f"/api/recognition/status/{task_id}"
        }), 202  # 202 Accepted

    except Exception as e:
        error_msg = f"🚨 ERROR EN ASYNC RECOGNITION: {str(e)}"
        print(error_msg)
        print(f"🚨 TRACEBACK: {traceback.format_exc()}")
        
        return jsonify({
            "error": str(e), 
            "error_type": str(type(e).__name__)
        }), 500

@recognition_bp.route("/status/<task_id>", methods=["GET"])
@jwt_required()
def get_recognition_status(task_id):
    """
    📊 CONSULTAR ESTADO: Obtiene el progreso y resultado de una tarea asíncrona
    """
    user_uid = get_jwt_identity()
    
    print(f"📊 [STATUS CHECK] Task: {task_id}, User: {user_uid}")
    
    try:
        task_status = async_task_service.get_task_status(task_id)
        
        if not task_status:
            print(f"❌ [STATUS CHECK] Task {task_id} not found")
            return jsonify({"error": "Tarea no encontrada"}), 404
        
        # Verificar que la tarea pertenece al usuario
        from src.infrastructure.db.models.async_task_orm import AsyncTaskORM
        task = AsyncTaskORM.query.filter_by(task_id=task_id).first()
        if not task or task.user_uid != user_uid:
            print(f"❌ [STATUS CHECK] Task {task_id} unauthorized for user {user_uid}")
            return jsonify({"error": "No tienes permiso para ver esta tarea"}), 403
        
        print(f"📊 [STATUS CHECK] Task {task_id}: {task_status['status']} - {task_status['progress_percentage']}%")
        
        # Si está completada, incluir verificación de alergias
        if task_status['status'] == 'completed' and task_status['result_data']:
            try:
                # Obtener preferencias del usuario para verificar alergias
                firestore_service = make_firestore_profile_service()
                user_profile = firestore_service.get_profile(user_uid)
                
                if user_profile:
                    print("🔍 [STATUS CHECK] Checking allergies in completed result...")
                    result_with_allergies = _check_allergies_in_recognition(
                        task_status['result_data'], 
                        user_profile, 
                        "ingredients"
                    )
                    task_status['result_data'] = result_with_allergies
                    
            except Exception as e:
                print(f"⚠️ [STATUS CHECK] Error checking allergies: {str(e)}")
                # No fallar la respuesta por esto
        
        return jsonify(task_status), 200

    except Exception as e:
        error_msg = f"🚨 ERROR EN STATUS CHECK: {str(e)}"
        print(error_msg)
        
        return jsonify({
            "error": str(e),
            "error_type": str(type(e).__name__)
        }), 500

@recognition_bp.route("/images/status/<task_id>", methods=["GET"])
@jwt_required()
def get_images_status(task_id):
    """
    🎨 CONSULTAR IMÁGENES: Obtiene el progreso y resultado de la generación de imágenes
    """
    user_uid = get_jwt_identity()
    
    print(f"🎨 [IMAGES STATUS] Task: {task_id}, User: {user_uid}")
    
    try:
        task_status = async_task_service.get_task_status(task_id)
        
        if not task_status:
            print(f"❌ [IMAGES STATUS] Task {task_id} not found")
            return jsonify({"error": "Tarea de imágenes no encontrada"}), 404
        
        # Verificar que la tarea pertenece al usuario
        from src.infrastructure.db.models.async_task_orm import AsyncTaskORM
        task = AsyncTaskORM.query.filter_by(task_id=task_id).first()
        if not task or task.user_uid != user_uid:
            print(f"❌ [IMAGES STATUS] Task {task_id} unauthorized for user {user_uid}")
            return jsonify({"error": "No tienes permiso para ver esta tarea"}), 403
        
        print(f"🎨 [IMAGES STATUS] Task {task_id}: {task_status['status']} - {task_status['progress_percentage']}%")
        
        # Formatear respuesta específica para imágenes
        response = {
            "task_id": task_id,
            "status": task_status['status'],
            "progress_percentage": task_status['progress_percentage'],
            "current_step": task_status['current_step'],
            "created_at": task_status['created_at'],
            "started_at": task_status['started_at'],
            "completed_at": task_status['completed_at']
        }
        
        if task_status['status'] == 'completed' and task_status['result_data']:
            response['images_data'] = task_status['result_data']
            response['message'] = "🎉 Imágenes generadas exitosamente"
        elif task_status['status'] == 'failed':
            response['error'] = task_status['error_message']
            response['message'] = "🚨 Error generando imágenes"
        elif task_status['status'] == 'processing':
            response['message'] = f"🎨 Generando imágenes... {task_status['progress_percentage']}%"
        else:
            response['message'] = "⏳ Esperando para procesar imágenes..."
        
        return jsonify(response), 200

    except Exception as e:
        error_msg = f"🚨 ERROR EN IMAGES STATUS: {str(e)}"
        print(error_msg)
        
        return jsonify({
            "error": str(e),
            "error_type": str(type(e).__name__)
        }), 500

@recognition_bp.route("/recognition/<recognition_id>/images", methods=["GET"])
@jwt_required()
def get_recognition_images(recognition_id):
    """
    🖼️ OBTENER IMÁGENES: Obtiene las imágenes actualizadas de un reconocimiento específico
    """
    user_uid = get_jwt_identity()
    
    print(f"🖼️ [GET IMAGES] Recognition: {recognition_id}, User: {user_uid}")
    
    try:
        # Obtener el reconocimiento de la base de datos
        from src.application.factories.recognition_usecase_factory import make_recognition_repository
        recognition_repository = make_recognition_repository(db)
        recognition = recognition_repository.find_by_uid(recognition_id)
        
        if not recognition:
            print(f"❌ [GET IMAGES] Recognition {recognition_id} not found")
            return jsonify({"error": "Reconocimiento no encontrado"}), 404
        
        # Verificar que pertenece al usuario
        if recognition.user_uid != user_uid:
            print(f"❌ [GET IMAGES] Recognition {recognition_id} unauthorized for user {user_uid}")
            return jsonify({"error": "No tienes permiso para ver este reconocimiento"}), 403
        
        # Obtener los ingredientes con imágenes actualizadas
        ingredients = recognition.raw_result.get('ingredients', [])
        
        # Verificar si todas las imágenes están listas
        images_ready = all(
            ingredient.get('image_path') is not None and 
            ingredient.get('image_status') == 'ready'
            for ingredient in ingredients
        )
        
        response = {
            "recognition_id": recognition_id,
            "ingredients": ingredients,
            "images_ready": images_ready,
            "total_ingredients": len(ingredients),
            "images_generated": sum(1 for ing in ingredients if ing.get('image_path') and ing.get('image_status') == 'ready'),
            "last_updated": recognition.recognized_at.isoformat()
        }
        
        if images_ready:
            response['message'] = "✅ Todas las imágenes están listas"
        else:
            response['message'] = "⏳ Algunas imágenes aún se están generando"
        
        print(f"✅ [GET IMAGES] Returned {len(ingredients)} ingredients for recognition {recognition_id}")
        return jsonify(response), 200

    except Exception as e:
        error_msg = f"🚨 ERROR EN GET IMAGES: {str(e)}"
        print(error_msg)
        
        return jsonify({
            "error": str(e),
            "error_type": str(type(e).__name__)
        }), 500