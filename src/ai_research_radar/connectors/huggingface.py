"""Hugging Face Hub model search connector."""

from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass

from ai_research_radar.brief import Finding
from ai_research_radar.connectors.base import SourceConnector

HF_MODELS_API = "https://huggingface.co/api/models"


@dataclass
class HuggingFaceConnector(SourceConnector):
    """Fetch Hugging Face models matching configured watch terms."""

    @property
    def name(self) -> str:
        return "huggingface"

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
                "search": query,
                "limit": str(max_results),
                "sort": "downloads",
                "direction": "-1",
            }
        )
        url = f"{HF_MODELS_API}?{params}"
        return self.fetch_text(url, timeout=timeout)

    def _parse(self, raw: str, *, max_results: int) -> list[Finding]:
        payload = json.loads(raw)
        if not isinstance(payload, list):
            raise ValueError("Hugging Face response must be a JSON list")

        findings: list[Finding] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            model_id = str(item.get("id") or item.get("modelId") or "").strip()
            if not model_id:
                continue
            url = f"https://huggingface.co/{model_id}"
            note = str(item.get("description") or item.get("pipeline_tag") or "").strip()
            findings.append(
                Finding(
                    title=model_id,
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
        return "agent"
    return " ".join(terms)
