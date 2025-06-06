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
    make_profile_repository,
    make_firestore_profile_service
)
from src.interface.middlewares.firebase_auth_decorator import verify_firebase_token
from src.infrastructure.security.rate_limiter import auth_rate_limit, refresh_rate_limit, api_rate_limit
from src.infrastructure.security.security_logger import security_logger, SecurityEventType
from src.shared.exceptions.custom import InvalidTokenException
from datetime import datetime, timezone
import uuid
import traceback

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/firebase-debug", methods=["GET"])
def firebase_debug():
    """Endpoint de debug para verificar la configuración de Firebase"""
    import firebase_admin
    from pathlib import Path
    
    debug_info = {
        "firebase_apps": len(firebase_admin._apps),
        "credentials_path": Config.FIREBASE_CREDENTIALS_PATH,
        "storage_bucket": Config.FIREBASE_STORAGE_BUCKET,
        "credentials_exists": False,
        "project_id": None
    }
    
    try:
        cred_path = Path(Config.FIREBASE_CREDENTIALS_PATH).resolve()
        debug_info["credentials_exists"] = cred_path.exists()
        debug_info["credentials_path_resolved"] = str(cred_path)
        
        if cred_path.exists():
            import json
            with open(cred_path, 'r') as f:
                creds_data = json.load(f)
                debug_info["project_id"] = creds_data.get("project_id")
                debug_info["client_email"] = creds_data.get("client_email")
        
    except Exception as e:
        debug_info["error"] = str(e)
    
    return jsonify(debug_info), 200

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
@refresh_rate_limit
@swag_from({
    'tags': ['Auth'],
    'security': [{"Bearer": []}],
    'summary': 'Renovación de token JWT con rotación',
    'description': 'Renueva tokens implementando rotación segura y detección de reutilización',
    'responses': {
        200: {'description': 'Nuevo token generado exitosamente'},
        401: {'description': 'Token inválido o revocado'},
        429: {'description': 'Demasiadas solicitudes - rate limit excedido'}
    }
})
def refresh_token():
    try:
        current_user = get_jwt_identity()
        use_case = make_refresh_token_use_case()
        result = use_case.execute(identity=current_user)
        
        # Log éxito en rotación
        security_logger.log_security_event(
            SecurityEventType.REFRESH_TOKEN_ROTATED,
            {"user_uid": current_user, "status": "success"}
        )
        
        return jsonify(result), 200
        
    except InvalidTokenException as e:
        security_logger.log_security_event(
            SecurityEventType.INVALID_TOKEN_ATTEMPT,
            {"endpoint": "refresh", "reason": "token_validation_failed"}
        )
        return jsonify({"error": "Invalid or expired token"}), 401
        
    except Exception as e:
        security_logger.log_security_event(
            SecurityEventType.AUTHENTICATION_FAILED,
            {"endpoint": "refresh", "reason": "unexpected_error"}
        )
        return jsonify({"error": "Authentication failed"}), 401

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
@api_rate_limit
@swag_from({
    'tags': ['Auth'],
    'summary': 'Cerrar sesión (logout) seguro',
    'description': 'Cierra sesión invalidando todos los tokens del usuario',
    'security': [{'Bearer': []}],
    'responses': {
        200: {'description': 'Sesión cerrada exitosamente'},
        401: {'description': 'Token inválido'},
        429: {'description': 'Demasiadas solicitudes'}
    }
})
def logout():
    try:
        uid = get_jwt_identity()
        use_case = make_logout_use_case()
        result = use_case.execute(uid)
        
        # Log logout exitoso
        security_logger.log_authentication_attempt(uid, success=True, reason="logout")
        
        return jsonify(result), 200
        
    except Exception as e:
        security_logger.log_security_event(
            SecurityEventType.AUTHENTICATION_FAILED,
            {"endpoint": "logout", "reason": "logout_failed"}
        )
        return jsonify({"error": "Logout failed"}), 500

