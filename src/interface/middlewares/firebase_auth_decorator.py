import firebase_admin.auth # type: ignore
from flask import request, jsonify, g
from functools import wraps
from src.shared.exceptions.custom import UnauthorizedAccessException 

def verify_firebase_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authorization header is missing or invalid"}), 401

        id_token = auth_header.split('Bearer ')[1]
        if not id_token:
            return jsonify({"error": "Firebase ID token is missing"}), 401

        try:
            decoded_token = firebase_admin.auth.verify_id_token(id_token)
            g.firebase_user_uid = decoded_token.get('uid')
            g.firebase_user = decoded_token
            if not g.firebase_user_uid:
                raise firebase_admin.auth.InvalidIdTokenError("UID not found in token.")
        except firebase_admin.auth.ExpiredIdTokenError:
            return jsonify({"error": "Firebase ID token has expired"}), 401
        except firebase_admin.auth.RevokedIdTokenError:
            return jsonify({"error": "Firebase ID token has been revoked"}), 401
        except firebase_admin.auth.InvalidIdTokenError as e:
            return jsonify({"error": f"Invalid Firebase ID token"}), 401 # Avoid leaking too much detail
        except Exception as e:
            return jsonify({"error": "Token verification failed"}), 401
        
        return f(*args, **kwargs)
    return decorated_function 