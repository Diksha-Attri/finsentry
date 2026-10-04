from typing import Literal, cast
from pydantic import BaseModel, Field
from app.agents.state import FinSentryState
from app.agents.llm_factory import get_chat_model


class RoutingDecision(BaseModel):
    intent: Literal["FULL_AUDIT", "FACTUAL_LOOKUP"] = Field(
        description="Select 'FULL_AUDIT' for comprehensive multi-year evaluations, or 'FACTUAL_LOOKUP' for single data points."
    )
    reasoning: str = Field(description="Explanation of the routing path.")


async def router_node(state: FinSentryState) -> dict[str, object]:
    """Evaluates query complexity to determine the execution graph route."""
    query = state.query
    system_prompt = (
        "You are the FinSentry Supervisor Router. Analyze the user request.\n"
        "If it requires verifying ratios, footnotes, balance sheets, or management risk factors, route to 'FULL_AUDIT'.\n"
        "If it is a simple single question (e.g. 'What is the ticker symbol for Apple?'), route to 'FACTUAL_LOOKUP'."
    )

    llm = get_chat_model(temperature=0.0, use_reasoning_model=False)

    try:
        structured_llm = llm.with_structured_output(RoutingDecision)  # type: ignore[attr-defined]
        raw_decision = await structured_llm.ainvoke(
            [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}]
        )
        decision = cast(RoutingDecision, raw_decision)
        intent = decision.intent
    except Exception:
        intent = "FULL_AUDIT"

    return {
        "messages": [{"role": "supervisor", "content": f"Routed query to workflow: {intent}"}]
    }
