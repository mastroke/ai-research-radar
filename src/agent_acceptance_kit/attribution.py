"""Layer attribution logic for cross-layer baseline comparison."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent_acceptance_kit.probes.base import CrossLayerProbeResult, ProbeOutcome


class AttributionClass(str, Enum):
    BASELINE_MET = "baseline_met"
    AGENT_VALUE_ADD = "agent_value_add"
    AGENT_REGRESSION = "agent_regression"
    SHARED_FAILURE = "shared_failure"
    PARTIAL_AGENT = "partial_agent"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class ProbeAttribution:
    probe_id: str
    suite: str
    classification: AttributionClass
    summary: str

    def to_dict(self) -> dict:
        return {
            "probe_id": self.probe_id,
            "suite": self.suite,
            "classification": self.classification.value,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class BaselineVerdict:
    scope: str
    classification: AttributionClass
    pass_rate_a: float
    pass_rate_b: float
    agent_value_add_count: int
    agent_regression_count: int
    shared_failure_count: int
    baseline_met_count: int
    total_probes: int
    summary: str

    def to_dict(self) -> dict:
        return {
            "scope": self.scope,
            "classification": self.classification.value,
            "pass_rate_a": self.pass_rate_a,
            "pass_rate_b": self.pass_rate_b,
            "agent_value_add_count": self.agent_value_add_count,
            "agent_regression_count": self.agent_regression_count,
            "shared_failure_count": self.shared_failure_count,
            "baseline_met_count": self.baseline_met_count,
            "total_probes": self.total_probes,
            "summary": self.summary,
        }


def _passed(outcome: ProbeOutcome) -> bool:
    return outcome == ProbeOutcome.PASS


def attribute_probe(result: CrossLayerProbeResult) -> ProbeAttribution:
    a_ok = _passed(result.layer_a.outcome)
    b_ok = _passed(result.layer_b.outcome)

    if a_ok and b_ok:
        cls = AttributionClass.BASELINE_MET
        summary = "Both layers pass; acceptance criteria met at agent and raw API."
    elif a_ok and not b_ok:
        cls = AttributionClass.AGENT_VALUE_ADD
        summary = (
            "Agent endpoint passes while raw API fails — value attributed to "
            "orchestration, tools, or retrieval layer."
        )
    elif b_ok and not a_ok:
        cls = AttributionClass.AGENT_REGRESSION
        summary = (
            "Raw API passes while agent endpoint fails — regression attributed "
            "to agent stack (routing, tools, or prompt assembly)."
        )
    elif result.layer_a.outcome == ProbeOutcome.ERROR or result.layer_b.outcome == ProbeOutcome.ERROR:
        cls = AttributionClass.INCONCLUSIVE
        summary = "Connector error prevented a clean A/B comparison."
    else:
        cls = AttributionClass.SHARED_FAILURE
        summary = (
            "Both layers fail — issue likely in model capability, probe design, "
            "or shared context, not agent-specific wiring."
        )

    return ProbeAttribution(
        probe_id=result.probe.id,
        suite=result.probe.suite,
        classification=cls,
        summary=summary,
    )


def summarize_verdict(attributions: list[ProbeAttribution], *, scope: str) -> BaselineVerdict:
    total = len(attributions)
    if total == 0:
        return BaselineVerdict(
            scope=scope,
            classification=AttributionClass.INCONCLUSIVE,
            pass_rate_a=0.0,
            pass_rate_b=0.0,
            agent_value_add_count=0,
            agent_regression_count=0,
            shared_failure_count=0,
            baseline_met_count=0,
            total_probes=0,
            summary="No probes executed.",
        )

    counts = {c: 0 for c in AttributionClass}
    for item in attributions:
        counts[item.classification] += 1

    pass_a = sum(
        1
        for _ in attributions
        if _.classification in (AttributionClass.BASELINE_MET, AttributionClass.AGENT_VALUE_ADD)
    )
    pass_b = sum(
        1
        for _ in attributions
        if _.classification in (AttributionClass.BASELINE_MET, AttributionClass.AGENT_REGRESSION)
    )

    overall = _pick_overall_class(counts, total)
    summary = _overall_summary(overall, counts, total)

    return BaselineVerdict(
        scope=scope,
        classification=overall,
        pass_rate_a=round(pass_a / total, 4),
        pass_rate_b=round(pass_b / total, 4),
        agent_value_add_count=counts[AttributionClass.AGENT_VALUE_ADD],
        agent_regression_count=counts[AttributionClass.AGENT_REGRESSION],
        shared_failure_count=counts[AttributionClass.SHARED_FAILURE],
        baseline_met_count=counts[AttributionClass.BASELINE_MET],
        total_probes=total,
        summary=summary,
    )


def _pick_overall_class(counts: dict[AttributionClass, int], total: int) -> AttributionClass:
    if counts[AttributionClass.AGENT_REGRESSION] > 0:
        return AttributionClass.AGENT_REGRESSION
    if counts[AttributionClass.SHARED_FAILURE] == total:
        return AttributionClass.SHARED_FAILURE
    if counts[AttributionClass.AGENT_VALUE_ADD] > counts[AttributionClass.BASELINE_MET]:
        return AttributionClass.AGENT_VALUE_ADD
    if counts[AttributionClass.BASELINE_MET] >= total // 2:
        return AttributionClass.BASELINE_MET
    if counts[AttributionClass.INCONCLUSIVE] == total:
        return AttributionClass.INCONCLUSIVE
    return AttributionClass.PARTIAL_AGENT


def _overall_summary(
    overall: AttributionClass,
    counts: dict[AttributionClass, int],
    total: int,
) -> str:
    if overall == AttributionClass.AGENT_REGRESSION:
        return (
            f"Agent regressions detected on {counts[AttributionClass.AGENT_REGRESSION]} "
            f"of {total} probes — investigate agent stack before acceptance."
        )
    if overall == AttributionClass.SHARED_FAILURE:
        return f"All {total} probes failed on both layers — revisit model or probe set."
    if overall == AttributionClass.AGENT_VALUE_ADD:
        return (
            f"Agent layer adds measurable value on "
            f"{counts[AttributionClass.AGENT_VALUE_ADD]} probes versus raw API."
        )
    if overall == AttributionClass.BASELINE_MET:
        return (
            f"Acceptance baseline met on {counts[AttributionClass.BASELINE_MET]} "
            f"of {total} probes with both layers passing."
        )
    return (
        f"Mixed attribution across {total} probes — see per-probe verdicts for procurement."
    )
