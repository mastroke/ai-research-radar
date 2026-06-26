from pathlib import Path

from ai_research_radar.cli import main


def test_once_prints_brief_from_cli_item(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(
        [
            "once",
            "--item",
            "Agent memory|https://example.com/memory|manual|Tracks durable state.",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# AI Research Radar Brief" in output
    assert "Agent memory" in output
    assert "Tracks durable state" in output


def test_once_loads_seed_items_from_config_file(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    config_path = tmp_path / "radar.toml"
    config_path.write_text(
        """
title = "Desk Radar"
watch_terms = ["memory"]

[[items]]
title = "Config seed"
url = "https://example.com/config-seed"
source = "manual"
note = "Loaded from TOML config."
""".strip(),
        encoding="utf-8",
    )

    exit_code = main(["once", "--config", str(config_path)])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# Desk Radar Brief" in output
    assert "Config seed" in output
    assert "Loaded from TOML config" in output


def test_once_writes_to_output_path(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    output_path = tmp_path / "briefs" / "today.md"

    exit_code = main(
        [
            "once",
            "--output",
            str(output_path),
            "--item",
            "Eval gates|https://example.com/eval",
        ]
    )

    assert exit_code == 0
    assert capsys.readouterr().out == ""
    assert "Eval gates" in output_path.read_text(encoding="utf-8")


def test_run_honors_limit_one(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(
        [
            "run",
            "--limit",
            "1",
            "--item",
            "Quant risk|https://example.com/risk|manual|Separates research from execution.",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert output.count("# AI Research Radar Brief") == 1
    assert "Quant risk" in output


def test_once_falls_back_when_synthesis_provider_has_no_credentials(
    monkeypatch,
    capsys,
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("RADAR_SYNTHESIS_PROVIDER", "openai")

    exit_code = main(
        [
            "once",
            "--item",
            "Memory paper|https://example.com/memory|arxiv|Cross-source note.",
            "--item",
            "Eval repo|https://example.com/eval|github|Tooling for eval loops.",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Signal" in output
    assert "## Summary" not in output
    assert "Memory paper" in output
