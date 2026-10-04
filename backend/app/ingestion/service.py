from typing import Any
from app.ingestion.edgar_client import EdgarClient
from app.ingestion.layout_parser import LayoutAwareParser
from app.rag.dense import DenseRetriever
from app.rag.sparse import SparseRetriever


class IngestionService:
    """Orchestrates live SEC filing downloads, parsing, and hybrid RAG indexing."""

    def __init__(
        self,
        edgar_client: EdgarClient | None = None,
        dense_retriever: DenseRetriever | None = None,
        sparse_retriever: SparseRetriever | None = None,
    ) -> None:
        self.edgar_client = edgar_client or EdgarClient()
        self.dense_retriever = dense_retriever or DenseRetriever()
        self.sparse_retriever = sparse_retriever or SparseRetriever()

    async def ingest_filing(self, ticker: str, form: str = "10-K") -> dict[str, Any]:
        """Fetches the latest filing metadata, downloads HTML, parses into DocumentChunks, and indexes."""
        clean_ticker = ticker.upper().strip()

        # 1. Fetch metadata and download filing HTML
        metadata = await self.edgar_client.get_latest_10k_metadata(ticker=clean_ticker)
        raw_html = await self.edgar_client.download_filing_raw(metadata=metadata)

        # 2. Parse layout-aware document chunks
        parser = LayoutAwareParser()
        chunks = parser.parse(raw_html=raw_html)

        # 3. Index dense vectors in Qdrant
        await self.dense_retriever.upsert_chunks(
            chunks=chunks,
            ticker=clean_ticker,
            report_date=metadata.report_date,
        )

        # 4. Index sparse BM25 tokens
        sparse_records = [
            {
                "id": str(i),
                "text": chunk.content,
                "metadata": {
                    "section_context": chunk.section_context,
                    "chunk_type": chunk.chunk_type,
                    "table_index": chunk.table_index,
                },
            }
            for i, chunk in enumerate(chunks)
        ]
        self.sparse_retriever.index_chunks(chunks=sparse_records)

        return {
            "ticker": clean_ticker,
            "form": form,
            "report_date": metadata.report_date,
            "status": "INDEXED",
            "total_chunks": len(chunks),
            "table_chunks": sum(1 for c in chunks if c.chunk_type == "table"),
            "prose_chunks": sum(1 for c in chunks if c.chunk_type == "prose"),
        }
