import asyncio
import uuid
from agents.pipeline import memory_pipeline

async def test():
    user_id = uuid.UUID("15fbd066-510b-4794-817b-ea111215bbff")
    conv_id = uuid.UUID("223ddcca-df31-4a02-bc47-7b61ff8f23e4")
    
    result = await memory_pipeline.process_message(
        user_id=user_id,
        conversation_id=conv_id,
        message="I am an AI Engineer and I prefer first-principles explanations",
        role="user"
    )
    
    print(f"stored_memories: {result.get('stored_memories', [])}")
    print(f"extracted_memories: {result.get('extracted_memories', [])}")
    print(f"evaluated_memories: {result.get('evaluated_memories', [])}")
    print(f"error: {result.get('error')}")

asyncio.run(test())