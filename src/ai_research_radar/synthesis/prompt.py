"""Prompt construction for cross-source brief synthesis."""

from __future__ import annotations

import json

from ai_research_radar.brief import Finding


def build_synthesis_prompt(
    findings: list[Finding],
    *,
    title: str,
    topic: str,
    watch_terms: tuple[str, ...],
    max_items: int,
) -> str:
    """Build a provider-agnostic instruction prompt for structured brief output."""

    payload = [
        {
            "title": finding.title,
            "url": finding.url,
            "source": finding.source,
            "note": finding.note,
        }
        for finding in findings[: max_items * 2]
    ]
    terms = ", ".join(watch_terms) if watch_terms else topic
    return (
        f"You are compiling the research brief titled {title!r} on topic {topic!r}.\n"
        f"Watch terms: {terms}.\n"
        "Synthesize findings from multiple source families into one concise brief.\n"
        "Return ONLY valid JSON with this shape:\n"
        '{"summary": "...", "themes": ["..."], "items": ['
        '{"title": "...", "url": "...", "source": "...", "synthesis": "..."}]}'
        "\nRules:\n"
        f"- Include at most {max_items} items, ranked by relevance.\n"
        "- summary must connect patterns across sources in 2-4 sentences.\n"
        "- themes are short cross-cutting labels (0-4 entries).\n"
        "- synthesis explains why each item matters relative to the watch terms.\n"
        "- Use only URLs from the input findings.\n"
        f"Findings JSON:\n{json.dumps(payload, indent=2)}"
    )
