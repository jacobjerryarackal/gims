import asyncio
from utils.embeddings import embedding_service

async def test():
    try:
        embedding = await embedding_service.generate_embedding("I love hiking")
        print(f"Embedding length: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")

asyncio.run(test())