import asyncio
import uuid
from storage.postgres import postgres_storage
import storage.chroma as c

async def main():
    user_id = uuid.UUID('15fbd066-510b-4794-817b-ea111215bbff')
    mems = await postgres_storage.get_memories_by_user(user_id=user_id, limit=20)
    print('db_count', len(mems))
    for m in mems:
        print('MEM', str(m.id), m.content, m.chroma_id, m.status)
    print('chroma client before', c.chroma_storage.client)
    try:
        await c.chroma_storage.connect()
        print('chroma connect success', c.chroma_storage.client is not None)
        print('chroma collections', list(c.chroma_storage._collections.keys()))
    except Exception as e:
        print('chroma connect failed', type(e).__name__, str(e))

asyncio.run(main())
