import time
from typing import Callable, Any
from functools import wraps
from core.exceptions import CircuitBreakerOpenException


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 60, expected_exception: type = Exception):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self._failures = 0
        self._last_failure_time = None
        self._state = "closed"

    @property
    def is_open(self) -> bool:
        if self._state == "open":
            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed > self._recovery_timeout:
                    self._state = "half-open"
                    return False
            return True
        return False

    def record_success(self):
        self._failures = 0
        self._state = "closed"

    def record_failure(self):
        self._failures += 1
        self._last_failure_time = time.time()
        if self._failures >= self.failure_threshold:
            self._state = "open"

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.is_open:
            raise CircuitBreakerOpenException(f"Circuit breaker '{self.name}' is open.")
        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except self.expected_exception as e:
            self.record_failure()
            raise


def circuit_breaker(name: str, failure_threshold: int = 5, recovery_timeout: int = 60, expected_exception: type = Exception):
    breaker = CircuitBreaker(name, failure_threshold, recovery_timeout, expected_exception)
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        wrapper._circuit_breaker = breaker
        return wrapper
    return decorator
