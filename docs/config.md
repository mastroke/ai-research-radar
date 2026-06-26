# Configuration reference

AI Research Radar loads settings from a TOML file and optional `RADAR_*`
environment variables. Environment values override file values.

## Root keys

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `title` | string | `AI Research Radar` | Brief title prefix. |
| `topic` | string | `agentic AI research` | Topic line in the brief. |
| `watch_terms` | list of strings | see `config.py` | Terms used for ranking and connector queries. |
| `output_path` | path or empty | none | Write brief markdown to this file. Empty means stdout. |
| `interval_seconds` | positive integer | `86400` | Sleep interval for `radar run` and `interval` schedule preset. |
| `max_items` | positive integer | `5` | Maximum items in one brief. |
| `sources` | list of strings | `()` | Connector names: `arxiv`, `hackernews`, `github`, `huggingface`. |
| `connector_timeout_seconds` | positive float | `10` | Per-connector HTTP timeout. |
| `memory_path` | path or empty | none | File-backed seen-store and findings persistence. |

## `[[items]]` tables

Manual seed findings merged before connector fetch.

| Key | Required | Description |
| --- | --- | --- |
| `title` | yes | Item title. |
| `url` | yes | Canonical URL. |
| `source` | no | Source label (default `manual`). |
| `note` | no | Operator note included in ranking context. |

## `[synthesis]` table

Optional LLM synthesis. Credentials stay in environment variables.

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `provider` | string | none | `openai`, `anthropic`, or `azure`. |
| `model` | string | provider default | Model or deployment name. |
| `timeout_seconds` | positive float | `30` | Provider HTTP timeout. |
| `min_source_families` | positive integer | `2` | Minimum distinct source families before synthesis runs. |

## `[telegram]` table

Optional Telegram delivery and control commands.

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `chat_id` | integer | none | Only this chat may receive briefs and send commands. |
| `timeout_seconds` | positive float | `30` | Telegram API timeout. |

Bot token is read from `RADAR_TELEGRAM_BOT_TOKEN` only.

## `[schedule]` table

Presets for `radar schedule`. Does not start timers by itself.

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `preset` | string | `daily` | `daily` (fixed local time) or `interval` (`interval_seconds`). |
| `at` | string | `08:00` | Local `HH:MM` run time for the `daily` preset. |

## Environment overrides

| Variable | Overrides |
| --- | --- |
| `RADAR_CONFIG` | Default config file path when `--config` is omitted. |
| `RADAR_TITLE` | `title` |
| `RADAR_TOPIC` | `topic` |
| `RADAR_WATCH_TERMS` | `watch_terms` (comma-separated) |
| `RADAR_OUTPUT_PATH` | `output_path` |
| `RADAR_INTERVAL_SECONDS` | `interval_seconds` |
| `RADAR_MAX_ITEMS` | `max_items` |
| `RADAR_SOURCES` | `sources` (comma-separated) |
| `RADAR_CONNECTOR_TIMEOUT_SECONDS` | `connector_timeout_seconds` |
| `RADAR_MEMORY_PATH` | `memory_path` |
| `RADAR_SYNTHESIS_PROVIDER` | `synthesis.provider` |
| `RADAR_SYNTHESIS_MODEL` | `synthesis.model` |
| `RADAR_SYNTHESIS_TIMEOUT_SECONDS` | `synthesis.timeout_seconds` |
| `RADAR_SYNTHESIS_MIN_SOURCE_FAMILIES` | `synthesis.min_source_families` |
| `RADAR_TELEGRAM_CHAT_ID` | `telegram.chat_id` |
| `RADAR_TELEGRAM_TIMEOUT_SECONDS` | `telegram.timeout_seconds` |
| `RADAR_SCHEDULE_PRESET` | `schedule.preset` |
| `RADAR_SCHEDULE_AT` | `schedule.at` |

Synthesis and Telegram credential variables are documented in the README.

## Scheduling helper

Generate host scheduler artifacts from the same config file:

```bash
radar schedule --config examples/radar.toml --format cron
radar schedule --config examples/radar.toml --format systemd --output-dir ./systemd
```

Static examples live in `examples/scheduling/`. See ADR 0006 for preset
trade-offs between cron and systemd.
