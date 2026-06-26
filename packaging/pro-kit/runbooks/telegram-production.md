# Telegram production runbook (Radar Pro)

Two-process model: a timer runs `radar once`; a long-lived poll handles
operator commands.

## 1. Create the bot

1. Message [@BotFather](https://t.me/BotFather), create a bot, save the token.
2. Export `RADAR_TELEGRAM_BOT_TOKEN` on the host (never commit it).

## 2. Lock delivery to one chat

1. Send any message to your bot from the operator chat.
2. Read updates once to discover `chat.id`:

```bash
curl -s "https://api.telegram.org/bot${RADAR_TELEGRAM_BOT_TOKEN}/getUpdates"
```

3. Set `RADAR_TELEGRAM_CHAT_ID` or uncomment `[telegram] chat_id` in config.

Only that chat can receive briefs or run `status` / `find` commands.

## 3. Smoke test delivery

```bash
export RADAR_TELEGRAM_BOT_TOKEN="..."
export RADAR_TELEGRAM_CHAT_ID="123456789"
radar once --config /etc/radar/radar.toml
```

Expect the markdown brief in Telegram after stdout/file output.

## 4. Start the control poll

```bash
radar telegram poll --config /etc/radar/radar.toml
```

Commands (authorized chat only):

| Command | Behavior |
| --- | --- |
| `status` | Sources, memory counts, synthesis mode |
| `find <url>` | Focused brief for one URL |

Run under systemd via `radar schedule --with-telegram-poll` or the Pro
`scheduling/radar-telegram-poll.service` template.

## Failure modes

- Missing token: CLI skips Telegram delivery; brief still writes locally.
- Wrong chat id: messages are dropped; check `getUpdates` and config.
- Poll down: scheduled briefs still deliver; interactive `find` is unavailable.
