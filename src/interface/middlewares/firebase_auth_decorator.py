import firebase_admin.auth # type: ignore
import firebase_admin
from firebase_admin import credentials
from flask import request, jsonify, g
from functools import wraps
from src.shared.exceptions.custom import UnauthorizedAccessException 
from src.config.config import Config
from pathlib import Path

def verify_firebase_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Asegurar que Firebase está inicializado
        if not firebase_admin._apps:
            try:
                cred_path = Path(Config.FIREBASE_CREDENTIALS_PATH).resolve()
                if not cred_path.exists():
                    print(f"🚨 ERROR: No se encontró el archivo de credenciales en {cred_path}")
                    return jsonify({"error": "Firebase configuration error"}), 500
                
                cred = credentials.Certificate(str(cred_path))
                firebase_admin.initialize_app(cred)
                print(f"✅ Firebase Admin inicializado desde {cred_path}")
            except Exception as init_error:
                print(f"🚨 ERROR inicializando Firebase: {init_error}")
                return jsonify({"error": "Firebase initialization failed"}), 500

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authorization header is missing or invalid"}), 401

        id_token = auth_header.split('Bearer ')[1]
        if not id_token:
            return jsonify({"error": "Firebase ID token is missing"}), 401

        print(f"🔍 FIREBASE DEBUG: Verificando token...")
        print(f"🔍 Token preview: {id_token[:50]}...")

        try:
            decoded_token = firebase_admin.auth.verify_id_token(id_token)
            print(f"✅ Token verificado exitosamente: UID={decoded_token.get('uid')}")
            print(f"✅ Token data: {decoded_token}")
            
            g.firebase_user_uid = decoded_token.get('uid')
            g.firebase_user = decoded_token
            if not g.firebase_user_uid:
                raise firebase_admin.auth.InvalidIdTokenError("UID not found in token.")
        except firebase_admin.auth.ExpiredIdTokenError as e:
            print(f"❌ Token expirado: {e}")
            return jsonify({"error": "Firebase ID token has expired"}), 401
        except firebase_admin.auth.RevokedIdTokenError as e:
            print(f"❌ Token revocado: {e}")
            return jsonify({"error": "Firebase ID token has been revoked"}), 401
        except firebase_admin.auth.InvalidIdTokenError as e:
            print(f"❌ Token inválido: {e}")
            return jsonify({"error": f"Invalid Firebase ID token"}), 401 # Avoid leaking too much detail
        except Exception as e:
            print(f"🚨 ERROR inesperado en verificación: {type(e).__name__}: {e}")
            return jsonify({"error": "Token verification failed"}), 401
        
        return f(*args, **kwargs)
    return decorated_function 