import uuid
from typing import List, Optional
from datetime import datetime
from models.user import User
from models.memory import Memory
from models.hitl import HITLQueue
from storage.postgres import postgres_storage
from utils.telemetry import telemetry
from core.exceptions import UserNotFoundException
from services.memory_service import memory_service


class GovernanceService:
    async def get_or_create_user(self, email: str, name: str = None) -> User:
        user = await postgres_storage.get_user_by_email(email)
        if user:
            return user
        user = await postgres_storage.create_user(email=email, name=name)
        telemetry.log_memory_operation("user_created", user_id=user.id, details={"email": email})
        return user

    async def get_user(self, user_id: uuid.UUID) -> User:
        return await postgres_storage.get_user(user_id)

    async def update_consent(self, user_id: uuid.UUID, consent_given: bool) -> User:
        telemetry.log_memory_operation("consent_updated", user_id=user_id, details={"consent_given": consent_given})
        return await postgres_storage.get_user(user_id)

    async def get_user_stats(self, user_id: uuid.UUID) -> dict:
        memory_count = await postgres_storage.get_memory_count(user_id)
        memories = await postgres_storage.get_memories_by_user(user_id, limit=1000)
        type_counts = {}
        for mem in memories:
            type_counts[mem.memory_type] = type_counts.get(mem.memory_type, 0) + 1
        return {"user_id": str(user_id), "total_memories": memory_count, "memory_types": type_counts, "avg_quality": sum(float(m.avg_score) for m in memories) / len(memories) if memories else 0}

    async def create_hitl_item(self, **kwargs) -> HITLQueue:
        return await postgres_storage.create_hitl_item(**kwargs)

    async def get_hitl_queue(self, user_id: uuid.UUID = None, status: str = "pending") -> List[HITLQueue]:
        return await postgres_storage.get_hitl_queue(user_id=user_id, status=status)

    async def review_hitl_item(self, item_id: uuid.UUID, action: str, reviewer_notes: str = None) -> HITLQueue:
        updates = {"status": "approved" if action == "approve" else "rejected", "reviewer_notes": reviewer_notes, "reviewed_at": datetime.utcnow()}
        item = await postgres_storage.update_hitl_item(item_id, **updates)
        if action == "approve" and item.memory_id:
            await memory_service.update_memory(item.memory_id, status="active")
        elif action == "reject" and item.memory_id:
            await memory_service.update_memory(item.memory_id, status="deleted")
        telemetry.log_memory_operation(f"hitl_{action}", user_id=item.user_id, memory_id=item.memory_id, details={"notes": reviewer_notes})
        return item

    async def get_audit_logs(self, user_id: uuid.UUID = None, action: str = None, limit: int = 100, offset: int = 0) -> List:
        return await postgres_storage.get_audit_logs(user_id=user_id, action=action, limit=limit, offset=offset)

    async def get_audit_log_count(self, user_id: uuid.UUID = None, action: str = None) -> int:
        return await postgres_storage.get_audit_log_count(user_id=user_id, action=action)

    async def delete_all_user_data(self, user_id: uuid.UUID) -> None:
        memories = await postgres_storage.get_memories_by_user(user_id, limit=10000)
        for memory in memories:
            await postgres_storage.delete_memory(memory.id)
        telemetry.log_memory_operation("user_data_deleted", user_id=user_id, details={"memories_deleted": len(memories)})


governance_service = GovernanceService()
