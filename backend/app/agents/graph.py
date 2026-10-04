from typing import Literal
from langgraph.graph import StateGraph, START, END
from app.agents.state import FinSentryState
from app.agents.router import router_node
from app.agents.quant_agent import quant_agent_node
from app.agents.qual_agent import qual_agent_node
from app.agents.discrepancy import discrepancy_agent_node
from app.agents.validator import validator_node


def route_decision(state: FinSentryState) -> Literal["quant_agent", "__end__"]:
    """Conditional edge evaluating router outcome."""
    last_message = state.messages[-1]["content"] if state.messages else ""
    if "FACTUAL_LOOKUP" in last_message:
        return "__end__"
    return "quant_agent"


def validation_decision(state: FinSentryState) -> Literal["__end__", "quant_agent"]:
    """Conditional self-healing loop: retries if validation fails."""
    if not state.validation_passed and state.retry_count <= state.max_retries:
        return "quant_agent"
    return "__end__"


def create_finsentry_graph() -> StateGraph:
    """Builds and compiles the FinSentry multi-agent state graph."""
    workflow = StateGraph(FinSentryState)

    # Register Nodes
    workflow.add_node("router", router_node)
    workflow.add_node("quant_agent", quant_agent_node)
    workflow.add_node("qual_agent", qual_agent_node)
    workflow.add_node("discrepancy_agent", discrepancy_agent_node)
    workflow.add_node("validator", validator_node)

    # Flow Edges
    workflow.add_edge(START, "router")
    workflow.add_conditional_edges("router", route_decision, {"quant_agent": "quant_agent", "__end__": END})
    workflow.add_edge("quant_agent", "qual_agent")
    workflow.add_edge("qual_agent", "discrepancy_agent")
    workflow.add_edge("discrepancy_agent", "validator")
    workflow.add_conditional_edges("validator", validation_decision, {"quant_agent": "quant_agent", "__end__": END})

    return workflow


finsentry_graph = create_finsentry_graph().compile()
