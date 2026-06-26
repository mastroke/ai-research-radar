"""Provider registry for model-agnostic synthesis."""

from __future__ import annotations

import os
from collections.abc import Mapping

from ai_research_radar.synthesis.base import PostJsonFn, SynthesisProvider
from ai_research_radar.synthesis.providers.anthropic import (
    DEFAULT_ANTHROPIC_MODEL,
    AnthropicProvider,
)
from ai_research_radar.synthesis.providers.azure import (
    DEFAULT_AZURE_API_VERSION,
    AzureOpenAIProvider,
)
from ai_research_radar.synthesis.providers.openai import (
    DEFAULT_OPENAI_MODEL,
    OpenAIProvider,
)

PROVIDER_NAMES: tuple[str, ...] = ("openai", "anthropic", "azure")

_PROVIDER_DEFAULT_MODELS: dict[str, str] = {
    "openai": DEFAULT_OPENAI_MODEL,
    "anthropic": DEFAULT_ANTHROPIC_MODEL,
}


def get_provider(
    name: str,
    *,
    model: str | None = None,
    environ: Mapping[str, str] | None = None,
    post_json: PostJsonFn | None = None,
) -> SynthesisProvider | None:
    """Return a configured provider or None when credentials are missing."""

    env = environ or os.environ
    normalized = name.strip().lower()
    resolved_model = model or _PROVIDER_DEFAULT_MODELS.get(normalized, DEFAULT_OPENAI_MODEL)
    kwargs: dict[str, object] = {"model": resolved_model}
    if post_json is not None:
        kwargs["post_json"] = post_json

    if normalized == "openai":
        api_key = env.get("RADAR_OPENAI_API_KEY", "")
        if not api_key.strip():
            return None
        return OpenAIProvider(api_key=api_key, **kwargs)

    if normalized == "anthropic":
        api_key = env.get("RADAR_ANTHROPIC_API_KEY", "")
        if not api_key.strip():
            return None
        return AnthropicProvider(api_key=api_key, **kwargs)

    if normalized == "azure":
        api_key = env.get("RADAR_AZURE_OPENAI_API_KEY", "")
        endpoint = env.get("RADAR_AZURE_OPENAI_ENDPOINT", "")
        deployment = env.get("RADAR_AZURE_OPENAI_DEPLOYMENT", "") or resolved_model
        api_version = env.get("RADAR_AZURE_OPENAI_API_VERSION", DEFAULT_AZURE_API_VERSION)
        if not api_key.strip() or not endpoint.strip() or not deployment.strip():
            return None
        return AzureOpenAIProvider(
            api_key=api_key,
            endpoint=endpoint,
            deployment=deployment,
            api_version=api_version,
            **kwargs,
        )

    raise ValueError(
        f"Unknown synthesis provider: {name!r}. Expected one of: {', '.join(PROVIDER_NAMES)}"
    )
