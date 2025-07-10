import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from src.config.config import Config

logger = logging.getLogger(__name__)

class AIResponseCacheService:
    """High-performance caching service for AI responses with Redis support"""
    
    def __init__(self):
        self.cache = self._initialize_cache()
        self.cache_ttl = {
            'recipe_generation': 3600,      # 1 hour for recipes
            'ingredient_recognition': 1800,  # 30 minutes for recognition
            'image_generation': 7200,       # 2 hours for images
            'default': 1800                 # 30 minutes default
        }
        self.hit_count = 0
        self.miss_count = 0
    
    def _initialize_cache(self):
        """Initialize cache backend (Redis or in-memory fallback)"""
        try:
            import redis
            # Try to connect to Redis
            redis_client = redis.Redis(
                host=getattr(Config, 'REDIS_HOST', 'localhost'),
                port=getattr(Config, 'REDIS_PORT', 6379),
                db=getattr(Config, 'REDIS_DB', 0),
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            redis_client.ping()
            logger.info("✅ Redis cache initialized successfully")
            return redis_client
        except Exception as e:
            logger.warning(f"⚠️ Redis not available ({e}), using in-memory cache")
            return {}  # Fallback to dict
    
    def _get_cache_key(self, operation_type: str, prompt: str, **kwargs) -> str:
        """Generate consistent cache key for prompts and parameters"""
        # Include relevant parameters in the key
        key_data = {
            'operation': operation_type,
            'prompt_hash': hashlib.md5(prompt.encode()).hexdigest(),
            'params': {k: v for k, v in kwargs.items() if k in ['temperature', 'num_recipes', 'language']}
        }
        
        content = json.dumps(key_data, sort_keys=True)
        cache_key = f"ai_response:{hashlib.md5(content.encode()).hexdigest()}"
        return cache_key
    
    def get_cached_response(self, operation_type: str, prompt: str, **kwargs) -> Optional[str]:
        """Get cached AI response if available"""
        try:
            cache_key = self._get_cache_key(operation_type, prompt, **kwargs)
            
            if isinstance(self.cache, dict):
                # In-memory cache
                if cache_key in self.cache:
                    entry = self.cache[cache_key]
                    if datetime.now() < entry['expires_at']:
                        self.hit_count += 1
                        logger.info(f"🎯 Cache HIT for {operation_type} (in-memory)")
                        return entry['response']
                    else:
                        del self.cache[cache_key]  # Expired entry
            else:
                # Redis cache
                cached_response = self.cache.get(cache_key)
                if cached_response:
                    self.hit_count += 1
                    logger.info(f"🎯 Cache HIT for {operation_type} (Redis)")
                    return cached_response
            
            self.miss_count += 1
            logger.info(f"💾 Cache MISS for {operation_type}")
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Cache get error: {e}")
            self.miss_count += 1
            return None
    
    def cache_response(self, operation_type: str, prompt: str, response: str, **kwargs) -> bool:
        """Cache AI response for future use"""
        try:
            cache_key = self._get_cache_key(operation_type, prompt, **kwargs)
            ttl = self.cache_ttl.get(operation_type, self.cache_ttl['default'])
            
            if isinstance(self.cache, dict):
                # In-memory cache with size limit
                if len(self.cache) > 1000:  # Max 1000 entries
                    # Remove oldest entries
                    sorted_items = sorted(
                        self.cache.items(), 
                        key=lambda x: x[1]['created_at']
                    )
                    for key, _ in sorted_items[:100]:  # Remove oldest 100
                        del self.cache[key]
                
                self.cache[cache_key] = {
                    'response': response,
                    'created_at': datetime.now(),
                    'expires_at': datetime.now() + timedelta(seconds=ttl),
                    'operation_type': operation_type
                }
                logger.info(f"💾 Cached response for {operation_type} (in-memory, TTL: {ttl}s)")
            else:
                # Redis cache
                self.cache.setex(cache_key, ttl, response)
                logger.info(f"💾 Cached response for {operation_type} (Redis, TTL: {ttl}s)")
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Cache set error: {e}")
            return False
    
    def invalidate_cache(self, operation_type: Optional[str] = None) -> int:
        """Invalidate cache entries by operation type or all"""
        try:
            if isinstance(self.cache, dict):
                if operation_type:
                    count = 0
                    keys_to_remove = []
                    for key, value in self.cache.items():
                        if value.get('operation_type') == operation_type:
                            keys_to_remove.append(key)
                    
                    for key in keys_to_remove:
                        del self.cache[key]
                        count += 1
                    
                    logger.info(f"🗑️ Invalidated {count} cache entries for {operation_type}")
                    return count
                else:
                    count = len(self.cache)
                    self.cache.clear()
                    logger.info(f"🗑️ Invalidated all {count} cache entries")
                    return count
            else:
                # Redis cache invalidation would require key pattern matching
                # For now, we'll just return 0 as Redis invalidation is more complex
                logger.info("🗑️ Redis cache invalidation not implemented")
                return 0
                
        except Exception as e:
            logger.warning(f"⚠️ Cache invalidation error: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            'total_requests': total_requests,
            'cache_hits': self.hit_count,
            'cache_misses': self.miss_count,
            'hit_rate_percentage': round(hit_rate, 2),
            'cache_type': 'Redis' if not isinstance(self.cache, dict) else 'In-Memory'
        }
        
        if isinstance(self.cache, dict):
            stats['cache_size'] = len(self.cache)
            stats['estimated_memory_usage'] = f"{len(str(self.cache)) / 1024:.1f} KB"
        
        return stats
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries (for in-memory cache)"""
        if not isinstance(self.cache, dict):
            return 0
        
        try:
            now = datetime.now()
            expired_keys = []
            
            for key, value in self.cache.items():
                if now >= value['expires_at']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
            
        except Exception as e:
            logger.warning(f"⚠️ Cache cleanup error: {e}")
            return 0

# Global cache instance
ai_cache = AIResponseCacheService()