# test_chroma_query.py
import asyncio
import uuid
from storage.chroma import chroma_storage
from utils.embeddings import embedding_service

async def test():
    await chroma_storage.connect()
    
    # Store a test memory
    test_id = uuid.uuid4()
    content = "I love hiking in the mountains every weekend"
    embedding = await embedding_service.generate_embedding(content)
    
    await chroma_storage.add_memory(
        user_id=uuid.UUID("15fbd066-510b-4794-817b-ea111215bbff"),
        memory_id=test_id,
        content=content,
        embedding=embedding,
        metadata={"status": "active", "memory_type": "procedural"}
    )
    print(f"Stored memory {test_id}")
    
    # Query with same embedding
    results = await chroma_storage.query_similar(
        user_id=uuid.UUID("15fbd066-510b-4794-817b-ea111215bbff"),
        query_embedding=embedding,
        top_k=5
    )
    print(f"Found {len(results)} results with same embedding")
    
    # Query with different text
    query_embedding = await embedding_service.generate_embedding("What do you know about me?")
    results2 = await chroma_storage.query_similar(
        user_id=uuid.UUID("15fbd066-510b-4794-817b-ea111215bbff"),
        query_embedding=query_embedding,
        top_k=5
    )
    print(f"Found {len(results2)} results with different query")

asyncio.run(test())
