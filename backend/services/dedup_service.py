import uuid
from typing import List, Dict, Any
from models.memory import Memory
from storage.postgres import postgres_storage
from storage.chroma import chroma_storage
from utils.embeddings import embedding_service
from utils.telemetry import telemetry
from core.config import settings


class DedupService:
    async def check_duplicates(self, user_id: uuid.UUID, content: str, memory_type: str, exclude_memory_id: uuid.UUID = None) -> Dict[str, Any]:
        exact_duplicate = await self._find_exact_duplicate(user_id, content, memory_type, exclude_memory_id=exclude_memory_id)
        if exact_duplicate:
            return {"is_duplicate": True, "action": "merge", "existing_memory": exact_duplicate, "similarity": 1.0}

        vector_duplicates = await self._check_vector_similarity(user_id, content, exclude_memory_id=exclude_memory_id)
        text_duplicates = await self._check_text_similarity(user_id, content, exclude_memory_id=exclude_memory_id)
        all_duplicates = vector_duplicates + text_duplicates
        if not all_duplicates:
            return {"is_duplicate": False, "action": "store", "existing_memory": None}
        best_match = max(all_duplicates, key=lambda x: x["similarity"])
        if best_match["similarity"] >= settings.DEDUP_SIMILARITY_THRESHOLD:
            return {"is_duplicate": True, "action": "merge", "existing_memory": best_match["memory"], "similarity": best_match["similarity"]}
        elif best_match["similarity"] >= 0.70:
            return {"is_duplicate": True, "action": "flag_for_review", "existing_memory": best_match["memory"], "similarity": best_match["similarity"]}
        return {"is_duplicate": False, "action": "store", "existing_memory": None}

    async def _check_vector_similarity(self, user_id: uuid.UUID, content: str, exclude_memory_id: uuid.UUID = None) -> List[Dict[str, Any]]:
        try:
            embedding = await embedding_service.generate_embedding(content)
            results = await chroma_storage.query_similar(user_id=user_id, query_embedding=embedding, top_k=5, where={"status": "active"})
            duplicates = []
            for result in results:
                distance = result.get("distance", 1.0)
                similarity = max(0, 1 - distance)
                try:
                    memory_id = uuid.UUID(result["id"])
                    if exclude_memory_id and memory_id == exclude_memory_id:
                        continue
                    memory = await postgres_storage.get_memory(memory_id)
                    duplicates.append({"memory": memory, "similarity": similarity, "method": "vector"})
                except:
                    continue
            return duplicates
        except Exception as e:
            telemetry.log_memory_operation("dedup_vector_check_failed", user_id=user_id, details={"error": str(e)})
            return []

    async def _check_text_similarity(self, user_id: uuid.UUID, content: str, exclude_memory_id: uuid.UUID = None) -> List[Dict[str, Any]]:
        try:
            similar_memories = await postgres_storage.find_similar_memories(user_id=user_id, content=content, threshold=0.6)
            duplicates = []
            for memory in similar_memories:
                if exclude_memory_id and memory.id == exclude_memory_id:
                    continue
                duplicates.append({"memory": memory, "similarity": 0.75, "method": "text"})
            return duplicates
        except Exception as e:
            telemetry.log_memory_operation("dedup_text_check_failed", user_id=user_id, details={"error": str(e)})
            return []

    async def _find_exact_duplicate(self, user_id: uuid.UUID, content: str, memory_type: str, exclude_memory_id: uuid.UUID = None) -> Any:
        normalized = content.strip().lower()
        try:
            memories = await postgres_storage.get_memories_by_user(user_id=user_id, memory_type=memory_type, status="active", limit=1000)
            for memory in memories:
                if exclude_memory_id and memory.id == exclude_memory_id:
                    continue
                if memory.content.strip().lower() == normalized:
                    return memory
            return None
        except Exception as e:
            telemetry.log_memory_operation("dedup_exact_check_failed", user_id=user_id, details={"error": str(e)})
            return None

    async def merge_memories(self, existing_memory: Memory, new_content: str, new_scores: Dict[str, float]) -> Memory:
        new_avg = (new_scores["relevance"] + new_scores["novelty"] + new_scores["accuracy"]) / 3.0
        existing_avg = float(existing_memory.avg_score)
        if new_avg > existing_avg:
            updated_content = self._merge_content(existing_memory.content, new_content)
            updates = {"content": updated_content, "relevance_score": max(existing_memory.relevance_score, new_scores["relevance"]), "novelty_score": max(existing_memory.novelty_score, new_scores["novelty"]), "accuracy_score": max(existing_memory.accuracy_score, new_scores["accuracy"]), "avg_score": max(existing_avg, new_avg)}
            updated = await postgres_storage.update_memory(existing_memory.id, **updates)
            try:
                await chroma_storage.update_memory(user_id=existing_memory.user_id, memory_id=existing_memory.id, content=updated_content)
            except Exception as e:
                telemetry.log_memory_operation("chroma_merge_update_failed", user_id=existing_memory.user_id, memory_id=existing_memory.id, details={"error": str(e)})
            telemetry.log_memory_operation("merged", user_id=existing_memory.user_id, memory_id=existing_memory.id, details={"new_avg": new_avg, "old_avg": existing_avg})
            return updated
        else:
            telemetry.log_memory_operation("rejected_duplicate", user_id=existing_memory.user_id, memory_id=existing_memory.id, details={"reason": "existing_has_higher_score"})
            return existing_memory

    def _merge_content(self, existing: str, new: str) -> str:
        if len(new) > len(existing) and existing.lower() in new.lower():
            return new
        if len(existing) > len(new):
            return existing
        return f"{existing} (Updated: {new})"

    async def run_dedup_scan(self, user_id: uuid.UUID) -> Dict[str, int]:
        memories = await postgres_storage.get_memories_by_user(user_id=user_id, status="active", limit=1000)
        duplicates_found = 0
        merged = 0
        flagged = 0
        # Sort top candidates by average score and age so we preserve the strongest canonical records first.
        memories = sorted(memories, key=lambda m: (-float(m.avg_score), m.created_at))

        for index, canonical in enumerate(memories):
            for duplicate in memories[index + 1:]:
                if canonical.memory_type != duplicate.memory_type:
                    continue
                if duplicate.status != "active":
                    continue
                # Avoid self-comparison for duplicate detection
                result = await self.check_duplicates(user_id=user_id, content=duplicate.content, memory_type=duplicate.memory_type, exclude_memory_id=duplicate.id)
                if not result["is_duplicate"]:
                    continue

                duplicates_found += 1
                if result["action"] == "merge":
                    # Prefer canonical memory as the target and delete the duplicate record.
                    await self._consolidate_duplicate_memory(primary_memory=canonical, duplicate_memory=duplicate)
                    merged += 1
                elif result["action"] == "flag_for_review":
                    flagged += 1
        return {"duplicates_found": duplicates_found, "merged": merged, "flagged": flagged}

    async def _consolidate_duplicate_memory(self, primary_memory: Memory, duplicate_memory: Memory) -> Memory:
        content = self._merge_content(primary_memory.content, duplicate_memory.content)
        updated_avg = max(float(primary_memory.avg_score), float(duplicate_memory.avg_score))
        updates = {
            "content": content,
            "relevance_score": max(primary_memory.relevance_score, duplicate_memory.relevance_score),
            "novelty_score": max(primary_memory.novelty_score, duplicate_memory.novelty_score),
            "accuracy_score": max(primary_memory.accuracy_score, duplicate_memory.accuracy_score),
            "avg_score": updated_avg,
        }
        await postgres_storage.update_memory(primary_memory.id, **updates)
        await postgres_storage.update_memory(duplicate_memory.id, status="deleted")
        try:
            await chroma_storage.update_memory(user_id=primary_memory.user_id, memory_id=primary_memory.id, content=content, metadata={"avg_score": float(updated_avg), "status": "active"})
            await chroma_storage.update_memory(user_id=duplicate_memory.user_id, memory_id=duplicate_memory.id, metadata={"status": "deleted"})
        except Exception as e:
            telemetry.log_memory_operation("chroma_duplicate_consolidation_failed", user_id=primary_memory.user_id, memory_id=primary_memory.id, details={"error": str(e)})
        telemetry.log_memory_operation("duplicate_consolidated", user_id=primary_memory.user_id, memory_id=primary_memory.id, details={"duplicate_id": str(duplicate_memory.id)})
        return await postgres_storage.get_memory(primary_memory.id)


dedup_service = DedupService()
