"""Synthesis provider interface and shared behavior."""

from __future__ import annotations

import json
import urllib.error
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ai_research_radar.brief import Finding
from ai_research_radar.synthesis.http import post_json as default_post_json
from ai_research_radar.synthesis.structured import StructuredBrief, parse_model_payload

PostJsonFn = Callable[..., dict[str, Any]]


@dataclass(kw_only=True)
class SynthesisProvider(ABC):
    """Best-effort LLM provider with injectable HTTP for tests."""

    api_key: str
    model: str
    post_json: PostJsonFn = field(default=default_post_json)

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable provider identifier used in config."""

    def synthesize(
        self,
        findings: list[Finding],
        *,
        title: str,
        topic: str,
        watch_terms: tuple[str, ...],
        timeout: float = 30.0,
        max_items: int = 5,
    ) -> StructuredBrief | None:
        """Return a structured brief or None when synthesis fails."""

        if not self.api_key.strip():
            return None

        try:
            raw = self._call_model(
                findings,
                title=title,
                topic=topic,
                watch_terms=watch_terms,
                timeout=timeout,
                max_items=max_items,
            )
            return parse_model_payload(
                raw,
                findings=findings,
                title=title,
                watch_terms=watch_terms,
                max_items=max_items,
            )
        except (
            OSError,
            TimeoutError,
            ValueError,
            json.JSONDecodeError,
            urllib.error.HTTPError,
            urllib.error.URLError,
            KeyError,
            TypeError,
        ):
            return None

    @abstractmethod
    def _call_model(
        self,
        findings: list[Finding],
        *,
        title: str,
        topic: str,
        watch_terms: tuple[str, ...],
        timeout: float,
        max_items: int,
    ) -> str:
        """Call the upstream model and return the assistant text payload."""
