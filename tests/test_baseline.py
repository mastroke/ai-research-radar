"""Integration tests for baseline runs."""

from __future__ import annotations

from pathlib import Path

from agent_acceptance_kit.attribution import AttributionClass
from agent_acceptance_kit.baseline import load_baseline_result, run_baseline, save_baseline_result
from agent_acceptance_kit.config import load_config
from agent_acceptance_kit.report.markdown import render_markdown_report
from agent_acceptance_kit.report.pdf import render_pdf_report


def test_mock_baseline_run(tmp_path: Path) -> None:
    config = load_config(Path("examples/baseline-mock.toml"))
    result = run_baseline(config)
    assert result.verdict.total_probes == 9
    assert result.verdict.classification in (
        AttributionClass.AGENT_VALUE_ADD,
        AttributionClass.PARTIAL_AGENT,
        AttributionClass.BASELINE_MET,
    )
    assert len(result.suites) == 3

    out = tmp_path / "result.json"
    save_baseline_result(result, out)
    data = load_baseline_result(out)
    assert data["verdict"]["total_probes"] == 9


def test_markdown_report_contains_verdict(tmp_path: Path) -> None:
    config = load_config(Path("examples/baseline-mock.toml"))
    result = run_baseline(config)
    md = render_markdown_report(result.to_dict())
    assert "Overall verdict" in md
    assert result.verdict.classification.value in md


def test_pdf_report_smoke(tmp_path: Path) -> None:
    config = load_config(Path("examples/baseline-mock.toml"))
    result = run_baseline(config)
    pdf_path = tmp_path / "report.pdf"
    render_pdf_report(result.to_dict(), pdf_path)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 100
