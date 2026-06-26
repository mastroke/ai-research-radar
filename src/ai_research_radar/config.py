"""Configuration loading for AI Research Radar."""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_research_radar.brief import Finding
from ai_research_radar.connectors import CONNECTOR_NAMES

DEFAULT_TOPIC = "agentic AI research"
DEFAULT_WATCH_TERMS = ("agents", "memory", "evaluation", "MLOps", "quant")
DEFAULT_CONNECTOR_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class RadarConfig:
    """Runtime settings for a local Radar run."""

    title: str = "AI Research Radar"
    topic: str = DEFAULT_TOPIC
    watch_terms: tuple[str, ...] = DEFAULT_WATCH_TERMS
    items: tuple[Finding, ...] = ()
    sources: tuple[str, ...] = ()
    output_path: Path | None = None
    interval_seconds: int = 86_400
    max_items: int = 5
    connector_timeout_seconds: float = DEFAULT_CONNECTOR_TIMEOUT_SECONDS


def load_config(
    path: str | Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> RadarConfig:
    """Load config from a TOML file and environment overrides."""

    env = environ or os.environ
    config_path = Path(path or env.get("RADAR_CONFIG", "")) if path or env.get("RADAR_CONFIG") else None
    raw = _read_toml(config_path) if config_path else {}

    title = str(raw.get("title", "AI Research Radar"))
    topic = str(raw.get("topic", DEFAULT_TOPIC))
    watch_terms = _as_string_tuple(raw.get("watch_terms", DEFAULT_WATCH_TERMS))
    output_path = _optional_path(raw.get("output_path"))
    interval_seconds = int(raw.get("interval_seconds", 86_400))
    max_items = int(raw.get("max_items", 5))
    items = tuple(_finding_from_raw(item) for item in raw.get("items", []))
    sources = _as_source_tuple(raw.get("sources", ()))
    connector_timeout_seconds = float(
        raw.get("connector_timeout_seconds", DEFAULT_CONNECTOR_TIMEOUT_SECONDS)
    )

    if "RADAR_TITLE" in env:
        title = env["RADAR_TITLE"]
    if "RADAR_TOPIC" in env:
        topic = env["RADAR_TOPIC"]
    if "RADAR_WATCH_TERMS" in env:
        watch_terms = _split_env_list(env["RADAR_WATCH_TERMS"])
    if "RADAR_OUTPUT_PATH" in env:
        output_path = Path(env["RADAR_OUTPUT_PATH"])
    if "RADAR_INTERVAL_SECONDS" in env:
        interval_seconds = int(env["RADAR_INTERVAL_SECONDS"])
    if "RADAR_MAX_ITEMS" in env:
        max_items = int(env["RADAR_MAX_ITEMS"])
    if "RADAR_SOURCES" in env:
        sources = _split_env_list(env["RADAR_SOURCES"])
    if "RADAR_CONNECTOR_TIMEOUT_SECONDS" in env:
        connector_timeout_seconds = float(env["RADAR_CONNECTOR_TIMEOUT_SECONDS"])

    if not watch_terms:
        watch_terms = (topic,)
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    if max_items <= 0:
        raise ValueError("max_items must be positive")
    if connector_timeout_seconds <= 0:
        raise ValueError("connector_timeout_seconds must be positive")
    _validate_sources(sources)

    return RadarConfig(
        title=title,
        topic=topic,
        watch_terms=watch_terms,
        items=items,
        sources=sources,
        output_path=output_path,
        interval_seconds=interval_seconds,
        max_items=max_items,
        connector_timeout_seconds=connector_timeout_seconds,
    )


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("rb") as config_file:
        data = tomllib.load(config_file)
    if not isinstance(data, dict):
        raise ValueError("Config file must contain a TOML table")
    return data


def _finding_from_raw(raw: Any) -> Finding:
    if not isinstance(raw, dict):
        raise ValueError("Each item must be a TOML table")

    title = str(raw.get("title", "")).strip()
    url = str(raw.get("url", "")).strip()
    source = str(raw.get("source", "manual")).strip() or "manual"
    note = str(raw.get("note", "")).strip()

    if not title:
        raise ValueError("Each item must include a title")
    if not url:
        raise ValueError("Each item must include a url")

    return Finding(title=title, url=url, source=source, note=note)


def _as_string_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return _split_env_list(value)
    if not isinstance(value, list | tuple):
        raise ValueError("watch_terms must be a list of strings")
    return tuple(str(item).strip() for item in value if str(item).strip())


def _split_env_list(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _optional_path(value: Any) -> Path | None:
    if value in (None, ""):
        return None
    return Path(str(value))


def _as_source_tuple(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        return _split_env_list(value)
    if not isinstance(value, list | tuple):
        raise ValueError("sources must be a list of connector names")
    return tuple(str(item).strip().lower() for item in value if str(item).strip())


def _validate_sources(sources: tuple[str, ...]) -> None:
    for source in sources:
        if source not in CONNECTOR_NAMES:
            allowed = ", ".join(CONNECTOR_NAMES)
            raise ValueError(f"Unknown source {source!r}. Expected one of: {allowed}")
