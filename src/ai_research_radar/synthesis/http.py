"""HTTP helpers for model synthesis providers."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Any

from ai_research_radar.connectors.http import DEFAULT_USER_AGENT


def post_json(
    url: str,
    *,
    payload: Mapping[str, Any],
    headers: Mapping[str, str] | None = None,
    timeout: float,
) -> dict[str, Any]:
    """POST JSON to a URL and return the parsed JSON response body."""

    merged_headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if headers:
        merged_headers.update(headers)

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=merged_headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        raw = response.read().decode(charset)
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object response")
    return parsed
