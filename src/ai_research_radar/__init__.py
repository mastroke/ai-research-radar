"""AI Research Radar package."""

from ai_research_radar.brief import Brief, Finding, compile_brief
from ai_research_radar.config import RadarConfig, load_config
from ai_research_radar.connectors import CONNECTOR_NAMES, fetch_from_sources

__version__ = "0.1.0"

__all__ = [
    "Brief",
    "CONNECTOR_NAMES",
    "Finding",
    "RadarConfig",
    "__version__",
    "compile_brief",
    "fetch_from_sources",
    "load_config",
]
