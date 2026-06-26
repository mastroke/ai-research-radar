"""HTTP helpers for source connectors."""

from __future__ import annotations

import urllib.error
import urllib.request
from collections.abc import Mapping

DEFAULT_USER_AGENT = "ai-research-radar/0.1.0"


def fetch_text(
    url: str,
    *,
    timeout: float,
    headers: Mapping[str, str] | None = None,
) -> str:
    """Fetch a URL and return the response body as text."""

    merged_headers = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        merged_headers.update(headers)

    request = urllib.request.Request(url, headers=merged_headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset)
