from datetime import datetime, timezone
from src.infrastructure.db.base import db
from src.infrastructure.db.schemas.token_blacklist_schema import TokenBlacklist, RefreshTokenTracking

class TokenSecurityRepository:
    
    def add_to_blacklist(self, jti: str, token_type: str, user_uid: str, expires_at: datetime, reason: str = None):
        """Añade un token a la blacklist"""
        blacklisted_token = TokenBlacklist(
            jti=jti,
            token_type=token_type,
            user_uid=user_uid,
            expires_at=expires_at,
            reason=reason or 'manual'
        )
        db.session.add(blacklisted_token)
        db.session.commit()
        return blacklisted_token
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """Verifica si un token está en la blacklist"""
        return TokenBlacklist.query.filter_by(jti=jti).first() is not None
    
    def blacklist_all_user_tokens(self, user_uid: str, reason: str = 'security_breach'):
        """Invalida todos los refresh tokens activos de un usuario"""
        # Marcar todos los refresh tokens como usados
        refresh_tokens = RefreshTokenTracking.query.filter_by(
            user_uid=user_uid, 
            used=False
        ).all()
        
        for token in refresh_tokens:
            # Marcar como usado
            token.used = True
            token.used_at = datetime.now(timezone.utc)
            
            # Añadir a blacklist
            self.add_to_blacklist(
                jti=token.jti,
                token_type='refresh',
                user_uid=user_uid,
                expires_at=token.expires_at,
                reason=reason
            )
        
        db.session.commit()
        return len(refresh_tokens)
    
    def track_refresh_token(self, jti: str, user_uid: str, expires_at: datetime, 
                           parent_jti: str = None, ip_address: str = None, user_agent: str = None):
        """Registra un nuevo refresh token para tracking"""
        tracking = RefreshTokenTracking(
            jti=jti,
            user_uid=user_uid,
            parent_jti=parent_jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(tracking)
        db.session.commit()
        return tracking
    
    def mark_refresh_token_used(self, jti: str) -> bool:
        """Marca un refresh token como usado y verifica si ya había sido usado antes"""
        token = RefreshTokenTracking.query.filter_by(jti=jti).first()
        if not token:
            return False  # Token no encontrado
        
        if token.used:
            # ¡ALERTA! Token ya había sido usado - posible ataque
            return False
        
        token.used = True
        token.used_at = datetime.now(timezone.utc)
        db.session.commit()
        return True
    
    def is_refresh_token_compromised(self, jti: str) -> bool:
        """Verifica si un refresh token podría estar comprometido"""
        token = RefreshTokenTracking.query.filter_by(jti=jti).first()
        if not token:
            return True  # Token no encontrado = sospechoso
        
        return token.used  # Si ya fue usado, está comprometido
    
    def get_refresh_token_info(self, jti: str):
        """Obtiene información de un refresh token"""
        return RefreshTokenTracking.query.filter_by(jti=jti).first()
    
    def cleanup_expired_tokens(self):
        """Limpia tokens expirados de la base de datos"""
        now = datetime.now(timezone.utc)
        
        # Limpiar blacklist de tokens expirados
        expired_blacklist = TokenBlacklist.query.filter(TokenBlacklist.expires_at < now).delete()
        
        # Limpiar tracking de refresh tokens expirados
        expired_tracking = RefreshTokenTracking.query.filter(RefreshTokenTracking.expires_at < now).delete()
        
        db.session.commit()
        return {"blacklist_cleaned": expired_blacklist, "tracking_cleaned": expired_tracking} 