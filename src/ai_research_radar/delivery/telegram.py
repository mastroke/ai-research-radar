"""Telegram delivery and locked-down two-way control commands."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from ai_research_radar.brief import Finding
from ai_research_radar.config import RadarConfig
from ai_research_radar.connectors.http import DEFAULT_USER_AGENT
from ai_research_radar.memory import MemoryStore
from ai_research_radar.synthesis import get_provider, synthesize_brief
from ai_research_radar.synthesis.base import SynthesisProvider

TELEGRAM_TOKEN_ENV = "RADAR_TELEGRAM_BOT_TOKEN"
DEFAULT_TELEGRAM_TIMEOUT_SECONDS = 30.0
MAX_MESSAGE_LENGTH = 4096

GetJsonFn = Callable[..., dict[str, Any]]
PostJsonFn = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class TelegramCommand:
    """Parsed operator command from a Telegram message."""

    name: str
    argument: str = ""


def resolve_telegram_token(
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """Read the bot token from the configured environment variable."""

    env = environ or os.environ
    token = env.get(TELEGRAM_TOKEN_ENV, "").strip()
    return token or None


def parse_telegram_command(text: str) -> TelegramCommand | None:
    """Parse supported control commands from plain Telegram message text."""

    stripped = text.strip()
    if not stripped:
        return None

    body = stripped[1:] if stripped.startswith("/") else stripped
    parts = body.split(maxsplit=1)
    name = parts[0].lower()
    if name not in {"status", "find"}:
        return None

    argument = parts[1].strip() if len(parts) > 1 else ""
    return TelegramCommand(name=name, argument=argument)


def build_status_message(config: RadarConfig, store: MemoryStore) -> str:
    """Render a concise runtime status summary for the operator."""

    stats = store.stats()
    sources = ", ".join(config.sources) if config.sources else "none"
    watch_terms = ", ".join(config.watch_terms) if config.watch_terms else "none"
    memory = str(config.memory_path) if config.memory_path else "disabled"
    synthesis = config.synthesis_provider or "deterministic"

    lines = [
        "AI Research Radar status",
        f"Title: {config.title}",
        f"Topic: {config.topic}",
        f"Sources: {sources}",
        f"Watch terms: {watch_terms}",
        f"Memory: {memory}",
        f"Findings stored: {stats.findings}",
        f"URLs briefed: {stats.seen}",
        f"Synthesis: {synthesis}",
        f"Telegram chat: {config.telegram_chat_id}",
    ]
    return "\n".join(lines)


def build_find_response(
    url: str,
    config: RadarConfig,
    store: MemoryStore,
    *,
    provider: SynthesisProvider | None = None,
) -> str:
    """Compile a focused brief for a single URL requested via Telegram."""

    target = url.strip()
    if not target:
        return "Usage: find <url>"

    finding = store.find_by_url(target)
    if finding is None:
        finding = Finding(
            title=_title_from_url(target),
            url=target,
            source="manual",
        )

    brief = synthesize_brief(
        [finding],
        watch_terms=list(config.watch_terms),
        title=config.title,
        topic=config.topic,
        provider=provider
        if provider is not None
        else _resolve_synthesis_provider(config),
        max_items=1,
        min_source_families=1,
    )
    return brief.markdown


def dispatch_telegram_command(
    text: str,
    config: RadarConfig,
    store: MemoryStore,
    *,
    provider: SynthesisProvider | None = None,
) -> str | None:
    """Handle an authorized Telegram message and return a reply when applicable."""

    command = parse_telegram_command(text)
    if command is None:
        return None
    if command.name == "status":
        return build_status_message(config, store)
    if command.name == "find":
        return build_find_response(
            command.argument,
            config,
            store,
            provider=provider,
        )
    return None


def split_message(text: str, *, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Split long briefs into Telegram-safe message chunks."""

    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n", 0, max_length)
        if split_at <= 0:
            split_at = max_length
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip("\n")
    return chunks


class TelegramClient:
    """Minimal Telegram Bot API client for send and long-poll receive."""

    def __init__(
        self,
        token: str,
        *,
        timeout: float = DEFAULT_TELEGRAM_TIMEOUT_SECONDS,
        get_json: GetJsonFn | None = None,
        post_json: PostJsonFn | None = None,
    ) -> None:
        self._token = token
        self._timeout = timeout
        self._base_url = f"https://api.telegram.org/bot{token}"
        self._get_json = get_json or self._default_get_json
        self._post_json = post_json or self._default_post_json

    def send_message(self, chat_id: int, text: str) -> None:
        """Send one or more message chunks to the configured chat."""

        for chunk in split_message(text):
            response = self._post_json(
                f"{self._base_url}/sendMessage",
                payload={"chat_id": chat_id, "text": chunk},
                timeout=self._timeout,
            )
            if not response.get("ok"):
                raise RuntimeError(f"Telegram sendMessage failed: {response!r}")

    def get_updates(
        self,
        *,
        offset: int | None = None,
        timeout: float | None = None,
    ) -> list[dict[str, Any]]:
        """Long-poll Telegram updates and return raw update objects."""

        params: dict[str, str | int] = {}
        if offset is not None:
            params["offset"] = offset
        poll_timeout = self._timeout if timeout is None else timeout
        if poll_timeout > 0:
            params["timeout"] = int(poll_timeout)

        query = urllib.parse.urlencode(params)
        url = f"{self._base_url}/getUpdates"
        if query:
            url = f"{url}?{query}"

        response = self._get_json(url, timeout=poll_timeout + 5.0)
        if not response.get("ok"):
            raise RuntimeError(f"Telegram getUpdates failed: {response!r}")

        result = response.get("result", [])
        if not isinstance(result, list):
            raise ValueError("Telegram getUpdates result must be a list")
        return [item for item in result if isinstance(item, dict)]

    def _default_get_json(self, url: str, *, timeout: float) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            raw = response.read().decode(charset)
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("Expected a JSON object response")
        return parsed

    def _default_post_json(
        self,
        url: str,
        *,
        payload: Mapping[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            raw = response.read().decode(charset)
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("Expected a JSON object response")
        return parsed


def deliver_brief_to_telegram(
    config: RadarConfig,
    markdown: str,
    *,
    client: TelegramClient | None = None,
    environ: Mapping[str, str] | None = None,
) -> bool:
    """Send a compiled brief to Telegram when delivery is configured."""

    if config.telegram_chat_id is None:
        return False

    token = resolve_telegram_token(environ)
    if not token:
        return False

    telegram = client or TelegramClient(
        token,
        timeout=config.telegram_timeout_seconds,
    )
    telegram.send_message(config.telegram_chat_id, markdown)
    return True


def is_authorized_chat(chat_id: int, allowed_chat_id: int) -> bool:
    """Return whether an incoming update belongs to the configured operator chat."""

    return chat_id == allowed_chat_id


def _resolve_synthesis_provider(config: RadarConfig) -> SynthesisProvider | None:
    if not config.synthesis_provider:
        return None
    return get_provider(
        config.synthesis_provider,
        model=config.synthesis_model,
    )


def _title_from_url(url: str) -> str:
    stripped = url.rstrip("/")
    if not stripped:
        return "Untitled finding"
    slug = stripped.rsplit("/", maxsplit=1)[-1]
    return slug.replace("-", " ").replace("_", " ").title()
