from dataclasses import dataclass
from typing import Any
import hashlib
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr
from app.core.config import get_settings
from app.ingestion.layout_parser import DocumentChunk

settings = get_settings()


@dataclass
class SearchResult:
    chunk_id: str
    content: str
    score: float
    chunk_type: str
    section_context: str
    metadata: dict[str, Any]


class DenseRetriever:
    """Manages dense vector embeddings and similarity search inside Qdrant."""

    def __init__(self) -> None:
        self.client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=None,
            https=False,
            check_compatibility=False,
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        
        # Only initialize real OpenAI client if a genuine key is provided
        has_valid_key = (
            settings.OPENAI_API_KEY
            and settings.OPENAI_API_KEY.startswith("sk-")
            and not settings.OPENAI_API_KEY.endswith("here")
        )
        self.embeddings = (
            OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                api_key=SecretStr(settings.OPENAI_API_KEY),
            )
            if has_valid_key
            else None
        )

    async def initialize_collection(self, vector_size: int = 1536) -> None:
        """Create the Qdrant collection if it does not already exist."""
        collections = await self.client.get_collections()
        exists = any(c.name == self.collection_name for c in collections.collections)

        if not exists:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
            )

    def _compute_offline_vector(self, text: str, dim: int = 1536) -> list[float]:
        """Deterministic pseudo-embedding for testing environments without API credits."""
        h = hashlib.sha256(text.encode("utf-8")).digest()
        pseudo = [float(b) / 255.0 for b in h]
        return (pseudo * (dim // len(pseudo) + 1))[:dim]

    async def upsert_chunks(
        self,
        chunks: list[DocumentChunk],
        ticker: str,
        report_date: str,
    ) -> list[str]:
        """Generate embeddings and upsert document chunks with metadata into Qdrant."""
        if not chunks:
            return []

        await self.initialize_collection()

        texts = [chunk.content for chunk in chunks]

        if self.embeddings:
            vectors = await self.embeddings.aembed_documents(texts)
        else:
            vectors = [self._compute_offline_vector(t) for t in texts]

        points = []
        chunk_ids: list[str] = []

        for idx, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
            chunk_id = f"{ticker}_{report_date}_{idx}"
            chunk_ids.append(chunk_id)
            payload = {
                "chunk_id": chunk_id,
                "ticker": ticker,
                "report_date": report_date,
                "chunk_type": chunk.chunk_type,
                "section_context": chunk.section_context,
                "table_index": chunk.table_index,
                "content": chunk.content,
            }
            points.append(
                models.PointStruct(
                    id=idx,
                    vector=vector,
                    payload=payload,
                )
            )

        await self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        return chunk_ids

    async def search(self, query: str, top_k: int = 15) -> list[SearchResult]:
        """Perform dense semantic similarity search."""
        if self.embeddings:
            query_vector = await self.embeddings.aembed_query(query)
        else:
            query_vector = self._compute_offline_vector(query)

        response = await self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
        )

        results: list[SearchResult] = []
        for scored_point in response.points:
            payload = scored_point.payload or {}
            results.append(
                SearchResult(
                    chunk_id=str(payload.get("chunk_id", "")),
                    content=str(payload.get("content", "")),
                    score=scored_point.score,
                    chunk_type=str(payload.get("chunk_type", "prose")),
                    section_context=str(payload.get("section_context", "")),
                    metadata=payload,
                )
            )
        return results
