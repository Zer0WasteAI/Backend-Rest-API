from flask import Flask
from functools import wraps

def add_security_headers(app: Flask):
    """Configura headers de seguridad para toda la aplicación"""
    
    @app.after_request
    def set_security_headers(response):
        # Prevenir XSS
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HSTS - HTTPS estricto
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # CSP - Content Security Policy básica
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response.headers['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=(), "
            "vibrate=(), "
            "fullscreen=()"
        )
        
        # Eliminar headers que revelan información del servidor
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)
        
        return response

def secure_endpoint(f):
    """Decorador para endpoints que requieren validación adicional de seguridad"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Aquí se pueden agregar validaciones adicionales específicas
        return f(*args, **kwargs)
    return decorated_function 