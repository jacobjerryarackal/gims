import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from models.memory import Memory
from storage.postgres import postgres_storage
from storage.chroma import chroma_storage
from utils.embeddings import embedding_service
from utils.telemetry import telemetry
from core.config import settings
from core.exceptions import CircuitBreakerOpenException
import time


class RetrievedMemory:
    def __init__(self, memory: Memory, similarity_score: float, retrieval_method: str, explanation: str):
        self.memory = memory
        self.similarity_score = similarity_score
        self.retrieval_method = retrieval_method
        self.explanation = explanation


class RetrievalService:
    async def retrieve_memories(self, user_id: uuid.UUID, query: str, top_k: int = None) -> List[RetrievedMemory]:
        if top_k is None: top_k = settings.RETRIEVAL_TOP_K
        start_time = time.time()
        vector_results = []
        keyword_results = []
        method_used = "hybrid"

        try:
            query_embedding = await embedding_service.generate_embedding(query)
            print(f"RETRIEVAL: Generated embedding length={len(query_embedding)}")
            vector_results = await chroma_storage.query_similar(user_id=user_id, query_embedding=query_embedding, top_k=top_k * 2)
            print(f"RETRIEVAL: ChromaDB returned {len(vector_results)} results")
        except CircuitBreakerOpenException:
            method_used = "keyword"
            print("RETRIEVAL: Vector search disabled by circuit breaker")
        except Exception as e:
            print(f"RETRIEVAL: ChromaDB vector search failed: {type(e).__name__}: {str(e)}")
            method_used = "keyword"
            print(f"RETRIEVAL: Vector search exception: {type(e).__name__}: {str(e)}")

        try:
            keyword_memories = await postgres_storage.search_memories_keyword(user_id=user_id, query=query, top_k=top_k * 2)
            keyword_results = [{"id": str(m.id), "content": m.content, "metadata": {"memory_type": m.memory_type, "avg_score": float(m.avg_score)}, "distance": 0.5} for m in keyword_memories]
            print(f"RETRIEVAL: Keyword search returned {len(keyword_results)} results")
        except Exception as e:
            print(f"RETRIEVAL: Keyword search exception: {type(e).__name__}: {str(e)}")
            keyword_results = []

        fused_results = self._reciprocal_rank_fusion(vector_results, keyword_results, k=60)

        generic_query = self._is_generic_recall_query(query)
        generic_fallback_results = []
        if generic_query:
            generic_fallback_results = await self._retrieve_top_memories(user_id=user_id, top_k=top_k)

        if generic_query and (not fused_results or self._is_low_confidence(fused_results)):
            if generic_fallback_results:
                method_used = "generic_recall"
                fused_results = generic_fallback_results
                print(f"RETRIEVAL: Generic recall query, returning top {len(fused_results)} memories")

        if not fused_results:
            recent_memories = await postgres_storage.get_recent_memories(user_id=user_id, limit=top_k)
            if recent_memories:
                method_used = "fallback"
                fused_results = [
                    {
                        "id": str(m.id),
                        "content": m.content,
                        "metadata": {"memory_type": m.memory_type, "avg_score": float(m.avg_score)},
                        "distance": 1.0,
                        "score": 0.1,
                    }
                    for m in recent_memories
                ]
                print(f"RETRIEVAL: No vector/keyword results, falling back to {len(fused_results)} recent memories")

        retrieved = []
        for result in fused_results[:top_k]:
            memory_id = uuid.UUID(result["id"])
            try:
                memory = await postgres_storage.get_memory(memory_id)
                await postgres_storage.update_memory(memory_id, access_count=memory.access_count + 1, last_accessed_at=datetime.utcnow())
                explanation = self._generate_explanation(query=query, memory=memory, similarity_score=result.get("score", 0.5), retrieval_method=method_used)
                retrieved.append(RetrievedMemory(memory=memory, similarity_score=result.get("score", 0.5), retrieval_method=method_used, explanation=explanation))
            except Exception as e:
                print(f"RETRIEVAL: ChromaDB failed 2: {str(e)}")
                continue

        latency_ms = (time.time() - start_time) * 1000
        telemetry.log_retrieval(user_id=user_id, query=query, method=method_used, results_count=len(retrieved), latency_ms=latency_ms)
        return retrieved

    def _reciprocal_rank_fusion(self, vector_results: List[Dict], keyword_results: List[Dict], k: int = 60) -> List[Dict]:
        # Compute a weighted fused score from vector and keyword results.
        # Convert raw distances to a similarity metric first, then apply configured weights.
        scores: Dict[str, float] = {}
        for rank, result in enumerate(vector_results):
            doc_id = result["id"]
            distance = result.get("distance", 1.0)
            similarity = self._convert_distance_to_similarity(distance)
            # Reciprocal rank scaling for vector ranks
            scores[doc_id] = scores.get(doc_id, 0.0) + similarity * settings.RETRIEVAL_VECTOR_WEIGHT * (1.0 / (k + rank + 1))

        for rank, result in enumerate(keyword_results):
            doc_id = result["id"]
            keyword_score = 1.0 / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0.0) + keyword_score * settings.RETRIEVAL_KEYWORD_WEIGHT

        # Normalize scores to 0..1 so explanations and downstream logic are meaningful
        if not scores:
            return []
        max_score = max(scores.values())
        normalized = {doc_id: (score / max_score if max_score > 0 else 0.0) for doc_id, score in scores.items()}

        sorted_results: List[Dict] = []
        for doc_id, score in sorted(normalized.items(), key=lambda x: x[1], reverse=True):
            full_result = next((r for r in vector_results + keyword_results if r["id"] == doc_id), None)
            if full_result:
                # assign normalized score
                full_result = dict(full_result)
                full_result["score"] = score
                sorted_results.append(full_result)
        return sorted_results

    def _convert_distance_to_similarity(self, distance: float) -> float:
        """Convert Chroma 'distance' to a 0..1 similarity score.

        Handles common cases: cosine-style distances (0..2), or other metric distances.
        """
        try:
            d = float(distance)
        except Exception:
            return 0.0
        # Common case: cosine distance reported in [0,2]
        if 0.0 <= d <= 2.0:
            # map 0->1.0, 2->0.0
            return max(0.0, 1.0 - (d / 2.0))
        # Fallback: L2 or other non-normalized distance -> soft invert
        return 1.0 / (1.0 + d)

    def _is_low_confidence(self, results: List[Dict[str, Any]]) -> bool:
        if not results:
            return True
        return all((result.get("score", 0.0) < 0.15 for result in results))

    def _generate_explanation(self, query: str, memory: Memory, similarity_score: float, retrieval_method: str) -> str:
        method_desc = {"hybrid": "semantic similarity and keyword matching", "vector": "semantic meaning similarity", "keyword": "keyword matching", "generic_recall": "general user memory recall", "fallback": "recent memory fallback"}.get(retrieval_method, "search")
        age_desc = self._describe_age(memory.created_at)
        return f"This memory was retrieved because your query '{query[:50]}...' matches this memory through {method_desc}. Relevance score: {similarity_score:.0%}. This memory was first recorded {age_desc}."

    def _is_generic_recall_query(self, query: str) -> bool:
        normalized = query.strip().lower()
        triggers = [
            "what do you know about me",
            "what can you remember",
            "do you remember",
            "what do you remember",
            "tell me about me",
            "what do i tell you",
            "what have i told you",
            "what do you recall",
            "remember anything about me",
        ]
        return any(trigger in normalized for trigger in triggers)

    async def _retrieve_top_memories(self, user_id: uuid.UUID, top_k: int) -> List[Dict[str, Any]]:
        memories = await postgres_storage.get_memories_by_user(user_id=user_id, status="active", limit=100)
        sorted_memories = sorted(memories, key=lambda m: (-float(m.avg_score), m.created_at), reverse=False)
        top_memories = sorted_memories[:top_k]
        return [
            {
                "id": str(m.id),
                "content": m.content,
                "metadata": {"memory_type": m.memory_type, "avg_score": float(m.avg_score)},
                "distance": 1.0,
                "score": float(m.avg_score),
            }
            for m in top_memories
        ]

    def _describe_age(self, created_at: datetime) -> str:
        if not created_at:
            return "at an unknown time"
        
        # Handle timezone-aware vs naive datetimes
        now = datetime.utcnow()
        if created_at.tzinfo is not None:
            # created_at is timezone-aware, make 'now' timezone-aware too
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)
        
        delta = now - created_at
        days = delta.days
        if days == 0:
            return "today"
        elif days == 1:
            return "yesterday"
        elif days < 7:
            return f"{days} days ago"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif days < 365:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"


retrieval_service = RetrievalService()
