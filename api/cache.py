"""
Caching utilities for performance optimization.
"""

import json
import hashlib
import logging
from typing import Optional, Any, Callable
from functools import wraps
import time

logger = logging.getLogger(__name__)

# Simple in-memory cache (in production, use Redis)
_cache: dict = {}
_cache_ttl: dict = {}


class CacheService:
    """Simple cache service with TTL support."""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache service.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in _cache:
            return None
        
        # Check TTL
        if key in _cache_ttl:
            if time.time() > _cache_ttl[key]:
                del _cache[key]
                del _cache_ttl[key]
                return None
        
        return _cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        _cache[key] = value
        _cache_ttl[key] = time.time() + (ttl or self.default_ttl)
    
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in _cache:
            del _cache[key]
        if key in _cache_ttl:
            del _cache_ttl[key]
    
    def clear(self) -> None:
        """Clear all cache."""
        _cache.clear()
        _cache_ttl.clear()
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"


# Global cache instance
cache = CacheService()


def cached(ttl: int = 3600, key_prefix: str = "cache"):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache.generate_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Compute and cache
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result
        
        return wrapper
    return decorator

