"""Azure OpenAI chat-completions synthesis provider."""

from __future__ import annotations

from dataclasses import dataclass

from ai_research_radar.brief import Finding
from ai_research_radar.synthesis.base import SynthesisProvider
from ai_research_radar.synthesis.prompt import build_synthesis_prompt

DEFAULT_AZURE_API_VERSION = "2024-02-15-preview"


@dataclass(kw_only=True)
class AzureOpenAIProvider(SynthesisProvider):
    """Synthesize briefs via Azure OpenAI chat completions."""

    endpoint: str
    deployment: str
    api_version: str = DEFAULT_AZURE_API_VERSION

    @property
    def name(self) -> str:
        return "azure"

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
        base = self.endpoint.rstrip("/")
        url = (
            f"{base}/openai/deployments/{self.deployment}/chat/completions"
            f"?api-version={self.api_version}"
        )
        response = self.post_json(
            url,
            payload={
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
            headers={"api-key": self.api_key},
            timeout=timeout,
        )
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Azure OpenAI response missing choices")
        message = choices[0].get("message", {})
        if not isinstance(message, dict):
            raise ValueError("Azure OpenAI response missing message")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Azure OpenAI response missing content")
        return content
