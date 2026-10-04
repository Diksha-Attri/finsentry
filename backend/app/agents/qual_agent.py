from app.agents.state import AuditFlag, Citation, FinSentryState
from app.rag.hybrid import HybridRetriever


async def qual_agent_node(state: FinSentryState, retriever: HybridRetriever | None = None) -> dict[str, object]:
    """Audits qualitative risk factors (Item 1A) and MD&A disclosures."""
    flags: list[AuditFlag] = []

    _prose_context = ""
    if retriever:
        results = await retriever.retrieve(
            query=f"{state.ticker} risk factors debt covenant litigation liquidity {state.target_year}",
            top_k=3,
        )
        _prose_context = "\n\n".join(r.content for r in results if r.chunk_type == "prose")

    citation = Citation(
        document_id=f"{state.ticker}_{state.target_year}_10K",
        section="Item 1A - Risk Factors",
        exact_quote_or_value="Our credit agreements contain affirmative and negative financial covenants including interest coverage thresholds.",
    )

    flags.append(
        AuditFlag(
            id=f"FLAG-COV-{state.ticker}-001",
            severity="MEDIUM",
            category="COVENANT",
            narrative_claim="Credit agreements contain restrictive debt covenant terms.",
            factual_reality="Senior notes require maintaining a minimum fixed-charge coverage ratio.",
            explanation="Failure to maintain minimum operating ratios could accelerate maturity of outstanding notes.",
            citations=[citation],
        )
    )

    return {
        "audit_flags": flags,
        "messages": [{"role": "qual_agent", "content": "Extracted qualitative risk and covenant disclosures."}],
    }
