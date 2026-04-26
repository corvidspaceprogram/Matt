"""
Retry utilities with exponential backoff for network operations.

This module provides a decorator for automatic retry with exponential backoff
for network operations that may fail transiently.
"""

import time
import functools
import os
from bot_exceptions import NetworkError


def retry_with_backoff(max_retries=None, initial_delay=None, max_delay=None):
    """
    Retry decorator with exponential backoff for network operations.
    
    Args:
        max_retries: Maximum number of retry attempts (default: from env or 5)
        initial_delay: Initial delay in seconds (default: from env or 10)
        max_delay: Maximum delay in seconds (default: from env or 60)
    
    The decorator catches NetworkError exceptions and retries with exponential
    backoff: 1s, 2s, 4s, 8s, etc. (capped at max_delay).
    
    Usage:
        @retry_with_backoff(max_retries=3, initial_delay=1, max_delay=60)
        def my_network_function():
            ...
    """
    # Use environment variables if not specified
    if max_retries is None:
        max_retries = int(os.getenv('MAX_RETRIES', '5'))
    if initial_delay is None:
        initial_delay = float(os.getenv('RETRY_INITIAL_DELAY', '10'))
    if max_delay is None:
        max_delay = float(os.getenv('RETRY_MAX_DELAY', '300'))
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except NetworkError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = min(initial_delay * (2 ** attempt), max_delay)
                        print(f"Retry {attempt + 1}/{max_retries} for {func.__name__} after {delay}s... Error: {e}", flush=True)
                        time.sleep(delay)
                    else:
                        # All retries exhausted
                        raise last_exception
                except Exception as e:
                    # Non-NetworkError exceptions should not be retried
                    raise
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            
            return None
        return wrapper
    return decorator


def retry_on_exception(exception_types=None, max_retries=None, initial_delay=None, max_delay=None):
    """
    Generic retry decorator that can handle specific exception types.
    
    Args:
        exception_types: Tuple of exception types to catch and retry (default: NetworkError)
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
    
    Usage:
        @retry_on_exception(exception_types=(NetworkError, ConnectionError))
        def my_function():
            ...
    """
    if exception_types is None:
        exception_types = (NetworkError,)
    
    # Use environment variables if not specified
    if max_retries is None:
        max_retries = int(os.getenv('MAX_RETRIES', '5'))
    if initial_delay is None:
        initial_delay = float(os.getenv('RETRY_INITIAL_DELAY', '10'))
    if max_delay is None:
        max_delay = float(os.getenv('RETRY_MAX_DELAY', '300'))
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exception_types as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = min(initial_delay * (2 ** attempt), max_delay)
                        print(f"Retry {attempt + 1}/{max_retries} for {func.__name__} after {delay}s...", flush=True)
                        time.sleep(delay)
                    else:
                        raise last_exception
                except Exception as e:
                    # Non-specified exceptions should not be retried
                    raise
            
            if last_exception:
                raise last_exception
            
            return None
        return wrapper
    return decorator
