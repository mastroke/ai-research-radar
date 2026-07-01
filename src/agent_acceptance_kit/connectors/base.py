"""Connector protocol and registry for evaluation layers."""

from __future__ import annotations

from typing import Protocol

from agent_acceptance_kit.config import LayerConfig


class Connector(Protocol):
    """Minimal interface for layer backends."""

    def complete(self, prompt: str, *, context: str = "") -> str:
        """Return model text for a probe prompt."""


def get_connector(layer: LayerConfig) -> Connector:
    if layer.kind == "mock":
        from agent_acceptance_kit.connectors.mock import MockConnector

        return MockConnector(layer.name)
    if layer.kind == "agent":
        from agent_acceptance_kit.connectors.http import AgentHttpConnector

        return AgentHttpConnector(layer)
    if layer.kind == "api":
        from agent_acceptance_kit.connectors.http import RawApiConnector

        return RawApiConnector(layer)
    msg = f"Unsupported layer kind: {layer.kind!r}"
    raise ValueError(msg)
