import os
from sqlalchemy import create_engine

# Import Base AND all models so they're registered
from models import Base
from models.user import User
from models.conversation import Conversation, ConversationTurn
from models.memory import Memory
from models.audit import MemoryAuditLog
from models.hitl import HITLQueue

# Get URL from env
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:15432/gims")

# Convert asyncpg URL to sync (psycopg2) URL
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
else:
    SYNC_DATABASE_URL = DATABASE_URL

print(f"Connecting to: {SYNC_DATABASE_URL}")

engine = create_engine(SYNC_DATABASE_URL, echo=True)
Base.metadata.create_all(engine)
print("Database tables created successfully!")