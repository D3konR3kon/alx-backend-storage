import requests
import redis
from functools import wraps
from typing import Optional

class RedisCache:
    """Wrapper class for Redis operations with error handling"""
    
    def __init__(self):
        self.redis_client = self._connect_to_redis()
    
    def _connect_to_redis(self) -> Optional[redis.Redis]:
        """Attempt to connect to Redis with error handling"""
        try:
            return redis.Redis()
        except redis.ConnectionError:
            print("Warning: Could not connect to Redis server. Caching and tracking will be disabled.")
            return None
    
    def get(self, key: str) -> Optional[str]:
        """Safe get operation with error handling"""
        if not self.redis_client:
            return None
        try:
            return self.redis_client.get(key)
        except redis.RedisError:
            return None
    
    def setex(self, key: str, time: int, value: str) -> bool:
        """Safe setex operation with error handling"""
        if not self.redis_client:
            return False
        try:
            return self.redis_client.setex(key, time, value)
        except redis.RedisError:
            return False
    
    def incr(self, key: str) -> Optional[int]:
        """Safe increment operation with error handling"""
        if not self.redis_client:
            return None
        try:
            return self.redis_client.incr(key)
        except redis.RedisError:
            return None


redis_cache = RedisCache()

def get_page(url: str) -> str:
    """
    Fetches HTML content of a URL, tracks access count, and caches results.
    
    Args:
        url: The URL to fetch content from
        
    Returns:
        The HTML content of the URL
    """
    cache_key = f"cache:{url}"
    cached_content = redis_cache.get(cache_key)
    
    if cached_content:
        return cached_content.decode('utf-8')
    
    response = requests.get(url)
    html_content = response.text
    
    redis_cache.setex(cache_key, 10, html_content)
    
    count_key = f"count:{url}"
    redis_cache.incr(count_key)
    
    return html_content

# Bonus: Decorator implementation
def cache_with_access_tracking(expiration: int = 10):
    """
    Decorator to cache function results with access tracking.
    
    Args:
        expiration: Cache expiration time in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(url: str) -> str:
            cache_key = f"decorator_cache:{url}"
            cached_content = redis_cache.get(cache_key)
            
            if cached_content:
                return cached_content.decode('utf-8')
            
            result = func(url)
            redis_cache.setex(cache_key, expiration, result)
 
            count_key = f"decorator_count:{url}"
            redis_cache.incr(count_key)
            
            return result
        return wrapper
    return decorator

if __name__ == "__main__":
    try:
      
        test_url = "http://slowwly.robertomurray.co.uk"
        print("Fetching content (first time - should be slow)...")
        content = get_page(test_url)
        print(f"Got content of length: {len(content)}")
        
        print("Fetching again (should be fast from cache)...")
        content = get_page(test_url)
        print(f"Got content of length: {len(content)}")
        
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")