import structlog
from typing import Dict, Any, Optional
import time
from contextlib import asynccontextmanager

logger = structlog.get_logger()


class Telemetry:
    @staticmethod
    def log_memory_operation(operation: str, user_id: str, memory_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        logger.info("memory_operation", operation=operation, user_id=str(user_id), memory_id=str(memory_id) if memory_id else None, details=details or {})

    @staticmethod
    def log_retrieval(user_id: str, query: str, method: str, results_count: int, latency_ms: float):
        logger.info("memory_retrieval", user_id=str(user_id), query=query, method=method, results_count=results_count, latency_ms=latency_ms)

    @staticmethod
    def log_evaluation(memory_content: str, relevance: float, novelty: float, accuracy: float, decision: str):
        logger.info("memory_evaluation", memory_content=memory_content[:100], relevance=relevance, novelty=novelty, accuracy=accuracy, decision=decision)

    @staticmethod
    @asynccontextmanager
    async def timed_operation(operation_name: str, user_id: Optional[str] = None):
        start = time.time()
        try:
            yield
        finally:
            elapsed = (time.time() - start) * 1000
            logger.info("timed_operation", operation=operation_name, user_id=str(user_id) if user_id else None, latency_ms=elapsed)


telemetry = Telemetry()
