from typing import List
import httpx
from core.config import settings
from core.exceptions import StorageException


class EmbeddingService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_EMBEDDING_MODEL
        self.base_url = "https://api.groq.com/openai/v1"

    async def generate_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            raise StorageException("Cannot generate embedding for empty text")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"input": text[:8000], "model": self.model, "encoding_format": "float"}
                )
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            raise StorageException(f"Failed to generate embedding: {e}")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        batch_size = 100
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = [t[:8000] for t in texts[i:i + batch_size] if t and t.strip()]
            if not batch: continue
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.base_url}/embeddings",
                        headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                        json={"input": batch, "model": self.model, "encoding_format": "float"}
                    )
                    response.raise_for_status()
                    data = response.json()
                    embeddings = [item["embedding"] for item in data["data"]]
                    all_embeddings.extend(embeddings)
            except Exception as e:
                raise StorageException(f"Failed to generate batch embeddings: {e}")
        return all_embeddings


embedding_service = EmbeddingService()
