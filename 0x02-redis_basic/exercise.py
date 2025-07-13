#!/usr/bin/env python3
"""
Redis Cache implementation
"""
import redis
import uuid
from typing import Union, Callable, Optional, Any
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """
    Decorator that counts how many times a method is called
    
    Args:
        method: The method to be decorated
        
    Returns:
        The wrapped method that increments a counter in Redis
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """
        Wrapper function that increments the call count and calls the original method
        """
        # Use the method's qualified name as the key
        key = method.__qualname__
        # Increment the counter in Redis
        self._redis.incr(key)
        # Call and return the original method
        return method(self, *args, **kwargs)
    return wrapper


class Cache:
    """Cache class for storing data in Redis"""
    
    def __init__(self):
        """Initialize Redis client and flush database"""
        self._redis = redis.Redis()
        self._redis.flushdb()
    
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store data in Redis with a random key
        
        Args:
            data: The data to store (str, bytes, int, or float)
            
        Returns:
            str: The generated key used to store the data
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key
    
    def get(self, key: str, fn: Optional[Callable] = None) -> Any:
        """
        Get data from Redis and optionally convert it using fn
        
        Args:
            key: The key to retrieve from Redis
            fn: Optional callable to convert the data back to desired format
            
        Returns:
            The data from Redis, optionally converted using fn
        """
        data = self._redis.get(key)
        if data is None:
            return None
        if fn is not None:
            return fn(data)
        return data
    
    def get_str(self, key: str) -> Optional[str]:
        """
        Get data from Redis and convert to string
        
        Args:
            key: The key to retrieve from Redis
            
        Returns:
            The data as a UTF-8 decoded string, or None if key doesn't exist
        """
        return self.get(key, fn=lambda d: d.decode("utf-8"))
    
    def get_int(self, key: str) -> Optional[int]:
        """
        Get data from Redis and convert to integer
        
        Args:
            key: The key to retrieve from Redis
            
        Returns:
            The data as an integer, or None if key doesn't exist
        """
        return self.get(key, fn=int)