from collections import defaultdict
from flashrank import Ranker, RerankRequest  # type: ignore[import-untyped]
from app.rag.dense import DenseRetriever, SearchResult
from app.rag.sparse import SparseRetriever


class HybridRetriever:
    """Fuses Dense Qdrant and Sparse BM25 results via RRF and FlashRank."""

    def __init__(
        self,
        dense: DenseRetriever,
        sparse: SparseRetriever,
        rrf_k: int = 60,
    ) -> None:
        self.dense = dense
        self.sparse = sparse
        self.rrf_k = rrf_k
        self.ranker = Ranker(model_name="ms-marco-TinyBERT-L-2-v2", cache_dir="/tmp/flashrank")

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        candidate_pool_size: int = 20,
    ) -> list[SearchResult]:
        """Performs hybrid retrieval with Reciprocal Rank Fusion and re-ranking."""
        dense_results = await self.dense.search(query, top_k=candidate_pool_size)
        sparse_results = self.sparse.search(query, top_k=candidate_pool_size)

        rrf_scores: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, SearchResult] = {}

        for rank, res in enumerate(dense_results):
            rrf_scores[res.chunk_id] += 1.0 / (self.rrf_k + (rank + 1))
            chunk_map[res.chunk_id] = res

        for rank, res in enumerate(sparse_results):
            rrf_scores[res.chunk_id] += 1.0 / (self.rrf_k + (rank + 1))
            chunk_map[res.chunk_id] = res

        sorted_candidates = sorted(
            rrf_scores.keys(),
            key=lambda cid: rrf_scores[cid],
            reverse=True,
        )[:candidate_pool_size]

        if not sorted_candidates:
            return []

        passages = [
            {"id": cid, "text": chunk_map[cid].content}
            for cid in sorted_candidates
        ]

        rerank_request = RerankRequest(query=query, passages=passages)
        reranked_output = self.ranker.rerank(rerank_request)

        final_results: list[SearchResult] = []
        for item in reranked_output[:top_k]:
            cid = str(item["id"])
            original = chunk_map[cid]
            final_results.append(
                SearchResult(
                    chunk_id=original.chunk_id,
                    content=original.content,
                    score=float(item["score"]),
                    chunk_type=original.chunk_type,
                    section_context=original.section_context,
                    metadata=original.metadata,
                )
            )

        return final_results
