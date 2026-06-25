"""Deterministic briefing primitives for the first Radar CLI milestone."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from textwrap import shorten


@dataclass(frozen=True)
class Finding:
    """A research item that can be included in a Radar brief."""

    title: str
    url: str
    source: str = "manual"
    note: str = ""

    @property
    def searchable_text(self) -> str:
        return f"{self.title} {self.note} {self.source}".lower()


@dataclass(frozen=True)
class Brief:
    """Rendered daily brief plus metadata useful to future delivery adapters."""

    title: str
    generated_at: datetime
    items: tuple[Finding, ...]
    watch_terms: tuple[str, ...]
    markdown: str


def compile_brief(
    findings: list[Finding],
    *,
    watch_terms: list[str],
    title: str = "AI Research Radar",
    generated_at: datetime | None = None,
    max_items: int = 5,
) -> Brief:
    """Rank configured findings and render a concise markdown brief."""

    timestamp = generated_at or datetime.now(UTC)
    ranked_items = _rank_findings(findings, watch_terms)[:max_items]
    markdown = _render_markdown(title, timestamp, ranked_items, watch_terms)

    return Brief(
        title=title,
        generated_at=timestamp,
        items=tuple(ranked_items),
        watch_terms=tuple(watch_terms),
        markdown=markdown,
    )


def _rank_findings(findings: list[Finding], watch_terms: list[str]) -> list[Finding]:
    terms = [term.lower() for term in watch_terms if term.strip()]

    def score(finding: Finding) -> tuple[int, str]:
        relevance = sum(term in finding.searchable_text for term in terms)
        return (-relevance, finding.title.lower())

    return sorted(findings, key=score)


def _render_markdown(
    title: str,
    generated_at: datetime,
    findings: list[Finding],
    watch_terms: list[str],
) -> str:
    date_label = generated_at.astimezone(UTC).strftime("%Y-%m-%d")
    lines = [
        f"# {title} Brief",
        "",
        f"Generated: {date_label} UTC",
        "",
        "## Signal",
    ]

    if not findings:
        lines.extend(
            [
                "",
                "No seed items were configured. Add `[[items]]` entries to the config "
                "file or pass `--item` URLs to start a radar run.",
            ]
        )
    else:
        for index, finding in enumerate(findings, start=1):
            note = shorten(finding.note, width=140, placeholder="...") if finding.note else ""
            source = f" ({finding.source})" if finding.source else ""
            lines.extend(
                [
                    "",
                    f"{index}. [{finding.title}]({finding.url}){source}",
                ]
            )
            if note:
                lines.append(f"   - Why it matters: {note}")

    lines.extend(["", "## Watch Terms"])
    if watch_terms:
        lines.append(", ".join(watch_terms))
    else:
        lines.append("No watch terms configured.")

    return "\n".join(lines).rstrip() + "\n"
