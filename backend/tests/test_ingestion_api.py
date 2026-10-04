import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app
from app.ingestion.layout_parser import DocumentChunk
from app.ingestion.edgar_client import FilingMetadata


@pytest.mark.asyncio
async def test_ingest_endpoint() -> None:
    transport = ASGITransport(app=app)

    mock_metadata = FilingMetadata(
        ticker="AAPL",
        cik="0000320193",
        accession_number="0000320193-24-000106",
        form="10-K",
        filing_date="2024-11-01",
        report_date="2024-09-28",
    )

    mock_chunks = [
        DocumentChunk(
            content="| Cash and Cash Equivalents | $29,943 |",
            chunk_type="table",
            section_context="Item 8 - Consolidated Financial Statements",
            table_index=1,
        ),
        DocumentChunk(
            content="Risk factors concerning debt covenant compliance.",
            chunk_type="prose",
            section_context="Item 1A - Risk Factors",
            table_index=None,
        ),
    ]

    with patch(
        "app.ingestion.service.EdgarClient.get_latest_10k_metadata",
        new_callable=AsyncMock,
        return_value=mock_metadata,
    ), patch(
        "app.ingestion.service.EdgarClient.download_filing_raw",
        new_callable=AsyncMock,
        return_value="<html><body>Mock Filing Content</body></html>",
    ), patch(
        "app.ingestion.service.LayoutAwareParser.parse",
        return_value=mock_chunks,
    ), patch(
        "app.ingestion.service.DenseRetriever.upsert_chunks",
        new_callable=AsyncMock,
        return_value=["id-1", "id-2"],
    ), patch(
        "app.ingestion.service.SparseRetriever.index_chunks",
        new_callable=MagicMock,
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ingest",
                json={"ticker": "AAPL", "form": "10-K"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["ticker"] == "AAPL"
            assert data["status"] == "INDEXED"
            assert data["report_date"] == "2024-09-28"
            assert data["total_chunks"] == 2
            assert data["table_chunks"] == 1
            assert data["prose_chunks"] == 1
