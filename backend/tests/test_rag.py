import pytest
from app.rag.dense import DenseRetriever
from app.rag.sparse import SparseRetriever
from app.rag.hybrid import HybridRetriever
from app.ingestion.layout_parser import DocumentChunk


@pytest.mark.asyncio
async def test_hybrid_retriever_pipeline() -> None:
    dense = DenseRetriever()
    sparse = SparseRetriever()
    hybrid = HybridRetriever(dense=dense, sparse=sparse)

    # Mock sample financial chunks
    chunks = [
        DocumentChunk(
            chunk_type="table",
            content="| Total Debt | $45,000M |\n| Cash Equivalents | $12,000M |",
            section_context="Item 8 - Financial Statements",
            table_index=1,
        ),
        DocumentChunk(
            chunk_type="prose",
            content="The company issued $5,000M of senior unsecured notes due 2031 under credit covenant agreements.",
            section_context="Item 8 - Note 9 Debt",
        ),
        DocumentChunk(
            chunk_type="prose",
            content="Our marketing expenses increased by 14% due to international product expansion in EMEA.",
            section_context="Item 7 - MD&A",
        ),
    ]

    # Index into Dense and Sparse
    await dense.upsert_chunks(chunks=chunks, ticker="AAPL", report_date="2024-09-30")

    sparse_corpus = [
        {
            "chunk_id": f"AAPL_2024-09-30_{idx}",
            "content": chunk.content,
            "chunk_type": chunk.chunk_type,
            "section_context": chunk.section_context,
        }
        for idx, chunk in enumerate(chunks)
    ]
    sparse.index_chunks(sparse_corpus)

    # Query targeting numerical table data
    results = await hybrid.retrieve(query="What is the Total Debt and Cash Equivalents?", top_k=2)

    assert len(results) > 0
    # Top result should be the table containing Total Debt
    assert any("Total Debt" in r.content for r in results)
