import uuid
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from core.config import settings
from core.exceptions import StorageException, CircuitBreakerOpenException
from datetime import datetime


class ChromaStorage:
    def __init__(self):
        self.client = None
        self._collections = {}
        self._circuit_failures = 0
        self._circuit_last_failure = None
        self._circuit_open = False
        self._circuit_recovery_timeout = 60
        self._circuit_threshold = 5

    async def connect(self):
        try:
            if settings.ENVIRONMENT == "development":
                self.client = chromadb.Client()
            else:
                self.client = chromadb.HttpClient(host=settings.CHROMADB_HOST, port=settings.CHROMADB_PORT, settings=ChromaSettings(allow_reset=True, anonymized_telemetry=False))
            self.client.heartbeat()
            self._circuit_failures = 0
            self._circuit_open = False
        except Exception as e:
            self._record_failure()
            raise StorageException(f"Failed to connect to ChromaDB: {e}")

    def _record_failure(self):
        self._circuit_failures += 1
        self._circuit_last_failure = datetime.utcnow()
        if self._circuit_failures >= self._circuit_threshold:
            self._circuit_open = True

    def _check_circuit(self):
        if self._circuit_open:
            if self._circuit_last_failure:
                elapsed = (datetime.utcnow() - self._circuit_last_failure).total_seconds()
                if elapsed > self._circuit_recovery_timeout:
                    self._circuit_open = False
                    self._circuit_failures = 0
                    return True
            raise CircuitBreakerOpenException("ChromaDB circuit breaker is open")
        return True

    def _get_collection(self, user_id: uuid.UUID):
        if self.client is None:
            raise StorageException("ChromaDB client not connected")
        collection_name = f"memories_{str(user_id)}"
        if collection_name not in self._collections:
            self._collections[collection_name] = self.client.get_or_create_collection(name=collection_name, metadata={"user_id": str(user_id)})
        return self._collections[collection_name]

    async def add_memory(self, user_id: uuid.UUID, memory_id: uuid.UUID, content: str, embedding: List[float], metadata: Dict[str, Any] = None) -> str:
        self._check_circuit()
        try:
            collection = self._get_collection(user_id)
            chroma_id = str(memory_id)
            doc_metadata = metadata or {}
            doc_metadata.update({"memory_id": str(memory_id), "user_id": str(user_id), "created_at": datetime.utcnow().isoformat()})
            collection.add(ids=[chroma_id], documents=[content], embeddings=[embedding], metadatas=[doc_metadata])
            return chroma_id
        except Exception as e:
            self._record_failure()
            raise StorageException(f"Failed to add memory to ChromaDB: {e}")

    async def query_similar(self, user_id: uuid.UUID, query_embedding: List[float], top_k: int = 5, where: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        self._check_circuit()
        try:
            collection = self._get_collection(user_id)
            results = collection.query(query_embeddings=[query_embedding], n_results=top_k, where=where, include=["documents", "metadatas", "distances"])
            memories = []
            if results["ids"] and results["ids"][0]:
                for i, memory_id in enumerate(results["ids"][0]):
                    memories.append({"id": memory_id, "content": results["documents"][0][i] if results["documents"] else "", "metadata": results["metadatas"][0][i] if results["metadatas"] else {}, "distance": results["distances"][0][i] if results["distances"] else 0.0})
            return memories
        except Exception as e:
            self._record_failure()
            raise StorageException(f"Failed to query ChromaDB: {e}")

    async def query_by_text(self, user_id: uuid.UUID, query_text: str, top_k: int = 5, where: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        self._check_circuit()
        try:
            collection = self._get_collection(user_id)
            results = collection.query(query_texts=[query_text], n_results=top_k, where=where, include=["documents", "metadatas", "distances"])
            memories = []
            if results["ids"] and results["ids"][0]:
                for i, memory_id in enumerate(results["ids"][0]):
                    memories.append({"id": memory_id, "content": results["documents"][0][i] if results["documents"] else "", "metadata": results["metadatas"][0][i] if results["metadatas"] else {}, "distance": results["distances"][0][i] if results["distances"] else 0.0})
            return memories
        except Exception as e:
            self._record_failure()
            raise StorageException(f"Failed to query ChromaDB by text: {e}")

    async def update_memory(self, user_id: uuid.UUID, memory_id: uuid.UUID, content: str = None, metadata: Dict[str, Any] = None) -> None:
        self._check_circuit()
        try:
            collection = self._get_collection(user_id)
            chroma_id = str(memory_id)
            update_data = {}
            if content: update_data["documents"] = [content]
            if metadata: update_data["metadatas"] = [metadata]
            if update_data: collection.update(ids=[chroma_id], **update_data)
        except Exception as e:
            self._record_failure()
            raise StorageException(f"Failed to update memory in ChromaDB: {e}")

    async def delete_memory(self, user_id: uuid.UUID, memory_id: uuid.UUID) -> None:
        self._check_circuit()
        try:
            collection = self._get_collection(user_id)
            collection.delete(ids=[str(memory_id)])
        except Exception as e:
            self._record_failure()
            raise StorageException(f"Failed to delete memory from ChromaDB: {e}")

    async def is_healthy(self) -> bool:
        try:
            if self.client is None: return False
            self.client.heartbeat()
            return True
        except:
            return False


chroma_storage = ChromaStorage()
