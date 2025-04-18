from flasgger import swag_from
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.infrastructure.db.schemas.profile_user_schema import ProfileUser

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
@swag_from(
    {
        'tags': ['User'],
        'security': [{"Bearer": []}],
        'responses': {
            200: {
                'description': 'Perfil de usuario obtenido exitosamente',
                'examples': {
                    'application/json': {
                        "uid": "123456789",
                        "name": "Juan Perez",
                        "phone": "+1234567890",
                        "photo_url": "https://example.com/photo.jpg",
                        "prefs": ["vegetarian", "gluten-free"]
                    }
                }
            },
            404: {
                'description': 'Perfil no encontrado'
            }
        }
    }
)
def get_user_profile():
    uid = get_jwt_identity()
    print('uid', uid)
    profile = ProfileUser.query.filter_by(uid=uid).first()
    if not profile:
        return jsonify({"message": "Perfil no encontrado"}), 404

    return jsonify({
        "uid": profile.uid,
        "name": profile.name,
        "phone": profile.phone,
        "photo_url": profile.photo_url,
        "prefs": profile.prefs
    }), 200
