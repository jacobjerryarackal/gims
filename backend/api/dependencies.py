from fastapi import Depends
from models import get_db
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db_session() -> AsyncSession:
    async for session in get_db():
        return session