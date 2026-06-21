import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

from agents.extractor import extractor_agent, CandidateMemory
from agents.evaluator import evaluator_agent, EvaluatedMemory
from agents.retriever import retriever_agent
from agents.explainability import explainability_agent
from services.memory_service import memory_service
from services.dedup_service import dedup_service
from services.governance_service import governance_service
from storage.postgres import postgres_storage
from utils.telemetry import telemetry
from core.config import settings
from core.exceptions import StorageException


class PipelineState:
    def __init__(self, user_id: uuid.UUID, conversation_id: uuid.UUID, message: str, role: str = "user", extracted_memories: List[CandidateMemory] = None, evaluated_memories: List[EvaluatedMemory] = None, stored_memories: List[Dict] = None, retrieved_memories: List = None, response: str = None, error: str = None):
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.message = message
        self.role = role
        self.extracted_memories = extracted_memories or []
        self.evaluated_memories = evaluated_memories or []
        self.stored_memories = stored_memories or []
        self.retrieved_memories = retrieved_memories or []
        self.response = response
        self.error = error


class MemoryPipeline:
    def __init__(self):
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("capture", self._capture_node)
        graph.add_node("evaluate", self._evaluate_node)
        graph.add_node("store", self._store_node)
        graph.add_node("dedup", self._dedup_node)
        graph.add_node("hitl", self._hitl_node)
        graph.add_node("reject", self._reject_node)
        graph.add_node("retrieve", self._retrieve_node)
        graph.add_node("context_builder", self._context_builder_node)
        graph.set_entry_point("capture")
        graph.add_edge("capture", "evaluate")
        graph.add_conditional_edges("evaluate", self._evaluation_router, {"store": "store", "dedup": "dedup", "hitl": "hitl", "reject": "reject"})
        graph.add_edge("store", "retrieve")
        graph.add_edge("dedup", "retrieve")
        graph.add_edge("hitl", "retrieve")
        graph.add_edge("reject", "retrieve")
        graph.add_edge("retrieve", "context_builder")
        graph.add_edge("context_builder", END)
        return graph.compile(checkpointer=self.checkpointer)

    async def _capture_node(self, state: dict) -> dict:
        try:
            print(f"PIPELINE CAPTURE: message={state['message'][:50]}...")
            turn = await postgres_storage.create_turn(conversation_id=state["conversation_id"], role=state["role"], content=state["message"])
            print(f"PIPELINE CAPTURE: Created turn {turn.id}")
            candidates = await extractor_agent.extract(conversation_text=state["message"], turn_id=str(turn.id))
            print(f"PIPELINE CAPTURE: Extractor returned {len(candidates)} candidates")
            for c in candidates:
                print(f"  - {c.memory_text[:50]} ({c.memory_type})")
            state["extracted_memories"] = [c.to_dict() for c in candidates]
            state["turn_id"] = str(turn.id)
        except Exception as e:
            print(f"PIPELINE CAPTURE ERROR: {str(e)}")
            state["error"] = f"Capture failed: {str(e)}"
            state["extracted_memories"] = []
        return state

    async def _evaluate_node(self, state: dict) -> dict:
        try:
            candidates = [CandidateMemory(**c) for c in state.get("extracted_memories", [])]
            print(f"PIPELINE EVALUATE: Evaluating {len(candidates)} candidates")
            if not candidates:
                print("PIPELINE EVALUATE: No candidates to evaluate")
                state["evaluated_memories"] = []
                return state
            existing = await postgres_storage.get_memories_by_user(user_id=uuid.UUID(state["user_id"]), limit=50)
            existing_texts = [m.content for m in existing]
            evaluated = await evaluator_agent.evaluate_batch(candidates, existing_texts)
            print(f"PIPELINE EVALUATE: Evaluator returned {len(evaluated)} results")
            for e in evaluated:
                print(f"  - decision={e.decision}, avg_score={e.avg_score:.2f}, reason={e.evaluation_reason[:50]}")
            state["evaluated_memories"] = [{"candidate": e.candidate.to_dict(), "relevance_score": e.relevance_score, "novelty_score": e.novelty_score, "accuracy_score": e.accuracy_score, "avg_score": e.avg_score, "evaluation_reason": e.evaluation_reason, "decision": e.decision} for e in evaluated]
        except Exception as e:
            print(f"PIPELINE EVALUATE ERROR: {str(e)}")
            state["error"] = f"Evaluation failed: {str(e)}"
            state["evaluated_memories"] = []
        return state

    async def _store_node(self, state: dict) -> dict:
        try:
            evaluated = state.get("evaluated_memories", [])
            print(f"PIPELINE STORE: Storing {len(evaluated)} evaluated memories")
            stored = []
            for e in evaluated:
                print(f"PIPELINE STORE: Processing decision={e['decision']}")
                if e["decision"] == "store":
                    print(f"PIPELINE STORE: Creating memory for {e['candidate']['memory_text'][:50]}")
                    memory = await memory_service.create_memory(...)
                    stored.append({"id": str(memory.id), "content": memory.content})
                    print(f"PIPELINE STORE: Memory created {memory.id}")
            state["stored_memories"] = stored
            print(f"PIPELINE STORE: Total stored {len(stored)}")
        except Exception as e:
            print(f"PIPELINE STORE ERROR: {str(e)}")
            state["error"] = f"Store failed: {str(e)}"
        return state

    def _evaluation_router(self, state: dict) -> str:
        evaluated = state.get("evaluated_memories", [])
        if not evaluated:
            return "reject"
        avg_scores = [e["avg_score"] for e in evaluated]
        max_score = max(avg_scores) if avg_scores else 0
        if max_score >= settings.EVALUATION_AUTO_STORE_THRESHOLD:
            return "store"
        elif max_score >= settings.EVALUATION_DEDUP_THRESHOLD:
            return "dedup"
        elif max_score >= settings.EVALUATION_HITL_THRESHOLD:
            return "hitl"
        else:
            return "reject"

    async def _dedup_node(self, state: dict) -> dict:
        try:
            evaluated = state.get("evaluated_memories", [])
            stored = []
            for e in evaluated:
                if e["decision"] in ["store", "dedup"]:
                    result = await dedup_service.check_duplicates(user_id=uuid.UUID(state["user_id"]), content=e["candidate"]["memory_text"], memory_type=e["candidate"]["memory_type"])
                    if result["is_duplicate"] and result["action"] == "merge":
                        await dedup_service.merge_memories(existing_memory=result["existing_memory"], new_content=e["candidate"]["memory_text"], new_scores={"relevance": e["relevance_score"], "novelty": e["novelty_score"], "accuracy": e["accuracy_score"]})
                    elif not result["is_duplicate"]:
                        memory = await memory_service.create_memory(user_id=uuid.UUID(state["user_id"]), content=e["candidate"]["memory_text"], memory_type=e["candidate"]["memory_type"], relevance_score=e["relevance_score"], novelty_score=e["novelty_score"], accuracy_score=e["accuracy_score"], conversation_id=uuid.UUID(state["conversation_id"]))
                        stored.append({"id": str(memory.id), "content": memory.content})
            state["stored_memories"] = stored
        except Exception as e:
            print(f"PIPELINE DEDUP ERROR: {str(e)}")
            state["error"] = f"Dedup failed: {str(e)}"
        return state

    async def _hitl_node(self, state: dict) -> dict:
        try:
            evaluated = state.get("evaluated_memories", [])
            for e in evaluated:
                if e["decision"] == "hitl":
                    await governance_service.create_hitl_item(user_id=uuid.UUID(state["user_id"]), reason=e["evaluation_reason"], confidence_score=e["avg_score"])
            state["stored_memories"] = []
        except Exception as e:
            print(f"PIPELINE HiTl ERROR: {str(e)}")
            state["error"] = f"HITL queue failed: {str(e)}"
        return state

    async def _reject_node(self, state: dict) -> dict:
        try:
            evaluated = state.get("evaluated_memories", [])
            for e in evaluated:
                if e["decision"] == "reject":
                    await postgres_storage.create_audit_log(user_id=uuid.UUID(state["user_id"]), action="rejected", actor="evaluator_agent", reason=e["evaluation_reason"])
            state["stored_memories"] = []
        except Exception as e:
            state["error"] = f"Reject logging failed: {str(e)}"
        return state

    async def _retrieve_node(self, state: dict) -> dict:
        try:
            results = await retriever_agent.retrieve(user_id=uuid.UUID(state["user_id"]), query=state["message"], top_k=settings.RETRIEVAL_TOP_K)
            state["retrieved_memories"] = [{"id": str(r.memory.id), "content": r.memory.content, "memory_type": r.memory.memory_type, "similarity_score": r.similarity_score, "retrieval_method": r.retrieval_method, "explanation": r.explanation} for r in results]
        except Exception as e:
            state["error"] = f"Retrieval failed: {str(e)}"
            state["retrieved_memories"] = []
        return state

    async def _context_builder_node(self, state: dict) -> dict:
        try:
            retrieved = state.get("retrieved_memories", [])
            if not retrieved:
                state["context"] = "No relevant memories found."
                return state
            context_parts = ["Relevant memories from previous conversations:"]
            for i, mem in enumerate(retrieved, 1):
                line1 = f"{i}. [{mem['memory_type'].upper()}] {mem['content']}"
                line2 = f"   Why retrieved: {mem['explanation']}"
                context_parts.append(line1)
                context_parts.append(line2)
            state["context"] = "\n".join(context_parts)
        except Exception as e:
            state["error"] = f"Context building failed: {str(e)}"
            state["context"] = ""
        return state

    async def process_message(self, user_id: uuid.UUID, conversation_id: uuid.UUID, message: str, role: str = "user") -> dict:
        initial_state = {"user_id": str(user_id), "conversation_id": str(conversation_id), "message": message, "role": role, "extracted_memories": [], "evaluated_memories": [], "stored_memories": [], "retrieved_memories": [], "context": "", "error": None}
        try:
            result = await self.graph.ainvoke(initial_state, config={"configurable": {"thread_id": str(conversation_id)}})
            return result
        except Exception as e:
            return {**initial_state, "error": f"Pipeline execution failed: {str(e)}"}


memory_pipeline = MemoryPipeline()
