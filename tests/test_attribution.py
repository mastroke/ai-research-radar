"""Tests for cross-layer attribution."""

from __future__ import annotations

from agent_acceptance_kit.attribution import AttributionClass, attribute_probe, summarize_verdict
from agent_acceptance_kit.probes.base import (
    CrossLayerProbeResult,
    LayerProbeResult,
    Probe,
    ProbeExpectation,
    ProbeOutcome,
)


def _probe(probe_id: str = "p1") -> Probe:
    return Probe(
        id=probe_id,
        suite="test",
        prompt="hello",
        expectation=ProbeExpectation(),
    )


def test_attribute_baseline_met() -> None:
    result = CrossLayerProbeResult(
        probe=_probe(),
        layer_a=LayerProbeResult("p1", "a", ProbeOutcome.PASS, "ok"),
        layer_b=LayerProbeResult("p1", "b", ProbeOutcome.PASS, "ok"),
    )
    attr = attribute_probe(result)
    assert attr.classification == AttributionClass.BASELINE_MET


def test_attribute_agent_value_add() -> None:
    result = CrossLayerProbeResult(
        probe=_probe(),
        layer_a=LayerProbeResult("p1", "a", ProbeOutcome.PASS, "ok"),
        layer_b=LayerProbeResult("p1", "b", ProbeOutcome.FAIL, "bad"),
    )
    attr = attribute_probe(result)
    assert attr.classification == AttributionClass.AGENT_VALUE_ADD


def test_attribute_agent_regression() -> None:
    result = CrossLayerProbeResult(
        probe=_probe(),
        layer_a=LayerProbeResult("p1", "a", ProbeOutcome.FAIL, "bad"),
        layer_b=LayerProbeResult("p1", "b", ProbeOutcome.PASS, "ok"),
    )
    attr = attribute_probe(result)
    assert attr.classification == AttributionClass.AGENT_REGRESSION


def test_summarize_verdict_flags_regression() -> None:
    attrs = [
        attribute_probe(
            CrossLayerProbeResult(
                probe=_probe("r1"),
                layer_a=LayerProbeResult("r1", "a", ProbeOutcome.FAIL, ""),
                layer_b=LayerProbeResult("r1", "b", ProbeOutcome.PASS, ""),
            )
        )
    ]
    verdict = summarize_verdict(attrs, scope="overall")
    assert verdict.classification == AttributionClass.AGENT_REGRESSION