@auth_bp.route("/firebase-signin", methods=["POST"])
@verify_firebase_token
@auth_rate_limit
@swag_from({
    'tags': ['Auth'],
    'summary': 'Sign in with Firebase ID Token and sync user',
    'description': 'Autentica con Firebase y sincroniza datos del usuario de forma segura',
    'security': [{"Bearer": []}],
    'responses': {
        200: {'description': 'Firebase sign-in successful, user synced, app tokens returned'},
        400: {'description': 'Invalid request data'},
        401: {'description': 'Invalid or missing Firebase ID Token'},
        429: {'description': 'Too many authentication attempts'}
    }
})
def firebase_signin():
    try:
        firebase_user_data = g.firebase_user
        firebase_uid = firebase_user_data.get("uid")
        email = firebase_user_data.get("email")
        name = firebase_user_data.get("name", "")
        picture = firebase_user_data.get("picture", "")
        email_verified = firebase_user_data.get("email_verified", False)
        # Obtener el proveedor de inicio de sesión real de Firebase
        firebase_info = firebase_user_data.get("firebase", {})
        sign_in_provider = firebase_info.get("sign_in_provider", "unknown") # Por defecto 'unknown' si no está presente

        print(f"🔍 FIREBASE SIGNIN DEBUG:")
        print(f"🔍 UID: {firebase_uid}")
        print(f"🔍 Email: {email}")
        print(f"🔍 Provider: {sign_in_provider}")
        print(f"🔍 Name: {name}")
        print(f"🔍 Email verified: {email_verified}")

        if not firebase_uid:
            security_logger.log_security_event(
                SecurityEventType.AUTHENTICATION_FAILED,
                {"reason": "missing_firebase_uid", "endpoint": "firebase-signin"}
            )
            return jsonify({"error": "Authentication failed"}), 400
        
        # Para usuarios anónimos, email puede ser None
        if not email and sign_in_provider != "anonymous":
            security_logger.log_security_event(
                SecurityEventType.AUTHENTICATION_FAILED,
                {"reason": "missing_email", "endpoint": "firebase-signin", "uid": firebase_uid, "provider": sign_in_provider}
            )
            return jsonify({"error": "Authentication failed"}), 400
        
        # Para usuarios anónimos, usar email vacío por defecto
        if not email and sign_in_provider == "anonymous":
            email = ""

        user_repo = make_user_repository()
        auth_repo = make_auth_repository()
        profile_repo = make_profile_repository()
        jwt_service = make_jwt_service()

        # Verificar si el usuario existe por UID
        user = user_repo.find_by_uid(firebase_uid)
        
        if user:
            # Usuario encontrado por UID - actualizar información si es necesario
            if user.email != email:
                user_repo.update(firebase_uid, {"email": email, "updated_at": datetime.now(timezone.utc)})
                user.email = email
            
            # Verificar si ya existe auth_users para este UID y proveedor
            auth_entry = auth_repo.find_by_uid_and_provider(firebase_uid, sign_in_provider)
            if not auth_entry:
                auth_repo.create({
                    "uid": firebase_uid,
                    "auth_provider": sign_in_provider,
                    "is_verified": email_verified,
                    "is_active": True
                })
            else:
                # Actualizar la entrada existente si es necesario
                if auth_entry.is_verified != email_verified:
                    auth_repo.update(firebase_uid, sign_in_provider, {"is_verified": email_verified})
            
            # Verificar/crear profile si es necesario
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
                # Actualizar profile si es necesario
                profile_update_data = {}
                if profile.name != name:
                    profile_update_data["name"] = name
                if profile.photo_url != picture:
                    profile_update_data["photo_url"] = picture
                
                if profile_update_data:
                    profile_repo.update(firebase_uid, profile_update_data)
        
        # Si no existe por UID, verificar si existe por email (solo para usuarios no anónimos)
        elif not user:
            # Verificar si ya existe un usuario con este email (skip para usuarios anónimos)
            existing_user_by_email = None
            if email and sign_in_provider != "anonymous":
                existing_user_by_email = user_repo.find_by_email(email)
            
            if existing_user_by_email:
                # Usuario existe con mismo email pero diferente UID
                # Usar el usuario existente y su UID original, pero actualizar datos de Firebase
                user = existing_user_by_email
                firebase_uid = user.uid  # Usar el UID original del usuario existente
                
                # Actualizar información del usuario si es necesario
                if user.email != email:
                    user_repo.update(user.uid, {"email": email, "updated_at": datetime.now(timezone.utc)})
                
                # Verificar si ya existe auth_users para este UID y proveedor
                auth_entry = auth_repo.find_by_uid_and_provider(firebase_uid, sign_in_provider)
                if not auth_entry:
                    auth_repo.create({
                        "uid": firebase_uid,
                        "auth_provider": sign_in_provider,
                        "is_verified": email_verified,
                        "is_active": True
                    })
                else:
                    # Actualizar la entrada existente si es necesario
                    if auth_entry.is_verified != email_verified:
                        auth_repo.update(firebase_uid, sign_in_provider, {"is_verified": email_verified})
                
                # Verificar/crear profile si es necesario
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
                    # Actualizar profile si es necesario
                    profile_update_data = {}
                    if profile.name != name:
                        profile_update_data["name"] = name
                    if profile.photo_url != picture:
                        profile_update_data["photo_url"] = picture
                    
                    if profile_update_data:
                        profile_repo.update(firebase_uid, profile_update_data)
            else:
                # Usuario completamente nuevo
                user = user_repo.create({
                    "uid": firebase_uid,
                    "email": email,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                })

                auth_repo.create({
                    "uid": firebase_uid, 
                    "auth_provider": sign_in_provider,
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
                
                # Log nuevo usuario
                security_logger.log_security_event(
                    SecurityEventType.SUSPICIOUS_LOGIN,
                    {"reason": "new_user_creation", "uid": firebase_uid, "provider": sign_in_provider}
                )
        
        if user:
            # Usar el UID del usuario (original o nuevo)
            firebase_uid = user.uid
            
            # Usuario existe - solo actualizar email si es diferente
            if user.email != email:
                user_repo.update(firebase_uid, {"email": email, "updated_at": datetime.now(timezone.utc)})
                user.email = email

        app_tokens = jwt_service.create_tokens(identity=firebase_uid)

        # Obtener perfil completo desde Firestore (fuente de verdad)
        firestore_service = make_firestore_profile_service()
        firestore_profile = firestore_service.get_profile(firebase_uid)
        
        # Si no existe perfil en Firestore, crear uno básico con información de Firebase
        if not firestore_profile:
            print(f"🔍 Creando nuevo perfil en Firestore para UID: {firebase_uid}")
            basic_profile_data = {
                "displayName": name,
                "email": email,
                "photoURL": picture,
                "emailVerified": email_verified,
                "authProvider": sign_in_provider,
                "language": "es",  # Por defecto
                "cookingLevel": "beginner",  # Por defecto
                "measurementUnit": "metric",  # Por defecto
                "allergies": [],
                "allergyItems": [],
                "preferredFoodTypes": [],
                "specialDietItems": [],
                "favoriteRecipes": [],
                "initialPreferencesCompleted": False
            }
            firestore_profile = firestore_service.create_profile(firebase_uid, basic_profile_data)
            print(f"✅ Perfil creado exitosamente en Firestore")
        
        # Sincronizar con MySQL para caché/performance
        try:
            mysql_profile_repo = make_profile_repository()
            firestore_service.sync_with_mysql(firebase_uid, mysql_profile_repo)
        except Exception as sync_error:
            # No fallar si hay error en sincronización, solo loguearlo
            print(f"⚠️ Warning: MySQL sync failed: {sync_error}")

        final_user = user_repo.find_by_uid(firebase_uid)
        
        # Log autenticación exitosa
        security_logger.log_authentication_attempt(
            firebase_uid, 
            success=True, 
            reason=f"firebase_signin_{sign_in_provider}"
        )

        return jsonify({
            **app_tokens,
            "user": {
                "uid": final_user.uid,
                "email": final_user.email,
                "name": firestore_profile.get("displayName", name),
                "photo_url": firestore_profile.get("photoURL", picture),
                "email_verified": email_verified
            },
            "profile": firestore_profile  # Incluir perfil completo desde Firestore
        }), 200
        
    except Exception as e:
        # Log más detallado para debug
        error_details = {
            "endpoint": "firebase-signin", 
            "reason": "unexpected_error", 
            "error": str(type(e).__name__),
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        security_logger.log_security_event(
            SecurityEventType.AUTHENTICATION_FAILED,
            error_details
        )
        
        # También imprimir el error completo
        print(f"🚨 ERROR EN FIREBASE-SIGNIN: {str(e)}")
        print(f"🚨 TRACEBACK: {traceback.format_exc()}")
        
        return jsonify({"error": "Authentication failed"}), 500
