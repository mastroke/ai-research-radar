"""arXiv Atom API connector."""

from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET

from dataclasses import dataclass

from ai_research_radar.brief import Finding
from ai_research_radar.connectors.base import SourceConnector

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
ARXIV_API = "https://export.arxiv.org/api/query"


@dataclass
class ArxivConnector(SourceConnector):
    """Fetch recent arXiv papers matching configured watch terms."""

    @property
    def name(self) -> str:
        return "arxiv"

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
                "search_query": query,
                "start": "0",
                "max_results": str(max_results),
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
        )
        url = f"{ARXIV_API}?{params}"
        return self.fetch_text(url, timeout=timeout)

    def _parse(self, raw: str, *, max_results: int) -> list[Finding]:
        root = ET.fromstring(raw)
        findings: list[Finding] = []

        for entry in root.findall("atom:entry", ATOM_NS):
            title = _element_text(entry, "atom:title", ATOM_NS).replace("\n", " ").strip()
            summary = _element_text(entry, "atom:summary", ATOM_NS).replace("\n", " ").strip()
            url = _entry_url(entry)
            if not title or not url:
                continue
            findings.append(
                Finding(
                    title=title,
                    url=url,
                    source=self.name,
                    note=summary,
                )
            )
            if len(findings) >= max_results:
                break

        return findings


def _build_query(watch_terms: tuple[str, ...]) -> str:
    terms = [term.strip() for term in watch_terms if term.strip()]
    if not terms:
        terms = ["artificial intelligence"]
    clauses = [f"all:{_escape_term(term)}" for term in terms]
    return " OR ".join(clauses)


def _escape_term(term: str) -> str:
    return term.replace('"', "")


def _element_text(
    parent: ET.Element,
    tag: str,
    namespaces: dict[str, str],
) -> str:
    element = parent.find(tag, namespaces)
    return element.text or "" if element is not None else ""


def _entry_url(entry: ET.Element) -> str:
    for link in entry.findall("atom:link", ATOM_NS):
        if link.attrib.get("rel") == "alternate" and link.attrib.get("href"):
            return link.attrib["href"]
    entry_id = _element_text(entry, "atom:id", ATOM_NS)
    return entry_id.strip()
