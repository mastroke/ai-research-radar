"""HTTP connectors for live agent endpoints and raw pinned APIs."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from agent_acceptance_kit.config import LayerConfig


class AgentHttpConnector:
    """POST probe prompts to a full agent endpoint."""

    def __init__(self, layer: LayerConfig) -> None:
        self.layer = layer

    def complete(self, prompt: str, *, context: str = "") -> str:
        payload = {
            "prompt": prompt,
            "context": context,
            "model": self.layer.model,
        }
        return _post_json(self.layer, payload, response_key="output")


class RawApiConnector:
    """POST probe prompts to a pinned raw model API (OpenAI-compatible shape)."""

    def __init__(self, layer: LayerConfig) -> None:
        self.layer = layer

    def complete(self, prompt: str, *, context: str = "") -> str:
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.layer.model,
            "messages": messages,
        }
        return _post_json(self.layer, payload, response_key="choices")


def _post_json(layer: LayerConfig, payload: dict, response_key: str) -> str:
    if not layer.endpoint:
        msg = f"Layer {layer.name!r} requires endpoint for HTTP mode"
        raise ValueError(msg)

    headers = {"Content-Type": "application/json", **layer.headers}
    if layer.api_key_env:
        token = os.environ.get(layer.api_key_env, "")
        if token:
            headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        layer.endpoint,
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=layer.timeout_seconds) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {layer.endpoint}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed for {layer.endpoint}: {exc}") from exc

    if response_key == "output":
        return str(body.get("output", body.get("text", "")))
    if response_key == "choices":
        choices = body.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("message", {})
        return str(message.get("content", ""))
    return str(body)
