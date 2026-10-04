import pytest
from evals.eval_runner import FinSentryEvaluator


@pytest.mark.asyncio
async def test_golden_dataset_evaluations() -> None:
    evaluator = FinSentryEvaluator()
    results = await evaluator.run_all()

    assert len(results) > 0
    for res in results:
        # Every golden case must maintain 100% citation grounding
        assert res.citation_grounding_score == 1.0, f"Scenario {res.scenario_id} produced ungrounded flags!"
        # Metric bounds must be respected
        assert res.detected_metric_match is True, f"Scenario {res.scenario_id} failed metric boundaries!"
        assert res.passed is True
