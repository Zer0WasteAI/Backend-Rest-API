from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.infrastructure.db.base import db
from src.application.factories.generation_usecase_factory import make_generation_repository
from src.infrastructure.async_tasks.async_task_service import async_task_service
from src.infrastructure.db.models.async_task_orm import AsyncTaskORM

generation_bp = Blueprint("generation", __name__)

@generation_bp.route("/images/status/<task_id>", methods=["GET"])
@jwt_required()
def get_generation_images_status(task_id):
    """
    🎨 CONSULTAR IMÁGENES DE GENERACIÓN: Obtiene el estado de generación de imágenes para recetas IA
    """
    user_uid = get_jwt_identity()
    print(f"🎨 [GENERATION IMAGES STATUS] Task: {task_id}, User: {user_uid}")

    try:
        task_status = async_task_service.get_task_status(task_id)
        if not task_status:
            return jsonify({"error": "Tarea de imágenes no encontrada"}), 404

        task = AsyncTaskORM.query.filter_by(task_id=task_id).first()
        if not task or task.user_uid != user_uid:
            return jsonify({"error": "No tienes permiso para ver esta tarea"}), 403

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
        print(f"🚨 ERROR EN GENERATION IMAGES STATUS: {str(e)}")
        return jsonify({
            "error": str(e),
            "error_type": str(type(e).__name__)
        }), 500


@generation_bp.route("/<generation_id>/images", methods=["GET"])
@jwt_required()
def get_generation_images(generation_id):
    """
    🖼️ OBTENER IMÁGENES DE GENERACIÓN: Devuelve recetas generadas con sus imágenes actualizadas
    """
    user_uid = get_jwt_identity()
    print(f"🖼️ [GET GENERATION IMAGES] Generation: {generation_id}, User: {user_uid}")

    try:
        generation_repository = make_generation_repository(db)
        generation = generation_repository.find_by_uid(generation_id)

        if not generation:
            return jsonify({"error": "Generación no encontrada"}), 404

        if generation.user_uid != user_uid:
            return jsonify({"error": "No tienes permiso para ver esta generación"}), 403

        recipes = generation.raw_result.get('generated_recipes', [])
        images_ready = all(
            recipe.get('image_path') is not None and
            recipe.get('image_status') == 'ready'
            for recipe in recipes
        )

        response = {
            "generation_id": generation_id,
            "recipes": recipes,
            "images_ready": images_ready,
            "total_recipes": len(recipes),
            "images_generated": sum(1 for r in recipes if r.get('image_path') and r.get('image_status') == 'ready'),
            "last_updated": generation.generated_at.isoformat()
        }

        response['message'] = "✅ Todas las imágenes están listas" if images_ready else "⏳ Algunas imágenes aún se están generando"
        return jsonify(response), 200

    except Exception as e:
        print(f"🚨 ERROR EN GET GENERATION IMAGES: {str(e)}")
        return jsonify({
            "error": str(e),
            "error_type": str(type(e).__name__)
        }), 500
