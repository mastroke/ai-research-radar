"""AI Research Radar package."""

from ai_research_radar.brief import Brief, Finding, compile_brief
from ai_research_radar.config import RadarConfig, load_config

__version__ = "0.1.0"

__all__ = [
    "Brief",
    "Finding",
    "RadarConfig",
    "__version__",
    "compile_brief",
    "load_config",
]
