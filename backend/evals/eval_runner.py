import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from app.agents.graph import finsentry_graph
from app.agents.state import FinSentryState


@dataclass
class EvalResult:
    scenario_id: str
    passed: bool
    citation_grounding_score: float
    detected_metric_match: bool
    flags_coverage_score: float
    details: dict[str, Any]


class FinSentryEvaluator:
    """Evaluates multi-agent audit faithfulness, metric precision, and citation coverage."""

    def __init__(self, dataset_path: Path | None = None) -> None:
        self.dataset_path = dataset_path or Path(__file__).parent / "golden_dataset.json"

    def load_dataset(self) -> list[dict[str, Any]]:
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]

    async def evaluate_scenario(self, scenario: dict[str, Any]) -> EvalResult:
        state = FinSentryState(
            ticker=scenario["ticker"],
            target_year=scenario["target_year"],
            query=scenario["input_query"],
        )

        final_state = await finsentry_graph.ainvoke(state)

        # 1. Evaluate Metric Precision
        metrics = final_state.get("quantitative_metrics", [])
        expected_metric_name = scenario["expected_metric"]
        min_val = scenario["expected_metric_min"]
        max_val = scenario["expected_metric_max"]

        metric_match = False
        for m in metrics:
            if m.name == expected_metric_name and min_val <= m.value_current_period <= max_val:
                metric_match = True
                break

        # 2. Evaluate Flag Category Coverage
        flags = final_state.get("audit_flags", [])
        detected_categories = {f.category for f in flags}
        expected_categories = set(scenario.get("expected_flags", []))
        
        common_flags = detected_categories.intersection(expected_categories)
        flag_coverage = len(common_flags) / len(expected_categories) if expected_categories else 1.0

        # 3. Evaluate Citation Grounding
        total_flags = len(flags)
        grounded_flags = sum(1 for f in flags if len(f.citations) > 0)
        citation_score = grounded_flags / total_flags if total_flags > 0 else 1.0

        # Scenario passes if grounding is 100% and metrics/flags meet thresholds
        passed = (citation_score == 1.0) and metric_match and (flag_coverage >= 0.5)

        return EvalResult(
            scenario_id=scenario["id"],
            passed=passed,
            citation_grounding_score=citation_score,
            detected_metric_match=metric_match,
            flags_coverage_score=flag_coverage,
            details={
                "metrics_found": [m.name for m in metrics],
                "categories_detected": list(detected_categories),
            },
        )

    async def run_all(self) -> list[EvalResult]:
        dataset = self.load_dataset()
        results: list[EvalResult] = []
        for item in dataset:
            result = await self.evaluate_scenario(item)
            results.append(result)
        return results
