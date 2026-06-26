"""Command line interface for AI Research Radar."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Sequence, TextIO

from ai_research_radar.brief import Finding
from ai_research_radar.config import RadarConfig, load_config
from ai_research_radar.connectors import fetch_from_sources
from ai_research_radar.memory import open_memory_store
from ai_research_radar.synthesis import get_provider, synthesize_brief
from ai_research_radar.synthesis.base import SynthesisProvider
from ai_research_radar.synthesis.structured import StructuredBrief


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="radar",
        description="Compile configured AI research seed items into a concise brief.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    once = subparsers.add_parser("once", help="Compile one research brief")
    _add_common_options(once)

    run = subparsers.add_parser("run", help="Compile briefs on a fixed interval")
    _add_common_options(run)
    run.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Stop after N iterations. Omit to run until interrupted.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "once":
            config = _load_cli_config(args)
            _emit_once(config, stdout=sys.stdout)
            return 0

        if args.command == "run":
            return _run_loop(args, stdout=sys.stdout)
    except KeyboardInterrupt:
        return 130

    parser.error(f"Unknown command: {args.command}")
    return 2


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=None,
        help="Path to a TOML config file. Defaults to RADAR_CONFIG if set.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write the brief to this path instead of stdout.",
    )
    parser.add_argument(
        "--item",
        action="append",
        default=[],
        metavar="TITLE|URL|SOURCE|NOTE",
        help="Add a seed item. URL alone is also accepted.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="Maximum number of items to include in the brief.",
    )


def _load_cli_config(args: argparse.Namespace) -> RadarConfig:
    config = load_config(args.config)
    cli_items = tuple(_parse_item(value) for value in args.item)
    output_path = args.output if args.output is not None else config.output_path
    max_items = args.max_items if args.max_items is not None else config.max_items

    return RadarConfig(
        title=config.title,
        topic=config.topic,
        watch_terms=config.watch_terms,
        items=config.items + cli_items,
        sources=config.sources,
        output_path=output_path,
        interval_seconds=config.interval_seconds,
        max_items=max_items,
        connector_timeout_seconds=config.connector_timeout_seconds,
        memory_path=config.memory_path,
        synthesis_provider=config.synthesis_provider,
        synthesis_model=config.synthesis_model,
        synthesis_timeout_seconds=config.synthesis_timeout_seconds,
        synthesis_min_source_families=config.synthesis_min_source_families,
    )


def _collect_findings(config: RadarConfig) -> list[Finding]:
    findings = list(config.items)
    if config.sources:
        findings.extend(
            fetch_from_sources(
                config.sources,
                watch_terms=config.watch_terms,
                timeout=config.connector_timeout_seconds,
                max_results=config.max_items,
            )
        )
    return findings


def _emit_once(config: RadarConfig, *, stdout: TextIO) -> str:
    store = open_memory_store(config.memory_path)
    all_findings = store.merge_findings(_collect_findings(config))
    unseen_findings = store.filter_unseen(all_findings)
    no_signal_message = None
    if not unseen_findings and all_findings:
        no_signal_message = (
            "No new items since the last brief. Findings remain in the memory store."
        )

    brief = synthesize_brief(
        unseen_findings,
        watch_terms=list(config.watch_terms),
        title=config.title,
        topic=config.topic,
        provider=_resolve_synthesis_provider(config),
        max_items=config.max_items,
        min_source_families=config.synthesis_min_source_families,
        no_signal_message=no_signal_message,
    )
    store.mark_briefed(_findings_from_structured_brief(brief))
    store.persist()

    if config.output_path:
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        config.output_path.write_text(brief.markdown, encoding="utf-8")
    else:
        stdout.write(brief.markdown)

    return brief.markdown


def _resolve_synthesis_provider(config: RadarConfig) -> SynthesisProvider | None:
    if not config.synthesis_provider:
        return None
    return get_provider(
        config.synthesis_provider,
        model=config.synthesis_model,
    )


def _findings_from_structured_brief(brief: StructuredBrief) -> list[Finding]:
    return [
        Finding(
            title=item.title,
            url=item.url,
            source=item.source,
            note=item.synthesis,
        )
        for item in brief.items
    ]


def _run_loop(args: argparse.Namespace, *, stdout: TextIO) -> int:
    config = _load_cli_config(args)
    limit = args.limit
    if limit is not None and limit <= 0:
        raise ValueError("--limit must be positive when provided")

    completed = 0
    while limit is None or completed < limit:
        _emit_once(config, stdout=stdout)
        completed += 1
        if limit is not None and completed >= limit:
            break
        time.sleep(config.interval_seconds)

    return 0


def _parse_item(value: str) -> Finding:
    parts = [part.strip() for part in value.split("|")]
    if len(parts) == 1:
        url = parts[0]
        title = _title_from_url(url)
        return Finding(title=title, url=url, source="manual")

    if len(parts) > 4:
        raise ValueError("--item accepts at most four pipe-separated fields")

    title = parts[0]
    url = parts[1] if len(parts) > 1 else ""
    source = parts[2] if len(parts) > 2 and parts[2] else "manual"
    note = parts[3] if len(parts) > 3 else ""

    if not title or not url:
        raise ValueError("--item must include a title and url")

    return Finding(title=title, url=url, source=source, note=note)


def _title_from_url(url: str) -> str:
    stripped = url.rstrip("/")
    if not stripped:
        raise ValueError("--item URL cannot be empty")
    return stripped.rsplit("/", maxsplit=1)[-1].replace("-", " ").replace("_", " ").title()


if __name__ == "__main__":
    raise SystemExit(main())
