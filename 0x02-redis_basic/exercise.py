#!/usr/bin/env python3
"""
Redis Cache implementation
"""
import redis
import uuid
from typing import Union, Callable, Optional, Any
from functools import wraps


def replay(method: Callable) -> None:
    """
    Display the history of calls of a particular function
    
    Args:
        method: The method to display call history for
    """
    # Get the Redis instance from the method's class (assuming it's a Cache method)
    # We need to access the Redis instance through the method's class
    redis_instance = method.__self__._redis
    
    # Generate keys for count, inputs, and outputs
    method_name = method.__qualname__
    count_key = method_name
    inputs_key = f"{method_name}:inputs"
    outputs_key = f"{method_name}:outputs"
    
    # Get the call count
    count = redis_instance.get(count_key)
    if count is None:
        count = 0
    else:
        count = int(count)
    
    # Get the inputs and outputs history
    inputs = redis_instance.lrange(inputs_key, 0, -1)
    outputs = redis_instance.lrange(outputs_key, 0, -1)
    
    # Display the summary
    print(f"{method_name} was called {count} times:")
    
    # Display each call with its input and output
    for input_args, output in zip(inputs, outputs):
        # Decode bytes to string if needed
        if isinstance(input_args, bytes):
            input_args = input_args.decode('utf-8')
        if isinstance(output, bytes):
            output = output.decode('utf-8')
        
        print(f"{method_name}(*{input_args}) -> {output}")


def call_history(method: Callable) -> Callable:
    """
    Decorator that stores the history of inputs and outputs for a function
    
    Args:
        method: The method to be decorated
        
    Returns:
        The wrapped method that stores input/output history in Redis lists
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """
        Wrapper function that stores input/output history and calls the original method
        """
        # Create keys for input and output lists
        input_key = f"{method.__qualname__}:inputs"
        output_key = f"{method.__qualname__}:outputs"
        
        # Store input arguments in Redis list (normalize to string)
        self._redis.rpush(input_key, str(args))
        
        # Execute the original method to get the output
        output = method(self, *args, **kwargs)
        
        # Store output in Redis list
        self._redis.rpush(output_key, output)
        
        return output
    return wrapper


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
    
    @call_history
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