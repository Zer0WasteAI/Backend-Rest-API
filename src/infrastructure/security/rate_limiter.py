import time
from functools import wraps
from flask import request, jsonify, current_app
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self):
        # En memoria para simplicidad - en producción usar Redis
        self.requests = defaultdict(list)
        self.blocked_ips = defaultdict(list)
    
    def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        """Verifica si una clave ha excedido el límite de rate"""
        now = time.time()
        
        # Limpiar requests antiguos
        self.requests[key] = [req_time for req_time in self.requests[key] 
                             if now - req_time < window]
        
        # Verificar límite
        if len(self.requests[key]) >= limit:
            return True
        
        # Registrar request actual
        self.requests[key].append(now)
        return False
    
    def block_ip(self, ip: str, duration: int = 300):  # 5 minutos por defecto
        """Bloquea una IP por un tiempo determinado"""
        until = time.time() + duration
        self.blocked_ips[ip].append(until)
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Verifica si una IP está bloqueada"""
        now = time.time()
        
        # Limpiar bloqueos expirados
        self.blocked_ips[ip] = [block_time for block_time in self.blocked_ips[ip] 
                               if block_time > now]
        
        return len(self.blocked_ips[ip]) > 0
    
    def get_client_ip(self) -> str:
        """Obtiene la IP real del cliente"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        return request.remote_addr or 'unknown'

# Instancia global
rate_limiter = RateLimiter()

def rate_limit(limit: int = 60, window: int = 60, per: str = 'ip', block_duration: int = 300):
    """
    Decorador para rate limiting
    
    Args:
        limit: Número máximo de requests
        window: Ventana de tiempo en segundos
        per: 'ip', 'user', o 'endpoint'
        block_duration: Duración del bloqueo en segundos tras exceder límite
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = rate_limiter.get_client_ip()
            
            # Verificar si la IP está bloqueada
            if rate_limiter.is_ip_blocked(ip):
                return jsonify({
                    "error": "Too many requests - IP temporarily blocked",
                    "retry_after": block_duration
                }), 429
            
            # Determinar la clave para rate limiting
            if per == 'ip':
                key = f"ip:{ip}"
            elif per == 'user':
                try:
                    from flask_jwt_extended import get_jwt_identity
                    user_id = get_jwt_identity()
                    key = f"user:{user_id}" if user_id else f"ip:{ip}"
                except:
                    key = f"ip:{ip}"
            elif per == 'endpoint':
                key = f"endpoint:{request.endpoint}:{ip}"
            else:
                key = f"ip:{ip}"
            
            # Verificar rate limit
            if rate_limiter.is_rate_limited(key, limit, window):
                # Bloquear IP por exceder límite
                rate_limiter.block_ip(ip, block_duration)
                
                return jsonify({
                    "error": "Rate limit exceeded",
                    "limit": limit,
                    "window": window,
                    "retry_after": block_duration
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Decoradores específicos para diferentes endpoints
def auth_rate_limit(f):
    """Rate limiting estricto para endpoints de autenticación"""
    return rate_limit(limit=5, window=60, per='ip', block_duration=600)(f)

def api_rate_limit(f):
    """Rate limiting normal para API endpoints"""
    return rate_limit(limit=100, window=60, per='user', block_duration=60)(f)

def refresh_rate_limit(f):
    """Rate limiting para refresh tokens"""
    return rate_limit(limit=10, window=60, per='user', block_duration=300)(f) 