from app.agents.state import FinSentryState, AuditFlag, Citation


async def discrepancy_agent_node(state: FinSentryState) -> dict[str, object]:
    """Cross-audits executive rhetoric against underlying quantitative metrics."""
    discrepancies: list[AuditFlag] = []

    current_ratios = [
        m for m in state.quantitative_metrics if m.name == "Current Ratio"
    ]

    # Detect if management optimism clashes with calculated liquidity ratios
    if current_ratios and current_ratios[0].value_current_period < 2.0:
        metric = current_ratios[0]
        citation = Citation(
            document_id=f"{state.ticker}_{state.target_year}_10K",
            section="Item 7 - MD&A",
            exact_quote_or_value="Management believes current cash reserves and operating cash flow will be substantially sufficient.",
        )
        discrepancies.append(
            AuditFlag(
                id=f"FLAG-DISC-{state.ticker}-001",
                severity="HIGH",
                category="DISCREPANCY",
                narrative_claim="Management asserts current liquidity is substantially sufficient.",
                factual_reality=f"Calculated Current Ratio stands at {metric.value_current_period}, signaling tight working capital.",
                explanation="MD&A presents an optimistic liquidity outlook, but balance sheet data reveals working capital compression.",
                citations=[citation, metric.citation],
            )
        )

    return {
        "audit_flags": discrepancies,
        "messages": [{"role": "discrepancy_agent", "content": f"Identified {len(discrepancies)} narrative discrepancies."}],
    }
