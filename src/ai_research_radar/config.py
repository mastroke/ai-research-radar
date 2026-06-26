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
from ai_research_radar.schedule import ScheduleSettings, parse_schedule_settings
from ai_research_radar.synthesis.registry import PROVIDER_NAMES

DEFAULT_TOPIC = "agentic AI research"
DEFAULT_WATCH_TERMS = ("agents", "memory", "evaluation", "MLOps", "quant")
DEFAULT_CONNECTOR_TIMEOUT_SECONDS = 10.0
DEFAULT_SYNTHESIS_TIMEOUT_SECONDS = 30.0
DEFAULT_MIN_SOURCE_FAMILIES = 2
DEFAULT_TELEGRAM_TIMEOUT_SECONDS = 30.0


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
    memory_path: Path | None = None
    synthesis_provider: str | None = None
    synthesis_model: str | None = None
    synthesis_timeout_seconds: float = DEFAULT_SYNTHESIS_TIMEOUT_SECONDS
    synthesis_min_source_families: int = DEFAULT_MIN_SOURCE_FAMILIES
    telegram_chat_id: int | None = None
    telegram_timeout_seconds: float = DEFAULT_TELEGRAM_TIMEOUT_SECONDS
    schedule: ScheduleSettings = ScheduleSettings()


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
    memory_path = _optional_path(raw.get("memory_path"))
    synthesis = raw.get("synthesis", {})
    if synthesis == "" or synthesis is None:
        synthesis_raw: dict[str, Any] = {}
    elif not isinstance(synthesis, dict):
        raise ValueError("synthesis must be a TOML table")
    else:
        synthesis_raw = synthesis
    synthesis_provider = _optional_string(synthesis_raw.get("provider"))
    synthesis_model = _optional_string(synthesis_raw.get("model"))
    synthesis_timeout_seconds = float(
        synthesis_raw.get("timeout_seconds", DEFAULT_SYNTHESIS_TIMEOUT_SECONDS)
    )
    synthesis_min_source_families = int(
        synthesis_raw.get("min_source_families", DEFAULT_MIN_SOURCE_FAMILIES)
    )
    telegram = raw.get("telegram", {})
    if telegram == "" or telegram is None:
        telegram_raw: dict[str, Any] = {}
    elif not isinstance(telegram, dict):
        raise ValueError("telegram must be a TOML table")
    else:
        telegram_raw = telegram
    telegram_chat_id = _optional_int(telegram_raw.get("chat_id"))
    telegram_timeout_seconds = float(
        telegram_raw.get("timeout_seconds", DEFAULT_TELEGRAM_TIMEOUT_SECONDS)
    )
    schedule = raw.get("schedule", {})
    if schedule == "" or schedule is None:
        schedule_raw: dict[str, Any] = {}
    elif not isinstance(schedule, dict):
        raise ValueError("schedule must be a TOML table")
    else:
        schedule_raw = schedule
    schedule_settings = parse_schedule_settings(
        _optional_string(schedule_raw.get("preset")),
        at=_optional_string(schedule_raw.get("at")),
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
    if "RADAR_MEMORY_PATH" in env:
        memory_path = Path(env["RADAR_MEMORY_PATH"])
    if "RADAR_SYNTHESIS_PROVIDER" in env:
        synthesis_provider = _optional_string(env["RADAR_SYNTHESIS_PROVIDER"])
    if "RADAR_SYNTHESIS_MODEL" in env:
        synthesis_model = _optional_string(env["RADAR_SYNTHESIS_MODEL"])
    if "RADAR_SYNTHESIS_TIMEOUT_SECONDS" in env:
        synthesis_timeout_seconds = float(env["RADAR_SYNTHESIS_TIMEOUT_SECONDS"])
    if "RADAR_SYNTHESIS_MIN_SOURCE_FAMILIES" in env:
        synthesis_min_source_families = int(env["RADAR_SYNTHESIS_MIN_SOURCE_FAMILIES"])
    if "RADAR_TELEGRAM_CHAT_ID" in env:
        telegram_chat_id = int(env["RADAR_TELEGRAM_CHAT_ID"])
    if "RADAR_TELEGRAM_TIMEOUT_SECONDS" in env:
        telegram_timeout_seconds = float(env["RADAR_TELEGRAM_TIMEOUT_SECONDS"])
    if "RADAR_SCHEDULE_PRESET" in env:
        schedule_settings = parse_schedule_settings(
            env["RADAR_SCHEDULE_PRESET"],
            at=schedule_settings.at,
        )
    if "RADAR_SCHEDULE_AT" in env:
        schedule_settings = parse_schedule_settings(
            schedule_settings.preset,
            at=env["RADAR_SCHEDULE_AT"],
        )

    if not watch_terms:
        watch_terms = (topic,)
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    if max_items <= 0:
        raise ValueError("max_items must be positive")
    if connector_timeout_seconds <= 0:
        raise ValueError("connector_timeout_seconds must be positive")
    if synthesis_timeout_seconds <= 0:
        raise ValueError("synthesis_timeout_seconds must be positive")
    if synthesis_min_source_families <= 0:
        raise ValueError("synthesis_min_source_families must be positive")
    if telegram_timeout_seconds <= 0:
        raise ValueError("telegram_timeout_seconds must be positive")
    _validate_sources(sources)
    _validate_synthesis_provider(synthesis_provider)

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
        memory_path=memory_path,
        synthesis_provider=synthesis_provider,
        synthesis_model=synthesis_model,
        synthesis_timeout_seconds=synthesis_timeout_seconds,
        synthesis_min_source_families=synthesis_min_source_families,
        telegram_chat_id=telegram_chat_id,
        telegram_timeout_seconds=telegram_timeout_seconds,
        schedule=schedule_settings,
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


def _optional_string(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value).strip().lower() or None


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


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


def _validate_synthesis_provider(provider: str | None) -> None:
    if provider is None:
        return
    if provider not in PROVIDER_NAMES:
        allowed = ", ".join(PROVIDER_NAMES)
        raise ValueError(
            f"Unknown synthesis provider {provider!r}. Expected one of: {allowed}"
        )
