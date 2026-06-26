"""Connector interface and shared fetch behavior."""

from __future__ import annotations

import urllib.error
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field

from ai_research_radar.brief import Finding
from ai_research_radar.connectors.http import fetch_text as default_fetch_text

FetchTextFn = Callable[..., str]


@dataclass
class SourceConnector(ABC):
    """Best-effort source connector with injectable HTTP for tests."""

    fetch_text: FetchTextFn = field(default=default_fetch_text)

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable connector identifier used in config and Finding.source."""

    def fetch(
        self,
        *,
        watch_terms: tuple[str, ...],
        timeout: float = 10.0,
        max_results: int = 10,
    ) -> list[Finding]:
        """Return findings from this source, or an empty list on failure."""

        try:
            raw = self._fetch_raw(
                watch_terms=watch_terms,
                timeout=timeout,
                max_results=max_results,
            )
            return self._parse(raw, max_results=max_results)
        except (
            OSError,
            TimeoutError,
            ValueError,
            urllib.error.HTTPError,
            urllib.error.URLError,
        ):
            return []

    @abstractmethod
    def _fetch_raw(
        self,
        *,
        watch_terms: tuple[str, ...],
        timeout: float,
        max_results: int,
    ) -> str:
        """Fetch the upstream payload as text."""

    @abstractmethod
    def _parse(self, raw: str, *, max_results: int) -> list[Finding]:
        """Parse a recorded or live payload into findings."""
