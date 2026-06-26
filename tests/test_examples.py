"""Validate bundled example configs and brief fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_research_radar.config import load_config

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_CONFIGS = (
    REPO_ROOT / "examples" / "radar.toml",
    REPO_ROOT / "examples" / "configs" / "minimal.toml",
    REPO_ROOT / "examples" / "configs" / "connectors.toml",
)
EXAMPLE_BRIEFS = (
    REPO_ROOT / "examples" / "briefs" / "deterministic-sample.md",
    REPO_ROOT / "examples" / "briefs" / "multi-source-sample.md",
)


@pytest.mark.parametrize("config_path", EXAMPLE_CONFIGS, ids=lambda p: p.name)
def test_example_configs_load(config_path: Path) -> None:
    config = load_config(config_path, environ={})
    assert config.title
    assert config.watch_terms


@pytest.mark.parametrize("brief_path", EXAMPLE_BRIEFS, ids=lambda p: p.name)
def test_example_briefs_have_signal_section(brief_path: Path) -> None:
    text = brief_path.read_text(encoding="utf-8")
    assert "## Signal" in text
    assert "## Watch Terms" in text
