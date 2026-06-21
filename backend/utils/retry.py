import asyncio
from functools import wraps
from typing import Callable, Any, Optional


class RetryConfig:
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0, max_delay: float = 10.0, exponential_base: float = 2.0, retryable_exceptions: tuple = (Exception,)):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions


def retry(config: Optional[RetryConfig] = None):
    if config is None:
        config = RetryConfig()
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    if attempt == config.max_retries:
                        break
                    delay = min(config.initial_delay * (config.exponential_base ** attempt), config.max_delay)
                    await asyncio.sleep(delay)
            raise last_exception
        return wrapper
    return decorator
