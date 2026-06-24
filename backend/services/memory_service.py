import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.memory import Memory
from storage.postgres import postgres_storage
from storage.chroma import chroma_storage
from utils.embeddings import embedding_service
from utils.telemetry import telemetry
from core.exceptions import StorageException
from services.dedup_service import dedup_service
from datetime import datetime, timezone

class MemoryService:
    async def create_memory(self, user_id: uuid.UUID, content: str, memory_type: str, relevance_score: float, novelty_score: float, accuracy_score: float, conversation_id: uuid.UUID = None, source_turn_id: uuid.UUID = None, event_date: datetime = None, participants: List[str] = None, dedup: bool = True) -> Memory:
        if dedup:
            result = await dedup_service.check_duplicates(user_id=user_id, content=content, memory_type=memory_type)
            if result["is_duplicate"]:
                if result["action"] == "merge":
                    return await dedup_service.merge_memories(existing_memory=result["existing_memory"], new_content=content, new_scores={"relevance": relevance_score, "novelty": novelty_score, "accuracy": accuracy_score})
                telemetry.log_memory_operation("dedup_flagged_not_stored", user_id=user_id, details={"memory_type": memory_type, "reason": "flagged as near duplicate"})
                return result["existing_memory"]

        avg_score = (relevance_score + novelty_score + accuracy_score) / 3.0
        if memory_type == "episodic":
            if event_date is None:
                event_date = datetime.now(timezone.utc)

            if participants is None:
                participants = []
        memory = Memory(user_id=user_id, conversation_id=conversation_id, memory_type=memory_type, content=content, relevance_score=relevance_score, novelty_score=novelty_score, accuracy_score=accuracy_score, avg_score=avg_score, status="active", source_turn_id=source_turn_id, event_date=event_date, participants=participants)
        print(
            f"STORE DEBUG: "
            f"type={memory_type}, "
            f"event_date={event_date}, "
            f"participants={participants}"
        )
        memory = await postgres_storage.create_memory(memory)
        await postgres_storage.create_audit_log(
            user_id=user_id,
            action="create",
            actor="system",
            reason=f"Created {memory_type} memory"
        )
        try:
            embedding = await embedding_service.generate_embedding(content)
            chroma_id = await chroma_storage.add_memory(user_id=user_id, memory_id=memory.id, content=content, embedding=embedding, metadata={"memory_type": memory_type, "avg_score": float(avg_score), "status": "active"})
            memory.chroma_id = chroma_id
            await postgres_storage.update_memory(memory.id, chroma_id=chroma_id)
        except Exception as e:
            telemetry.log_memory_operation("chroma_store_failed", user_id=user_id, memory_id=memory.id, details={"error": str(e)})
        telemetry.log_memory_operation("created", user_id=user_id, memory_id=memory.id, details={"type": memory_type, "avg_score": float(avg_score)})
        return memory

    async def get_memory(self, memory_id: uuid.UUID) -> Memory:
        return await postgres_storage.get_memory(memory_id)

    async def get_user_memories(self, user_id: uuid.UUID, memory_type: str = None, status: str = "active", limit: int = 50) -> List[Memory]:
        return await postgres_storage.get_memories_by_user(user_id=user_id, memory_type=memory_type, status=status, limit=limit)

    async def update_memory(self, memory_id: uuid.UUID, content: str = None, status: str = None, expires_at: datetime = None) -> Memory:
        updates = {}
        if content is not None: updates["content"] = content
        if status is not None: updates["status"] = status
        if expires_at is not None: updates["expires_at"] = expires_at
        memory = await postgres_storage.update_memory(memory_id, **updates)
        if content:
            try:
                await chroma_storage.update_memory(user_id=memory.user_id, memory_id=memory_id, content=content)
            except Exception as e:
                telemetry.log_memory_operation("chroma_update_failed", user_id=memory.user_id, memory_id=memory_id, details={"error": str(e)})
        telemetry.log_memory_operation("updated", user_id=memory.user_id, memory_id=memory_id, details={"fields": list(updates.keys())})
        return memory

    async def delete_memory(self, memory_id: uuid.UUID) -> None:
        memory = await postgres_storage.get_memory(memory_id)
        await postgres_storage.delete_memory(memory_id)
        try:
            await chroma_storage.update_memory(user_id=memory.user_id, memory_id=memory_id, metadata={"status": "deleted"})
        except Exception as e:
            telemetry.log_memory_operation("chroma_delete_failed", user_id=memory.user_id, memory_id=memory_id, details={"error": str(e)})
        telemetry.log_memory_operation("deleted", user_id=memory.user_id, memory_id=memory_id)

    async def get_memory_count(self, user_id: uuid.UUID) -> int:
        return await postgres_storage.get_memory_count(user_id)

    async def get_recent_memories(self, user_id: uuid.UUID, limit: int = 5) -> List[Memory]:
        return await postgres_storage.get_recent_memories(user_id, limit)


memory_service = MemoryService()
