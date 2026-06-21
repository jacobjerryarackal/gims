import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Numeric, DateTime, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from models import Base
from core.config import settings


class Memory(Base):
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    memory_type = Column(String(20), nullable=False)
    content = Column(String, nullable=False)

    relevance_score = Column(Numeric(3, 2), nullable=False)
    novelty_score = Column(Numeric(3, 2), nullable=False)
    accuracy_score = Column(Numeric(3, 2), nullable=False)
    avg_score = Column(Numeric(3, 2), nullable=False)

    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    event_date = Column(DateTime(timezone=True), nullable=True)
    participants = Column(ARRAY(String), nullable=True)

    source_turn_id = Column(UUID(as_uuid=True), ForeignKey("conversation_turns.id"), nullable=True)
    metadata = Column(String, default="{}")
    chroma_id = Column(String(255), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "memory_type != 'episodic' OR (event_date IS NOT NULL AND participants IS NOT NULL)",
            name="chk_episodic_fields"
        ),
    )

    def set_ttl(self):
        if self.memory_type == "semantic":
            days = settings.SEMANTIC_MEMORY_TTL_DAYS
        elif self.memory_type == "procedural":
            days = settings.PROCEDURAL_MEMORY_TTL_DAYS
        elif self.memory_type == "episodic":
            days = settings.EPISODIC_MEMORY_TTL_DAYS
        else:
            days = 365
        self.expires_at = datetime.utcnow() + timedelta(days=days)
