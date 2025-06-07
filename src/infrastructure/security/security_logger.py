import logging
import json
from datetime import datetime, timezone
from flask import request, g
from enum import Enum

class SecurityEventType(Enum):
    TOKEN_REUSE_DETECTED = "token_reuse_detected"
    INVALID_TOKEN_ATTEMPT = "invalid_token_attempt"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_LOGIN = "suspicious_login"
    TOKEN_BLACKLISTED = "token_blacklisted"
    AUTHENTICATION_FAILED = "authentication_failed"
    LOGOUT_SUCCESS = "logout_success"
    REFRESH_TOKEN_ROTATED = "refresh_token_rotated"
    IP_BLOCKED = "ip_blocked"
    SECURITY_BREACH_DETECTED = "security_breach_detected"

class SecurityLogger:
    def __init__(self):
        # Configurar logger específico para seguridad
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # Handler para archivo de seguridad (si no existe)
        if not self.logger.handlers:
            handler = logging.FileHandler('security.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _get_request_context(self):
        """Obtiene contexto de la request actual"""
        context = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ip_address": self._get_client_ip(),
            "user_agent": request.headers.get('User-Agent', 'Unknown'),
            "endpoint": request.endpoint,
            "method": request.method,
            "url": request.url
        }
        
        # Agregar user ID si está disponible
        try:
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
            if user_id:
                context["user_uid"] = user_id
        except:
            pass
        
        return context
    
    def _get_client_ip(self) -> str:
        """Obtiene la IP real del cliente"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        return request.remote_addr or 'unknown'
    
    def log_security_event(self, event_type: SecurityEventType, details: dict = None):
        """Log de eventos de seguridad"""
        try:
            event_data = {
                "event_type": event_type.value,
                "severity": self._get_severity(event_type),
                **self._get_request_context()
            }
            
            if details:
                event_data["details"] = details
            
            # Log según la severidad
            if event_data["severity"] == "CRITICAL":
                self.logger.critical(json.dumps(event_data))
            elif event_data["severity"] == "HIGH":
                self.logger.error(json.dumps(event_data))
            elif event_data["severity"] == "MEDIUM":
                self.logger.warning(json.dumps(event_data))
            else:
                self.logger.info(json.dumps(event_data))
                
        except Exception as e:
            # Fallback logging en caso de error
            self.logger.error(f"Error logging security event: {str(e)}")
    
    def _get_severity(self, event_type: SecurityEventType) -> str:
        """Determina la severidad del evento"""
        critical_events = [
            SecurityEventType.TOKEN_REUSE_DETECTED,
            SecurityEventType.SECURITY_BREACH_DETECTED
        ]
        
        high_events = [
            SecurityEventType.SUSPICIOUS_LOGIN,
            SecurityEventType.IP_BLOCKED
        ]
        
        medium_events = [
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            SecurityEventType.INVALID_TOKEN_ATTEMPT,
            SecurityEventType.AUTHENTICATION_FAILED
        ]
        
        if event_type in critical_events:
            return "CRITICAL"
        elif event_type in high_events:
            return "HIGH"
        elif event_type in medium_events:
            return "MEDIUM"
        else:
            return "LOW"
    
    def log_token_reuse(self, user_uid: str, jti: str, ip_address: str = None):
        """Log específico para reutilización de tokens"""
        self.log_security_event(
            SecurityEventType.TOKEN_REUSE_DETECTED,
            {
                "user_uid": user_uid,
                "token_jti": jti,
                "source_ip": ip_address or self._get_client_ip(),
                "action_taken": "all_user_tokens_revoked"
            }
        )
    
    def log_rate_limit_exceeded(self, ip_address: str, endpoint: str, limit: int):
        """Log específico para rate limit excedido"""
        self.log_security_event(
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            {
                "source_ip": ip_address,
                "target_endpoint": endpoint,
                "limit_exceeded": limit,
                "action_taken": "ip_temporarily_blocked"
            }
        )
    
    def log_authentication_attempt(self, user_uid: str = None, success: bool = True, reason: str = None):
        """Log de intentos de autenticación"""
        event_type = SecurityEventType.LOGOUT_SUCCESS if success else SecurityEventType.AUTHENTICATION_FAILED
        details = {"success": success}
        
        if user_uid:
            details["user_uid"] = user_uid
        if reason:
            details["reason"] = reason
            
        self.log_security_event(event_type, details)
    
    def log_token_rotation(self, user_uid: str, old_jti: str, new_jti: str):
        """Log de rotación de tokens"""
        self.log_security_event(
            SecurityEventType.REFRESH_TOKEN_ROTATED,
            {
                "user_uid": user_uid,
                "old_token_jti": old_jti,
                "new_token_jti": new_jti
            }
        )

# Instancia global
security_logger = SecurityLogger() 