"""Anthropic messages synthesis provider."""

from __future__ import annotations

from dataclasses import dataclass

from ai_research_radar.brief import Finding
from ai_research_radar.synthesis.base import SynthesisProvider
from ai_research_radar.synthesis.prompt import build_synthesis_prompt

DEFAULT_ANTHROPIC_MODEL = "claude-3-5-haiku-latest"
_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"


@dataclass(kw_only=True)
class AnthropicProvider(SynthesisProvider):
    """Synthesize briefs via the Anthropic messages API."""

    @property
    def name(self) -> str:
        return "anthropic"

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
        prompt = build_synthesis_prompt(
            findings,
            title=title,
            topic=topic,
            watch_terms=watch_terms,
            max_items=max_items,
        )
        response = self.post_json(
            _ANTHROPIC_URL,
            payload={
                "model": self.model,
                "max_tokens": 2048,
                "temperature": 0.2,
                "system": "You compile cross-source AI research briefs as JSON.",
                "messages": [{"role": "user", "content": prompt}],
            },
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": _ANTHROPIC_VERSION,
            },
            timeout=timeout,
        )
        content_blocks = response.get("content")
        if not isinstance(content_blocks, list) or not content_blocks:
            raise ValueError("Anthropic response missing content")
        first = content_blocks[0]
        if not isinstance(first, dict):
            raise ValueError("Anthropic response content must be objects")
        text = first.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Anthropic response missing text")
        return text
