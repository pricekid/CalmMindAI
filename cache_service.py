"""
Smart Caching Service for Journal Entries
Provides fast retrieval and intelligent caching mechanisms.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
import hashlib
import json

logger = logging.getLogger(__name__)

class JournalCache:
    """
    Smart caching system for journal entries with automatic expiration
    and intelligent invalidation strategies.
    """
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default TTL
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.access_counts: Dict[str, int] = {}
        self.last_access: Dict[str, float] = {}
        self.user_caches: Dict[str, Dict[str, Any]] = {}
        
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key from parameters."""
        key_data = f"{prefix}:{':'.join(map(str, args))}"
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_data += f":{':'.join(f'{k}={v}' for k, v in sorted_kwargs)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if a cache entry has expired."""
        return time.time() > cache_entry['expires_at']
    
    def _cleanup_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry['expires_at']
        ]
        for key in expired_keys:
            del self.cache[key]
            self.access_counts.pop(key, None)
            self.last_access.pop(key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired."""
        self._cleanup_expired()
        
        if key in self.cache and not self._is_expired(self.cache[key]):
            self.access_counts[key] = self.access_counts.get(key, 0) + 1
            self.last_access[key] = time.time()
            return self.cache[key]['data']
        
        return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache with TTL."""
        if ttl is None:
            ttl = self.default_ttl
        
        self.cache[key] = {
            'data': data,
            'created_at': time.time(),
            'expires_at': time.time() + ttl,
            'ttl': ttl
        }
        self.access_counts[key] = 0
        self.last_access[key] = time.time()
    
    def delete(self, key: str) -> None:
        """Remove item from cache."""
        self.cache.pop(key, None)
        self.access_counts.pop(key, None)
        self.last_access.pop(key, None)
    
    def invalidate_user_entries(self, user_id: str) -> None:
        """Invalidate all cached entries for a specific user."""
        keys_to_delete = [
            key for key in self.cache.keys()
            if f"user:{user_id}" in key
        ]
        for key in keys_to_delete:
            self.delete(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        total_accesses = sum(self.access_counts.values())
        
        return {
            'total_entries': total_entries,
            'total_accesses': total_accesses,
            'avg_accesses_per_entry': total_accesses / max(total_entries, 1),
            'cache_size_mb': len(str(self.cache)) / (1024 * 1024)
        }

# Global cache instance
journal_cache = JournalCache(default_ttl=600)  # 10 minutes

def cached_query(cache_key_prefix: str, ttl: int = 300):
    """
    Decorator for caching database query results.
    
    Args:
        cache_key_prefix: Prefix for the cache key
        ttl: Time to live in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = journal_cache._generate_key(cache_key_prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = journal_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for key: {cache_key}, executing query")
            result = func(*args, **kwargs)
            
            # Cache the result
            journal_cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def cache_user_entries(user_id: str, entries: List[Any], ttl: int = 300) -> None:
    """Cache user's journal entries."""
    cache_key = journal_cache._generate_key("user_entries", user_id)
    journal_cache.set(cache_key, entries, ttl)

def get_cached_user_entries(user_id: str) -> Optional[List[Any]]:
    """Get cached user journal entries."""
    cache_key = journal_cache._generate_key("user_entries", user_id)
    return journal_cache.get(cache_key)

def cache_entry_details(entry_id: str, entry_data: Dict[str, Any], ttl: int = 600) -> None:
    """Cache detailed journal entry data."""
    cache_key = journal_cache._generate_key("entry_details", entry_id)
    journal_cache.set(cache_key, entry_data, ttl)

def get_cached_entry_details(entry_id: str) -> Optional[Dict[str, Any]]:
    """Get cached journal entry details."""
    cache_key = journal_cache._generate_key("entry_details", entry_id)
    return journal_cache.get(cache_key)

def invalidate_user_cache(user_id: str) -> None:
    """Invalidate all cache entries for a user."""
    journal_cache.invalidate_user_entries(user_id)
    logger.info(f"Invalidated cache for user: {user_id}")

def cache_user_stats(user_id: str, stats: Dict[str, Any], ttl: int = 900) -> None:
    """Cache user statistics (15 minutes TTL)."""
    cache_key = journal_cache._generate_key("user_stats", user_id)
    journal_cache.set(cache_key, stats, ttl)

def get_cached_user_stats(user_id: str) -> Optional[Dict[str, Any]]:
    """Get cached user statistics."""
    cache_key = journal_cache._generate_key("user_stats", user_id)
    return journal_cache.get(cache_key)

def preload_user_data(user_id: str, force_refresh: bool = False) -> None:
    """
    Preload and cache commonly accessed user data.
    
    Args:
        user_id: The user ID to preload data for
        force_refresh: Whether to force refresh cached data
    """
    from models import JournalEntry, User
    from sqlalchemy.orm import joinedload
    
    if force_refresh:
        invalidate_user_cache(user_id)
    
    # Check if already cached
    if not force_refresh and get_cached_user_entries(user_id) is not None:
        return
    
    try:
        # Preload recent entries with optimized query
        recent_entries = JournalEntry.query.options(
            joinedload(JournalEntry.author)
        ).filter(
            JournalEntry.user_id == user_id
        ).order_by(
            JournalEntry.created_at.desc()
        ).limit(20).all()
        
        # Cache the entries
        entry_data = []
        for entry in recent_entries:
            entry_dict = {
                'id': entry.id,
                'title': entry.title,
                'content': entry.content,
                'anxiety_level': entry.anxiety_level,
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
                'is_analyzed': entry.is_analyzed,
                'coach_response': entry.coach_response
            }
            entry_data.append(entry_dict)
            
            # Also cache individual entry details
            cache_entry_details(str(entry.id), entry_dict)
        
        cache_user_entries(user_id, entry_data)
        logger.info(f"Preloaded {len(entry_data)} entries for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error preloading user data for {user_id}: {e}")

def get_cache_status() -> Dict[str, Any]:
    """Get overall cache status and statistics."""
    return {
        'cache_stats': journal_cache.get_stats(),
        'active_entries': len(journal_cache.cache),
        'total_users_cached': len(set(
            key.split(':')[1] for key in journal_cache.cache.keys()
            if key.startswith('user_entries:')
        ))
    }