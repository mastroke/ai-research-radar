from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class Turn:
    role: str
    content: str
    tool_calls: tuple[ToolCall, ...] = ()
    name: str | None = None


@dataclass(frozen=True)
class PromptDriftCheck:
    required_fragments: tuple[str, ...] = ()
    forbidden_fragments: tuple[str, ...] = ()
    baseline_prompt_file: str | None = None


@dataclass(frozen=True)
class ToolSchemaCheck:
    allowed_tools: tuple[str, ...] = ()
    required_calls: tuple[str, ...] = ()
    schema_file: str | None = None


@dataclass(frozen=True)
class MemoryBleedCheck:
    forbidden_in_context: tuple[str, ...] = ()
    max_context_chars: int | None = None


@dataclass(frozen=True)
class RetrievalCheck:
    required_sources: tuple[str, ...] = ()
    retrieved_sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScenarioChecks:
    prompt_drift: PromptDriftCheck | None = None
    tool_schema: ToolSchemaCheck | None = None
    memory_bleed: MemoryBleedCheck | None = None
    retrieval: RetrievalCheck | None = None


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    system_prompt: str
    turns: tuple[Turn, ...]
    checks: ScenarioChecks


@dataclass(frozen=True)
class ScenarioConfig:
    version: str
    name: str
    fixtures_root: str
    scenarios: tuple[Scenario, ...]


@dataclass(frozen=True)
class LayerResult:
    layer: str
    passed: bool
    message: str
    details: tuple[str, ...] = ()


@dataclass
class ScenarioResult:
    scenario_id: str
    scenario_name: str
    passed: bool
    layers: list[LayerResult] = field(default_factory=list)


@dataclass
class BaselineRunResult:
    config_name: str
    config_path: str
    passed: bool
    scenarios: list[ScenarioResult] = field(default_factory=list)

    def summary_counts(self) -> dict[str, int]:
        total = len(self.scenarios)
        passed = sum(1 for scenario in self.scenarios if scenario.passed)
        return {"total": total, "passed": passed, "failed": total - passed}
