"""Tests for connector-related config fields."""

from pathlib import Path

import pytest

from ai_research_radar.config import load_config


def test_load_config_reads_sources_and_timeout(tmp_path: Path) -> None:
    config_path = tmp_path / "radar.toml"
    config_path.write_text(
        """
title = "Connector Radar"
watch_terms = ["memory"]
sources = ["arxiv", "github"]
connector_timeout_seconds = 5.5

[[items]]
title = "Seed"
url = "https://example.com/seed"
source = "manual"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.sources == ("arxiv", "github")
    assert config.connector_timeout_seconds == 5.5


def test_load_config_rejects_unknown_source(tmp_path: Path) -> None:
    config_path = tmp_path / "radar.toml"
    config_path.write_text(
        'sources = ["twitter"]\nwatch_terms = ["agents"]\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown source 'twitter'"):
        load_config(config_path)


def test_load_config_reads_sources_from_env(tmp_path: Path) -> None:
    config_path = tmp_path / "radar.toml"
    config_path.write_text('watch_terms = ["agents"]\n', encoding="utf-8")

    config = load_config(
        config_path,
        environ={
            "RADAR_SOURCES": "arxiv,hackernews",
            "RADAR_CONNECTOR_TIMEOUT_SECONDS": "3",
        },
    )

    assert config.sources == ("arxiv", "hackernews")
    assert config.connector_timeout_seconds == 3.0
