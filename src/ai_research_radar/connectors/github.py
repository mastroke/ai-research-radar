"""GitHub repository search connector."""

from __future__ import annotations

import json
import os
import urllib.parse
from dataclasses import dataclass

from ai_research_radar.brief import Finding
from ai_research_radar.connectors.base import SourceConnector

GITHUB_SEARCH_API = "https://api.github.com/search/repositories"


@dataclass
class GitHubConnector(SourceConnector):
    """Fetch GitHub repositories matching configured watch terms."""

    @property
    def name(self) -> str:
        return "github"

    def _fetch_raw(
        self,
        *,
        watch_terms: tuple[str, ...],
        timeout: float,
        max_results: int,
    ) -> str:
        query = _build_query(watch_terms)
        params = urllib.parse.urlencode(
            {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": str(max_results),
            }
        )
        url = f"{GITHUB_SEARCH_API}?{params}"
        headers = {"Accept": "application/vnd.github+json"}
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return self.fetch_text(url, timeout=timeout, headers=headers)

    def _parse(self, raw: str, *, max_results: int) -> list[Finding]:
        payload = json.loads(raw)
        items = payload.get("items", [])
        if not isinstance(items, list):
            raise ValueError("GitHub response must include an items list")

        findings: list[Finding] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            full_name = str(item.get("full_name", "")).strip()
            html_url = str(item.get("html_url", "")).strip()
            description = str(item.get("description") or "").strip()
            if not full_name or not html_url:
                continue
            findings.append(
                Finding(
                    title=full_name,
                    url=html_url,
                    source=self.name,
                    note=description,
                )
            )
            if len(findings) >= max_results:
                break

        return findings


def _build_query(watch_terms: tuple[str, ...]) -> str:
    terms = [term.strip() for term in watch_terms if term.strip()]
    if not terms:
        return "artificial intelligence in:name,description,readme"
    joined = " ".join(terms)
    return f"{joined} in:name,description,readme"
