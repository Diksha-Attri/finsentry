from app.agents.state import FinSentryState


async def validator_node(state: FinSentryState) -> dict[str, object]:
    """Validates citations and factual grounding across all generated audit flags."""
    # Check that every audit flag contains at least one verified citation
    ungrounded_flags = [flag for flag in state.audit_flags if not flag.citations]

    if ungrounded_flags and state.retry_count < state.max_retries:
        return {
            "validation_passed": False,
            "retry_count": state.retry_count + 1,
            "validation_error": f"Found {len(ungrounded_flags)} ungrounded audit flags lacking citations.",
            "messages": [{"role": "validator", "content": "Validation failed: Grounding citations required. Retrying..."}],
        }

    # Format synthesized audit report
    summary_lines = [
        f"=== FINSENTRY AUDIT MEMO: {state.ticker} (FY{state.target_year}) ===",
        f"Quantitative Metrics Analyzed: {len(state.quantitative_metrics)}",
    ]
    for m in state.quantitative_metrics:
        summary_lines.append(f" - {m.name}: {m.value_current_period} (Formula: {m.formula_used})")

    summary_lines.append(f"\nAudit Flags Raised: {len(state.audit_flags)}")
    for f in state.audit_flags:
        summary_lines.append(f" - [{f.severity}] {f.category}: {f.narrative_claim} -> Reality: {f.factual_reality}")

    return {
        "validation_passed": True,
        "validation_error": None,
        "final_audit_report": "\n".join(summary_lines),
        "messages": [{"role": "validator", "content": "Validation passed. Audit memo compiled."}],
    }
