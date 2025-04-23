import json
import time
import logging
from typing import Dict, Any, Optional, Union, List
import asyncio
from functools import lru_cache

from config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """
    Simple in-memory cache service with expiration.
    In a production environment, this would be replaced with Redis or another cache backend.
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cleanup_task = None
    
    async def start(self):
        """Start the cache cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the cache cleanup task."""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_loop(self):
        """Periodically clean up expired cache entries."""
        while True:
            try:
                self._cleanup_expired()
                await asyncio.sleep(60)  # Run cleanup every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {str(e)}")
                await asyncio.sleep(60)  # Continue despite errors
    
    def _cleanup_expired(self):
        """Remove expired entries from the cache."""
        current_time = time.time()
        keys_to_remove = []
        
        for key, entry in self._cache.items():
            if entry["expires_at"] <= current_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
        
        if keys_to_remove:
            logger.debug(f"Removed {len(keys_to_remove)} expired cache entries")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        
        # Check if entry has expired
        if entry["expires_at"] <= time.time():
            del self._cache[key]
            return None
        
        # Deserialize the cached data
        return self._deserialize(entry["value"])
    
    async def set(self, key: str, value: Any, expiry: int = settings.CACHE_EXPIRATION):
        """Set a value in the cache with an expiration time in seconds."""
        expires_at = time.time() + expiry
        
        # Serialize the data before storing
        serialized_value = self._serialize(value)
        
        self._cache[key] = {
            "value": serialized_value,
            "expires_at": expires_at
        }
    
    async def delete(self, key: str):
        """Delete a value from the cache."""
        if key in self._cache:
            del self._cache[key]
    
    async def clear(self):
        """Clear all values from the cache."""
        self._cache.clear()
    
    def _serialize(self, value: Any) -> str:
        """Serialize any Python object to a JSON string."""
        try:
            if hasattr(value, '__dict__') or isinstance(value, (list, dict)):
                # Handle Pydantic models, custom classes, or collections of them
                return json.dumps(value, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o))
            else:
                return json.dumps(value)
        except Exception as e:
            logger.error(f"Error serializing cache value: {str(e)}")
            return json.dumps(str(value))
    
    def _deserialize(self, serialized_value: str) -> Any:
        """Deserialize a JSON string back to a Python object.
        Note: This doesn't recreate custom objects, only basic Python types.
        For Pydantic models, you'd need to reconstruct them after deserialization.
        """
        try:
            return json.loads(serialized_value)
        except Exception as e:
            logger.error(f"Error deserializing cache value: {str(e)}")
            return serialized_value

# Singleton pattern to ensure we use the same cache instance throughout the application
_cache_instance = None

@lru_cache(maxsize=1)
def get_cache_service() -> CacheService:
    """Get the global cache service instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance

async def initialize_cache_service():
    """Initialize the cache service and start the cleanup task."""
    service = get_cache_service()
    await service.start()