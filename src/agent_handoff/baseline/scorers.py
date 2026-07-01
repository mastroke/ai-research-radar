from __future__ import annotations

import json
from pathlib import Path

from agent_handoff.models import (
    LayerResult,
    MemoryBleedCheck,
    PromptDriftCheck,
    RetrievalCheck,
    Scenario,
    ToolSchemaCheck,
)


def _build_context(scenario: Scenario) -> str:
    parts = [scenario.system_prompt]
    for turn in scenario.turns:
        label = turn.name or turn.role
        parts.append(f"{label}: {turn.content}")
        for call in turn.tool_calls:
            parts.append(f"tool_call:{call.name}:{json.dumps(call.arguments, sort_keys=True)}")
    return "\n".join(parts)


def score_prompt_drift(
    scenario: Scenario,
    check: PromptDriftCheck,
    fixtures_root: Path,
) -> LayerResult:
    prompt = scenario.system_prompt
    details: list[str] = []

    for fragment in check.required_fragments:
        if fragment not in prompt:
            details.append(f"missing required fragment: {fragment!r}")

    for fragment in check.forbidden_fragments:
        if fragment in prompt:
            details.append(f"forbidden fragment present: {fragment!r}")

    if check.baseline_prompt_file:
        baseline_path = fixtures_root / check.baseline_prompt_file
        if not baseline_path.exists():
            details.append(f"baseline prompt file not found: {baseline_path}")
        else:
            baseline = baseline_path.read_text(encoding="utf-8")
            if prompt.strip() != baseline.strip():
                details.append("system prompt drifted from frozen baseline file")

    passed = not details
    message = "prompt matches frozen baseline" if passed else "prompt drift detected"
    return LayerResult("prompt_drift", passed, message, tuple(details))


def score_tool_schema(
    scenario: Scenario,
    check: ToolSchemaCheck,
    fixtures_root: Path,
) -> LayerResult:
    details: list[str] = []
    observed_calls: list[str] = []

    for turn in scenario.turns:
        for call in turn.tool_calls:
            observed_calls.append(call.name)
            if check.allowed_tools and call.name not in check.allowed_tools:
                details.append(f"unexpected tool call: {call.name}")

    for required in check.required_calls:
        if required not in observed_calls:
            details.append(f"missing required tool call: {required}")

    if check.schema_file:
        schema_path = fixtures_root / check.schema_file
        if not schema_path.exists():
            details.append(f"tool schema file not found: {schema_path}")
        else:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            for turn in scenario.turns:
                for call in turn.tool_calls:
                    tool_schema = schema.get(call.name)
                    if tool_schema is None:
                        details.append(f"no schema entry for tool: {call.name}")
                        continue
                    required_args = set(tool_schema.get("required") or [])
                    missing = required_args - set(call.arguments)
                    if missing:
                        details.append(
                            f"{call.name} missing required arguments: {sorted(missing)}"
                        )

    passed = not details
    message = "tool calls match frozen schema" if passed else "tool/schema mismatch"
    return LayerResult("tool_schema", passed, message, tuple(details))


def score_memory_bleed(scenario: Scenario, check: MemoryBleedCheck) -> LayerResult:
    context = _build_context(scenario)
    details: list[str] = []

    for fragment in check.forbidden_in_context:
        if fragment in context:
            details.append(f"forbidden context fragment leaked: {fragment!r}")

    if check.max_context_chars is not None and len(context) > check.max_context_chars:
        details.append(
            f"context length {len(context)} exceeds limit {check.max_context_chars}"
        )

    passed = not details
    message = "no memory bleed detected" if passed else "memory bleed detected"
    return LayerResult("memory_bleed", passed, message, tuple(details))


def score_retrieval(check: RetrievalCheck) -> LayerResult:
    details: list[str] = []
    retrieved = set(check.retrieved_sources)

    for source in check.required_sources:
        if source not in retrieved:
            details.append(f"required source not retrieved: {source}")

    passed = not details
    message = "retrieval matches frozen fixture" if passed else "retrieval miss"
    return LayerResult("retrieval", passed, message, tuple(details))
