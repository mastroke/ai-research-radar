"""Cross-layer baseline orchestration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from agent_acceptance_kit.attribution import BaselineVerdict, attribute_probe, summarize_verdict
from agent_acceptance_kit.config import BaselineConfig
from agent_acceptance_kit.probes.base import CrossLayerProbeResult, ProbeOutcome, ProbeSuite
from agent_acceptance_kit.probes.loader import load_suites
from agent_acceptance_kit.probes.runner import run_suite_cross_layer


@dataclass(frozen=True)
class SuiteRunResult:
    suite: ProbeSuite
    probes: tuple[CrossLayerProbeResult, ...]
    verdict: BaselineVerdict


@dataclass(frozen=True)
class BaselineRunResult:
    config: BaselineConfig
    started_at: str
    finished_at: str
    suites: tuple[SuiteRunResult, ...]
    verdict: BaselineVerdict

    def to_dict(self) -> dict:
        return {
            "title": self.config.title,
            "frozen_probe_version": self.config.frozen_probe_version,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "layer_a": asdict(self.config.layer_a),
            "layer_b": asdict(self.config.layer_b),
            "verdict": self.verdict.to_dict(),
            "suites": [
                {
                    "name": s.suite.name,
                    "version": s.suite.version,
                    "description": s.suite.description,
                    "verdict": s.verdict.to_dict(),
                    "probes": [_probe_dict(p) for p in s.probes],
                }
                for s in self.suites
            ],
        }


def run_baseline(config: BaselineConfig) -> BaselineRunResult:
    started = datetime.now(tz=UTC).isoformat()
    suites = load_suites(config.suites)
    suite_results: list[SuiteRunResult] = []

    for suite in suites:
        probes = run_suite_cross_layer(suite, config.layer_a, config.layer_b)
        attributions = [attribute_probe(p) for p in probes]
        verdict = summarize_verdict(attributions, scope=suite.name)
        suite_results.append(
            SuiteRunResult(suite=suite, probes=tuple(probes), verdict=verdict)
        )

    all_attributions = [
        attribute_probe(p) for sr in suite_results for p in sr.probes
    ]
    overall = summarize_verdict(all_attributions, scope="overall")
    finished = datetime.now(tz=UTC).isoformat()
    return BaselineRunResult(
        config=config,
        started_at=started,
        finished_at=finished,
        suites=tuple(suite_results),
        verdict=overall,
    )


def save_baseline_result(result: BaselineRunResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")


def load_baseline_result(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _probe_dict(result: CrossLayerProbeResult) -> dict:
    attribution = attribute_probe(result)
    return {
        "probe_id": result.probe.id,
        "suite": result.probe.suite,
        "tags": list(result.probe.tags),
        "layer_a": _layer_result_dict(result.layer_a),
        "layer_b": _layer_result_dict(result.layer_b),
        "attribution": attribution.to_dict(),
    }


def _layer_result_dict(layer_result) -> dict:
    return {
        "layer": layer_result.layer,
        "outcome": layer_result.outcome.value,
        "detail": layer_result.detail,
        "response_excerpt": layer_result.response[:240],
    }
