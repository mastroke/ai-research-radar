"""Command line interface for Agent Acceptance Kit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent_acceptance_kit import __version__
from agent_acceptance_kit.baseline import (
    load_baseline_result,
    run_baseline,
    save_baseline_result,
)
from agent_acceptance_kit.config import load_config
from agent_acceptance_kit.probes.loader import list_suites, load_suite
from agent_acceptance_kit.report.markdown import render_markdown_report
from agent_acceptance_kit.report.pdf import render_pdf_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aak",
        description=(
            "Run cross-layer agent acceptance baselines and emit attribution reports."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    baseline = sub.add_parser("baseline", help="Cross-layer baseline commands")
    baseline_sub = baseline.add_subparsers(dest="baseline_command", required=True)
    run = baseline_sub.add_parser(
        "run",
        help="Run frozen probes against Layer A (agent) and Layer B (raw API)",
    )
    run.add_argument(
        "-c",
        "--config",
        type=Path,
        default=None,
        help="TOML config path. Defaults to AAK_CONFIG or built-in mock layers.",
    )
    run.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write JSON results to this path.",
    )
    run.add_argument(
        "--report-md",
        type=Path,
        default=None,
        help="Also write a markdown acceptance report.",
    )
    run.add_argument(
        "--report-pdf",
        type=Path,
        default=None,
        help="Also write a PDF acceptance report (requires [pdf] extra).",
    )

    suites = sub.add_parser("suites", help="Inspect packaged probe suites")
    suites_sub = suites.add_subparsers(dest="suites_command", required=True)
    suites_list = suites_sub.add_parser("list", help="List starter probe suites")
    suites_show = suites_sub.add_parser("show", help="Show probes in one suite")
    suites_show.add_argument("name", help="Suite name, e.g. rag")

    report = sub.add_parser("report", help="Render reports from saved baseline JSON")
    report.add_argument("results", type=Path, help="Baseline JSON from `aak baseline run`")
    report.add_argument(
        "--format",
        choices=("markdown", "pdf", "json"),
        default="markdown",
        help="Output format",
    )
    report.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Destination file",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "baseline" and args.baseline_command == "run":
        return _cmd_baseline_run(args)
    if args.command == "suites" and args.suites_command == "list":
        return _cmd_suites_list()
    if args.command == "suites" and args.suites_command == "show":
        return _cmd_suites_show(args.name)
    if args.command == "report":
        return _cmd_report(args)
    parser.error("Unknown command")
    return 2


def _cmd_baseline_run(args) -> int:
    config = load_config(args.config)
    result = run_baseline(config)
    payload = result.to_dict()

    output = args.output or config.output_dir / "baseline-result.json"
    save_baseline_result(result, output)

    if args.report_md:
        args.report_md.write_text(render_markdown_report(payload), encoding="utf-8")
    if args.report_pdf:
        render_pdf_report(payload, args.report_pdf)

    print(json.dumps({"verdict": payload["verdict"], "output": str(output)}, indent=2))
    return 0


def _cmd_suites_list() -> int:
    for name in list_suites():
        suite = load_suite(name)
        print(f"{name}\tv{suite.version}\t{len(suite.probes)} probes\t{suite.description}")
    return 0


def _cmd_suites_show(name: str) -> int:
    suite = load_suite(name)
    print(f"# {suite.name} v{suite.version}")
    print(suite.description)
    for probe in suite.probes:
        print(f"- {probe.id}: {probe.prompt[:80]}...")
    return 0


def _cmd_report(args) -> int:
    data = load_baseline_result(args.results)
    if args.format == "json":
        args.output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    elif args.format == "markdown":
        args.output.write_text(render_markdown_report(data), encoding="utf-8")
    elif args.format == "pdf":
        render_pdf_report(data, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
