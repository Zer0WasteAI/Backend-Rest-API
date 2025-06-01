import uuid
from datetime import datetime, timezone, timedelta
from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jti,
    get_jwt
)
from src.domain.services.auth_service import AuthService
from src.shared.exceptions.custom import InvalidTokenException
from src.infrastructure.db.token_security_repository import TokenSecurityRepository
from src.infrastructure.security.security_logger import security_logger, SecurityEventType
from src.config.config import Config


class JWTService(AuthService):
    def __init__(self):
        self.token_security_repo = TokenSecurityRepository()
    
    def create_tokens(self, identity: str, parent_refresh_jti: str = None) -> dict:
        """Crea tokens con JTI y tracking de seguridad"""
        # Generar JTIs únicos
        access_jti = str(uuid.uuid4())
        refresh_jti = str(uuid.uuid4())
        
        # Calcular fecha de expiración del refresh token
        refresh_expires = datetime.now(timezone.utc) + Config.JWT_REFRESH_TOKEN_EXPIRES
        
        # Crear tokens con JTI
        access_token = create_access_token(
            identity=identity,
            additional_claims={"jti": access_jti}
        )
        refresh_token = create_refresh_token(
            identity=identity,
            additional_claims={"jti": refresh_jti}
        )
        
        # Obtener información de la request para tracking
        ip_address = self._get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        
        # Registrar el refresh token para tracking
        self.token_security_repo.track_refresh_token(
            jti=refresh_jti,
            user_uid=identity,
            expires_at=refresh_expires,
            parent_jti=parent_refresh_jti,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Log rotación si es aplicable
        if parent_refresh_jti:
            security_logger.log_token_rotation(identity, parent_refresh_jti, refresh_jti)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "access_jti": access_jti,
            "refresh_jti": refresh_jti
        }
    
    def decode_token(self, token: str) -> dict:
        """Decodifica token y verifica blacklist"""
        try:
            decoded = decode_token(token)
            
            # Verificar si el token está en blacklist
            jti = decoded.get('jti')
            if jti and self.token_security_repo.is_token_blacklisted(jti):
                security_logger.log_security_event(
                    SecurityEventType.INVALID_TOKEN_ATTEMPT,
                    {"reason": "token_blacklisted", "jti": jti}
                )
                raise InvalidTokenException("Token has been revoked")
            
            return decoded
        except Exception as e:
            security_logger.log_security_event(
                SecurityEventType.INVALID_TOKEN_ATTEMPT,
                {"reason": "token_decode_failed", "error": str(e)}
            )
            raise InvalidTokenException() from e
    
    def validate_refresh_token_use(self, refresh_jti: str, user_uid: str) -> bool:
        """Valida el uso de un refresh token y detecta reutilización"""
        # Verificar si el token está en blacklist
        if self.token_security_repo.is_token_blacklisted(refresh_jti):
            security_logger.log_security_event(
                SecurityEventType.INVALID_TOKEN_ATTEMPT,
                {"reason": "refresh_token_blacklisted", "jti": refresh_jti, "user_uid": user_uid}
            )
            raise InvalidTokenException("Token has been revoked")
        
        # Verificar si el token ya fue usado (detección de reutilización)
        if self.token_security_repo.is_refresh_token_compromised(refresh_jti):
            # ¡ALERTA! Token comprometido - invalidar todos los tokens del usuario
            security_logger.log_token_reuse(user_uid, refresh_jti)
            self.token_security_repo.blacklist_all_user_tokens(
                user_uid=user_uid,
                reason='refresh_token_reuse_detected'
            )
            security_logger.log_security_event(
                SecurityEventType.SECURITY_BREACH_DETECTED,
                {
                    "reason": "refresh_token_reuse_detected",
                    "user_uid": user_uid,
                    "jti": refresh_jti,
                    "action_taken": "all_user_sessions_invalidated"
                }
            )
            raise InvalidTokenException("Security breach detected - all sessions invalidated")
        
        # Marcar el token como usado
        if not self.token_security_repo.mark_refresh_token_used(refresh_jti):
            # El token ya había sido usado - posible ataque
            security_logger.log_token_reuse(user_uid, refresh_jti)
            self.token_security_repo.blacklist_all_user_tokens(
                user_uid=user_uid,
                reason='refresh_token_reuse_detected'
            )
            security_logger.log_security_event(
                SecurityEventType.SECURITY_BREACH_DETECTED,
                {
                    "reason": "refresh_token_double_use",
                    "user_uid": user_uid,
                    "jti": refresh_jti,
                    "action_taken": "all_user_sessions_invalidated"
                }
            )
            raise InvalidTokenException("Security breach detected - all sessions invalidated")
        
        return True
    
    def revoke_token(self, jti: str, token_type: str, user_uid: str, reason: str = 'logout'):
        """Revoca un token específico"""
        # Calcular fecha de expiración basada en el tipo de token
        if token_type == 'access':
            expires_at = datetime.now(timezone.utc) + Config.JWT_ACCESS_TOKEN_EXPIRES
        else:
            expires_at = datetime.now(timezone.utc) + Config.JWT_REFRESH_TOKEN_EXPIRES
        
        result = self.token_security_repo.add_to_blacklist(
            jti=jti,
            token_type=token_type,
            user_uid=user_uid,
            expires_at=expires_at,
            reason=reason
        )
        
        security_logger.log_security_event(
            SecurityEventType.TOKEN_BLACKLISTED,
            {
                "jti": jti,
                "token_type": token_type,
                "user_uid": user_uid,
                "reason": reason
            }
        )
        
        return result
    
    def revoke_all_user_tokens(self, user_uid: str, reason: str = 'logout'):
        """Revoca todos los tokens de un usuario"""
        revoked_count = self.token_security_repo.blacklist_all_user_tokens(user_uid, reason)
        
        security_logger.log_security_event(
            SecurityEventType.TOKEN_BLACKLISTED,
            {
                "user_uid": user_uid,
                "reason": reason,
                "tokens_revoked": revoked_count,
                "action": "all_user_tokens_revoked"
            }
        )
        
        return revoked_count
    
    def _get_client_ip(self) -> str:
        """Obtiene la IP real del cliente considerando proxies"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        return request.remote_addr or 'unknown'