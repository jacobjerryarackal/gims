# backfill_chroma.py
import asyncio
import uuid
from storage.postgres import postgres_storage
from storage.chroma import chroma_storage
from utils.embeddings import embedding_service

async def backfill():
    await chroma_storage.connect()
    
    # Get all memories from PostgreSQL
    user_id = uuid.UUID("15fbd066-510b-4794-817b-ea111215bbff")
    memories = await postgres_storage.get_memories_by_user(user_id=user_id, limit=100)
    
    print(f"Found {len(memories)} memories in PostgreSQL")
    
    for memory in memories:
        try:
            embedding = await embedding_service.generate_embedding(memory.content)
            chroma_id = await chroma_storage.add_memory(
                user_id=user_id,
                memory_id=memory.id,
                content=memory.content,
                embedding=embedding,
                metadata={
                    "memory_type": memory.memory_type,
                    "avg_score": float(memory.avg_score),
                    "status": memory.status
                }
            )
            print(f"  Stored in ChromaDB: {memory.content[:50]} (id: {chroma_id})")
        except Exception as e:
            print(f"  FAILED: {memory.content[:50]} - {str(e)}")
    
    # Verify
    collection = chroma_storage._get_collection(user_id)
    results = collection.get()
    print(f"\nTotal items in ChromaDB collection: {len(results['ids'])}")

asyncio.run(backfill())