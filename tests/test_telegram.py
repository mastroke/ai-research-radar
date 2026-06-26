"""Tests for Telegram delivery and control commands."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_research_radar.brief import Finding
from ai_research_radar.cli import main
from ai_research_radar.config import RadarConfig, load_config
from ai_research_radar.delivery.telegram import (
    TELEGRAM_TOKEN_ENV,
    TelegramClient,
    build_find_response,
    build_status_message,
    deliver_brief_to_telegram,
    dispatch_telegram_command,
    is_authorized_chat,
    parse_telegram_command,
    split_message,
)
from ai_research_radar.memory import open_memory_store


def test_parse_telegram_command_accepts_slash_and_plain_text() -> None:
    assert parse_telegram_command("/status") == parse_telegram_command("status")
    assert parse_telegram_command("find https://example.com/paper").argument == (
        "https://example.com/paper"
    )


def test_parse_telegram_command_ignores_unknown_commands() -> None:
    assert parse_telegram_command("hello") is None
    assert parse_telegram_command("/start") is None


def test_is_authorized_chat_matches_configured_chat_id() -> None:
    assert is_authorized_chat(42, 42) is True
    assert is_authorized_chat(99, 42) is False


def test_build_status_message_reports_memory_counts(tmp_path: Path) -> None:
    memory_path = tmp_path / "memory.json"
    store = open_memory_store(memory_path)
    store.merge_findings(
        [
            Finding(
                title="Stored",
                url="https://example.com/stored",
                source="manual",
            )
        ]
    )
    store.mark_briefed(
        [Finding(title="Stored", url="https://example.com/stored", source="manual")]
    )
    config = RadarConfig(
        title="Desk Radar",
        topic="agents",
        watch_terms=("memory",),
        sources=("arxiv",),
        memory_path=memory_path,
        telegram_chat_id=12345,
    )

    message = build_status_message(config, store)

    assert "Desk Radar" in message
    assert "Findings stored: 1" in message
    assert "URLs briefed: 1" in message
    assert "Telegram chat: 12345" in message


def test_build_find_response_uses_persisted_finding(tmp_path: Path) -> None:
    memory_path = tmp_path / "memory.json"
    store = open_memory_store(memory_path)
    store.merge_findings(
        [
            Finding(
                title="Persisted paper",
                url="https://example.com/paper",
                source="arxiv",
                note="Already in memory.",
            )
        ]
    )
    config = RadarConfig(title="Desk Radar", watch_terms=("memory",))

    message = build_find_response("https://example.com/paper", config, store)

    assert "Persisted paper" in message
    assert "Already in memory" in message


def test_dispatch_telegram_command_returns_none_for_non_commands() -> None:
    config = RadarConfig()
    store = open_memory_store(None)

    assert dispatch_telegram_command("random text", config, store) is None


def test_split_message_chunks_long_briefs() -> None:
    text = "a" * 5000

    chunks = split_message(text, max_length=4096)

    assert len(chunks) == 2
    assert sum(len(chunk) for chunk in chunks) == 5000


def test_telegram_client_send_message_splits_payloads() -> None:
    sent: list[dict[str, object]] = []

    def fake_post(
        url: str,
        *,
        payload: dict[str, object],
        timeout: float,
    ) -> dict[str, object]:
        sent.append(payload)
        return {"ok": True}

    client = TelegramClient("token", post_json=fake_post)
    client.send_message(42, "x" * 5000)

    assert len(sent) == 2
    assert sent[0]["chat_id"] == 42


def test_deliver_brief_to_telegram_requires_token_and_chat_id() -> None:
    config = RadarConfig(telegram_chat_id=42)
    assert deliver_brief_to_telegram(config, "brief", environ={}) is False

    sent: list[str] = []

    class FakeClient:
        def send_message(self, chat_id: int, text: str) -> None:
            sent.append(text)

    assert (
        deliver_brief_to_telegram(
            config,
            "brief",
            client=FakeClient(),  # type: ignore[arg-type]
            environ={TELEGRAM_TOKEN_ENV: "token"},
        )
        is True
    )
    assert sent == ["brief"]


def test_once_delivers_brief_to_telegram(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    sent: list[tuple[int, str]] = []
    monkeypatch.setenv("RADAR_TELEGRAM_CHAT_ID", "99")

    def fake_deliver(config, markdown, *, client=None, environ=None):
        assert config.telegram_chat_id == 99
        sent.append((99, markdown))
        return True

    monkeypatch.setattr("ai_research_radar.cli.deliver_brief_to_telegram", fake_deliver)

    exit_code = main(
        [
            "once",
            "--item",
            "Agent memory|https://example.com/memory|manual|Tracks durable state.",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# AI Research Radar Brief" in output
    assert sent == [(99, output)]


def test_load_config_reads_telegram_table(tmp_path: Path) -> None:
    config_path = tmp_path / "radar.toml"
    config_path.write_text(
        """
