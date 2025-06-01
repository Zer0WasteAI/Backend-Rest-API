from flask_jwt_extended import JWTManager
from src.infrastructure.db.token_security_repository import TokenSecurityRepository

def configure_jwt_callbacks(jwt_manager: JWTManager):
    """Configura todos los callbacks de seguridad para JWT"""
    token_security_repo = TokenSecurityRepository()
    
    @jwt_manager.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Verifica si un token está en la blacklist"""
        jti = jwt_payload.get('jti')
        if not jti:
            return True  # Si no tiene JTI, es inseguro
        return token_security_repo.is_token_blacklisted(jti)
    
    @jwt_manager.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Respuesta cuando un token está revocado"""
        return {"error": "Token has been revoked"}, 401
    
    @jwt_manager.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Respuesta cuando un token ha expirado"""
        return {"error": "Token has expired"}, 401
    
    @jwt_manager.invalid_token_loader
    def invalid_token_callback(error):
        """Respuesta cuando un token es inválido"""
        return {"error": "Invalid token"}, 401
    
    @jwt_manager.unauthorized_loader
    def missing_token_callback(error):
        """Respuesta cuando falta el token"""
        return {"error": "Authorization token is required"}, 401
    
    @jwt_manager.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        """Respuesta cuando se necesita un token fresco"""
        return {"error": "Fresh token required"}, 401 