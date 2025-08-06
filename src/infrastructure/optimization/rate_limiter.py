"""
Rate Limiter inteligente para ZeroWasteAI API
Protección contra abuso de recursos y costos IA
"""
import os
import logging
from functools import wraps
from typing import Optional, Callable, Any

from flask import request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from src.config.optimization_config import OptimizationConfig

logger = logging.getLogger(__name__)

class ZeroWasteRateLimiter:
    """Rate Limiter personalizado para ZeroWasteAI con lógica inteligente"""
    
    def __init__(self):
        self.limiter: Optional[Limiter] = None
        self.config = OptimizationConfig()
    
    def init_app(self, app):
        """Inicializar rate limiter con la app Flask"""
        
        # Skip rate limiting en ambientes de desarrollo/testing
        if app.config.get('TESTING') or os.getenv('FLASK_ENV') in ['testing', 'development']:
            logger.info("🚫 Rate limiting deshabilitado en ambiente de desarrollo/testing")
            self.limiter = None
            return
        
        self.limiter = Limiter(
            app=app,
            key_func=self._get_rate_limit_key,
            default_limits=[self.config.RATELIMIT_DEFAULT],
            storage_uri=self.config.RATELIMIT_STORAGE_URL,
            strategy=self.config.RATELIMIT_STRATEGY,
            on_breach=self._on_rate_limit_breach,
        )
        
        logger.info("✅ Rate Limiter inicializado correctamente")
    
    def _get_rate_limit_key(self) -> str:
        """
        Clave inteligente para rate limiting:
        1. Usuario autenticado = por user_uid
        2. Usuario anónimo = por IP
        """
        try:
            # Intentar obtener usuario autenticado
            verify_jwt_in_request(optional=True)
            user_uid = get_jwt_identity()
            
            if user_uid:
                return f"user:{user_uid}"
            else:
                # Fallback a IP para usuarios no autenticados
                return f"ip:{get_remote_address()}"
                
        except Exception:
            # Si hay error con JWT, usar IP
            return f"ip:{get_remote_address()}"
    
    def _on_rate_limit_breach(self, request_limit):
        """Manejo personalizado cuando se excede el rate limit"""
        
        # Log del abuse para monitoreo
        user_key = self._get_rate_limit_key()
        logger.warning(
            f"🚨 Rate limit excedido - Key: {user_key}, "
            f"Limit: {request_limit}, "
            f"Endpoint: {request.endpoint}, "
            f"IP: {get_remote_address()}, "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
        )
        
        # Respuesta JSON amigable
        response = jsonify({
            "error": "Rate limit exceeded",
            "message": "Demasiadas solicitudes. Por favor, espera un momento antes de reintentar.",
            "details": {
                "limit": str(request_limit.limit),
                "window": request_limit.per,
                "retry_after": request_limit.retry_after
            },
            "tips": [
                "Espera unos segundos antes de hacer otra solicitud",
                "Si necesitas más capacidad, contacta soporte"
            ]
        })
        response.status_code = 429
        response.headers['Retry-After'] = str(request_limit.retry_after)
        
        return response
    
    def _is_exempt_request(self) -> bool:
        """Verifica si la request está exenta de rate limiting"""
        
        # Headers especiales de bypass
        for header in self.config.RATELIMIT_EXEMPT_HEADERS:
            if request.headers.get(header):
                logger.debug(f"🔓 Request exenta por header {header}")
                return True
        
        # IPs whitelisted (admin, monitoring)
        exempt_ips = current_app.config.get('RATELIMIT_EXEMPT_IPS', [])
        client_ip = get_remote_address()
        if client_ip in exempt_ips:
            logger.debug(f"🔓 IP exenta: {client_ip}")
            return True
        
        return False
    
    def limit(self, rate_limit: str, endpoint_type: str = None):
        """
        Decorator para aplicar rate limiting a endpoints
        
        Args:
            rate_limit: Límite (ej: "5 per minute")
            endpoint_type: Tipo de endpoint para obtener límite de config
        """
        def decorator(func: Callable) -> Callable:
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                
                # Si no hay limiter (dev/testing), ejecutar normal
                if not self.limiter:
                    return func(*args, **kwargs)
                
                # Si está exenta, ejecutar sin límite
                if self._is_exempt_request():
                    return func(*args, **kwargs)
                
                # Aplicar rate limiting
                try:
                    # Usar límite específico o el del config
                    final_limit = rate_limit
                    if endpoint_type:
                        final_limit = self.config.get_rate_limit(endpoint_type)
                    
                    # Verificar límite
                    self.limiter.limit(final_limit)(func)(*args, **kwargs)
                    
                except Exception as e:
                    logger.error(f"❌ Error en rate limiting: {str(e)}")
                    # En caso de error, permitir la request (fail-open)
                    return func(*args, **kwargs)
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator

# Instancia global del rate limiter
rate_limiter = ZeroWasteRateLimiter()

def smart_rate_limit(endpoint_type: str, custom_limit: str = None):
    """
    Decorator conveniente para rate limiting inteligente
    
    Usage:
        @smart_rate_limit('ai_recognition')
        def recognize_ingredients():
            pass
    
        @smart_rate_limit('inventory_crud', '20 per minute') 
        def update_inventory():
            pass
    """
    def decorator(func):
        if rate_limiter.limiter:
            # Obtener límite del config o usar custom
            limit = custom_limit or OptimizationConfig.get_rate_limit(endpoint_type)
            return rate_limiter.limiter.limit(limit)(func)
        else:
            # Sin rate limiting en dev/testing
            return func
    
    return decorator

def get_rate_limit_status(user_key: str = None) -> dict:
    """
    Obtiene el estado actual de rate limiting para debugging
    """
    if not rate_limiter.limiter:
        return {"status": "disabled", "reason": "development/testing mode"}
    
    try:
        key = user_key or rate_limiter._get_rate_limit_key()
        
        # Aquí podrías agregar lógica para consultar Redis directamente
        # y obtener contadores actuales, pero eso requiere acceso directo a Redis
        
        return {
            "status": "active",
            "key": key,
            "limiter_configured": True
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}