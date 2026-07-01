"""PDF acceptance report generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_acceptance_kit.report.markdown import render_markdown_report


def render_pdf_report(data: dict[str, Any], output_path: Path) -> None:
    try:
        from fpdf import FPDF
    except ImportError as exc:
        msg = "PDF output requires the pdf extra: pip install agent-acceptance-kit[pdf]"
        raise RuntimeError(msg) from exc

    markdown = render_markdown_report(data)
    plain = _markdown_to_plain(markdown)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    effective_width = pdf.w - pdf.l_margin - pdf.r_margin

    for line in plain.splitlines():
        safe = _latin1_safe(line)
        for chunk in _wrap_line(safe, width=96):
            pdf.multi_cell(effective_width, 5, chunk)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))


def _wrap_line(line: str, width: int) -> list[str]:
    if len(line) <= width:
        return [line or " "]
    chunks: list[str] = []
    start = 0
    while start < len(line):
        chunks.append(line[start : start + width])
        start += width
    return chunks or [" "]


def _latin1_safe(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _markdown_to_plain(text: str) -> str:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw
        for token in ("**", "`", "_"):
            line = line.replace(token, "")
        if line.startswith("# "):
            lines.append(line[2:].upper())
            lines.append("=" * min(72, len(line) - 2))
        elif line.startswith("## "):
            lines.append("")
            lines.append(line[3:])
            lines.append("-" * min(72, len(line) - 3))
        elif line.startswith("|"):
            lines.append(line.replace("|", " | "))
        else:
            lines.append(line)
    return "\n".join(lines)
