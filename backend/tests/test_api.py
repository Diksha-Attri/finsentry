import json
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_sync_audit_endpoint() -> None:
    transport = ASGITransport(app=app)
    payload = {
        "ticker": "AAPL",
        "target_year": "2024",
        "query": "Verify balance sheet debt and working capital liquidity.",
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/audit/sync", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["validation_passed"] is True
        assert len(data["quantitative_metrics"]) > 0
        assert len(data["audit_flags"]) > 0
        assert data["final_audit_report"] is not None


@pytest.mark.asyncio
async def test_stream_audit_endpoint() -> None:
    transport = ASGITransport(app=app)
    payload = {
        "ticker": "AAPL",
        "target_year": "2024",
        "query": "Stream audit progress for Apple.",
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/audit/stream", json=payload)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        # Verify stream content contains our SSE event tokens
        body = response.text
        assert "event: workflow_start" in body
        assert "event: node_update" in body
        assert "event: workflow_complete" in body
