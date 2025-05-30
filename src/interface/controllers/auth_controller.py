from flasgger import swag_from # type: ignore
from flask import Blueprint, request, jsonify, redirect, g
from flask_jwt_extended import get_jwt_identity, jwt_required # type: ignore

from src.config.config import Config

from src.application.factories.auth_usecase_factory import (
    make_logout_use_case,
    make_refresh_token_use_case,
    make_jwt_service,
    make_user_repository,
    make_auth_repository,
    make_profile_repository
)
from src.interface.middlewares.firebase_auth_decorator import verify_firebase_token
from datetime import datetime, timezone
import uuid

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
@swag_from({
    'tags': ['Auth'],
    'security': [{"Bearer": []}],
    'summary': 'Renovación de token JWT',
    'responses': {
        200: {'description': 'Nuevo token generado'}
    }
})
def refresh_token():
    current_user = get_jwt_identity()
    use_case = make_refresh_token_use_case()
    result = use_case.execute(identity=current_user)
    return jsonify(result), 200

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Auth'],
    'summary': 'Cerrar sesión (logout)',
    'security': [{'Bearer': []}],
    'responses': {
        200: {'description': 'Sesión cerrada'}
    }
})
def logout():
    uid = get_jwt_identity()
    use_case = make_logout_use_case()
    result = use_case.execute(uid)
    return jsonify(result), 200

@auth_bp.route("/firebase-signin", methods=["POST"])
@verify_firebase_token
@swag_from({
    'tags': ['Auth'],
    'summary': 'Sign in with Firebase ID Token and sync user',
    'security': [{"Bearer": []}],
    'responses': {
        200: {'description': 'Firebase sign-in successful, user synced, app tokens returned'},
        400: {'description': 'User data missing from Firebase token or other error'},
        401: {'description': 'Invalid or missing Firebase ID Token'}
    }
})
def firebase_signin():
    firebase_user_data = g.firebase_user
    firebase_uid = firebase_user_data.get("uid")
    email = firebase_user_data.get("email")
    name = firebase_user_data.get("name", "")
    picture = firebase_user_data.get("picture", "")
    email_verified = firebase_user_data.get("email_verified", False)
    # Obtener el proveedor de inicio de sesión real de Firebase
    firebase_info = firebase_user_data.get("firebase", {})
    sign_in_provider = firebase_info.get("sign_in_provider", "unknown") # Por defecto 'unknown' si no está presente

    if not firebase_uid:
        return jsonify({"error": "Firebase UID not found in token"}), 400
    
    if not email:
        return jsonify({"error": "Email not found in Firebase token"}), 400

    user_repo = make_user_repository()
    auth_repo = make_auth_repository()
    profile_repo = make_profile_repository()
    jwt_service = make_jwt_service()

    user = user_repo.find_by_uid(firebase_uid)

    if not user:
        user = user_repo.create({
            "uid": firebase_uid,
            "email": email,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

        auth_repo.create({
            "uid": firebase_uid, 
            "auth_provider": sign_in_provider, # Usar el proveedor real
            "is_verified": email_verified,
            "is_active": True
        })

        profile_repo.create({
            "uid": firebase_uid,
            "name": name,
            "phone": "",
            "photo_url": picture,
            "prefs": {}
        })
    else:
        if user.email != email:
            user_repo.update(firebase_uid, {"email": email, "updated_at": datetime.now(timezone.utc)})
            user.email = email
        
        auth_entry = auth_repo.find_by_uid_and_provider(firebase_uid, sign_in_provider) # Usar el proveedor real
        if not auth_entry:
            auth_repo.create({
                "uid": firebase_uid,
                "auth_provider": sign_in_provider, # Usar el proveedor real
                "is_verified": email_verified,
                "is_active": True
            })
        else: # Actualizar estado de verificación si cambió
            if auth_entry.is_verified != email_verified:
                 auth_repo.update(firebase_uid, sign_in_provider, {"is_verified": email_verified})

        profile = profile_repo.find_by_uid(firebase_uid)
        if not profile:
            profile_repo.create({
                "uid": firebase_uid,
                "name": name,
                "phone": "",
                "photo_url": picture,
                "prefs": {}
            })
        else:
            profile_update_data = {}
            if profile.name != name:
                profile_update_data["name"] = name
            if profile.photo_url != picture:
                profile_update_data["photo_url"] = picture
            
            if profile_update_data:
                profile_repo.update(firebase_uid, profile_update_data)

    app_tokens = jwt_service.create_tokens(identity=firebase_uid)

    final_profile = profile_repo.find_by_uid(firebase_uid)
    final_user = user_repo.find_by_uid(firebase_uid)

    return jsonify({
        **app_tokens,
        "user": {
            "uid": final_user.uid,
            "email": final_user.email,
            "name": final_profile.name if final_profile else name,
            "photo_url": final_profile.photo_url if final_profile else picture,
            "email_verified": email_verified
        }
    }), 200
