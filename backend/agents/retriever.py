import uuid
from typing import List
from services.retrieval_service import retrieval_service, RetrievedMemory
from utils.telemetry import telemetry


class MemoryRetrieverAgent:
    async def retrieve(self, user_id: uuid.UUID, query: str, top_k: int = 5) -> List[RetrievedMemory]:
        print(f"RETRIEVER AGENT: user_id={user_id}, query='{query}', top_k={top_k}")
        telemetry.log_memory_operation("retrieval_started", user_id=user_id, details={"query": query[:100], "top_k": top_k})
        results = await retrieval_service.retrieve_memories(user_id=user_id, query=query, top_k=top_k)
        print(f"RETRIEVER AGENT: retrieval_service returned {len(results)} results")
        return results


retriever_agent = MemoryRetrieverAgent()
