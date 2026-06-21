import json
from typing import List, Dict, Any, Optional
import httpx
from core.config import settings
from utils.telemetry import telemetry
from agents.extractor import CandidateMemory


class EvaluatedMemory:
    def __init__(self, candidate: CandidateMemory, relevance_score: float, novelty_score: float, accuracy_score: float, avg_score: float, evaluation_reason: str, decision: str):
        self.candidate = candidate
        self.relevance_score = relevance_score
        self.novelty_score = novelty_score
        self.accuracy_score = accuracy_score
        self.avg_score = avg_score
        self.evaluation_reason = evaluation_reason
        self.decision = decision


class MemoryEvaluatorAgent:
    SYSTEM_PROMPT = """You are a Memory Evaluator Agent. Your job is to judge whether a candidate memory should be stored in the user long-term memory.

Evaluate each candidate on three dimensions (0.0 to 1.0):

1. RELEVANCE: Is this memory useful for future conversations?
   - 1.0: Extremely useful (core identity, key preferences, major achievements)
   - 0.5: Somewhat useful (minor preferences, tangential facts)
   - 0.0: Not useful (transient, trivial, or irrelevant)

2. NOVELTY: Is this new information, or already known?
   - 1.0: Completely new information
   - 0.5: Partially new (adds detail to known fact)
   - 0.0: Already known (exact duplicate)

3. ACCURACY: Is this fact likely to be true and correctly attributed?
   - 1.0: Definitely true, directly stated by user
   - 0.5: Probably true, but inferred or second-hand
   - 0.0: Likely false, hallucinated, or misattributed

Return a JSON object with:
- relevance_score: float (0.0 to 1.0)
- novelty_score: float (0.0 to 1.0)
- accuracy_score: float (0.0 to 1.0)
- evaluation_reason: Brief explanation of your scoring
- decision: One of "store" (high confidence), "dedup" (check for duplicates), "hitl" (needs human review), "reject" (low quality)

Be conservative. It is better to miss a memory than to store a false one."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.base_url = "https://api.openai.com/v1"

    async def evaluate(self, candidate: CandidateMemory, existing_memories_text: List[str] = None) -> EvaluatedMemory:
        context = ""
        if existing_memories_text:
            # FIXED: Changed single quotes to triple quotes for multi-line block
            context = """

Existing memories:
""" + "\n".join([f"- {m}" for m in existing_memories_text[:10]])
        
        # FIXED: Changed standard f-string literal to f-string triple quotes
        prompt = f"""Evaluate this candidate memory:

Memory text: {candidate.memory_text}
Memory type: {candidate.memory_type}
Extractor confidence: {candidate.confidence}
{context}

Provide your evaluation as JSON."""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={
                        "model": self.model, 
                        "messages": [
                            {"role": "system", "content": self.SYSTEM_PROMPT}, 
                            {"role": "user", "content": prompt}
                        ], 
                        "temperature": 0.2, 
                        "max_tokens": 500, 
                        "response_format": {"type": "json_object"}
                    }
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                relevance = float(parsed.get("relevance_score", 0.5))
                novelty = float(parsed.get("novelty_score", 0.5))
                accuracy = float(parsed.get("accuracy_score", 0.5))
                avg = (relevance + novelty + accuracy) / 3.0
                reason = parsed.get("evaluation_reason", "No reason provided")
                decision = parsed.get("decision", "hitl")
                
                if decision not in ["store", "dedup", "hitl", "reject"]:
                    if avg >= settings.EVALUATION_AUTO_STORE_THRESHOLD:
                        decision = "store"
                    elif avg >= settings.EVALUATION_DEDUP_THRESHOLD:
                        decision = "dedup"
                    elif avg >= settings.EVALUATION_HITL_THRESHOLD:
                        decision = "hitl"
                    else:
                        decision = "reject"
                        
                evaluated = EvaluatedMemory(
                    candidate=candidate, 
                    relevance_score=relevance, 
                    novelty_score=novelty, 
                    accuracy_score=accuracy, 
                    avg_score=avg, 
                    evaluation_reason=reason, 
                    decision=decision
                )
                telemetry.log_evaluation(memory_content=candidate.memory_text[:100], relevance=relevance, novelty=novelty, accuracy=accuracy, decision=decision)
                return evaluated
        except Exception as e:
            telemetry.log_memory_operation("evaluation_failed", user_id=None, details={"error": str(e), "memory": candidate.memory_text[:100]})
            return EvaluatedMemory(candidate=candidate, relevance_score=0.3, novelty_score=0.3, accuracy_score=0.3, avg_score=0.3, evaluation_reason=f"Evaluation failed: {str(e)}", decision="reject")

    async def evaluate_batch(self, candidates: List[CandidateMemory], existing_memories_text: List[str] = None) -> List[EvaluatedMemory]:
        results = []
        for candidate in candidates:
            evaluated = await self.evaluate(candidate, existing_memories_text)
            results.append(evaluated)
        return results


evaluator_agent = MemoryEvaluatorAgent()