import json
from typing import List, Dict, Any, Optional
import httpx
from core.config import settings
from utils.telemetry import telemetry


class CandidateMemory:
    def __init__(self, memory_text: str, memory_type: str, confidence: float, source_turn_id: Optional[str] = None):
        self.memory_text = memory_text
        self.memory_type = memory_type
        self.confidence = confidence
        self.source_turn_id = source_turn_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {"memory_text": self.memory_text, "memory_type": self.memory_type, "confidence": self.confidence, "source_turn_id": self.source_turn_id}


class MemoryExtractorAgent:
    SYSTEM_PROMPT = """
You are a Memory Extraction Agent.

Extract memories from user messages.

Memory Types:

1. SEMANTIC
   Facts about the user's identity, background, profession, skills, education, location, relationships, goals, or long-term attributes.

Examples:

* I am a Machine Learning Engineer.
* I work as a Software Developer.
* I live in Kerala.
* I studied Computer Science.
* I build AI workflows.

2. PROCEDURAL
   Preferences, habits, routines, workflows, or ways the user likes things done.

Examples:

* I prefer step-by-step explanations.
* I like concise answers.
* I usually code in Python.
* I prefer dark mode.

3. EPISODIC
   Experiences, events, achievements, projects completed, things learned, travel, conferences, and milestones.

Examples:

* Yesterday I learned how audit logs work.
* Last week I attended an AI conference.
* I completed a hackathon in March.
* I built an AI CTO Agent.

Rules:

* Extract only information explicitly stated by the user.
* Identity statements are semantic memories.
* Profession statements are semantic memories.
* Learning experiences are episodic memories.
* Preferences are procedural memories.
* Return ONLY valid JSON.

Example output:

[
{
"memory_text": "I am a Machine Learning Engineer",
"memory_type": "semantic",
"confidence": 0.95
}
]

If nothing should be extracted return:
[]
"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.base_url = "https://api.groq.com/openai/v1"
    
    
    async def extract(self, conversation_text: str, turn_id: Optional[str] = None) -> List[CandidateMemory]:
        if not conversation_text or len(conversation_text.strip()) < 10:
            print("EXTRACTOR: Text too short, skipping")
            return []
        try:
            print(f"EXTRACTOR: Calling Groq API with model={self.model}")
            print(f"EXTRACTOR: API key starts with={self.api_key[:15]}...")
            
            prompt_text = f"Extract memories from this conversation:\n\n{conversation_text}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self.SYSTEM_PROMPT},
                            {"role": "user", "content": prompt_text}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1000
                    }
                )
                print(f"EXTRACTOR: Response status={response.status_code}")
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"EXTRACTOR: Raw response={content}")
                
                parsed = json.loads(content)
                print(f"EXTRACTOR: Parsed type={type(parsed)}")
                
                memories = []
                if "memories" in parsed:
                    items = parsed["memories"]
                    print(f"EXTRACTOR: Found 'memories' key with {len(items)} items")
                elif isinstance(parsed, list):
                    items = parsed
                    print(f"EXTRACTOR: Found list with {len(items)} items")
                else:
                    items = []
                    print(f"EXTRACTOR: Unknown format, keys={parsed.keys() if isinstance(parsed, dict) else 'N/A'}")
                
                for item in items:
                    if isinstance(item, dict) and "memory_text" in item:
                        memory = CandidateMemory(
                            memory_text=item["memory_text"],
                            memory_type=item.get("memory_type", "semantic"),
                            confidence=item.get("confidence", 0.5),
                            source_turn_id=turn_id
                        )
                        memories.append(memory)
                        print(f"EXTRACTOR: Extracted memory: {item['memory_text'][:50]}...")
                
                print(f"EXTRACTOR: Total extracted: {len(memories)}")
                telemetry.log_memory_operation("extracted", user_id=None, details={"candidates_found": len(memories), "input_length": len(conversation_text)})
                return memories
                
        except Exception as e:
            print(f"EXTRACTOR ERROR: {type(e).__name__}: {str(e)}")
            telemetry.log_memory_operation("extract_failed", user_id=None, details={"error": str(e)})
            return []


extractor_agent = MemoryExtractorAgent()