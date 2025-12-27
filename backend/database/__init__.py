"""
Database package for Document Intelligence Platform
Handles MongoDB and Redis connections
"""

from .mongodb import mongodb
from .redis_cache import redis_client

__all__ = ['mongodb', 'redis_client']