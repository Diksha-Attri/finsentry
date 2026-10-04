import json
from collections.abc import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse  # type: ignore[import-untyped]
from app.agents.graph import finsentry_graph
from app.agents.state import FinSentryState
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="FinSentry Financial Intelligence Gateway",
    version="0.1.0",
    description="Production Multi-Agent Financial Due Diligence Engine with Hybrid RAG and Sandboxed Verification.",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuditRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol, e.g. AAPL")
    target_year: str = Field(..., description="Target fiscal year, e.g. 2024")
    query: str = Field(..., description="Specific due diligence or audit inquiry")


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Service health and liveness probe."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.ENVIRONMENT,
    )


@app.post("/api/v1/audit/sync")
async def run_audit_sync(request: AuditRequest) -> dict[str, object]:
    """Synchronous execution returning the final audit state once complete."""
    initial_state = FinSentryState(
        ticker=request.ticker.upper(),
        target_year=request.target_year,
        query=request.query,
    )

    try:
        final_state = await finsentry_graph.ainvoke(initial_state)
        return {
            "ticker": final_state["ticker"],
            "target_year": final_state["target_year"],
            "validation_passed": final_state["validation_passed"],
            "quantitative_metrics": [m.model_dump() for m in final_state["quantitative_metrics"]],
            "audit_flags": [f.model_dump() for f in final_state["audit_flags"]],
            "final_audit_report": final_state["final_audit_report"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit execution failed: {str(e)}") from e


@app.post("/api/v1/audit/stream")
async def run_audit_stream(request: AuditRequest) -> EventSourceResponse:
    """Streams live multi-agent execution events via Server-Sent Events (SSE)."""
    initial_state = FinSentryState(
        ticker=request.ticker.upper(),
        target_year=request.target_year,
        query=request.query,
    )

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        # Send initial start event
        yield {
            "event": "workflow_start",
            "data": json.dumps({"ticker": request.ticker.upper(), "year": request.target_year}),
        }

        try:
            # astream yields whenever a node completes execution
            async for step_output in finsentry_graph.astream(initial_state):
                for node_name, node_update in step_output.items():
                    event_payload = {
                        "node": node_name,
                        "messages": node_update.get("messages", []),
                    }
                    if "quantitative_metrics" in node_update:
                        event_payload["metrics_count"] = len(node_update["quantitative_metrics"])
                    if "audit_flags" in node_update:
                        event_payload["flags_count"] = len(node_update["audit_flags"])
                    if "final_audit_report" in node_update:
                        event_payload["report"] = node_update["final_audit_report"]

                    yield {
                        "event": "node_update",
                        "data": json.dumps(event_payload),
                    }

            yield {
                "event": "workflow_complete",
                "data": json.dumps({"status": "SUCCESS"}),
            }
        except Exception as err:
            yield {
                "event": "workflow_error",
                "data": json.dumps({"error": str(err)}),
            }

    return EventSourceResponse(event_generator())
