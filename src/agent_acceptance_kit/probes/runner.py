"""Execute probes against evaluation layers."""

from __future__ import annotations

from agent_acceptance_kit.config import LayerConfig
from agent_acceptance_kit.connectors.base import Connector, get_connector
from agent_acceptance_kit.probes.base import (
    CrossLayerProbeResult,
    LayerProbeResult,
    Probe,
    ProbeOutcome,
    ProbeSuite,
)
from agent_acceptance_kit.probes.loader import evaluate_response


def run_probe_on_layer(
    probe: Probe,
    layer: LayerConfig,
    connector: Connector | None = None,
) -> LayerProbeResult:
    client = connector or get_connector(layer)
    try:
        response = client.complete(probe.prompt, context=probe.context)
        passed, detail = evaluate_response(response, probe.expectation)
        outcome = ProbeOutcome.PASS if passed else ProbeOutcome.FAIL
        return LayerProbeResult(
            probe_id=probe.id,
            layer=layer.name,
            outcome=outcome,
            response=response,
            detail=detail,
        )
    except Exception as exc:  # noqa: BLE001 — surface connector errors as probe errors
        return LayerProbeResult(
            probe_id=probe.id,
            layer=layer.name,
            outcome=ProbeOutcome.ERROR,
            response="",
            detail=str(exc),
        )


def run_cross_layer_probe(
    probe: Probe,
    layer_a: LayerConfig,
    layer_b: LayerConfig,
    connector_a: Connector | None = None,
    connector_b: Connector | None = None,
) -> CrossLayerProbeResult:
    return CrossLayerProbeResult(
        probe=probe,
        layer_a=run_probe_on_layer(probe, layer_a, connector_a),
        layer_b=run_probe_on_layer(probe, layer_b, connector_b),
    )


def run_suite_cross_layer(
    suite: ProbeSuite,
    layer_a: LayerConfig,
    layer_b: LayerConfig,
    connector_a: Connector | None = None,
    connector_b: Connector | None = None,
) -> list[CrossLayerProbeResult]:
    return [
        run_cross_layer_probe(probe, layer_a, layer_b, connector_a, connector_b)
        for probe in suite.probes
    ]