[telegram]
chat_id = 424242
timeout_seconds = 15
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path, environ={})

    assert config.telegram_chat_id == 424242
    assert config.telegram_timeout_seconds == 15.0


def test_load_config_applies_telegram_environment_overrides(tmp_path: Path) -> None:
    config_path = tmp_path / "radar.toml"
    config_path.write_text("", encoding="utf-8")

    config = load_config(
        config_path,
        environ={
            "RADAR_TELEGRAM_CHAT_ID": "515151",
            "RADAR_TELEGRAM_TIMEOUT_SECONDS": "20",
        },
    )

    assert config.telegram_chat_id == 515151
    assert config.telegram_timeout_seconds == 20.0


def test_telegram_poll_ignores_unauthorized_chat(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv(TELEGRAM_TOKEN_ENV, "token")
    config_path = tmp_path / "radar.toml"
    config_path.write_text(
        """
[telegram]
chat_id = 42
""".strip(),
        encoding="utf-8",
    )

    poll_calls = 0

    class FakeClient:
        def get_updates(self, *, offset: int | None = None, timeout: float | None = None):
            nonlocal poll_calls
            poll_calls += 1
            if poll_calls == 1:
                return [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 999},
                            "text": "status",
                        },
                    }
                ]
            raise KeyboardInterrupt

        def send_message(self, chat_id: int, text: str) -> None:
            raise AssertionError("unauthorized chats must not receive replies")

    monkeypatch.setattr("ai_research_radar.cli.TelegramClient", lambda token, timeout: FakeClient())

    exit_code = main(["telegram", "poll", "--config", str(config_path)])

    assert exit_code == 130


def test_telegram_poll_replies_to_authorized_status_command(
    monkeypatch,
    tmp_path: Path,
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv(TELEGRAM_TOKEN_ENV, "token")
    config_path = tmp_path / "radar.toml"
    config_path.write_text(
        """
[telegram]
chat_id = 42
""".strip(),
        encoding="utf-8",
    )
    replies: list[str] = []
    poll_calls = 0

    class FakeClient:
        def get_updates(self, *, offset: int | None = None, timeout: float | None = None):
            nonlocal poll_calls
            poll_calls += 1
            if poll_calls == 1:
                return [
                    {
                        "update_id": 7,
                        "message": {
                            "chat": {"id": 42},
                            "text": "/status",
                        },
                    }
                ]
            raise KeyboardInterrupt

        def send_message(self, chat_id: int, text: str) -> None:
            assert chat_id == 42
            replies.append(text)

    monkeypatch.setattr("ai_research_radar.cli.TelegramClient", lambda token, timeout: FakeClient())

    exit_code = main(["telegram", "poll", "--config", str(config_path)])

    assert exit_code == 130
    assert len(replies) == 1
    assert "AI Research Radar status" in replies[0]
