from flasgger import swag_from
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.infrastructure.db.schemas.profile_user_schema import ProfileUser
from src.application.factories.auth_usecase_factory import make_profile_repository, make_firestore_profile_service
from src.infrastructure.security.rate_limiter import api_rate_limit
from src.infrastructure.security.security_logger import security_logger, SecurityEventType
from src.infrastructure.optimization.cache_service import cache_user_data

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
@api_rate_limit
@cache_user_data('user_profile', timeout=600)  # 🚀 Cache: 10 min for user profile data
@swag_from(
    {
        'tags': ['User'],
        'security': [{'Bearer': []}],
        'responses': {
            200: {
                'description': 'Perfil de usuario obtenido exitosamente desde Firestore',
                'examples': {
                    'application/json': {
                        "uid": "00HkiYIBxoVGnIZQQ76S7dbM52E3",
                        "displayName": "Carlos Primo",
                        "email": "carlos@gm.co",
                        "photoURL": None,
                        "emailVerified": True,
                        "authProvider": "password",
                        "language": "es",
                        "cookingLevel": "intermediate",
                        "measurementUnit": "metric",
                        "allergies": [],
                        "allergyItems": [],
                        "preferredFoodTypes": [],
                        "specialDietItems": [],
                        "favoriteRecipes": [],
                        "initialPreferencesCompleted": True,
                        "createdAt": "2025-05-23T08:16:24Z",
                        "lastLoginAt": "2025-05-23T08:16:25Z"
                    }
                }
            },
            404: {
                'description': 'Perfil no encontrado'
            },
            429: {
                'description': 'Demasiadas solicitudes'
            }
        }
    }
)
def get_user_profile():
    try:
        uid = get_jwt_identity()
        
        # Usar Firestore como fuente principal
        firestore_service = make_firestore_profile_service()
        profile = firestore_service.get_profile(uid)
        
        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        # Opcional: Sincronizar con MySQL para caché
        try:
            mysql_profile_repo = make_profile_repository()
            firestore_service.sync_with_mysql(uid, mysql_profile_repo)
        except Exception as sync_error:
            # No fallar si hay error en sincronización
            security_logger.log_security_event(
                SecurityEventType.AUTHENTICATION_FAILED,
                {"endpoint": "get_user_profile", "reason": "mysql_sync_failed", "error": str(sync_error)}
            )

        return jsonify(profile), 200
        
    except Exception as e:

        
        error_details = {

        
            "error_type": type(e).__name__,

        
            "error_message": str(e),

        
            "traceback": str(e.__traceback__.tb_frame.f_code.co_filename) + ":" + str(e.__traceback__.tb_lineno) if e.__traceback__ else "No traceback"

        
        }

        
        

        
        # Log the detailed error

        
        print(f"ERROR: {error_details}")

        
        

        security_logger.log_security_event(
            SecurityEventType.AUTHENTICATION_FAILED,
            {"endpoint": "get_user_profile", "reason": "firestore_access_failed", "error": str(e)}
        )
        return jsonify({"error": "Failed to retrieve profile", "details": error_details}), 500

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
@api_rate_limit
@swag_from(
    {
        'tags': ['User'],
        'security': [{'Bearer': []}],
        'summary': 'Actualizar perfil de usuario en Firestore',
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'required': True,
                'schema': {
                    'type': 'object',
                    'properties': {
                        'displayName': {'type': 'string', 'description': 'Nombre completo del usuario'},
                        'name': {'type': 'string', 'description': 'Alias para displayName (compatibilidad)'},
                        'photoURL': {'type': 'string', 'description': 'URL de la foto de perfil'},
                        'photo_url': {'type': 'string', 'description': 'Alias para photoURL (compatibilidad)'},
                        'language': {'type': 'string', 'enum': ['es', 'en'], 'description': 'Idioma preferido'},
                        'cookingLevel': {'type': 'string', 'enum': ['beginner', 'intermediate', 'advanced'], 'description': 'Nivel de cocina'},
                        'measurementUnit': {'type': 'string', 'enum': ['metric', 'imperial'], 'description': 'Sistema de medidas'},
                        'allergies': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Lista de alergias'},
                        'allergyItems': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Items específicos de alergia'},
                        'preferredFoodTypes': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Tipos de comida preferidos'},
                        'specialDietItems': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Items de dieta especial'},
                        'favoriteRecipes': {'type': 'array', 'items': {'type': 'string'}, 'description': 'IDs de recetas favoritas'},
                        'initialPreferencesCompleted': {'type': 'boolean', 'description': 'Si completó preferencias iniciales'},
                        'prefs': {
                            'type': 'object',
                            'description': 'Objeto con preferencias (para compatibilidad con versión anterior)'
                        }
                    }
                }
            }
        ],
        'responses': {
            200: {'description': 'Perfil actualizado exitosamente en Firestore'},
            400: {'description': 'Datos de entrada inválidos'},
            404: {'description': 'Perfil no encontrado'},
            500: {'description': 'Error al actualizar perfil'}
        }
    }
)
def update_user_profile():
    try:
        uid = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify({"message": "No input data provided"}), 400

        # Usar Firestore como fuente principal
        firestore_service = make_firestore_profile_service()
        
        # Actualizar en Firestore
        updated_profile = firestore_service.update_profile(uid, data)
        
        if not updated_profile:
            return jsonify({"message": "Perfil no encontrado o error al actualizar"}), 404

        # Opcional: Sincronizar con MySQL para caché
        try:
            mysql_profile_repo = make_profile_repository()
            firestore_service.sync_with_mysql(uid, mysql_profile_repo)
        except Exception as sync_error:
            # No fallar si hay error en sincronización
            security_logger.log_security_event(
                SecurityEventType.AUTHENTICATION_FAILED,
                {"endpoint": "update_user_profile", "reason": "mysql_sync_failed", "error": str(sync_error)}
            )

        return jsonify({
            "message": "Perfil actualizado exitosamente",
            "profile": updated_profile
        }), 200

    except Exception as e:


        error_details = {


            "error_type": type(e).__name__,


            "error_message": str(e),


            "traceback": str(e.__traceback__.tb_frame.f_code.co_filename) + ":" + str(e.__traceback__.tb_lineno) if e.__traceback__ else "No traceback"


        }


        


        # Log the detailed error


        print(f"ERROR: {error_details}")


        

        security_logger.log_security_event(
            SecurityEventType.AUTHENTICATION_FAILED,
            {"endpoint": "update_user_profile", "reason": "firestore_update_failed", "error": str(e)}
        )
        return jsonify({"error": "Failed to update profile", "details": error_details}), 500
