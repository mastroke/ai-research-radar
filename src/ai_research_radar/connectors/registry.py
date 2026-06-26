"""Connector registry and orchestration."""

from __future__ import annotations

from ai_research_radar.brief import Finding
from ai_research_radar.connectors.arxiv import ArxivConnector
from ai_research_radar.connectors.base import FetchTextFn, SourceConnector
from ai_research_radar.connectors.github import GitHubConnector
from ai_research_radar.connectors.hackernews import HackerNewsConnector
from ai_research_radar.connectors.huggingface import HuggingFaceConnector

CONNECTOR_NAMES: tuple[str, ...] = ("arxiv", "hackernews", "github", "huggingface")

_CONNECTOR_TYPES: dict[str, type[SourceConnector]] = {
    "arxiv": ArxivConnector,
    "hackernews": HackerNewsConnector,
    "github": GitHubConnector,
    "huggingface": HuggingFaceConnector,
}


def get_connector(
    name: str,
    *,
    fetch_text: FetchTextFn | None = None,
) -> SourceConnector:
    """Return a connector instance for a configured source name."""

    normalized = name.strip().lower()
    connector_type = _CONNECTOR_TYPES.get(normalized)
    if connector_type is None:
        raise ValueError(
            f"Unknown source connector: {name!r}. "
            f"Expected one of: {', '.join(CONNECTOR_NAMES)}"
        )
    if fetch_text is None:
        return connector_type()
    return connector_type(fetch_text=fetch_text)


def fetch_from_sources(
    source_names: tuple[str, ...],
    *,
    watch_terms: tuple[str, ...],
    timeout: float = 10.0,
    max_results: int = 10,
    fetch_text: FetchTextFn | None = None,
) -> list[Finding]:
    """Fetch findings from each configured source, best-effort."""

    findings: list[Finding] = []
    for source_name in source_names:
        connector = get_connector(source_name, fetch_text=fetch_text)
        findings.extend(
            connector.fetch(
                watch_terms=watch_terms,
                timeout=timeout,
                max_results=max_results,
            )
        )
    return findings
