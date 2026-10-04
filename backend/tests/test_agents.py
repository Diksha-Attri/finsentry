import pytest
from app.agents.graph import finsentry_graph
from app.agents.state import FinSentryState


@pytest.mark.asyncio
async def test_finsentry_graph_full_audit_workflow() -> None:
    initial_state = FinSentryState(
        ticker="AAPL",
        target_year="2024",
        query="Audit balance sheet liquidity and debt covenant risk factors for Apple.",
    )

    final_state = await finsentry_graph.ainvoke(initial_state)

    assert final_state["validation_passed"] is True
    assert len(final_state["quantitative_metrics"]) > 0
    assert len(final_state["audit_flags"]) >= 2
    assert final_state["final_audit_report"] is not None
    assert "FINSENTRY AUDIT MEMO" in final_state["final_audit_report"]
