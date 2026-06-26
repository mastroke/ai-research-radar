"""Hacker News Algolia search connector."""

from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass

from ai_research_radar.brief import Finding
from ai_research_radar.connectors.base import SourceConnector

HN_SEARCH_API = "https://hn.algolia.com/api/v1/search"


@dataclass
class HackerNewsConnector(SourceConnector):
    """Fetch Hacker News stories matching configured watch terms."""

    @property
    def name(self) -> str:
        return "hackernews"

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
                "query": query,
                "tags": "story",
                "hitsPerPage": str(max_results),
            }
        )
        url = f"{HN_SEARCH_API}?{params}"
        return self.fetch_text(url, timeout=timeout)

    def _parse(self, raw: str, *, max_results: int) -> list[Finding]:
        payload = json.loads(raw)
        hits = payload.get("hits", [])
        if not isinstance(hits, list):
            raise ValueError("Hacker News response must include a hits list")

        findings: list[Finding] = []
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            title = str(hit.get("title", "")).strip()
            url = str(hit.get("url") or hit.get("story_url") or "").strip()
            if not title:
                continue
            if not url:
                object_id = hit.get("objectID")
                if object_id is not None:
                    url = f"https://news.ycombinator.com/item?id={object_id}"
            if not url:
                continue

            note = str(hit.get("story_text") or hit.get("comment_text") or "").strip()
            findings.append(
                Finding(
                    title=title,
                    url=url,
                    source=self.name,
                    note=note,
                )
            )
            if len(findings) >= max_results:
                break

        return findings


def _build_query(watch_terms: tuple[str, ...]) -> str:
    terms = [term.strip() for term in watch_terms if term.strip()]
    if not terms:
        return "artificial intelligence"
    return " ".join(terms)
