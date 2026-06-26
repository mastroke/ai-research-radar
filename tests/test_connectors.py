"""Tests for pluggable source connectors."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_research_radar.connectors import (
    CONNECTOR_NAMES,
    fetch_from_sources,
    get_connector,
)
from ai_research_radar.connectors.arxiv import ArxivConnector
from ai_research_radar.connectors.github import GitHubConnector
from ai_research_radar.connectors.hackernews import HackerNewsConnector
from ai_research_radar.connectors.huggingface import HuggingFaceConnector

FIXTURES = Path(__file__).parent / "fixtures" / "connectors"


def _fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _fixture_fetcher(name: str):
    payload = _fixture_text(name)

    def fetch_text(url: str, *, timeout: float, headers=None) -> str:  # type: ignore[no-untyped-def]
        return payload

    return fetch_text


@pytest.mark.parametrize("name", CONNECTOR_NAMES)
def test_get_connector_accepts_known_names(name: str) -> None:
    connector = get_connector(name)
    assert connector.name == name


def test_get_connector_rejects_unknown_name() -> None:
    with pytest.raises(ValueError, match="Unknown source connector"):
        get_connector("twitter")


def test_arxiv_connector_parses_recorded_fixture() -> None:
    connector = ArxivConnector(fetch_text=_fixture_fetcher("arxiv.xml"))
    findings = connector.fetch(watch_terms=("memory", "evaluation"), timeout=1.0)

    assert len(findings) == 2
    assert findings[0].title == "Agent Memory Evaluation Harness"
    assert findings[0].url == "http://arxiv.org/abs/2401.12345"
    assert findings[0].source == "arxiv"
    assert "regression gates" in findings[0].note


def test_hackernews_connector_parses_recorded_fixture() -> None:
    connector = HackerNewsConnector(fetch_text=_fixture_fetcher("hackernews.json"))
    findings = connector.fetch(watch_terms=("agents", "memory"), timeout=1.0)

    assert len(findings) == 2
    assert findings[0].title == "Show HN: Agent memory framework"
    assert findings[0].url == "https://example.com/agent-memory"
    assert findings[0].source == "hackernews"
    assert findings[1].url == "https://news.ycombinator.com/item?id=40123457"


def test_github_connector_parses_recorded_fixture() -> None:
    connector = GitHubConnector(fetch_text=_fixture_fetcher("github.json"))
    findings = connector.fetch(watch_terms=("agents", "memory"), timeout=1.0)

    assert len(findings) == 2
    assert findings[0].title == "org/agent-memory"
    assert findings[0].url == "https://github.com/org/agent-memory"
    assert findings[0].source == "github"
    assert "conflict handling" in findings[0].note


def test_huggingface_connector_parses_recorded_fixture() -> None:
    connector = HuggingFaceConnector(fetch_text=_fixture_fetcher("huggingface.json"))
    findings = connector.fetch(watch_terms=("agent",), timeout=1.0)

    assert len(findings) == 2
    assert findings[0].title == "org/agent-memory-model"
    assert findings[0].url == "https://huggingface.co/org/agent-memory-model"
    assert findings[0].source == "huggingface"
    assert "agent memory" in findings[0].note.lower()


def test_connector_returns_empty_list_on_fetch_failure() -> None:
    def failing_fetch(url: str, *, timeout: float, headers=None) -> str:  # type: ignore[no-untyped-def]
        raise TimeoutError("upstream timed out")

    connector = ArxivConnector(fetch_text=failing_fetch)
    assert connector.fetch(watch_terms=("agents",), timeout=0.1) == []


def test_fetch_from_sources_aggregates_best_effort() -> None:
    def selective_fetch(url: str, *, timeout: float, headers=None) -> str:  # type: ignore[no-untyped-def]
        if "arxiv.org" in url:
            raise OSError("network down")
        if "hn.algolia.com" in url:
            return _fixture_text("hackernews.json")
        if "github.com" in url:
            return _fixture_text("github.json")
        if "huggingface.co" in url:
            return _fixture_text("huggingface.json")
        raise AssertionError(f"unexpected url: {url}")

    findings = fetch_from_sources(
        CONNECTOR_NAMES,
        watch_terms=("memory",),
        timeout=1.0,
        fetch_text=selective_fetch,
    )

    assert len(findings) == 6
    assert {finding.source for finding in findings} == {
        "hackernews",
        "github",
        "huggingface",
    }
