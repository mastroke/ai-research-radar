"""OpenAI chat-completions synthesis provider."""

from __future__ import annotations

from dataclasses import dataclass

from ai_research_radar.brief import Finding
from ai_research_radar.synthesis.base import SynthesisProvider
from ai_research_radar.synthesis.prompt import build_synthesis_prompt

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
_OPENAI_URL = "https://api.openai.com/v1/chat/completions"


@dataclass(kw_only=True)
class OpenAIProvider(SynthesisProvider):
    """Synthesize briefs via the OpenAI chat completions API."""

    @property
    def name(self) -> str:
        return "openai"

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
            _OPENAI_URL,
            payload={
                "model": self.model,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": "You compile cross-source AI research briefs as JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
            },
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=timeout,
        )
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("OpenAI response missing choices")
        message = choices[0].get("message", {})
        if not isinstance(message, dict):
            raise ValueError("OpenAI response missing message")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("OpenAI response missing content")
        return content
