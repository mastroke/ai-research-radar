"""Structured brief types and markdown rendering."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from textwrap import shorten

from ai_research_radar.brief import Brief, Finding, compile_brief


@dataclass(frozen=True)
class SynthesizedItem:
    """One ranked item with model-generated synthesis text."""

    title: str
    url: str
    source: str
    synthesis: str


@dataclass(frozen=True)
class StructuredBrief:
    """Cross-source brief with optional LLM synthesis metadata."""

    title: str
    generated_at: datetime
    summary: str
    themes: tuple[str, ...]
    items: tuple[SynthesizedItem, ...]
    watch_terms: tuple[str, ...]
    source_families: tuple[str, ...]
    markdown: str
    synthesized: bool


def source_families(findings: list[Finding]) -> tuple[str, ...]:
    """Return distinct normalized source labels from findings."""

    families = {finding.source.strip().lower() for finding in findings if finding.source.strip()}
    return tuple(sorted(families))


def fallback_structured_brief(
    findings: list[Finding],
    *,
    watch_terms: list[str],
    title: str = "AI Research Radar",
    generated_at: datetime | None = None,
    max_items: int = 5,
    no_signal_message: str | None = None,
) -> StructuredBrief:
    """Compile a deterministic brief wrapped as StructuredBrief."""

    timestamp = generated_at or datetime.now(UTC)
    brief = compile_brief(
        findings,
        watch_terms=watch_terms,
        title=title,
        generated_at=timestamp,
        max_items=max_items,
        no_signal_message=no_signal_message,
    )
    return brief_to_structured(brief, synthesized=False)


def brief_to_structured(brief: Brief, *, synthesized: bool) -> StructuredBrief:
    """Wrap a deterministic Brief as StructuredBrief."""

    items = tuple(
        SynthesizedItem(
            title=finding.title,
            url=finding.url,
            source=finding.source,
            synthesis=finding.note,
        )
        for finding in brief.items
    )
    return StructuredBrief(
        title=brief.title,
        generated_at=brief.generated_at,
        summary=_deterministic_summary(brief.items),
        themes=(),
        items=items,
        watch_terms=brief.watch_terms,
        source_families=source_families(list(brief.items)),
        markdown=brief.markdown,
        synthesized=synthesized,
    )


def parse_model_payload(
    raw: str,
    *,
    findings: list[Finding],
    title: str,
    watch_terms: tuple[str, ...],
    max_items: int,
    generated_at: datetime | None = None,
) -> StructuredBrief:
    """Parse provider JSON into a structured brief."""

    payload = _extract_json_object(raw)
    summary = str(payload.get("summary", "")).strip()
    themes = _as_string_tuple(payload.get("themes", ()))
    items = _parse_items(payload.get("items", []), findings=findings, max_items=max_items)
    if not summary:
        raise ValueError("Model payload must include a non-empty summary")
    if not items:
        raise ValueError("Model payload must include at least one item")

    timestamp = generated_at or datetime.now(UTC)
    families = source_families([_item_to_finding(item) for item in items])
    markdown = _render_synthesized_markdown(
        title,
        timestamp,
        summary,
        themes,
        items,
        watch_terms,
    )
    return StructuredBrief(
        title=title,
        generated_at=timestamp,
        summary=summary,
        themes=themes,
        items=items,
        watch_terms=watch_terms,
        source_families=families,
        markdown=markdown,
        synthesized=True,
    )


def _deterministic_summary(items: tuple[Finding, ...]) -> str:
    if not items:
        return "No new signal matched the configured watch terms."
    sources = ", ".join(source_families(list(items)))
    return f"Ranked {len(items)} item(s) across {sources} using deterministic scoring."


def _extract_json_object(raw: str) -> dict[str, object]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Model payload must be a JSON object")
    return parsed


def _as_string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if not isinstance(value, list | tuple):
        raise ValueError("themes must be a list of strings")
    return tuple(str(item).strip() for item in value if str(item).strip())


def _parse_items(
    value: object,
    *,
    findings: list[Finding],
    max_items: int,
) -> tuple[SynthesizedItem, ...]:
    if not isinstance(value, list):
        raise ValueError("items must be a list")

    known_urls = {finding.url.strip().lower(): finding for finding in findings}
    parsed: list[SynthesizedItem] = []
    for entry in value[:max_items]:
        if not isinstance(entry, dict):
            raise ValueError("Each item must be an object")
        title = str(entry.get("title", "")).strip()
        url = str(entry.get("url", "")).strip()
        source = str(entry.get("source", "")).strip()
        synthesis = str(entry.get("synthesis", "")).strip()
        if not title or not url or not synthesis:
            raise ValueError("Each item must include title, url, and synthesis")

        known = known_urls.get(url.lower())
        if known is not None:
            title = known.title
            if not source:
                source = known.source

        parsed.append(
            SynthesizedItem(
                title=title,
                url=url,
                source=source or "unknown",
                synthesis=synthesis,
            )
        )
    return tuple(parsed)


def _item_to_finding(item: SynthesizedItem) -> Finding:
    return Finding(title=item.title, url=item.url, source=item.source, note=item.synthesis)


def _render_synthesized_markdown(
    title: str,
    generated_at: datetime,
    summary: str,
    themes: tuple[str, ...],
    items: tuple[SynthesizedItem, ...],
    watch_terms: tuple[str, ...],
) -> str:
    date_label = generated_at.astimezone(UTC).strftime("%Y-%m-%d")
    lines = [
        f"# {title} Brief",
        "",
        f"Generated: {date_label} UTC",
        "",
        "## Summary",
        "",
        summary,
        "",
        "## Signal",
    ]

    for index, item in enumerate(items, start=1):
        source = f" ({item.source})" if item.source else ""
        note = shorten(item.synthesis, width=200, placeholder="...")
        lines.extend(
            [
                "",
                f"{index}. [{item.title}]({item.url}){source}",
                f"   - Why it matters: {note}",
            ]
        )

    if themes:
        lines.extend(["", "## Themes"])
        for theme in themes:
            lines.append(f"- {theme}")

    lines.extend(["", "## Watch Terms"])
    if watch_terms:
        lines.append(", ".join(watch_terms))
    else:
        lines.append("No watch terms configured.")

    return "\n".join(lines).rstrip() + "\n"
