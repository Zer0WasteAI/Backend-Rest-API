"""
Configuración de optimizaciones de rendimiento
Rate Limiting + Caché Redis
"""
import os
from typing import Dict, Any

class OptimizationConfig:
    """Configuración centralizada para optimizaciones de performance"""
    
    # =================== REDIS CACHE CONFIG ===================
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = 'redis'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutos por defecto
    
    # =================== RATE LIMITING CONFIG ===================
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_DEFAULT = "1000 per hour"  # Límite general
    
    # =================== RATE LIMITS POR ENDPOINT ===================
    ENDPOINT_RATE_LIMITS: Dict[str, str] = {
        # 🤖 AI ENDPOINTS - MÁS RESTRICTIVOS (costosos)
        'ai_recognition': "5 per minute",           # Reconocimiento de imagen
        'ai_environmental': "10 per minute",        # Cálculos ambientales
        'ai_recipe_generation': "8 per minute",     # Generación de recetas
        'ai_inventory_complete': "3 per minute",    # Inventario enriquecido (muy costoso)
        
        # 📦 INVENTORY ENDPOINTS - MODERADOS
        'inventory_crud': "50 per minute",          # CRUD básico de inventario
        'inventory_bulk': "10 per minute",          # Operaciones en lote
        
        # 📅 PLANNING ENDPOINTS - NORMALES
        'planning_crud': "30 per minute",           # Planes de comida
        
        # 🔐 AUTH ENDPOINTS - SEGUROS
        'auth_login': "10 per minute",              # Login attempts
        'auth_signup': "5 per minute",              # Registro
        'auth_sensitive': "3 per minute",           # Operaciones sensibles
        
        # 📊 DATA ENDPOINTS - NORMALES  
        'data_read': "100 per minute",              # Lectura general
        'data_write': "40 per minute",              # Escritura general
    }
    
    # =================== CACHE TIMEOUTS POR TIPO ===================
    CACHE_TIMEOUTS: Dict[str, int] = {
        # 🤖 AI RESULTS - CACHE LARGO (costosos de regenerar)
        'ai_environmental_impact': 3600,           # 1 hora - raramente cambia
        'ai_utilization_ideas': 1800,             # 30 min - puede variar un poco
        'ai_recognition_result': 7200,            # 2 horas - imagen no cambia
        
        # 📦 INVENTORY - CACHE MEDIO (cambia frecuentemente)
        'inventory_complete': 600,                 # 10 min - puede cambiar
        'inventory_basic': 300,                    # 5 min - cambia más seguido
        'expiring_items': 900,                     # 15 min - importante pero no crítico
        
        # 📅 PLANNING - CACHE CORTO (usuario puede editar)
        'meal_plans': 300,                         # 5 min - usuario edita
        'meal_plan_dates': 600,                    # 10 min - no cambia tanto
        
        # 📊 CALCULATIONS - CACHE LARGO (históricos)
        'environmental_summary': 1800,            # 30 min - datos históricos
        'environmental_calculations': 3600,       # 1 hora - no cambian
        
        # 🔍 SEARCH RESULTS - CACHE MEDIO
        'search_results': 900,                     # 15 min - balance performance/freshness
    }
    
    # =================== CACHE KEYS PATTERNS ===================
    CACHE_KEY_PATTERNS: Dict[str, str] = {
        'user_inventory': "inventory:user:{user_id}:basic",
        'user_inventory_complete': "inventory:user:{user_id}:complete",
        'ingredient_analysis': "ai:ingredient:{ingredient_name}:analysis",
        'ingredient_utilization': "ai:ingredient:{ingredient_name}:utilization",
        'user_environmental_summary': "environmental:user:{user_id}:summary",
        'meal_plan_by_date': "planning:user:{user_id}:date:{date}",
        'user_meal_plans': "planning:user:{user_id}:all",
        'expiring_items': "inventory:user:{user_id}:expiring:{days}",
    }
    
    # =================== CONFIGURACIÓN AVANZADA ===================
    
    # Headers para bypass de rate limiting (admin, testing)
    RATELIMIT_EXEMPT_HEADERS = ['X-Admin-Token', 'X-Test-Suite']
    
    # Ambientes sin rate limiting
    RATELIMIT_EXEMPT_ENVIRONMENTS = ['testing', 'development']
    
    # Logs de rate limiting
    RATELIMIT_LOG_VIOLATIONS = True
    
    # Cache warming (precalentar caché común)
    ENABLE_CACHE_WARMING = True
    CACHE_WARMING_ENDPOINTS = [
        'user_inventory_basic',
        'expiring_items'
    ]

    @classmethod
    def get_cache_config(cls) -> Dict[str, Any]:
        """Retorna configuración completa para Flask-Caching"""
        return {
            'CACHE_TYPE': cls.CACHE_TYPE,
            'CACHE_REDIS_URL': cls.REDIS_URL,
            'CACHE_DEFAULT_TIMEOUT': cls.CACHE_DEFAULT_TIMEOUT,
            'CACHE_KEY_PREFIX': 'zerowasteai:',
        }
    
    @classmethod
    def get_limiter_config(cls) -> Dict[str, Any]:
        """Retorna configuración completa para Flask-Limiter"""
        return {
            'RATELIMIT_STORAGE_URL': cls.RATELIMIT_STORAGE_URL,
            'RATELIMIT_STRATEGY': cls.RATELIMIT_STRATEGY,
            'RATELIMIT_DEFAULT': cls.RATELIMIT_DEFAULT,
        }
    
    @classmethod
    def get_rate_limit(cls, endpoint_type: str) -> str:
        """Obtiene rate limit específico para un tipo de endpoint"""
        return cls.ENDPOINT_RATE_LIMITS.get(endpoint_type, cls.RATELIMIT_DEFAULT)
    
    @classmethod
    def get_cache_timeout(cls, cache_type: str) -> int:
        """Obtiene timeout de caché para un tipo específico"""
        return cls.CACHE_TIMEOUTS.get(cache_type, cls.CACHE_DEFAULT_TIMEOUT)
    
    @classmethod
    def get_cache_key(cls, pattern_name: str, **kwargs) -> str:
        """Genera clave de caché usando pattern y parámetros"""
        pattern = cls.CACHE_KEY_PATTERNS.get(pattern_name, f"{pattern_name}:{{key}}")
        return pattern.format(**kwargs)