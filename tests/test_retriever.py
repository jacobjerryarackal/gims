import asyncio
import uuid
from agents.retriever import retriever_agent

async def test():
    user_id = uuid.UUID("15fbd066-510b-4794-817b-ea111215bbff")
    results = await retriever_agent.retrieve(
        user_id=user_id,
        query="What do you know about me?",
        top_k=5
    )
    print(f"Found {len(results)} results")
    for r in results:
        print(f"  - {r.memory.content} (score: {r.similarity_score}, method: {r.retrieval_method})")

asyncio.run(test())
