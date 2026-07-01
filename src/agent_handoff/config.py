from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agent_handoff.models import (
    MemoryBleedCheck,
    PromptDriftCheck,
    RetrievalCheck,
    Scenario,
    ScenarioChecks,
    ScenarioConfig,
    ToolCall,
    ToolSchemaCheck,
    Turn,
)


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)


def _parse_tool_calls(raw_calls: Any) -> tuple[ToolCall, ...]:
    if not raw_calls:
        return ()
    calls: list[ToolCall] = []
    for item in raw_calls:
        calls.append(
            ToolCall(
                name=str(item["name"]),
                arguments=dict(item.get("arguments") or {}),
            )
        )
    return tuple(calls)


def _parse_turn(raw: dict[str, Any]) -> Turn:
    return Turn(
        role=str(raw["role"]),
        content=str(raw.get("content") or ""),
        tool_calls=_parse_tool_calls(raw.get("tool_calls")),
        name=str(raw["name"]) if raw.get("name") else None,
    )


def _parse_checks(raw: dict[str, Any] | None) -> ScenarioChecks:
    if not raw:
        return ScenarioChecks()

    prompt_raw = raw.get("prompt_drift") or {}
    tool_raw = raw.get("tool_schema") or {}
    memory_raw = raw.get("memory_bleed") or {}
    retrieval_raw = raw.get("retrieval") or {}

    return ScenarioChecks(
        prompt_drift=PromptDriftCheck(
            required_fragments=_as_tuple(prompt_raw.get("required_fragments")),
            forbidden_fragments=_as_tuple(prompt_raw.get("forbidden_fragments")),
            baseline_prompt_file=prompt_raw.get("baseline_prompt_file"),
        )
        if prompt_raw
        else None,
        tool_schema=ToolSchemaCheck(
            allowed_tools=_as_tuple(tool_raw.get("allowed_tools")),
            required_calls=_as_tuple(tool_raw.get("required_calls")),
            schema_file=tool_raw.get("schema_file"),
        )
        if tool_raw
        else None,
        memory_bleed=MemoryBleedCheck(
            forbidden_in_context=_as_tuple(memory_raw.get("forbidden_in_context")),
            max_context_chars=memory_raw.get("max_context_chars"),
        )
        if memory_raw
        else None,
        retrieval=RetrievalCheck(
            required_sources=_as_tuple(retrieval_raw.get("required_sources")),
            retrieved_sources=_as_tuple(retrieval_raw.get("retrieved_sources")),
        )
        if retrieval_raw
        else None,
    )


def _parse_scenario(raw: dict[str, Any]) -> Scenario:
    return Scenario(
        id=str(raw["id"]),
        name=str(raw.get("name") or raw["id"]),
        system_prompt=str(raw.get("system_prompt") or ""),
        turns=tuple(_parse_turn(turn) for turn in raw.get("turns") or []),
        checks=_parse_checks(raw.get("checks")),
    )


def load_scenario_config(path: Path) -> ScenarioConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid scenario config: {path}")

    scenarios_raw = data.get("scenarios") or []
    return ScenarioConfig(
        version=str(data.get("version") or "1"),
        name=str(data.get("name") or path.stem),
        fixtures_root=str(data.get("fixtures_root") or "fixtures"),
        scenarios=tuple(_parse_scenario(item) for item in scenarios_raw),
    )
