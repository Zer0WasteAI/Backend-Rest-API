"""
Sistema de Caché Inteligente para ZeroWasteAI
Optimización de operaciones costosas de IA y base de datos
"""
import os
import json
import logging
import hashlib
from typing import Any, Optional, Callable, Union, Dict
from functools import wraps

from flask import current_app
from flask_caching import Cache
from flask_jwt_extended import get_jwt_identity

from src.config.optimization_config import OptimizationConfig

logger = logging.getLogger(__name__)

class ZeroWasteCacheService:
    """Servicio de caché inteligente para operaciones costosas"""
    
    def __init__(self):
        self.cache: Optional[Cache] = None
        self.config = OptimizationConfig()
        self.enabled = True
    
    def init_app(self, app):
        """Inicializar caché con la app Flask"""
        
        # Deshabilitar caché si estamos en testing
        if app.config.get('TESTING'):
            logger.info("🚫 Caché deshabilitado en modo testing")
            self.enabled = False
            return
        
        try:
            # Configurar Flask-Caching
            cache_config = self.config.get_cache_config()
            self.cache = Cache(app, config=cache_config)
            
            # Test de conexión Redis
            self.cache.set('test_key', 'test_value', timeout=5)
            test_result = self.cache.get('test_key')
            
            if test_result == 'test_value':
                logger.info("✅ Cache Redis conectado correctamente")
                self.cache.delete('test_key')
            else:
                raise Exception("Test de Redis falló")
                
        except Exception as e:
            logger.warning(f"⚠️ No se pudo conectar a Redis: {str(e)}")
            logger.info("🔄 Fallback a caché en memoria")
            
            # Fallback a caché simple en memoria
            self.cache = Cache(app, config={'CACHE_TYPE': 'simple'})
            
        logger.info("🗄️ Cache Service inicializado")
    
    def _generate_cache_key(self, pattern_name: str, **kwargs) -> str:
        """Genera clave de caché única y consistente"""
        
        # Usar pattern del config si existe
        if pattern_name in self.config.CACHE_KEY_PATTERNS:
            base_key = self.config.get_cache_key(pattern_name, **kwargs)
        else:
            # Generar clave básica
            base_key = f"{pattern_name}:" + ":".join([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        
        # Hash para claves muy largas (Redis tiene límite de 512MB por clave)
        if len(base_key) > 200:
            base_key = f"hashed:{hashlib.md5(base_key.encode()).hexdigest()}"
        
        return f"zerowasteai:{base_key}"
    
    def get(self, key: str, pattern_name: str = None, **kwargs) -> Any:
        """Obtiene valor del caché"""
        
        if not self.enabled or not self.cache:
            return None
        
        try:
            if pattern_name:
                key = self._generate_cache_key(pattern_name, key=key, **kwargs)
            
            result = self.cache.get(key)
            
            if result is not None:
                logger.debug(f"🎯 Cache HIT: {key[:50]}...")
                return result
            else:
                logger.debug(f"❌ Cache MISS: {key[:50]}...")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo caché: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, timeout: int = None, pattern_name: str = None, **kwargs) -> bool:
        """Almacena valor en caché"""
        
        if not self.enabled or not self.cache:
            return False
        
        try:
            if pattern_name:
                key = self._generate_cache_key(pattern_name, key=key, **kwargs)
                timeout = timeout or self.config.get_cache_timeout(pattern_name)
            
            timeout = timeout or self.config.CACHE_DEFAULT_TIMEOUT
            
            self.cache.set(key, value, timeout=timeout)
            logger.debug(f"💾 Cache SET: {key[:50]}... (timeout: {timeout}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando en caché: {str(e)}")
            return False
    
    def delete(self, key: str, pattern_name: str = None, **kwargs) -> bool:
        """Elimina valor del caché"""
        
        if not self.enabled or not self.cache:
            return False
        
        try:
            if pattern_name:
                key = self._generate_cache_key(pattern_name, key=key, **kwargs)
            
            self.cache.delete(key)
            logger.debug(f"🗑️ Cache DELETE: {key[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error eliminando caché: {str(e)}")
            return False
    
    def clear_user_cache(self, user_uid: str) -> bool:
        """Limpia todo el caché de un usuario específico"""
        
        if not self.enabled or not self.cache:
            return False
        
        try:
            # Patrones comunes de caché de usuario
            user_patterns = [
                f"zerowasteai:inventory:user:{user_uid}:*",
                f"zerowasteai:planning:user:{user_uid}:*",
                f"zerowasteai:environmental:user:{user_uid}:*"
            ]
            
            # Nota: delete_many requiere implementación específica de Redis
            # Por ahora, marcar para limpieza manual
            logger.info(f"🧹 Caché de usuario {user_uid} marcado para limpieza")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error limpiando caché de usuario: {str(e)}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché para monitoreo"""
        
        if not self.enabled or not self.cache:
            return {"status": "disabled"}
        
        try:
            # Stats básicas
            stats = {
                "status": "enabled",
                "backend": self.cache.cache._write_client.__class__.__name__ if hasattr(self.cache.cache, '_write_client') else "Unknown",
                "default_timeout": self.config.CACHE_DEFAULT_TIMEOUT,
            }
            
            # Si es Redis, obtener stats adicionales
            try:
                if hasattr(self.cache.cache, '_write_client'):
                    redis_client = self.cache.cache._write_client
                    info = redis_client.info()
                    stats.update({
                        "redis_version": info.get('redis_version'),
                        "used_memory": info.get('used_memory_human'),
                        "connected_clients": info.get('connected_clients'),
                        "keyspace_hits": info.get('keyspace_hits'),
                        "keyspace_misses": info.get('keyspace_misses')
                    })
            except:
                pass
            
            return stats
            
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Instancia global del cache service
cache_service = ZeroWasteCacheService()

def smart_cache(cache_type: str, timeout: int = None, key_suffix: str = None):
    """
    Decorator para cachear resultados de funciones costosas
    
    Args:
        cache_type: Tipo de caché del config (ej: 'ai_environmental_impact')
        timeout: Timeout personalizado en segundos
        key_suffix: Sufijo adicional para la clave de caché
    
    Usage:
        @smart_cache('ai_environmental_impact', timeout=3600)
        def analyze_environmental_impact(ingredient_name):
            # Operación costosa
            return expensive_ai_call(ingredient_name)
        
        @smart_cache('inventory_basic')
        def get_user_inventory(user_uid):
            return database_query(user_uid)
    """
    def decorator(func: Callable) -> Callable:
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            # Si caché no está habilitado, ejecutar función normal
            if not cache_service.enabled:
                return func(*args, **kwargs)
            
            # Generar clave de caché basada en función y argumentos
            cache_key_parts = [
                func.__name__,
                str(hash(str(args))),
                str(hash(str(sorted(kwargs.items()))))
            ]
            
            if key_suffix:
                cache_key_parts.append(str(key_suffix))
            
            cache_key = ":".join(cache_key_parts)
            
            # Intentar obtener del caché
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 Usando resultado cacheado para {func.__name__}")
                return cached_result
            
            # Ejecutar función y cachear resultado
            logger.debug(f"⚙️ Ejecutando {func.__name__} (no en caché)")
            result = func(*args, **kwargs)
            
            # Guardar en caché
            final_timeout = timeout or cache_service.config.get_cache_timeout(cache_type)
            cache_service.set(cache_key, result, timeout=final_timeout)
            
            return result
        
        return wrapper
    return decorator

def cache_user_data(cache_type: str, timeout: int = None):
    """
    Decorator especializado para cachear datos por usuario
    Automáticamente usa el JWT del usuario actual como parte de la clave
    
    Usage:
        @cache_user_data('inventory_basic')
        def get_user_inventory():
            user_uid = get_jwt_identity()
            return query_inventory(user_uid)
    """
    def decorator(func: Callable) -> Callable:
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            if not cache_service.enabled:
                return func(*args, **kwargs)
            
            # Obtener usuario actual para la clave
            try:
                user_uid = get_jwt_identity()
                if not user_uid:
                    # Sin usuario, no cachear
                    return func(*args, **kwargs)
            except:
                # Error obteniendo JWT, no cachear
                return func(*args, **kwargs)
            
            # Generar clave específica del usuario
            cache_key = f"user:{user_uid}:{func.__name__}:{hash(str(args))}:{hash(str(sorted(kwargs.items())))}"
            
            # Intentar caché
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 Cache hit para usuario {user_uid[:8]}... en {func.__name__}")
                return cached_result
            
            # Ejecutar y cachear
            result = func(*args, **kwargs)
            final_timeout = timeout or cache_service.config.get_cache_timeout(cache_type)
            cache_service.set(cache_key, result, timeout=final_timeout)
            
            logger.debug(f"💾 Resultado cacheado para usuario {user_uid[:8]}... en {func.__name__}")
            return result
        
        return wrapper
    return decorator