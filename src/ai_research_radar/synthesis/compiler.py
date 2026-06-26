"""Cross-source brief synthesis with deterministic fallback."""

from __future__ import annotations

from datetime import datetime

from ai_research_radar.brief import Finding, compile_brief
from ai_research_radar.synthesis.base import SynthesisProvider
from ai_research_radar.synthesis.structured import (
    StructuredBrief,
    brief_to_structured,
    source_families,
)

DEFAULT_MIN_SOURCE_FAMILIES = 2


def synthesize_brief(
    findings: list[Finding],
    *,
    watch_terms: list[str],
    title: str = "AI Research Radar",
    topic: str = "agentic AI research",
    provider: SynthesisProvider | None = None,
    generated_at: datetime | None = None,
    max_items: int = 5,
    min_source_families: int = DEFAULT_MIN_SOURCE_FAMILIES,
    no_signal_message: str | None = None,
) -> StructuredBrief:
    """Compile a structured brief, using LLM synthesis when eligible."""

    deterministic = compile_brief(
        findings,
        watch_terms=watch_terms,
        title=title,
        generated_at=generated_at,
        max_items=max_items,
        no_signal_message=no_signal_message,
    )
    ranked = list(deterministic.items)
    families = source_families(ranked)

    if provider is None or len(families) < min_source_families:
        return brief_to_structured(deterministic, synthesized=False)

    synthesized = provider.synthesize(
        ranked,
        title=title,
        topic=topic,
        watch_terms=tuple(watch_terms),
        max_items=max_items,
    )
    if synthesized is None:
        return brief_to_structured(deterministic, synthesized=False)

    if generated_at is not None:
        return StructuredBrief(
            title=synthesized.title,
            generated_at=generated_at,
            summary=synthesized.summary,
            themes=synthesized.themes,
            items=synthesized.items,
            watch_terms=synthesized.watch_terms,
            source_families=synthesized.source_families,
            markdown=_replace_generated_at(synthesized.markdown, generated_at),
            synthesized=True,
        )
    return synthesized


def _replace_generated_at(markdown: str, generated_at: datetime) -> str:
    from datetime import UTC

    date_label = generated_at.astimezone(UTC).strftime("%Y-%m-%d")
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("Generated:"):
            lines[index] = f"Generated: {date_label} UTC"
            break
    return "\n".join(lines).rstrip() + "\n"
