import redis.asyncio as redis
from typing import Optional, Any
import json
import logging

from config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache manager"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.is_connected = False
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            # Test connection
            await self.client.ping()
            
            self.is_connected = True
            logger.info(f"✅ Connected to Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.is_connected = False
            # Don't raise - app should work without Redis
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self.is_connected = False
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_connected:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: int = 3600):
        """Set value in cache with expiration (default 1 hour)"""
        if not self.is_connected:
            return False
        
        try:
            serialized = json.dumps(value)
            await self.client.setex(key, expire, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.is_connected:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.is_connected:
            return False
        
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False
    
    async def get_keys(self, pattern: str = "*"):
        """Get all keys matching pattern"""
        if not self.is_connected:
            return []
        
        try:
            return await self.client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS error: {e}")
            return []
    
    async def increment(self, key: str):
        """Increment a counter"""
        if not self.is_connected:
            return 0
        
        try:
            return await self.client.incr(key)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return 0
    
    async def set_hash(self, key: str, mapping: dict):
        """Set hash field"""
        if not self.is_connected:
            return False
        
        try:
            await self.client.hset(key, mapping=mapping)
            return True
        except Exception as e:
            logger.error(f"Redis HSET error: {e}")
            return False
    
    async def get_hash(self, key: str):
        """Get all hash fields"""
        if not self.is_connected:
            return {}
        
        try:
            return await self.client.hgetall(key)
        except Exception as e:
            logger.error(f"Redis HGETALL error: {e}")
            return {}
    
    async def add_to_set(self, key: str, *values):
        """Add values to a set"""
        if not self.is_connected:
            return False
        
        try:
            await self.client.sadd(key, *values)
            return True
        except Exception as e:
            logger.error(f"Redis SADD error: {e}")
            return False
    
    async def get_set(self, key: str):
        """Get all members of a set"""
        if not self.is_connected:
            return set()
        
        try:
            return await self.client.smembers(key)
        except Exception as e:
            logger.error(f"Redis SMEMBERS error: {e}")
            return set()
    
    async def clear_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        if not self.is_connected:
            return 0
        
        try:
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis CLEAR error: {e}")
            return 0
    
    # Helper methods for document caching
    async def cache_document(self, doc_id: str, data: dict, expire: int = 3600):
        """Cache document data"""
        return await self.set(f"doc:{doc_id}", data, expire)
    
    async def get_cached_document(self, doc_id: str):
        """Get cached document"""
        return await self.get(f"doc:{doc_id}")
    
    async def cache_analysis(self, doc_id: str, analysis_type: str, data: dict, expire: int = 7200):
        """Cache analysis results"""
        return await self.set(f"analysis:{doc_id}:{analysis_type}", data, expire)
    
    async def get_cached_analysis(self, doc_id: str, analysis_type: str):
        """Get cached analysis"""
        return await self.get(f"analysis:{doc_id}:{analysis_type}")

# Global Redis instance
redis_client = RedisCache()