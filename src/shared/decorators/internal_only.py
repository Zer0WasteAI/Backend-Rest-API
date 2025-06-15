from flask import request, jsonify, current_app
from functools import wraps

def internal_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        secret = request.headers.get("X-Internal-Secret")
        if secret != current_app.config.get("INTERNAL_SECRET_KEY"):
            return jsonify({"error": "No autorizado"}), 403
        return func(*args, **kwargs)
    return wrapper