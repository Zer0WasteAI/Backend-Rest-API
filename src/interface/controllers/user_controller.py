from flasgger import swag_from
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.infrastructure.db.schemas.profile_user_schema import ProfileUser
from src.application.factories.auth_usecase_factory import make_profile_repository
from src.infrastructure.security.rate_limiter import api_rate_limit
from src.infrastructure.security.security_logger import security_logger, SecurityEventType

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
@api_rate_limit
@swag_from(
    {
        'tags': ['User'],
        'security': [{'Bearer': []}],
        'responses': {
            200: {
                'description': 'Perfil de usuario obtenido exitosamente',
                'examples': {
                    'application/json': {
                        "uid": "123456789",
                        "name": "Juan Perez",
                        "phone": "+1234567890",
                        "photo_url": "https://example.com/photo.jpg",
                        "prefs": { 
                            "cookingLevel": "intermediate",
                            "language": "es",
                            "allergies": ["nuts"]
                         }
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
        profile_repo = make_profile_repository()
        profile = profile_repo.find_by_uid(uid)
        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        return jsonify({
            "uid": profile.uid,
            "name": profile.name,
            "phone": profile.phone,
            "photo_url": profile.photo_url,
            "prefs": profile.prefs
        }), 200
        
    except Exception as e:
        security_logger.log_security_event(
            SecurityEventType.AUTHENTICATION_FAILED,
            {"endpoint": "get_user_profile", "reason": "profile_access_failed"}
        )
        return jsonify({"error": "Failed to retrieve profile"}), 500

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
@swag_from(
    {
        'tags': ['User'],
        'security': [{'Bearer': []}],
        'summary': 'Actualizar perfil de usuario',
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'required': True,
                'schema': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'phone': {'type': 'string'},
                        'photo_url': {'type': 'string'},
                        'prefs': {
                            'type': 'object',
                            'description': 'Objeto JSON con las preferencias del usuario (cookingLevel, allergies, language, etc.)'
                        }
                    }
                }
            }
        ],
        'responses': {
            200: {'description': 'Perfil actualizado exitosamente'},
            400: {'description': 'Datos de entrada inválidos'},
            404: {'description': 'Perfil no encontrado'}
        }
    }
)
def update_user_profile():
    uid = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"message": "No input data provided"}), 400

    profile_repo = make_profile_repository()
    
    profile_data_to_update = {}
    if 'name' in data:
        profile_data_to_update['name'] = data.pop('name')
    if 'phone' in data:
        profile_data_to_update['phone'] = data.pop('phone')
    if 'photo_url' in data:
        profile_data_to_update['photo_url'] = data.pop('photo_url')
    
    if 'prefs' in data:
        if isinstance(data['prefs'], dict):
            profile_data_to_update['prefs'] = data['prefs']
        else:
            return jsonify({"message": "'prefs' must be an object"}), 400
    elif data:
        profile_data_to_update['prefs'] = data

    if not profile_data_to_update:
         return jsonify({"message": "No fields to update provided"}), 400

    updated_profile = profile_repo.update(uid, profile_data_to_update)

    if not updated_profile:
        return jsonify({"message": "Perfil no encontrado o error al actualizar"}), 404

    return jsonify({
        "message": "Perfil actualizado exitosamente",
        "profile": {
            "uid": updated_profile.uid,
            "name": updated_profile.name,
            "phone": updated_profile.phone,
            "photo_url": updated_profile.photo_url,
            "prefs": updated_profile.prefs
        }
    }), 200
