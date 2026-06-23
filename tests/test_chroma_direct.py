# test_chroma_direct.py
import asyncio
import uuid
from storage.chroma import chroma_storage

async def test():
    await chroma_storage.connect()
    collection = chroma_storage._get_collection(uuid.UUID("15fbd066-510b-4794-817b-ea111215bbff"))
    results = collection.get()
    print(f"Total items in collection: {len(results['ids'])}")
    for i, id in enumerate(results['ids']):
        print(f"  {id}: {results['documents'][i]}")

asyncio.run(test())