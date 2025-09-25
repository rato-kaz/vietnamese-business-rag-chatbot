import asyncio
import json
import time
from typing import Any, Optional, Dict
import threading
from datetime import datetime, timedelta

from src.core.interfaces.services import CacheService
from src.infrastructure.logging.context import get_logger

logger = get_logger(__name__)


class InMemoryCacheService(CacheService):
    """In-memory implementation of cache service."""
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 10000):
        self.default_ttl = default_ttl
        self.max_size = max_size
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Start cleanup task
        self._start_cleanup_task()
        
        logger.info(
            "Cache service initialized",
            extra={
                "default_ttl": default_ttl,
                "max_size": max_size
            }
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            with self._lock:
                if key not in self._cache:
                    logger.debug(
                        "Cache miss",
                        extra={"key": key}
                    )
                    return None
                
                entry = self._cache[key]
                
                # Check if expired
                if entry["expires_at"] and datetime.now() > entry["expires_at"]:
                    del self._cache[key]
                    logger.debug(
                        "Cache entry expired",
                        extra={"key": key}
                    )
                    return None
                
                # Update access time
                entry["accessed_at"] = datetime.now()
                
                logger.debug(
                    "Cache hit",
                    extra={"key": key}
                )
                
                return entry["value"]
                
        except Exception as e:
            logger.error(
                "Failed to get from cache",
                extra={
                    "key": key,
                    "error": str(e)
                },
                exc_info=True
            )
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> None:
        """Set value in cache."""
        try:
            ttl = ttl or self.default_ttl
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
            
            with self._lock:
                # Check cache size and evict if necessary
                if len(self._cache) >= self.max_size and key not in self._cache:
                    self._evict_lru()
                
                self._cache[key] = {
                    "value": value,
                    "created_at": datetime.now(),
                    "accessed_at": datetime.now(),
                    "expires_at": expires_at
                }
            
            logger.debug(
                "Cache entry set",
                extra={
                    "key": key,
                    "ttl": ttl,
                    "expires_at": expires_at.isoformat() if expires_at else None
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to set cache entry",
                extra={
                    "key": key,
                    "ttl": ttl,
                    "error": str(e)
                },
                exc_info=True
            )
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        try:
            with self._lock:
                if key in self._cache:
                    del self._cache[key]
                    logger.debug(
                        "Cache entry deleted",
                        extra={"key": key}
                    )
                else:
                    logger.debug(
                        "Cache entry not found for deletion",
                        extra={"key": key}
                    )
                    
        except Exception as e:
            logger.error(
                "Failed to delete from cache",
                extra={
                    "key": key,
                    "error": str(e)
                },
                exc_info=True
            )
    
    async def clear(self) -> None:
        """Clear all cache."""
        try:
            with self._lock:
                count = len(self._cache)
                self._cache.clear()
            
            logger.info(
                "Cache cleared",
                extra={"cleared_entries": count}
            )
            
        except Exception as e:
            logger.error(
                "Failed to clear cache",
                extra={"error": str(e)},
                exc_info=True
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self._cache)
            expired_entries = 0
            now = datetime.now()
            
            for entry in self._cache.values():
                if entry["expires_at"] and now > entry["expires_at"]:
                    expired_entries += 1
            
            return {
                "total_entries": total_entries,
                "expired_entries": expired_entries,
                "active_entries": total_entries - expired_entries,
                "max_size": self.max_size,
                "usage_percent": (total_entries / self.max_size) * 100
            }
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]["accessed_at"]
        )
        
        del self._cache[lru_key]
        
        logger.debug(
            "LRU cache entry evicted",
            extra={"evicted_key": lru_key}
        )
    
    def _start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        def cleanup_expired():
            while True:
                try:
                    self._cleanup_expired_entries()
                    # Sleep for 5 minutes
                    time.sleep(300)
                except Exception as e:
                    logger.error(
                        "Error in cache cleanup task",
                        extra={"error": str(e)},
                        exc_info=True
                    )
                    # Sleep for 1 minute before retrying
                    time.sleep(60)
        
        cleanup_thread = threading.Thread(target=cleanup_expired, daemon=True)
        cleanup_thread.start()
        logger.info("Cache cleanup task started")
    
    def _cleanup_expired_entries(self) -> None:
        """Clean up expired cache entries."""
        now = datetime.now()
        expired_keys = []
        
        with self._lock:
            for key, entry in self._cache.items():
                if entry["expires_at"] and now > entry["expires_at"]:
                    expired_keys.append(key)
            
            # Remove expired entries
            for key in expired_keys:
                del self._cache[key]
        
        if expired_keys:
            logger.debug(
                "Expired cache entries cleaned up",
                extra={"expired_count": len(expired_keys)}
            )