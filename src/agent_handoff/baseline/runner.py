from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from agent_handoff.baseline.scorers import (
    score_memory_bleed,
    score_prompt_drift,
    score_retrieval,
    score_tool_schema,
)
from agent_handoff.config import load_scenario_config
from agent_handoff.models import (
    BaselineRunResult,
    LayerResult,
    Scenario,
    ScenarioResult,
)


def _evaluate_scenario(scenario: Scenario, fixtures_root: Path) -> ScenarioResult:
    layers: list[LayerResult] = []
    checks = scenario.checks

    if checks.prompt_drift:
        layers.append(
            score_prompt_drift(scenario, checks.prompt_drift, fixtures_root)
        )
    if checks.tool_schema:
        layers.append(score_tool_schema(scenario, checks.tool_schema, fixtures_root))
    if checks.memory_bleed:
        layers.append(score_memory_bleed(scenario, checks.memory_bleed))
    if checks.retrieval:
        layers.append(score_retrieval(checks.retrieval))

    passed = all(layer.passed for layer in layers) if layers else True
    return ScenarioResult(
        scenario_id=scenario.id,
        scenario_name=scenario.name,
        passed=passed,
        layers=layers,
    )


def run_baseline(config_path: Path) -> BaselineRunResult:
    config = load_scenario_config(config_path)
    fixtures_root = config_path.parent / config.fixtures_root
    scenario_results = [
        _evaluate_scenario(scenario, fixtures_root) for scenario in config.scenarios
    ]
    passed = all(result.passed for result in scenario_results)
    return BaselineRunResult(
        config_name=config.name,
        config_path=str(config_path),
        passed=passed,
        scenarios=scenario_results,
    )


def save_baseline_result(result: BaselineRunResult, output_path: Path) -> None:
    payload = asdict(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_baseline_result(path: Path) -> BaselineRunResult:
    data = json.loads(path.read_text(encoding="utf-8"))
    scenarios: list[ScenarioResult] = []
    for item in data.get("scenarios") or []:
        layers = [
            LayerResult(
                layer=layer["layer"],
                passed=layer["passed"],
                message=layer["message"],
                details=tuple(layer.get("details") or ()),
            )
            for layer in item.get("layers") or []
        ]
        scenarios.append(
            ScenarioResult(
                scenario_id=item["scenario_id"],
                scenario_name=item["scenario_name"],
                passed=item["passed"],
                layers=layers,
            )
        )
    return BaselineRunResult(
        config_name=data["config_name"],
        config_path=data["config_path"],
        passed=data["passed"],
        scenarios=scenarios,
    )
