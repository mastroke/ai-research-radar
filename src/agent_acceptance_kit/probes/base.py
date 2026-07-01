"""Probe and probe-suite data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProbeOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


@dataclass(frozen=True)
class ProbeExpectation:
    """Frozen acceptance criteria for a single probe."""

    contains: tuple[str, ...] = ()
    not_contains: tuple[str, ...] = ()
    regex: tuple[str, ...] = ()
    min_length: int = 0


@dataclass(frozen=True)
class Probe:
    """One immutable probe in a frozen suite."""

    id: str
    suite: str
    prompt: str
    expectation: ProbeExpectation
    tags: tuple[str, ...] = ()
    context: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProbeSuite:
    """Versioned collection of probes for one capability area."""

    name: str
    version: str
    description: str
    probes: tuple[Probe, ...]


@dataclass(frozen=True)
class LayerProbeResult:
    """Outcome of running one probe against one layer."""

    probe_id: str
    layer: str
    outcome: ProbeOutcome
    response: str
    detail: str = ""


@dataclass(frozen=True)
class CrossLayerProbeResult:
    """Paired A/B results for one probe."""

    probe: Probe
    layer_a: LayerProbeResult
    layer_b: LayerProbeResult
