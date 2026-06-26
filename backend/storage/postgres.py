from typing import Optional, List
from sqlalchemy import select, update, func, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, selectinload
from core.config import settings
import os
from models import AsyncSessionLocal
from models.user import User
from models.conversation import Conversation, ConversationTurn
from models.memory import Memory
from models.audit import MemoryAuditLog
from models.hitl import HITLQueue
from core.exceptions import UserNotFoundException, MemoryNotFoundException, ConversationNotFoundException
import uuid
from datetime import datetime


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:15432/gims")

# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

class PostgresStorage:
    def __init__(self):
        self.session_factory = AsyncSessionLocal

    async def create_user(self, email: str, name: str = None, consent_given: bool = False) -> User:
        async with self.session_factory() as session:
            user = User(email=email, name=name, consent_given=consent_given)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def get_user(self, user_id: uuid.UUID) -> Optional[User]:
        async with self.session_factory() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise UserNotFoundException(f"User {user_id} not found")
            return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        async with self.session_factory() as session:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()

    async def create_conversation(self, user_id: uuid.UUID, title: str = None, memory_consent: bool = True) -> Conversation:
        async with self.session_factory() as session:
            conv = Conversation(user_id=user_id, title=title, memory_consent=memory_consent)
            session.add(conv)
            await session.commit()
            await session.refresh(conv)
            return conv

    async def get_conversation(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        async with self.session_factory() as session:
            result = await session.execute(select(Conversation).where(Conversation.id == conversation_id))
            conv = result.scalar_one_or_none()
            if not conv:
                raise ConversationNotFoundException(f"Conversation {conversation_id} not found")
            return conv

    async def create_turn(self, conversation_id: uuid.UUID, role: str, content: str) -> ConversationTurn:
        async with self.session_factory() as session:
            turn = ConversationTurn(conversation_id=conversation_id, role=role, content=content)
            session.add(turn)
            await session.commit()
            await session.refresh(turn)
            return turn

    async def create_memory(self, memory: Memory) -> Memory:
        async with self.session_factory() as session:
            memory.set_ttl()
            session.add(memory)
            await session.commit()
            await session.refresh(memory)
            return memory

    async def get_memory(self, memory_id: uuid.UUID) -> Optional[Memory]:
        async with self.session_factory() as session:
            result = await session.execute(select(Memory).where(Memory.id == memory_id))
            memory = result.scalar_one_or_none()
            if not memory:
                raise MemoryNotFoundException(f"Memory {memory_id} not found")
            return memory

    async def get_memories_by_user(self, user_id: uuid.UUID, memory_type: str = None, status: str = "active", limit: int = 50, offset: int = 0) -> List[Memory]:
        async with self.session_factory() as session:
            query = select(Memory).where(Memory.user_id == user_id)
            if memory_type:
                query = query.where(Memory.memory_type == memory_type)
            if status:
                query = query.where(Memory.status == status)
            query = query.order_by(Memory.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(query)
            return result.scalars().all()

    async def update_memory(self, memory_id: uuid.UUID, **updates) -> Memory:
        async with self.session_factory() as session:
            await session.execute(update(Memory).where(Memory.id == memory_id).values(**updates))
            await session.commit()
            return await self.get_memory(memory_id)

    async def delete_memory(self, memory_id: uuid.UUID) -> None:
        async with self.session_factory() as session:
            await session.execute(update(Memory).where(Memory.id == memory_id).values(status="deleted"))
            await session.commit()

    async def search_memories_keyword(self, user_id: uuid.UUID, query: str, top_k: int = 5) -> List[Memory]:
        async with self.session_factory() as session:
            sql = text("SELECT id, content, memory_type, relevance_score, novelty_score, accuracy_score, avg_score, created_at FROM memories WHERE user_id = :user_id AND status = 'active' AND to_tsvector('english', content) @@ plainto_tsquery('english', :query) ORDER BY ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', :query)) DESC LIMIT :limit")
            result = await session.execute(sql, {"user_id": str(user_id), "query": query, "limit": top_k})
            rows = result.fetchall()
            memories = []
            for row in rows:
                mem = Memory(id=row.id, user_id=user_id, content=row.content, memory_type=row.memory_type, relevance_score=row.relevance_score, novelty_score=row.novelty_score, accuracy_score=row.accuracy_score, avg_score=row.avg_score, created_at=row.created_at)
                memories.append(mem)
            return memories

    async def find_similar_memories(self, user_id: uuid.UUID, content: str, threshold: float = 0.6) -> List[Memory]:
        async with self.session_factory() as session:
            sql = text("SELECT id, content, memory_type, relevance_score, novelty_score, accuracy_score, avg_score, created_at FROM memories WHERE user_id = :user_id AND status = 'active' AND similarity(content, :content) > :threshold ORDER BY similarity(content, :content) DESC")
            result = await session.execute(sql, {"user_id": str(user_id), "content": content, "threshold": threshold})
            rows = result.fetchall()
            memories = []
            for row in rows:
                mem = Memory(id=row.id, user_id=user_id, content=row.content, memory_type=row.memory_type, relevance_score=row.relevance_score, novelty_score=row.novelty_score, accuracy_score=row.accuracy_score, avg_score=row.avg_score, created_at=row.created_at)
                memories.append(mem)
            return memories

    async def create_audit_log(self, **kwargs) -> MemoryAuditLog:
        async with self.session_factory() as session:
            log = MemoryAuditLog(**kwargs)
            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log

    async def get_audit_logs(self, user_id: uuid.UUID = None, action: str = None, limit: int = 100, offset: int = 0) -> List[MemoryAuditLog]:
        async with self.session_factory() as session:
            query = select(MemoryAuditLog)
            if user_id:
                query = query.where(MemoryAuditLog.user_id == user_id)
            if action:
                query = query.where(MemoryAuditLog.action == action)
            query = query.order_by(MemoryAuditLog.created_at.desc()).offset(offset).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_audit_log_count(self, user_id: uuid.UUID = None, action: str = None) -> int:
        async with self.session_factory() as session:
            query = select(func.count(MemoryAuditLog.id))
            if user_id:
                query = query.where(MemoryAuditLog.user_id == user_id)
            if action:
                query = query.where(MemoryAuditLog.action == action)
            result = await session.execute(query)
            return result.scalar() or 0

    async def create_hitl_item(self, **kwargs) -> HITLQueue:
        async with self.session_factory() as session:
            item = HITLQueue(**kwargs)
            session.add(item)
            await session.commit()
            await session.refresh(item)
            return item

    async def get_hitl_queue(self, user_id: uuid.UUID = None, status: str = "pending") -> List[HITLQueue]:
        async with self.session_factory() as session:
            query = select(HITLQueue).options(selectinload(HITLQueue.memory)).where(HITLQueue.status == status)
            if user_id:
                query = query.where(HITLQueue.user_id == user_id)
            query = query.order_by(HITLQueue.created_at.desc())
            result = await session.execute(query)
            return result.scalars().all()

    async def update_hitl_item(self, item_id: uuid.UUID, **updates) -> HITLQueue:
        async with self.session_factory() as session:
            await session.execute(update(HITLQueue).where(HITLQueue.id == item_id).values(**updates))
            await session.commit()
            result = await session.execute(select(HITLQueue).where(HITLQueue.id == item_id))
            return result.scalar_one()

    async def get_memory_count(self, user_id: uuid.UUID) -> int:
        async with self.session_factory() as session:
            result = await session.execute(select(func.count(Memory.id)).where(Memory.user_id == user_id, Memory.status == "active"))
            return result.scalar()

    async def get_recent_memories(self, user_id: uuid.UUID, limit: int = 5) -> List[Memory]:
        async with self.session_factory() as session:
            result = await session.execute(select(Memory).where(Memory.user_id == user_id, Memory.status == "active").order_by(Memory.last_accessed_at.desc().nulls_last(), Memory.created_at.desc()).limit(limit))
            return result.scalars().all()

    async def get_conversation_turns(self, conversation_id: uuid.UUID) -> List[ConversationTurn]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(ConversationTurn).where(ConversationTurn.conversation_id == conversation_id)
            )
            return result.scalars().all()

    async def delete_conversation(self, conversation_id: uuid.UUID) -> None:
        async with self.session_factory() as session:
            await session.execute(
                update(Conversation).where(Conversation.id == conversation_id).values(is_active=False)
            )
            await session.commit()
    
    async def get_conversations_by_user(self, user_id: uuid.UUID) -> List[Conversation]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Conversation).where(
                    Conversation.user_id == user_id,
                    Conversation.is_active == True
                ).order_by(Conversation.created_at.desc())
            )
            return result.scalars().all()


postgres_storage = PostgresStorage()
