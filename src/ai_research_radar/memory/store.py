"""File-backed seen-store and finding persistence."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ai_research_radar.brief import Finding

_STORE_VERSION = 1


def finding_key(url: str) -> str:
    """Normalize a finding URL for deduplication and seen tracking."""

    return url.strip().rstrip("/").lower()


def dedup_findings(findings: list[Finding]) -> list[Finding]:
    """Return findings deduplicated by normalized URL, keeping the last entry."""

    by_key: dict[str, Finding] = {}
    for finding in findings:
        by_key[finding_key(finding.url)] = finding
    return list(by_key.values())


class MemoryStore(ABC):
    """Contract for cross-run finding memory and seen-url tracking."""

    @abstractmethod
    def merge_findings(self, incoming: list[Finding]) -> list[Finding]:
        """Merge incoming findings into memory and return the full deduped set."""

    @abstractmethod
    def filter_unseen(self, findings: list[Finding]) -> list[Finding]:
        """Return findings that have not yet appeared in a brief."""

    @abstractmethod
    def mark_briefed(self, findings: list[Finding]) -> None:
        """Record findings included in a compiled brief."""

    @abstractmethod
    def persist(self) -> None:
        """Flush in-memory state to durable storage when applicable."""


class NullMemoryStore(MemoryStore):
    """No-op store used when memory persistence is disabled."""

    def merge_findings(self, incoming: list[Finding]) -> list[Finding]:
        return dedup_findings(incoming)

    def filter_unseen(self, findings: list[Finding]) -> list[Finding]:
        return list(findings)

    def mark_briefed(self, findings: list[Finding]) -> None:
        return None

    def persist(self) -> None:
        return None


class FileMemoryStore(MemoryStore):
    """JSON file store for accumulated findings and briefed URL keys."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._findings: list[Finding] = []
        self._seen_urls: set[str] = set()
        self._load()

    def merge_findings(self, incoming: list[Finding]) -> list[Finding]:
        merged = dedup_findings(self._findings + incoming)
        self._findings = merged
        return list(merged)

    def filter_unseen(self, findings: list[Finding]) -> list[Finding]:
        return [finding for finding in findings if finding_key(finding.url) not in self._seen_urls]

    def mark_briefed(self, findings: list[Finding]) -> None:
        for finding in findings:
            self._seen_urls.add(finding_key(finding.url))

    def persist(self) -> None:
        payload = {
            "version": _STORE_VERSION,
            "findings": [_finding_to_dict(finding) for finding in self._findings],
            "seen_urls": sorted(self._seen_urls),
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        temp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temp_path.replace(self._path)

    def _load(self) -> None:
        if not self._path.exists():
            return

        raw = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"Memory store must be a JSON object: {self._path}")

        version = raw.get("version", _STORE_VERSION)
        if version != _STORE_VERSION:
            raise ValueError(
                f"Unsupported memory store version {version!r} in {self._path}. "
                f"Expected {_STORE_VERSION}."
            )

        findings_raw = raw.get("findings", [])
        if not isinstance(findings_raw, list):
            raise ValueError(f"Memory store findings must be a list: {self._path}")

        self._findings = [_finding_from_dict(item) for item in findings_raw]

        seen_raw = raw.get("seen_urls", [])
        if not isinstance(seen_raw, list):
            raise ValueError(f"Memory store seen_urls must be a list: {self._path}")

        self._seen_urls = {finding_key(str(url)) for url in seen_raw}


def open_memory_store(path: Path | None) -> MemoryStore:
    """Open a file-backed store or a null store when persistence is disabled."""

    if path is None:
        return NullMemoryStore()
    return FileMemoryStore(path)


def _finding_to_dict(finding: Finding) -> dict[str, str]:
    return {
        "title": finding.title,
        "url": finding.url,
        "source": finding.source,
        "note": finding.note,
    }


def _finding_from_dict(raw: Any) -> Finding:
    if not isinstance(raw, dict):
        raise ValueError("Each persisted finding must be a JSON object")

    title = str(raw.get("title", "")).strip()
    url = str(raw.get("url", "")).strip()
    source = str(raw.get("source", "manual")).strip() or "manual"
    note = str(raw.get("note", "")).strip()

    if not title:
        raise ValueError("Each persisted finding must include a title")
    if not url:
        raise ValueError("Each persisted finding must include a url")

    return Finding(title=title, url=url, source=source, note=note)
