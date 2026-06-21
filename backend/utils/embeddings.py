from sentence_transformers import SentenceTransformer
import asyncio
from typing import List

# Load model once at startup
_model = SentenceTransformer('all-MiniLM-L6-v2')

class EmbeddingService:
    async def generate_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")
        # Run in thread pool to avoid blocking the async event loop
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, _model.encode, text)
        return embedding.tolist()

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return []
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, _model.encode, valid_texts)
        return embeddings.tolist()


embedding_service = EmbeddingService()