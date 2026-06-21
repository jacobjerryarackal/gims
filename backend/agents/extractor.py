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
    SYSTEM_PROMPT = """You are a Memory Extraction Agent. Your job is to identify facts, preferences, and experiences from user messages that would be valuable to remember for future conversations.

Extract ONLY information that the user explicitly states about themselves. Do NOT infer information that is not directly stated.

Memory Types:
1. SEMANTIC: Facts about who the user is (identity, profession, skills, background)
   Examples: "I am an AI Engineer", "I live in San Francisco", "I speak Spanish"

2. PROCEDURAL: Preferences, habits, and behavioral patterns
   Examples: "I prefer first-principles explanations", "I like concise answers", "I work best in the morning"

3. EPISODIC: Specific events, experiences, and achievements
   Examples: "I built an AI CTO Agent last month", "I attended NeurIPS 2025", "I got promoted in January"

Rules:
- Only extract facts the user explicitly stated about THEMSELVES
- Use exact quotes when possible
- Distinguish between "User said X" and "User's friend/colleague said X"
- If uncertain, do NOT extract
- Do NOT extract: opinions about others, general knowledge, transient information

Return a JSON array of extracted memories. Each memory must have:
- memory_text: The exact or closely paraphrased fact
- memory_type: "semantic", "procedural", or "episodic"
- confidence: 0.0 to 1.0 (how certain you are this is a real, useful fact)

If no memories should be extracted, return an empty array []."""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.base_url = "https://api.openai.com/v1"
    
    async def extract(self, conversation_text: str, turn_id: Optional[str] = None) -> List[CandidateMemory]:
        if not conversation_text or len(conversation_text.strip()) < 10:
            return []
        try:
            prompt_text = f"Extract memories from this conversation:\n\n{conversation_text}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"model": self.model, "messages": [{"role": "system", "content": self.SYSTEM_PROMPT}, {"role": "user", "content": prompt_text}], "temperature": 0.3, "max_tokens": 1000, "response_format": {"type": "json_object"}}
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                memories = []
                if "memories" in parsed:
                    items = parsed["memories"]
                elif isinstance(parsed, list):
                    items = parsed
                else:
                    items = []
                for item in items:
                    if isinstance(item, dict) and "memory_text" in item:
                        memory = CandidateMemory(memory_text=item["memory_text"], memory_type=item.get("memory_type", "semantic"), confidence=item.get("confidence", 0.5), source_turn_id=turn_id)
                        memories.append(memory)
                telemetry.log_memory_operation("extracted", user_id=None, details={"candidates_found": len(memories), "input_length": len(conversation_text)})
                return memories
        except Exception as e:
            telemetry.log_memory_operation("extract_failed", user_id=None, details={"error": str(e)})
            return []


extractor_agent = MemoryExtractorAgent()