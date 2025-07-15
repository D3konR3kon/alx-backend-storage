#!/usr/bin/env python3
"""
Web page caching with Redis
"""
import redis
import requests
from typing import Callable
from functools import wraps

redis_client = redis.Redis(decode_responses=True)

def url_access_count(method: Callable) -> Callable:
    """
    Decorator to count URL access and cache results with expiration
    
    Args:
        method: The method to be decorated
        
    Returns:
        The wrapped method that counts access and caches results
    """
    @wraps(method)
    def wrapper(url: str) -> str:
        """
        Wrapper function that counts URL access and handles caching
        """

        count_key = f"count:{url}"
        cache_key = f"cache:{url}"

        # Increment access count
        redis_client.incr(count_key)

        # Check for cached result
        cached_result = redis_client.get(cache_key)
        if cached_result:
            return cached_result

        # Get fresh result and cache it
        result = method(url)
        redis_client.setex(cache_key, 10, result)

        return result
    return wrapper


@url_access_count
def get_page(url: str) -> str:
    """
    Get HTML content of a URL with caching and access counting
    
    Args:
        url: The URL to fetch
        
    Returns:
        The HTML content of the page
    """
    response = requests.get(url)
    return response.text


def get_page_no_decorator(url: str) -> str:
    """
    Get HTML content of a URL with caching and access counting (no decorator)
    
    Args:
        url: The URL to fetch
        
    Returns:
        The HTML content of the page
    """

    count_key = f"count:{url}"
    cache_key = f"cache:{url}"

    # Increment access count
    redis_client.incr(count_key)

    # Check for cached result
    cached_result = redis_client.get(cache_key)
    if cached_result:
        return cached_result

    # Get fresh result and cache it
    response = requests.get(url)
    result = response.text
    redis_client.setex(cache_key, 10, result)

    return result


def get_url_access_count(url: str) -> int:
    """
    Get the number of times a URL has been accessed
    
    Args:
        url: The URL to check
        
    Returns:
        The number of times the URL has been accessed
    """
    count = redis_client.get(f"count:{url}")
    return int(count) if count else 0


def clear_url_cache(url: str) -> None:
    """
    Clear the cache for a specific URL
    
    Args:
        url: The URL to clear from cache
    """
    redis_client.delete(f"cache:{url}")


def clear_all_cache() -> None:
    """
    Clear all cached URLs and counts
    """
    redis_client.flushdb()


if __name__ == "__main__":
    import time

    print("Testing get_page function with caching...")
    slow_url = "http://www.google.com"
    print(f"First request to {slow_url}...")
    start_time = time.time()
    result1 = get_page(slow_url)
    end_time = time.time()
    print(f"First request took {end_time - start_time:.2f} seconds")
    print(f"Access count: {get_url_access_count(slow_url)}")

    print(f"\nSecond request to {slow_url} (should be cached)...")
    start_time = time.time()
    result2 = get_page(slow_url)
    end_time = time.time()
    print(f"Second request took {end_time - start_time:.2f} seconds")
    print(f"Access count: {get_url_access_count(slow_url)}")

    print(f"\nResults are identical: {result1 == result2}")

    print("\nWaiting 11 seconds for cache to expire...")
    time.sleep(11)
    print(f"Third request to {slow_url} (cache should be expired)...")
    start_time = time.time()
    result3 = get_page(slow_url)
    end_time = time.time()
    print(f"Third request took {end_time - start_time:.2f} seconds")
    print(f"Access count: {get_url_access_count(slow_url)}")