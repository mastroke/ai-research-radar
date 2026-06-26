# ADR 0005: Telegram Delivery With Locked-Down Control

## Context

Milestone r5 needs the compiled daily brief delivered to Telegram and a small
set of operator commands (`status`, `find <url>`) without opening a public
control surface. The rest of the stack is stdlib-only and config-driven via TOML
plus `RADAR_*` environment variables.

## Decision

Add a `delivery.telegram` module that wraps the Telegram Bot API with urllib.
Delivery is enabled when `[telegram].chat_id` (or `RADAR_TELEGRAM_CHAT_ID`) is
set and `RADAR_TELEGRAM_BOT_TOKEN` is present at runtime. The bot token is never
stored in config files.

`radar once` and `radar run` call `deliver_brief_to_telegram` after the usual
stdout or file write. Long briefs are split into 4096-character chunks.

Two-way control lives behind `radar telegram poll`. Incoming updates are
accepted only when `message.chat.id` matches the configured chat id; all other
chats are ignored without a reply. Supported commands:

- `status` — runtime summary (sources, memory counts, synthesis mode)
- `find <url>` — focused brief for one URL, using persisted memory when present

## Consequences

Operators run a second long-lived process for Telegram control alongside the
brief scheduler. Credentials stay in environment variables, matching the BYOK
synthesis pattern.

The trade-off is no inline Telegram webhook server: long polling is simpler to
self-host but requires `telegram poll` to stay running. Webhooks and richer
command menus are out of scope for this milestone.
