from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from agent_handoff.cli import main


def test_cli_baseline_run_sample_config(tmp_path: Path) -> None:
    output = tmp_path / "results.json"
    code = main(
        [
            "baseline",
            "run",
            "--config",
            "scenarios/support-agent/scenarios.yaml",
            "--output",
            str(output),
        ]
    )
    assert code == 0
    assert output.exists()


def test_cli_report_generate(tmp_path: Path) -> None:
    results = tmp_path / "results.json"
    report = tmp_path / "report.md"
    assert (
        main(
            [
                "baseline",
                "run",
                "--config",
                "scenarios/support-agent/scenarios.yaml",
                "--output",
                str(results),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "report",
                "generate",
                "--results",
                str(results),
                "--output",
                str(report),
                "--client-name",
                "Test Client",
            ]
        )
        == 0
    )
    text = report.read_text(encoding="utf-8")
    assert "Test Client" in text


def test_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "agent_handoff.cli", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "agent-handoff" in result.stdout


def test_entry_point_help() -> None:
    script = Path.home() / ".local" / "bin" / "agent-handoff"
    if not script.exists():
        pytest.skip("console script not installed on PATH")
    result = subprocess.run(
        [str(script), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "baseline" in result.stdout
