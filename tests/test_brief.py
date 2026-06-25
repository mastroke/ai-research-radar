from datetime import UTC, datetime

from ai_research_radar import Finding, compile_brief


def test_compile_brief_ranks_matching_watch_terms_first() -> None:
    findings = [
        Finding(
            title="Generic model release",
            url="https://example.com/model",
            source="github",
        ),
        Finding(
            title="Agent memory evaluation",
            url="https://example.com/memory",
            source="arxiv",
            note="Connects memory design to regression checks.",
        ),
    ]

    brief = compile_brief(
        findings,
        watch_terms=["memory", "evaluation"],
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )

    assert brief.items[0].title == "Agent memory evaluation"
    assert "Generated: 2026-06-25 UTC" in brief.markdown
    assert "Why it matters: Connects memory design" in brief.markdown


def test_compile_brief_handles_empty_seed_items() -> None:
    brief = compile_brief([], watch_terms=["agents"])

    assert brief.items == ()
    assert "No seed items were configured" in brief.markdown
    assert "agents" in brief.markdown
