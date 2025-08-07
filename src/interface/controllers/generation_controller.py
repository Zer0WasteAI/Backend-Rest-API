from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from # type: ignore
from src.infrastructure.db.base import db
from src.application.factories.generation_usecase_factory import make_generation_repository
from src.infrastructure.async_tasks.async_task_service import async_task_service
from src.infrastructure.db.models.async_task_orm import AsyncTaskORM
from src.infrastructure.optimization.rate_limiter import smart_rate_limit

generation_bp = Blueprint("generation", __name__)

@generation_bp.route("/images/status/<task_id>", methods=["GET"])
@jwt_required()
@smart_rate_limit('data_read')  # 🛡️ Rate limit: 100 requests/min for status checks
@swag_from({
    'tags': ['Image Generation'],
    'summary': 'Verificar estado de generación de imagen',
    'description': '''
Verifica el estado actual de una tarea de generación de imagen ejecutándose de forma asíncrona.

### Información de Estado:
- **Estado actual**: pending, processing, completed, failed
- **Progreso**: Porcentaje de completitud (cuando disponible)
- **Tiempo estimado**: Tiempo restante aproximado
- **Detalles de error**: Información específica si la generación falló
- **Metadatos**: Información adicional sobre el proceso

### Estados Posibles:
- **pending**: Tarea en cola, esperando procesamiento
- **processing**: Generación de imagen en progreso
- **completed**: Imagen generada exitosamente
- **failed**: Error en la generación
- **expired**: Tarea expirada (más de 10 minutos)

### Casos de Uso:
- Polling del estado desde aplicaciones frontend
- Mostrar progreso al usuario durante generación
- Manejo de errores en generación de imágenes
- Implementación de retry logic automático
    ''',
    'parameters': [
        {
            'name': 'task_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'ID único de la tarea de generación de imagen',
            'example': 'img_gen_123456789'
        }
    ],
    'responses': {
        200: {
            'description': 'Estado de generación obtenido exitosamente',
            'examples': {
                'application/json': {
                    "task_id": "img_gen_123456789",
                    "status": "completed",
                    "progress": 100,
                    "estimated_remaining_time": 0,
                    "started_at": "2024-01-16T10:30:00Z",
                    "completed_at": "2024-01-16T10:32:45Z",
                    "processing_time": 165,
                    "result": {
                        "image_url": "https://storage.googleapis.com/bucket/generated_images/img_gen_123456789.jpg",
                        "image_path": "generated_images/img_gen_123456789.jpg",
                        "generation_method": "ai_enhanced",
                        "image_quality": "high",
                        "dimensions": {
                            "width": 1024,
                            "height": 1024
                        },
                        "file_size": 245760,
                        "format": "JPEG"
                    },
                    "generation_details": {
                        "recipe_name": "Pasta carbonara",
                        "style": "food_photography",
                        "enhancement_applied": True,
                        "quality_score": 0.92
                    }
                }
            }
        },
        202: {
            'description': 'Generación en proceso',
            'examples': {
                'application/json': {
                    "task_id": "img_gen_123456789",
                    "status": "processing",
                    "progress": 65,
                    "estimated_remaining_time": 45,
                    "started_at": "2024-01-16T10:30:00Z",
                    "current_step": "ai_generation",
                    "steps_completed": 2,
                    "total_steps": 3,
                    "message": "Generando imagen con IA, por favor espere..."
                }
            }
        },
        404: {
            'description': 'Tarea no encontrada',
            'examples': {
                'application/json': {
                    'error': 'Task not found',
                    'details': 'La tarea de generación no existe o ha expirado'
                }
            }
        },
        500: {
            'description': 'Error en el estado de generación',
            'examples': {
                'application/json': {
                    "task_id": "img_gen_123456789",
                    "status": "failed",  
                    "error": "AI service unavailable",
                    "error_details": "Error en el servicio de generación de imágenes con IA",
                    "failed_at": "2024-01-16T10:31:30Z",
                    "retry_possible": True,
                    "suggestions": [
                        "Intente nuevamente en unos minutos",
                        "Verifique que la descripción de la receta sea clara"
                    ]
                }
            }
        }
    }
})
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
@smart_rate_limit('data_read')  # 🛡️ Rate limit: 100 requests/min for status checks
@swag_from({
    'tags': ['Image Generation'],
    'summary': 'Obtener recetas generadas con imágenes actualizadas',
    'description': '''
Obtiene las recetas de una generación específica con el estado actualizado de sus imágenes generadas.

### Funcionalidad:
- **Recetas completas**: Retorna todas las recetas de la generación especificada
- **Estado de imágenes**: Información actualizada sobre el progreso de generación de imágenes
- **Datos enriquecidos**: Incluye URLs de imágenes cuando están disponibles
- **Metadatos de generación**: Información sobre el proceso y resultados

### Estados Posibles de Imágenes:
- **ready**: Imagen generada y disponible con URL
- **generating**: Imagen en proceso de generación
- **failed**: Error en la generación de imagen específica
- **pending**: Imagen en cola para generación

### Casos de Uso:
- Obtener recetas con imágenes después de completarse la generación asíncrona
- Verificar el estado final de una generación de recetas
- Mostrar resultados completos con imágenes en interfaces de usuario
- Integrar con sistemas de caché de imágenes
- Implementar galerías de recetas generadas

### Información Incluida:
- Recetas completas con ingredientes e instrucciones
- URLs de imágenes cuando están disponibles
- Estado de generación por receta
- Metadatos de la generación original
- Estadísticas de éxito de generación de imágenes
    ''',
    'parameters': [
        {
            'name': 'generation_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'ID único de la generación de recetas',
            'example': 'gen_abc123def456'
        }
    ],
    'responses': {
        200: {
            'description': 'Recetas con imágenes obtenidas exitosamente',
            'examples': {
                'application/json': {
                    "generation_id": "gen_abc123def456",
                    "recipes": [
                        {
                            "name": "Ensalada de Tomates Cherry con Queso",
                            "description": "Ensalada fresca y saludable aprovechando los tomates cherry del refrigerador",
                            "ingredients": [
                                {
                                    "name": "Tomates cherry",
                                    "quantity": 300,
                                    "unit": "gr",
                                    "available_in_inventory": True
                                },
                                {
                                    "name": "Queso manchego",
                                    "quantity": 100,
                                    "unit": "gr",
                                    "available_in_inventory": True
                                }
                            ],
                            "instructions": [
                                "Lavar y cortar los tomates cherry por la mitad",
                                "Cortar el queso en cubos pequeños",
                                "Mezclar en un bowl y aliñar con aceite de oliva"
                            ],
                            "prep_time": 10,
                            "difficulty": "easy",
                            "servings": 2,
                            "calories_per_serving": 180,
                            "image_path": "https://storage.googleapis.com/bucket/generated-images/ensalada-tomates-cherry-abc123.jpg",
                            "image_status": "ready",
                            "generated_at": "2024-01-16T10:30:00Z"
                        },
                        {
                            "name": "Pasta con Verduras",
                            "description": "Pasta nutritiva con verduras frescas del inventario",
                            "ingredients": [
                                {
                                    "name": "Pasta",
                                    "quantity": 200,
                                    "unit": "gr",
                                    "available_in_inventory": True
                                },
                                {
                                    "name": "Zucchini",
                                    "quantity": 150,
                                    "unit": "gr",
                                    "available_in_inventory": True
                                }
                            ],
                            "instructions": [
                                "Hervir agua con sal para la pasta",
                                "Cortar el zucchini en rodajas",
                                "Saltear las verduras y mezclar con pasta"
                            ],
                            "prep_time": 25,
                            "difficulty": "intermedio",
                            "servings": 3,
                            "calories_per_serving": 320,
                            "image_path": "https://storage.googleapis.com/bucket/generated-images/pasta-verduras-def456.jpg",
                            "image_status": "ready",
                            "generated_at": "2024-01-16T10:30:00Z"
                        }
                    ],
                    "images_ready": True,
                    "total_recipes": 2,
                    "images_generated": 2,
                    "generation_summary": {
                        "generated_at": "2024-01-16T10:30:00Z",
                        "generation_type": "inventory",
                        "user_uid": "firebase_user_123",
                        "processing_completed_at": "2024-01-16T10:32:45Z"
                    },
                    "image_generation_stats": {
                        "total_images_requested": 2,
                        "images_successfully_generated": 2,
                        "images_failed": 0,
                        "average_generation_time": 67.5,
                        "total_generation_time": 135
                    },
                    "last_updated": "2024-01-16T10:32:45Z",
                    "message": "✅ Todas las imágenes están listas"
                }
            }
        },
        200: {
            'description': 'Recetas obtenidas, algunas imágenes aún generándose',
            'examples': {
                'application/json': {
                    "generation_id": "gen_abc123def456",
                    "recipes": [
                        {
                            "name": "Ensalada de Tomates Cherry con Queso",
                            "image_path": "https://storage.googleapis.com/bucket/generated-images/ensalada-tomates-cherry-abc123.jpg",
                            "image_status": "ready"
                        },
                        {
                            "name": "Pasta con Verduras",
                            "image_path": None,
                            "image_status": "generating"
                        }
                    ],
                    "images_ready": False,
                    "total_recipes": 2,
                    "images_generated": 1,
                    "message": "⏳ Algunas imágenes aún se están generando"
                }
            }
        },
        404: {
            'description': 'Generación no encontrada',
            'examples': {
                'application/json': {
                    'error': 'Generación no encontrada',
                    'generation_id': 'gen_invalid123'
                }
            }
        },
        403: {
            'description': 'Sin permisos para ver esta generación',
            'examples': {
                'application/json': {
                    'error': 'No tienes permiso para ver esta generación',
                    'details': 'La generación pertenece a otro usuario'
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno del servidor'
        }
    }
})
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
