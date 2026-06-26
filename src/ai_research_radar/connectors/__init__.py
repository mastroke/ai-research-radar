"""Pluggable source connectors for AI Research Radar."""

from ai_research_radar.connectors.base import FetchTextFn, SourceConnector
from ai_research_radar.connectors.registry import (
    CONNECTOR_NAMES,
    fetch_from_sources,
    get_connector,
)

__all__ = [
    "CONNECTOR_NAMES",
    "FetchTextFn",
    "SourceConnector",
    "fetch_from_sources",
    "get_connector",
]
