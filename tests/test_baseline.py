from __future__ import annotations

from pathlib import Path

import pytest

from agent_handoff.baseline.runner import (
    load_baseline_result,
    run_baseline,
    save_baseline_result,
)
from agent_handoff.config import load_scenario_config
from agent_handoff.models import (
    BaselineRunResult,
    LayerResult,
    ScenarioResult,
)
from agent_handoff.report.generator import generate_report

SCENARIO_CONFIG = Path("scenarios/support-agent/scenarios.yaml")


def test_load_scenario_config_has_three_scenarios() -> None:
    config = load_scenario_config(SCENARIO_CONFIG)
    assert config.name == "Generic support-agent handoff baseline"
    assert len(config.scenarios) == 3
    assert config.scenarios[0].id == "billing-duplicate-charge"


def test_sample_baseline_passes() -> None:
    result = run_baseline(SCENARIO_CONFIG)
    assert result.passed is True
    assert len(result.scenarios) == 3
    for scenario in result.scenarios:
        assert scenario.passed is True
        assert len(scenario.layers) == 4


def test_prompt_drift_failure_detected(tmp_path: Path) -> None:
    config_path = tmp_path / "scenarios.yaml"
    config_path.write_text(
        """
version: "1"
name: drift-test
fixtures_root: fixtures
scenarios:
  - id: drift
    name: Drift
    system_prompt: "You are support."
    turns: []
    checks:
      prompt_drift:
        required_fragments:
          - billing policy
""",
        encoding="utf-8",
    )
    result = run_baseline(config_path)
    assert result.passed is False
    layer = result.scenarios[0].layers[0]
    assert layer.layer == "prompt_drift"
    assert layer.passed is False


def test_tool_schema_failure_detected(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures" / "schemas"
    fixtures.mkdir(parents=True)
    (fixtures / "tools.json").write_text(
        '{"lookup": {"required": ["id"]}}',
        encoding="utf-8",
    )
    config_path = tmp_path / "scenarios.yaml"
    config_path.write_text(
        """
version: "1"
name: tool-test
fixtures_root: fixtures
scenarios:
  - id: tool
    name: Tool
    system_prompt: ""
    turns:
      - role: assistant
        content: hi
        tool_calls:
          - name: lookup
            arguments: {}
    checks:
      tool_schema:
        allowed_tools: [lookup]
        required_calls: [lookup]
        schema_file: schemas/tools.json
""",
        encoding="utf-8",
    )
    result = run_baseline(config_path)
    assert result.passed is False
    assert result.scenarios[0].layers[0].passed is False


def test_memory_bleed_failure_detected(tmp_path: Path) -> None:
    config_path = tmp_path / "scenarios.yaml"
    config_path.write_text(
        """
version: "1"
name: memory-test
fixtures_root: fixtures
scenarios:
  - id: bleed
    name: Bleed
    system_prompt: "internal escalation notes"
    turns: []
    checks:
      memory_bleed:
        forbidden_in_context:
          - internal escalation notes
""",
        encoding="utf-8",
    )
    result = run_baseline(config_path)
    assert result.passed is False


def test_retrieval_miss_failure_detected(tmp_path: Path) -> None:
    config_path = tmp_path / "scenarios.yaml"
    config_path.write_text(
        """
version: "1"
name: retrieval-test
fixtures_root: fixtures
scenarios:
  - id: miss
    name: Miss
    system_prompt: ""
    turns: []
    checks:
      retrieval:
        required_sources: [policy.md]
        retrieved_sources: []
""",
        encoding="utf-8",
    )
    result = run_baseline(config_path)
    assert result.passed is False


def test_baseline_result_round_trip(tmp_path: Path) -> None:
    result = run_baseline(SCENARIO_CONFIG)
    output = tmp_path / "results.json"
    save_baseline_result(result, output)
    loaded = load_baseline_result(output)
    assert loaded.passed == result.passed
    assert len(loaded.scenarios) == len(result.scenarios)


def test_generate_report_includes_sections() -> None:
    result = run_baseline(SCENARIO_CONFIG)
    markdown = generate_report(result, client_name="Acme Corp")
    assert "Executive summary" in markdown
    assert "Per-layer results" in markdown
    assert "Known limitations" in markdown
    assert "Acme Corp" in markdown
    assert "Approved for handoff" in markdown


def test_generate_report_blocked_on_failure() -> None:
    result = BaselineRunResult(
        config_name="fail",
        config_path="scenarios.yaml",
        passed=False,
        scenarios=[
            ScenarioResult(
                scenario_id="x",
                scenario_name="X",
                passed=False,
                layers=[
                    LayerResult(
                        layer="retrieval",
                        passed=False,
                        message="retrieval miss",
                        details=("missing doc",),
                    )
                ],
            )
        ],
    )
    markdown = generate_report(result)
    assert "Blocked — regressions detected" in markdown
    assert "missing doc" in markdown
