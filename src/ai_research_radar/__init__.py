"""AI Research Radar package."""

from ai_research_radar.brief import Brief, Finding, compile_brief
from ai_research_radar.config import RadarConfig, load_config
from ai_research_radar.connectors import CONNECTOR_NAMES, fetch_from_sources
from ai_research_radar.synthesis import PROVIDER_NAMES, get_provider, synthesize_brief

__version__ = "0.1.0"

__all__ = [
    "Brief",
    "CONNECTOR_NAMES",
    "Finding",
    "PROVIDER_NAMES",
    "RadarConfig",
    "__version__",
    "compile_brief",
    "fetch_from_sources",
    "get_provider",
    "load_config",
    "synthesize_brief",
]
