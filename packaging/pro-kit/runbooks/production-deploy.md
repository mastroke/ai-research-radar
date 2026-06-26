# Production deploy runbook (Radar Pro)

Deploy a daily brief on a single Linux host with systemd timers.

## Prerequisites

- Python 3.11+
- `radar` installed (`pip install` from GitHub)
- Pro persona config copied to `/etc/radar/radar.toml`
- API keys and optional Telegram token in `/etc/radar/environment`

## Layout

```text
/etc/radar/
  radar.toml
  environment          # RADAR_* secrets, chmod 600
/var/lib/radar/
  briefs/              # output_path targets
  .radar/              # memory_path JSON store
```

## systemd units

Generate units from your config:

```bash
radar schedule --config /etc/radar/radar.toml --format systemd --output-dir /etc/systemd/system
```

When Telegram control is enabled, add the poll service:

```bash
radar schedule --config /etc/radar/radar.toml --format systemd \
  --output-dir /etc/systemd/system --with-telegram-poll
```

Pro templates under `scheduling/` add `EnvironmentFile` and log notes. Merge
those lines into the generated units before `systemctl daemon-reload`.

## Enable

```bash
systemctl enable --now radar-once.timer
systemctl enable --now radar-telegram-poll.service   # when using Telegram control
```

## Verify

```bash
systemctl start radar-once.service
journalctl -u radar-once.service -n 50
radar once --config /etc/radar/radar.toml   # manual smoke test
```

## Rollback

Disable timers, restore the previous `radar.toml`, and re-run `radar schedule`.
Memory JSON is append-only; delete `.radar/*.json` only when intentionally
resetting seen URLs.
