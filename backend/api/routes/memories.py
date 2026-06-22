from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime

from services.memory_service import memory_service
from services.dedup_service import dedup_service
from storage.postgres import postgres_storage
from core.exceptions import MemoryNotFoundException

router = APIRouter(tags=["memories"])

class MemoryCreateRequest(BaseModel):
    user_id: str
    content: str = Field(..., max_length=2000)
    memory_type: str
    expires_at: Optional[datetime] = None

class MemoryResponse(BaseModel):
    id: str
    user_id: str
    content: str
    memory_type: str
    status: str
    avg_score: float
    created_at: datetime
    expires_at: Optional[datetime] = None

class MemoryListResponse(BaseModel):
    memories: List[MemoryResponse]
    total: int

@router.get("", response_model=MemoryListResponse)
async def list_memories(user_id: str, memory_type: Optional[str] = None, status: str = "active", limit: int = 50):
    user_uuid = uuid.UUID(user_id)
    memories = await memory_service.get_user_memories(user_id=user_uuid, memory_type=memory_type, status=status, limit=limit)
    return MemoryListResponse(memories=[
        MemoryResponse(id=str(m.id), user_id=str(m.user_id), content=m.content, memory_type=m.memory_type, status=m.status, avg_score=float(m.avg_score) if m.avg_score else 0.0, created_at=m.created_at, expires_at=m.expires_at)
        for m in memories
    ], total=len(memories))

@router.post("", response_model=MemoryResponse, status_code=201)
async def create_memory(request: MemoryCreateRequest):
    user_id = uuid.UUID(request.user_id)
    memory = await memory_service.create_memory(user_id=user_id, content=request.content, memory_type=request.memory_type, relevance_score=0.9, novelty_score=0.9, accuracy_score=0.9)
    if request.expires_at:
        await memory_service.update_memory(memory.id, expires_at=request.expires_at)
    return MemoryResponse(id=str(memory.id), user_id=str(memory.user_id), content=memory.content, memory_type=memory.memory_type, status=memory.status, avg_score=float(memory.avg_score) if memory.avg_score else 0.0, created_at=memory.created_at, expires_at=memory.expires_at)

@router.get("/stats")
async def get_memory_stats(user_id: str = Query(...)):
    """Get memory statistics for a user."""
    import traceback
    try:
        user_uuid = uuid.UUID(user_id)
        print(f"STATS DEBUG: user_uuid={user_uuid}")
        
        # Test get_memory_count
        try:
            total = await memory_service.get_memory_count(user_uuid)
            print(f"STATS DEBUG: total={total}")
        except Exception as e:
            print(f"STATS DEBUG ERROR get_memory_count: {traceback.format_exc()}")
            total = 0
        
        # Test get_user_memories with no type filter
        try:
            all_memories = await memory_service.get_user_memories(user_uuid, limit=1000)
            print(f"STATS DEBUG: all_memories={len(all_memories)}")
        except Exception as e:
            print(f"STATS DEBUG ERROR get_user_memories: {traceback.format_exc()}")
            all_memories = []
        
        # Calculate by type manually
        semantic = sum(1 for m in all_memories if m.memory_type == "semantic")
        procedural = sum(1 for m in all_memories if m.memory_type == "procedural")
        episodic = sum(1 for m in all_memories if m.memory_type == "episodic")
        
        return {
            "total_memories": len(all_memories),
            "by_type": {
                "semantic": semantic,
                "procedural": procedural,
                "episodic": episodic
            },
            "recently_added": len(all_memories),
            "active_memories": len(all_memories)
        }
    except Exception as e:
        print(f"STATS DEBUG ERROR: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: str):
    memory_uuid = uuid.UUID(memory_id)
    memory = await memory_service.get_memory(memory_uuid)
    return MemoryResponse(id=str(memory.id), user_id=str(memory.user_id), content=memory.content, memory_type=memory.memory_type, status=memory.status, avg_score=float(memory.avg_score) if memory.avg_score else 0.0, created_at=memory.created_at, expires_at=memory.expires_at)

@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(memory_id: str, request: dict):
    memory_uuid = uuid.UUID(memory_id)
    memory = await memory_service.update_memory(memory_uuid, content=request.get("content"), status=request.get("status"), expires_at=request.get("expires_at"))
    return MemoryResponse(id=str(memory.id), user_id=str(memory.user_id), content=memory.content, memory_type=memory.memory_type, status=memory.status, avg_score=float(memory.avg_score) if memory.avg_score else 0.0, created_at=memory.created_at, expires_at=memory.expires_at)

@router.delete("/{memory_id}", status_code=204)
async def delete_memory(memory_id: str):
    memory_uuid = uuid.UUID(memory_id)
    await memory_service.delete_memory(memory_uuid)

@router.post("/search")
async def search_memories(user_id: str, query: str, search_method: str = "hybrid", top_k: int = 5):
    user_uuid = uuid.UUID(user_id)
    if search_method == "keyword":
        memories = await postgres_storage.search_memories_keyword(user_id=user_uuid, query=query, top_k=top_k)
    else:
        from services.retrieval_service import retrieval_service
        results = await retrieval_service.retrieve_memories(user_id=user_uuid, query=query, top_k=top_k)
        memories = [r.memory for r in results]
    return {"results": [{"id": str(m.id), "content": m.content, "memory_type": m.memory_type, "avg_score": float(m.avg_score) if m.avg_score else 0.0} for m in memories], "method_used": search_method}

@router.post("/dedup")
async def run_dedup(user_id: str, similarity_threshold: float = 0.85):
    user_uuid = uuid.UUID(user_id)
    return await dedup_service.run_dedup_scan(user_uuid)