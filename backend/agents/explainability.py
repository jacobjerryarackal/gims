import uuid
from typing import List, Optional
from datetime import datetime, timezone
from services.retrieval_service import RetrievedMemory


class ExplainabilityAgent:
    def explain_retrieval(self, query: str, retrieved_memories: List[RetrievedMemory]) -> List[str]:
        explanations = []
        for rm in retrieved_memories:
            explanation = self._generate_explanation(query, rm)
            explanations.append(explanation)
        return explanations

    def _get_memory_age_string(self, created_at: Optional[datetime]) -> Optional[str]:
        if not created_at:
            return None
        
        # Ensure the created_at datetime is aware of its timezone (UTC)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        age = datetime.now(timezone.utc) - created_at
        if age.days == 0: return "Recorded today."
        if age.days == 1: return "Recorded yesterday."
        return f"Recorded {age.days} days ago."

    def _generate_explanation(self, query: str, retrieved: RetrievedMemory) -> str:
        memory = retrieved.memory
        score = retrieved.similarity_score
        method = retrieved.retrieval_method
        query_lower = query.lower()
        content_lower = memory.content.lower()
        if any(word in content_lower for word in query_lower.split()):
            connection = "contains words from your query"
        elif memory.memory_type == "semantic":
            connection = "is semantically related to your query"
        elif memory.memory_type == "procedural":
            connection = "matches your preferences or habits"
        elif memory.memory_type == "episodic":
            connection = "relates to your past experiences"
        else:
            connection = "is relevant to your query"
        parts = [f"This memory was retrieved because it {connection}.", f"Relevance score: {score:.0%}."]
        if method == "hybrid":
            parts.append("Found through both semantic and keyword search.")
        elif method == "vector":
            parts.append("Found through meaning-based search.")
        elif method == "keyword":
            parts.append("Found through keyword matching.")
        
        age_string = self._get_memory_age_string(memory.created_at)
        if age_string:
            parts.append(age_string)

        if memory.access_count > 0:
            parts.append(f"Retrieved {memory.access_count} times before.")
        return " ".join(parts)

    def explain_storage_decision(self, memory_text: str, relevance: float, novelty: float, accuracy: float, decision: str) -> str:
        if decision == "store":
            return f"This memory was automatically stored because it scored highly on relevance ({relevance:.0%}), novelty ({novelty:.0%}), and accuracy ({accuracy:.0%})."
        elif decision == "dedup":
            return "This memory was flagged for duplicate checking because it has good scores but may already exist in the database."
        elif decision == "hitl":
            return f"This memory was queued for human review because its scores (avg: {(relevance + novelty + accuracy)/3:.0%}) were uncertain. A person will decide whether to store it."
        elif decision == "reject":
            return f"This memory was rejected because its scores were too low (avg: {(relevance + novelty + accuracy)/3:.0%}). Storing it would risk polluting the memory database."
        else:
            return "Storage decision could not be determined."


explainability_agent = ExplainabilityAgent()
