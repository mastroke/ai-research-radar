from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent_handoff import __version__
from agent_handoff.baseline.runner import run_baseline, save_baseline_result
from agent_handoff.report.generator import generate_report_from_file


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-handoff",
        description=(
            "Deterministic baseline replay and sign-off reporting for agent handoffs."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    baseline = subparsers.add_parser(
        "baseline",
        help="Run frozen multi-turn scenario baselines.",
    )
    baseline_sub = baseline.add_subparsers(dest="baseline_command", required=True)

    baseline_run = baseline_sub.add_parser(
        "run",
        help="Replay scenarios and score cross-layer regressions.",
    )
    baseline_run.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to scenarios.yaml baseline config.",
    )
    baseline_run.add_argument(
        "--output",
        type=Path,
        default=Path(".handoff/baseline-results.json"),
        help="JSON results path (default: .handoff/baseline-results.json).",
    )

    report = subparsers.add_parser(
        "report",
        help="Generate client-ready sign-off reports.",
    )
    report_sub = report.add_subparsers(dest="report_command", required=True)

    report_generate = report_sub.add_parser(
        "generate",
        help="Render Markdown sign-off report from baseline results.",
    )
    report_generate.add_argument(
        "--results",
        type=Path,
        default=Path(".handoff/baseline-results.json"),
        help="Baseline JSON results (default: .handoff/baseline-results.json).",
    )
    report_generate.add_argument(
        "--output",
        type=Path,
        default=Path(".handoff/handoff-report.md"),
        help="Markdown output path (default: .handoff/handoff-report.md).",
    )
    report_generate.add_argument(
        "--client-name",
        default="Client",
        help="Client name for the report header.",
    )
    report_generate.add_argument(
        "--project-name",
        default=None,
        help="Optional project title override.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "baseline" and args.baseline_command == "run":
        if not args.config.exists():
            parser.error(f"config not found: {args.config}")
        result = run_baseline(args.config)
        save_baseline_result(result, args.output)

        counts = result.summary_counts()
        print(f"Baseline: {result.config_name}")
        print(f"Scenarios: {counts['passed']}/{counts['total']} passed")
        for scenario in result.scenarios:
            status = "PASS" if scenario.passed else "FAIL"
            print(f"  [{status}] {scenario.scenario_id}")
            for layer in scenario.layers:
                layer_status = "pass" if layer.passed else "fail"
                print(f"    - {layer.layer}: {layer_status} — {layer.message}")

        print(f"Results written to {args.output}")
        return 0 if result.passed else 1

    if args.command == "report" and args.report_command == "generate":
        if not args.results.exists():
            parser.error(f"results not found: {args.results}")
        generate_report_from_file(
            args.results,
            args.output,
            client_name=args.client_name,
            project_name=args.project_name,
        )
        print(f"Report written to {args.output}")
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
