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
        except Exception as e:
            method_used = "keyword"

        try:
            keyword_memories = await postgres_storage.search_memories_keyword(user_id=user_id, query=query, top_k=top_k * 2)
            keyword_results = [{"id": str(m.id), "content": m.content, "metadata": {"memory_type": m.memory_type, "avg_score": float(m.avg_score)}, "distance": 0.5} for m in keyword_memories]
        except Exception as e:
            print(f"RETRIEVAL: ChromaDB failed: {str(e)}")
            pass

        fused_results = self._reciprocal_rank_fusion(vector_results, keyword_results, k=60)
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
        scores = {}
        for rank, result in enumerate(vector_results):
            doc_id = result["id"]
            distance = result.get("distance", 0.5)
            similarity = max(0, 1 - distance)
            scores[doc_id] = scores.get(doc_id, 0) + similarity * (1.0 / (k + rank + 1))
        for rank, result in enumerate(keyword_results):
            doc_id = result["id"]
            keyword_score = 1.0 / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + keyword_score * settings.RETRIEVAL_KEYWORD_WEIGHT
        sorted_results = []
        for doc_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            full_result = None
            for r in vector_results + keyword_results:
                if r["id"] == doc_id:
                    full_result = r
                    break
            if full_result:
                full_result["score"] = score
                sorted_results.append(full_result)
        return sorted_results

    def _generate_explanation(self, query: str, memory: Memory, similarity_score: float, retrieval_method: str) -> str:
        method_desc = {"hybrid": "semantic similarity and keyword matching", "vector": "semantic meaning similarity", "keyword": "keyword matching"}.get(retrieval_method, "search")
        age_desc = self._describe_age(memory.created_at)
        return f"This memory was retrieved because your query '{query[:50]}...' matches this memory through {method_desc}. Relevance score: {similarity_score:.0%}. This memory was first recorded {age_desc}."

    def _describe_age(self, created_at: datetime) -> str:
        if not created_at: return "at an unknown time"
        delta = datetime.utcnow() - created_at
        days = delta.days
        if days == 0: return "today"
        elif days == 1: return "yesterday"
        elif days < 7: return f"{days} days ago"
        elif days < 30: weeks = days // 7; return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif days < 365: months = days // 30; return f"{months} month{'s' if months > 1 else ''} ago"
        else: years = days // 365; return f"{years} year{'s' if years > 1 else ''} ago"


retrieval_service = RetrievalService()
