"""
Rate Limiter Module
Provides rate limiting for API calls
"""

import time
from functools import wraps
from typing import Callable, Optional

from ratelimit import limits, sleep_and_retry


class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, calls: int = 30, period: int = 60):
        """
        Initialize rate limiter
        
        Args:
            calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self._last_call_time: float = 0
        self._min_interval: float = period / calls
    
    def wait(self):
        """Wait if necessary to respect rate limit"""
        elapsed = time.time() - self._last_call_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call_time = time.time()
    
    def limit(self, func: Callable) -> Callable:
        """
        Decorator to rate limit a function
        
        Args:
            func: Function to rate limit
        
        Returns:
            Rate limited function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.wait()
            return func(*args, **kwargs)
        return wrapper


def rate_limit(calls: int = 30, period: int = 60):
    """
    Decorator factory for rate limiting
    
    Args:
        calls: Maximum number of calls allowed
        period: Time period in seconds
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @sleep_and_retry
        @limits(calls=calls, period=period)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
