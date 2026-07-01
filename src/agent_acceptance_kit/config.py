"""Configuration models for cross-layer baseline runs."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LayerConfig:
    """Connection settings for one evaluation layer."""

    name: str
    kind: str  # "agent" | "api" | "mock"
    endpoint: str = ""
    model: str = ""
    api_key_env: str = ""
    timeout_seconds: float = 30.0
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class BaselineConfig:
    """Full cross-layer baseline configuration."""

    title: str
    layer_a: LayerConfig
    layer_b: LayerConfig
    suites: tuple[str, ...] = ()
    output_dir: Path = Path("acceptance-runs")
    frozen_probe_version: str = "1.0.0"

    @property
    def agent_layer(self) -> LayerConfig:
        return self.layer_a

    @property
    def api_layer(self) -> LayerConfig:
        return self.layer_b


def _layer_from_dict(data: dict[str, Any], default_name: str) -> LayerConfig:
    return LayerConfig(
        name=str(data.get("name", default_name)),
        kind=str(data.get("kind", "mock")),
        endpoint=str(data.get("endpoint", "")),
        model=str(data.get("model", "")),
        api_key_env=str(data.get("api_key_env", "")),
        timeout_seconds=float(data.get("timeout_seconds", 30.0)),
        headers={str(k): str(v) for k, v in data.get("headers", {}).items()},
    )


def load_config(path: Path | None = None) -> BaselineConfig:
    """Load baseline config from TOML file or environment defaults."""

    config_path = path or _config_path_from_env()
    if config_path is None:
        return _default_config()

    raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    layer_a = _layer_from_dict(raw.get("layer_a", {}), "agent-endpoint")
    layer_b = _layer_from_dict(raw.get("layer_b", {}), "raw-api")
    suites = tuple(str(s) for s in raw.get("suites", ()))
    output_dir = Path(str(raw.get("output_dir", "acceptance-runs")))
    return BaselineConfig(
        title=str(raw.get("title", "Agent Acceptance Baseline")),
        layer_a=layer_a,
        layer_b=layer_b,
        suites=suites,
        output_dir=output_dir,
        frozen_probe_version=str(raw.get("frozen_probe_version", "1.0.0")),
    )


def _config_path_from_env() -> Path | None:
    env = os.environ.get("AAK_CONFIG")
    if not env:
        return None
    return Path(env)


def _default_config() -> BaselineConfig:
    return BaselineConfig(
        title="Agent Acceptance Baseline",
        layer_a=LayerConfig(name="agent-endpoint", kind="mock"),
        layer_b=LayerConfig(name="raw-api", kind="mock"),
        suites=("rag", "tool_use", "coding_agent"),
    )
