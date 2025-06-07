from flask_jwt_extended import get_jwt
from src.shared.exceptions.custom import InvalidTokenException

class RefreshTokenUseCase:
    def __init__(self, auth_service):
        self.auth_service = auth_service

    def execute(self, identity: str) -> dict:
        """Ejecuta la rotación segura de refresh token"""
        try:
            # Obtener información del token actual
            current_token_claims = get_jwt()
            current_refresh_jti = current_token_claims.get('jti')
            
            if not current_refresh_jti:
                raise InvalidTokenException("Invalid refresh token - missing JTI")
            
            # Validar el uso del refresh token actual (detecta reutilización)
            self.auth_service.validate_refresh_token_use(current_refresh_jti, identity)
            
            # Crear nuevos tokens (rotación)
            # El nuevo refresh token tendrá como parent el JTI del token actual
            new_tokens = self.auth_service.create_tokens(
                identity=identity, 
                parent_refresh_jti=current_refresh_jti
            )
            
            return new_tokens
            
        except Exception as e:
            # En caso de cualquier error, invalidar sesión por seguridad
            if hasattr(self.auth_service, 'revoke_all_user_tokens'):
                self.auth_service.revoke_all_user_tokens(identity, 'refresh_error')
            raise InvalidTokenException("Refresh token validation failed")