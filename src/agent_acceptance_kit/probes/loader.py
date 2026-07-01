"""Load frozen probe suites from packaged YAML."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from agent_acceptance_kit.probes.base import Probe, ProbeExpectation, ProbeSuite

SUITE_NAMES = ("rag", "tool_use", "coding_agent")


def suite_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "suites"


def list_suites() -> list[str]:
    names: list[str] = []
    for path in sorted(suite_dir().glob("*.yaml")):
        names.append(path.stem)
    return names


def load_suite(name: str) -> ProbeSuite:
    path = suite_dir() / f"{name}.yaml"
    if not path.exists():
        msg = f"Unknown probe suite: {name!r}. Available: {', '.join(list_suites())}"
        raise FileNotFoundError(msg)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _parse_suite(raw, fallback_name=name)


def load_suites(names: tuple[str, ...] | list[str]) -> list[ProbeSuite]:
    if not names:
        return [load_suite(n) for n in SUITE_NAMES]
    return [load_suite(n) for n in names]


def _parse_suite(raw: dict[str, Any], fallback_name: str) -> ProbeSuite:
    probes: list[Probe] = []
    for item in raw.get("probes", []):
        probes.append(_parse_probe(item, suite_name=str(raw.get("name", fallback_name))))
    return ProbeSuite(
        name=str(raw.get("name", fallback_name)),
        version=str(raw.get("version", "1.0.0")),
        description=str(raw.get("description", "")),
        probes=tuple(probes),
    )


def _parse_probe(raw: dict[str, Any], suite_name: str) -> Probe:
    exp_raw = raw.get("expectation", {})
    expectation = ProbeExpectation(
        contains=tuple(str(x) for x in exp_raw.get("contains", ())),
        not_contains=tuple(str(x) for x in exp_raw.get("not_contains", ())),
        regex=tuple(str(x) for x in exp_raw.get("regex", ())),
        min_length=int(exp_raw.get("min_length", 0)),
    )
    return Probe(
        id=str(raw["id"]),
        suite=suite_name,
        prompt=str(raw["prompt"]),
        expectation=expectation,
        tags=tuple(str(t) for t in raw.get("tags", ())),
        context=str(raw.get("context", "")),
        metadata=dict(raw.get("metadata", {})),
    )


def evaluate_response(text: str, expectation: ProbeExpectation) -> tuple[bool, str]:
    if len(text) < expectation.min_length:
        return False, f"Response shorter than min_length={expectation.min_length}"

    for needle in expectation.contains:
        if needle.lower() not in text.lower():
            return False, f"Missing required substring: {needle!r}"

    for needle in expectation.not_contains:
        if needle.lower() in text.lower():
            return False, f"Forbidden substring present: {needle!r}"

    for pattern in expectation.regex:
        if not re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            return False, f"Regex did not match: {pattern!r}"

    return True, "All expectations met"
