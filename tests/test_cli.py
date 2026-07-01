"""CLI smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

from agent_acceptance_kit.cli import main


def test_cli_suites_list(capsys) -> None:
    assert main(["suites", "list"]) == 0
    out = capsys.readouterr().out
    assert "rag" in out
    assert "tool_use" in out


def test_cli_baseline_run(tmp_path: Path, capsys) -> None:
    out_json = tmp_path / "baseline-result.json"
    report_md = tmp_path / "report.md"
    rc = main(
        [
            "baseline",
            "run",
            "--config",
            "examples/baseline-mock.toml",
            "--output",
            str(out_json),
            "--report-md",
            str(report_md),
        ]
    )
    assert rc == 0
    assert out_json.exists()
    assert report_md.exists()
    payload = json.loads(capsys.readouterr().out)
    assert "verdict" in payload
