# test_extractor.py
import asyncio
from agents.extractor import extractor_agent

async def test():
    result = await extractor_agent.extract("I am an AI Engineer and I prefer first-principles explanations")
    print(f"Extracted {len(result)} memories:")
    for m in result:
        print(f"  - {m.memory_text} ({m.memory_type}, {m.confidence})")

asyncio.run(test())
