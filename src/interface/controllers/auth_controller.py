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
@swag_from({
    'tags': ['Auth'],
    'summary': 'Debug de configuración Firebase (desarrollo)',
    'description': '''
Endpoint de debug para verificar la configuración de Firebase durante desarrollo.

⚠️ **Solo para desarrollo**: Este endpoint se debe deshabilitar en producción.

### Información Proporcionada:
- Estado de inicialización de Firebase
- Validación de archivos de credenciales
- Configuración de Storage Bucket
- Project ID y Client Email
- Errores de configuración si existen

### Casos de Uso:
- Verificar configuración durante desarrollo
- Diagnosticar problemas de conexión con Firebase
- Validar archivos de credenciales
- Debuggear problemas de autenticación

### Configuración Requerida:
- `FIREBASE_CREDENTIALS_PATH`: Ruta al archivo de credenciales JSON
- `FIREBASE_STORAGE_BUCKET`: Nombre del bucket de Firebase Storage
    ''',
    'responses': {
        200: {
            'description': 'Información de debug de Firebase',
            'examples': {
                'application/json': {
                    "firebase_apps": 1,
                    "credentials_path": "/path/to/firebase-credentials.json",
                    "storage_bucket": "zerowasteai-12345.appspot.com",
                    "credentials_exists": True,
                    "credentials_path_resolved": "/absolute/path/to/firebase-credentials.json",
                    "project_id": "zerowasteai-12345",
                    "client_email": "firebase-adminsdk-abc123@zerowasteai-12345.iam.gserviceaccount.com"
                }
            }
        },
        500: {
            'description': 'Error de configuración Firebase',
            'examples': {
                'application/json': {
                    "firebase_apps": 0,
                    "credentials_path": "/path/to/firebase-credentials.json",
                    "credentials_exists": False,
                    "error": "Firebase credentials file not found"
                }
            }
        }
    }
})
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
    'summary': 'Renovación de tokens JWT con rotación segura',
    'description': '''
Renueva tokens JWT implementando rotación segura y detección de reutilización de tokens.

### Características de Seguridad:
- **Rotación de Tokens**: El refresh token anterior se invalida automáticamente
- **Detección de Reutilización**: Detecta intentos de reutilizar tokens expirados
- **Rate Limiting**: Máximo 10 renovaciones por minuto

### Flujo de Renovación:
1. Cliente envía refresh token válido en Authorization header
2. Sistema valida el token y verifica que no esté en blacklist
3. Se genera nuevo par de tokens (access + refresh)
4. El refresh token anterior se marca como usado/invalidado
5. Se retornan los nuevos tokens

### Cuándo Usar:
- Cuando el access token expira (normalmente cada 1 hora)
- Antes de hacer requests importantes si el token está cerca de expirar
- No usar si el usuario cerró sesión (tokens invalidados)

⚠️ **Importante**: Cada refresh token solo puede usarse una vez.
    ''',
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Refresh Token JWT. Formato: Bearer <refresh_token>',
            'example': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJI...'
        }
    ],
    'responses': {
        200: {
            'description': 'Tokens renovados exitosamente',
            'examples': {
                'application/json': {
                    "message": "Tokens refreshed successfully",
                    "tokens": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJI...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJI...",
                        "token_type": "Bearer",
                        "expires_in": 3600
                    },
                    "rotated": True,
                    "previous_token_invalidated": True
                }
            }
        },
        401: {
            'description': 'Refresh token inválido, expirado o ya usado',
            'examples': {
                'application/json': {
                    "error": "Invalid or expired token",
                    "details": "Refresh token has been used or revoked"
                }
            }
        },
        429: {
            'description': 'Rate limit excedido - demasiadas renovaciones',
            'examples': {
                'application/json': {
                    "error": "Too many refresh attempts",
                    "retry_after": 60,
                    "limit": "10 per minute"
                }
            }
        },
        500: {
            'description': 'Error interno durante renovación de tokens',
            'examples': {
                'application/json': {
                    "error": "Token refresh failed",
                    "details": "Internal error during token generation"
                }
            }
        }
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
    'description': '''
Cierra sesión del usuario invalidando todos los tokens JWT activos de forma segura.

### Proceso de Logout:
1. Invalida el token actual usado en la request
2. Invalida todos los refresh tokens del usuario
3. Añade tokens a blacklist para prevenir reutilización
4. Registra evento de logout en logs de seguridad

### Efectos del Logout:
- **Todos los dispositivos**: Se cierran todas las sesiones activas del usuario
- **Tokens Invalidados**: Ningún token anterior funcionará después del logout
- **Nuevo Login Requerido**: Usuario debe autenticarse nuevamente con Firebase

### Cuándo Usar:
- Cuando el usuario decide cerrar sesión voluntariamente
- En cambio de cuenta o usuario
- Por seguridad si se sospecha compromiso de tokens
- Al desinstalar la aplicación (opcional)

⚠️ **Nota**: Después del logout, todos los tokens JWT del usuario quedan inválidos.
    ''',
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Access Token JWT válido. Formato: Bearer <access_token>',
            'example': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJI...'
        }
    ],
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Sesión cerrada exitosamente',
            'examples': {
                'application/json': {
                    "message": "Logout successful",
                    "logged_out_at": "2024-01-15T10:30:00Z",
                    "tokens_invalidated": True,
                    "all_sessions_closed": True
                }
            }
        },
        401: {
            'description': 'Token de acceso inválido o expirado',
            'examples': {
                'application/json': {
                    "error": "Invalid access token",
                    "details": "Token expired or malformed"
                }
            }
        },
        429: {
            'description': 'Rate limit excedido',
            'examples': {
                'application/json': {
                    "error": "Too many requests",
                    "retry_after": 60
                }
            }
        },
        500: {
            'description': 'Error interno durante logout',
            'examples': {
                'application/json': {
                    "error": "Logout failed",
                    "details": "Internal server error"
                }
            }
        }
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
    'summary': 'Autenticación con Firebase ID Token',
    'description': '''
Autentica usuarios usando Firebase ID Token y sincroniza datos del usuario de forma segura.

Este endpoint:
- Valida el Firebase ID Token
- Crea o actualiza el usuario en la base de datos local
- Genera tokens JWT internos para usar en la API
- Sincroniza el perfil con Firestore
- Maneja usuarios anónimos y con múltiples proveedores

### Flujo de Autenticación:
1. Cliente obtiene Firebase ID Token (tras autenticarse con Firebase)
2. Cliente envía token en header Authorization: Bearer <firebase_token>
3. API valida token con Firebase
4. API retorna tokens JWT internos para uso posterior

### Proveedores Soportados:
- Email/Password (password)
- Google (google.com)  
- Facebook (facebook.com)
- Anonymous (anonymous)
- Custom tokens (custom)

### Rate Limiting:
- Máximo 5 intentos por minuto por IP
    ''',
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Firebase ID Token. Formato: Bearer <firebase_id_token>',
            'example': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6...'
        }
    ],
    'responses': {
        200: {
            'description': 'Autenticación exitosa, usuario sincronizado, tokens JWT retornados',
            'examples': {
                'application/json': {
                    "message": "Authentication successful",
                    "user": {
                        "uid": "firebase_user_uid_123",
                        "email": "usuario@ejemplo.com",
                        "name": "Juan Pérez",
                        "picture": "https://lh3.googleusercontent.com/...",
                        "email_verified": True,
                        "sign_in_provider": "google.com"
                    },
                    "tokens": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJI...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJI...",
                        "token_type": "Bearer",
                        "expires_in": 3600
                    },
                    "profile_synced": True
                }
            }
        },
        400: {
            'description': 'Datos de request inválidos o Firebase token malformado',
            'examples': {
                'application/json': {
                    "error": "Authentication failed",
                    "details": "Invalid Firebase token format"
                }
            }
        },
        401: {
            'description': 'Firebase ID Token inválido o expirado',
            'examples': {
                'application/json': {
                    "error": "Invalid or expired Firebase token",
                    "details": "Token signature verification failed"
                }
            }
        },
        429: {
            'description': 'Demasiados intentos de autenticación - rate limit excedido',
            'examples': {
                'application/json': {
                    "error": "Too many authentication attempts",
                    "retry_after": 60
                }
            }
        },
        500: {
            'description': 'Error interno del servidor durante autenticación',
            'examples': {
                'application/json': {
                    "error": "Internal server error",
                    "details": "Failed to sync user profile"
                }
            }
        }
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
        # Aceptar tanto 'anonymous' como 'custom' para usuarios anónimos (custom tokens se convierten en 'custom')
        anonymous_providers = ["anonymous", "custom"]
        if not email and sign_in_provider not in anonymous_providers:
            security_logger.log_security_event(
                SecurityEventType.AUTHENTICATION_FAILED,
                {"reason": "missing_email", "endpoint": "firebase-signin", "uid": firebase_uid, "provider": sign_in_provider}
            )
            return jsonify({"error": "Authentication failed"}), 400
        
        # Para usuarios anónimos, usar NULL en lugar de string vacío para evitar duplicates
        if not email and sign_in_provider in anonymous_providers:
            email = None

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
            if email and sign_in_provider not in anonymous_providers:
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
                "email": email or "",  # Firestore usa string vacío en lugar de NULL
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
                "email": final_user.email or "",  # Convertir NULL a string vacío para response
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
