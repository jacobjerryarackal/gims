# test_chroma_search.py
import asyncio
import uuid
from storage.chroma import chroma_storage
from utils.embeddings import embedding_service

async def test():
    await chroma_storage.connect()
    
    # Generate embedding for query
    query = "What do you know about me?"
    embedding = await embedding_service.generate_embedding(query)
    print(f"Query embedding length: {len(embedding)}")
    
    # Use query_similar (not search)
    results = await chroma_storage.query_similar(
        user_id=uuid.UUID("15fbd066-510b-4794-817b-ea111215bbff"),
        query_embedding=embedding,
        top_k=5,
        where={"status": "active"}
    )
    print(f"Found {len(results)} results in ChromaDB")
    for r in results:
        print(f"  - {r}")

asyncio.run(test())