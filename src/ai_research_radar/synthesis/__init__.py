"""Model-agnostic synthesis backends for structured brief generation."""

from ai_research_radar.synthesis.base import PostJsonFn, SynthesisProvider
from ai_research_radar.synthesis.compiler import synthesize_brief
from ai_research_radar.synthesis.registry import PROVIDER_NAMES, get_provider
from ai_research_radar.synthesis.structured import (
    StructuredBrief,
    SynthesizedItem,
    fallback_structured_brief,
    source_families,
)

__all__ = [
    "PROVIDER_NAMES",
    "PostJsonFn",
    "StructuredBrief",
    "SynthesizedItem",
    "SynthesisProvider",
    "fallback_structured_brief",
    "get_provider",
    "source_families",
    "synthesize_brief",
]
