from pathlib import Path

import pytest

from ai_research_radar.config import load_config


def test_load_config_reads_toml_items(tmp_path: Path) -> None:
    config_path = tmp_path / "radar.toml"
    config_path.write_text(
        """
title = "Desk Radar"
topic = "agent systems"
watch_terms = ["memory", "eval"]
output_path = "briefs/today.md"
interval_seconds = 60
max_items = 3

[[items]]
title = "Memory agents"
url = "https://example.com/memory"
source = "manual"
note = "Useful for durable state."
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path, environ={})

    assert config.title == "Desk Radar"
    assert config.watch_terms == ("memory", "eval")
    assert config.output_path == Path("briefs/today.md")
    assert config.interval_seconds == 60
    assert config.max_items == 3
    assert config.items[0].title == "Memory agents"


def test_load_config_applies_environment_overrides(tmp_path: Path) -> None:
    config_path = tmp_path / "radar.toml"
    config_path.write_text('watch_terms = ["memory"]', encoding="utf-8")

    config = load_config(
        config_path,
        environ={
            "RADAR_TITLE": "Morning Desk",
            "RADAR_TOPIC": "quant agents",
            "RADAR_WATCH_TERMS": "risk, backtest",
            "RADAR_OUTPUT_PATH": "out.md",
            "RADAR_INTERVAL_SECONDS": "120",
            "RADAR_MAX_ITEMS": "2",
        },
    )

    assert config.title == "Morning Desk"
    assert config.topic == "quant agents"
    assert config.watch_terms == ("risk", "backtest")
    assert config.output_path == Path("out.md")
    assert config.interval_seconds == 120
    assert config.max_items == 2


def test_load_config_resolves_radar_config_env(tmp_path: Path) -> None:
    config_path = tmp_path / "nested" / "radar.toml"
    config_path.parent.mkdir()
    config_path.write_text(
        'title = "Env Path Radar"\n[[items]]\ntitle = "Seed"\nurl = "https://example.com/seed"',
        encoding="utf-8",
    )

    config = load_config(
        environ={"RADAR_CONFIG": str(config_path)},
    )

    assert config.title == "Env Path Radar"
    assert config.items[0].title == "Seed"


def test_load_config_rejects_invalid_interval(tmp_path: Path) -> None:
    config_path = tmp_path / "radar.toml"
    config_path.write_text("interval_seconds = 0", encoding="utf-8")

    with pytest.raises(ValueError, match="interval_seconds"):
        load_config(config_path, environ={})


def test_load_config_reads_synthesis_table(tmp_path: Path) -> None:
    config_path = tmp_path / "radar.toml"
    config_path.write_text(
        """
[synthesis]
provider = "openai"
model = "gpt-4o-mini"
timeout_seconds = 45
min_source_families = 2
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path, environ={})

    assert config.synthesis_provider == "openai"
    assert config.synthesis_model == "gpt-4o-mini"
    assert config.synthesis_timeout_seconds == 45.0
    assert config.synthesis_min_source_families == 2


def test_load_config_applies_synthesis_environment_overrides(tmp_path: Path) -> None:
    config_path = tmp_path / "radar.toml"
    config_path.write_text("", encoding="utf-8")

    config = load_config(
        config_path,
        environ={
            "RADAR_SYNTHESIS_PROVIDER": "anthropic",
            "RADAR_SYNTHESIS_MODEL": "claude-3-5-haiku-latest",
            "RADAR_SYNTHESIS_TIMEOUT_SECONDS": "60",
            "RADAR_SYNTHESIS_MIN_SOURCE_FAMILIES": "3",
        },
    )

    assert config.synthesis_provider == "anthropic"
    assert config.synthesis_model == "claude-3-5-haiku-latest"
    assert config.synthesis_timeout_seconds == 60.0
    assert config.synthesis_min_source_families == 3


def test_load_config_rejects_unknown_synthesis_provider(tmp_path: Path) -> None:
    config_path = tmp_path / "radar.toml"
    config_path.write_text('[synthesis]\nprovider = "unknown"', encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown synthesis provider"):
        load_config(config_path, environ={})
