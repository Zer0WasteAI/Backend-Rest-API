from flask_jwt_extended import get_jwt_identity, get_jwt
from src.shared.exceptions.custom import InvalidTokenException

class LogoutUseCase:
    def __init__(self, auth_repository, jwt_service):
        self.auth_repository = auth_repository
        self.jwt_service = jwt_service

    def execute(self, uid: str):
        """Ejecuta logout seguro invalidando todos los tokens del usuario"""
        try:
            # Obtener información del token actual para logging
            current_token_claims = get_jwt()
            current_jti = current_token_claims.get('jti')
            
            # Invalidar todos los tokens del usuario
            revoked_count = self.jwt_service.revoke_all_user_tokens(uid, 'logout')
            
            # Mantener compatibilidad con el méto/do anterior (aunque no haga nada real)
            self.auth_repository.update_jwt_token(uid, None)
            
            return {
                "message": "Sesión cerrada exitosamente",
                "tokens_revoked": revoked_count,
                "status": "success"
            }
            
        except Exception as e:
            # En caso de error, intentar invalidar al menos el token actual
            if current_jti:
                self.jwt_service.revoke_token(current_jti, 'access', uid, 'logout_error')
            
            return {
                "message": "Sesión cerrada con advertencias",
                "status": "partial_success"
            }