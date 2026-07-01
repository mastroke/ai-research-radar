"""Deterministic mock connectors for offline baseline runs."""

from __future__ import annotations

import hashlib

from agent_acceptance_kit.probes.loader import evaluate_response
from agent_acceptance_kit.probes.loader import load_suite
from agent_acceptance_kit.probes.base import ProbeExpectation


class MockConnector:
    """Simulates layer behavior using frozen probe expectations."""

    def __init__(self, layer_name: str) -> None:
        self.layer_name = layer_name
        self._is_agent = "agent" in layer_name.lower()

    def complete(self, prompt: str, *, context: str = "") -> str:
        probe = _match_probe(prompt, context)
        if probe is None:
            return f"[{self.layer_name}] Unrecognized probe prompt."

        if self._is_agent:
            return _agent_response(probe.id, probe.expectation, context)
        return _api_response(probe.id, probe.expectation, context)


def _match_probe(prompt: str, context: str):
    for suite_name in ("rag", "tool_use", "coding_agent"):
        suite = load_suite(suite_name)
        for probe in suite.probes:
            if probe.prompt.strip() == prompt.strip() and probe.context.strip() == context.strip():
                return probe
    return None


def _agent_response(probe_id: str, expectation: ProbeExpectation, context: str) -> str:
    """Agent layer generally meets expectations; injects structured framing."""

    parts = [
        f"Agent layer response for {probe_id}.",
        "Orchestration: tools and retrieval engaged.",
    ]
    if context:
        parts.append(f"Context used: {context[:120]}")
    parts.extend(expectation.contains)
    if expectation.regex:
        seed = hashlib.sha256(probe_id.encode()).hexdigest()[:8]
        parts.append(f"trace_id={seed}")
    return "\n".join(parts)


def _api_response(probe_id: str, expectation: ProbeExpectation, context: str) -> str:
    """Raw API layer omits agent affordances; some probes intentionally fail."""

    if probe_id.startswith("rag-"):
        # Raw API lacks retrieval — miss citation markers.
        return (
            f"Raw API response for {probe_id}. "
            "Based on general knowledge, I cannot cite the provided document."
        )
    if probe_id.startswith("tool-"):
        # Raw API cannot invoke tools.
        return (
            f"Raw API response for {probe_id}. "
            "I do not have access to tools in this mode."
        )
    if probe_id.startswith("code-"):
        # Raw API can answer simple coding probes but may skip tests mention.
        body = f"Raw API response for {probe_id}.\n```python\n# partial solution\npass\n```"
        if "pytest" in " ".join(expectation.contains).lower():
            return body
        return body + "\n" + "\n".join(expectation.contains)

    passed, _ = evaluate_response("\n".join(expectation.contains), expectation)
    if passed:
        return "\n".join(expectation.contains)
    return f"Raw API response for {probe_id} without agent scaffolding."
