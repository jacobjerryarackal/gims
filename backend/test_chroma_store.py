# test_chroma_store.py
import asyncio
import uuid
from storage.chroma import chroma_storage
from utils.embeddings import embedding_service

async def test():
    await chroma_storage.connect()
    try:
        embedding = await embedding_service.generate_embedding("I love hiking in the mountains")
        chroma_id = await chroma_storage.add_memory(
            user_id=uuid.UUID("15fbd066-510b-4794-817b-ea111215bbff"),
            memory_id=uuid.uuid4(),
            content="I love hiking in the mountains",
            embedding=embedding,
            metadata={"memory_type": "procedural"}
        )
        print(f"Stored in ChromaDB with ID: {chroma_id}")
        
        # Now search
        results = await chroma_storage.search(
            user_id="15fbd066-510b-4794-817b-ea111215bbff",
            query_embedding=embedding,
            top_k=5
        )
        print(f"Search found {len(results)} results")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")

asyncio.run(test())