import re
from typing import Any
from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]
from app.rag.dense import SearchResult


class SparseRetriever:
    """In-memory BM25 lexical retriever for exact token and numerical search."""

    def __init__(self) -> None:
        self.bm25: BM25Okapi | None = None
        self.corpus_chunks: list[dict[str, Any]] = []

    def _tokenize(self, text: str) -> list[str]:
        """Lowercase and extract alphanumeric tokens."""
        return re.findall(r"\w+", text.lower())

    def index_chunks(self, chunks: list[dict[str, Any]]) -> None:
        """Build the BM25 inverted index over chunk contents."""
        self.corpus_chunks = chunks
        tokenized_corpus = [self._tokenize(chunk["content"]) for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query: str, top_k: int = 15) -> list[SearchResult]:
        """Execute BM25 score ranking against indexed documents."""
        if not self.bm25 or not self.corpus_chunks:
            return []

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: float(scores[i]),
            reverse=True,
        )[:top_k]

        results: list[SearchResult] = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score <= 0.0:
                continue

            chunk = self.corpus_chunks[idx]
            results.append(
                SearchResult(
                    chunk_id=chunk["chunk_id"],
                    content=chunk["content"],
                    score=score,
                    chunk_type=chunk.get("chunk_type", "prose"),
                    section_context=chunk.get("section_context", ""),
                    metadata=chunk,
                )
            )

        return results
