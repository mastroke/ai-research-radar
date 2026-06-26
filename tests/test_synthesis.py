"""Tests for model-agnostic synthesis backends."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from ai_research_radar.brief import Finding
from ai_research_radar.synthesis import (
    StructuredBrief,
    get_provider,
    source_families,
    synthesize_brief,
)
from ai_research_radar.synthesis.providers.openai import OpenAIProvider
from ai_research_radar.synthesis.structured import parse_model_payload


def _model_payload() -> str:
    return json.dumps(
        {
            "summary": "Memory and evaluation themes connect arXiv papers to GitHub tooling.",
            "themes": ["agent memory", "eval gates"],
            "items": [
                {
                    "title": "Agent memory evaluation",
                    "url": "https://example.com/memory",
                    "source": "arxiv",
                    "synthesis": "Links memory design to regression checks.",
                },
                {
                    "title": "Eval harness toolkit",
                    "url": "https://example.com/eval",
                    "source": "github",
                    "synthesis": "Operationalizes evaluation loops for agents.",
                },
            ],
        }
    )


def _openai_response(content: str) -> dict[str, object]:
    return {"choices": [{"message": {"content": content}}]}


def test_source_families_counts_distinct_connectors() -> None:
    findings = [
        Finding(title="A", url="https://example.com/a", source="arxiv"),
        Finding(title="B", url="https://example.com/b", source="github"),
        Finding(title="C", url="https://example.com/c", source="arxiv"),
    ]

    assert source_families(findings) == ("arxiv", "github")


def test_synthesize_brief_falls_back_without_provider() -> None:
    findings = [
        Finding(title="Paper", url="https://example.com/paper", source="arxiv"),
        Finding(title="Repo", url="https://example.com/repo", source="github"),
    ]

    brief = synthesize_brief(
        findings,
        watch_terms=["memory"],
        generated_at=datetime(2026, 6, 26, tzinfo=UTC),
    )

    assert isinstance(brief, StructuredBrief)
    assert brief.synthesized is False
    assert "## Signal" in brief.markdown
    assert "Generated: 2026-06-26 UTC" in brief.markdown


def test_synthesize_brief_falls_back_with_single_source_family() -> None:
    provider = OpenAIProvider(
        api_key="test-key",
        model="gpt-4o-mini",
        post_json=lambda *args, **kwargs: _openai_response(_model_payload()),
    )
    findings = [
        Finding(title="Paper A", url="https://example.com/a", source="arxiv"),
        Finding(title="Paper B", url="https://example.com/b", source="arxiv"),
    ]

    brief = synthesize_brief(
        findings,
        watch_terms=["memory"],
        provider=provider,
    )

    assert brief.synthesized is False
    assert "## Summary" not in brief.markdown


def test_synthesize_brief_uses_provider_for_multi_source_findings() -> None:
    calls: list[dict[str, object]] = []

    def fake_post_json(url: str, *, payload, headers, timeout: float) -> dict[str, object]:
        calls.append({"url": url, "payload": payload, "headers": headers, "timeout": timeout})
        return _openai_response(_model_payload())

    provider = OpenAIProvider(
        api_key="test-key",
        model="gpt-4o-mini",
        post_json=fake_post_json,
    )
    findings = [
        Finding(
            title="Agent memory evaluation",
            url="https://example.com/memory",
            source="arxiv",
            note="arxiv note",
        ),
        Finding(
            title="Eval harness toolkit",
            url="https://example.com/eval",
            source="github",
            note="github note",
        ),
    ]

    brief = synthesize_brief(
        findings,
        watch_terms=["memory", "evaluation"],
        provider=provider,
        generated_at=datetime(2026, 6, 26, tzinfo=UTC),
    )

    assert brief.synthesized is True
    assert brief.summary.startswith("Memory and evaluation")
    assert brief.themes == ("agent memory", "eval gates")
    assert len(brief.items) == 2
    assert "## Summary" in brief.markdown
    assert "Why it matters: Links memory design" in brief.markdown
    assert calls
    assert calls[0]["url"] == "https://api.openai.com/v1/chat/completions"


def test_synthesize_brief_falls_back_when_provider_errors() -> None:
    def failing_post_json(*args, **kwargs) -> dict[str, object]:
        raise TimeoutError("upstream timeout")

    provider = OpenAIProvider(
        api_key="test-key",
        model="gpt-4o-mini",
        post_json=failing_post_json,
    )
    findings = [
        Finding(title="Paper", url="https://example.com/paper", source="arxiv"),
        Finding(title="Repo", url="https://example.com/repo", source="github"),
    ]

    brief = synthesize_brief(findings, watch_terms=["memory"], provider=provider)

    assert brief.synthesized is False
    assert "## Signal" in brief.markdown


def test_get_provider_returns_none_without_api_key() -> None:
    assert get_provider("openai", environ={}) is None


def test_get_provider_builds_anthropic_provider() -> None:
    provider = get_provider(
        "anthropic",
        environ={"RADAR_ANTHROPIC_API_KEY": "secret"},
    )

    assert provider is not None
    assert provider.name == "anthropic"


def test_get_provider_builds_azure_provider() -> None:
    provider = get_provider(
        "azure",
        model="gpt-4o-mini",
        environ={
            "RADAR_AZURE_OPENAI_API_KEY": "secret",
            "RADAR_AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
            "RADAR_AZURE_OPENAI_DEPLOYMENT": "radar-synth",
        },
    )

    assert provider is not None
    assert provider.name == "azure"


def test_get_provider_rejects_unknown_name() -> None:
    with pytest.raises(ValueError, match="Unknown synthesis provider"):
        get_provider("unknown", environ={"RADAR_OPENAI_API_KEY": "secret"})


def test_parse_model_payload_accepts_fenced_json() -> None:
    findings = [
        Finding(title="Paper", url="https://example.com/memory", source="arxiv"),
        Finding(title="Repo", url="https://example.com/eval", source="github"),
    ]
    fenced = f"```json\n{_model_payload()}\n```"

    brief = parse_model_payload(
        fenced,
        findings=findings,
        title="Desk Radar",
        watch_terms=("memory",),
        max_items=5,
    )

    assert brief.synthesized is True
    assert brief.title == "Desk Radar"
