# ADR 0006: Scheduling Presets for Host Timers

## Context

Operators who self-host AI Research Radar need a repeatable way to run
`radar once` on a fixed cadence without keeping `radar run` alive in a shell.
Cron and systemd are the common choices on Linux servers, but hand-written unit
files drift from the installed config path and working directory.

Milestone r6 asks for scheduling presets, a `radar schedule` helper, and
documented config options.

## Decision

Add a `[schedule]` config table with two presets:

| Preset | Behavior |
| --- | --- |
| `daily` | Run once per day at a local `at` time (default `08:00`). |
| `interval` | Run on `interval_seconds` from the root config. |

Expose `radar schedule --format cron|systemd` to render a cron line or systemd
unit pair from the resolved config path. The helper always targets
`radar once`, not the long-running `radar run` loop. Optional
`--with-telegram-poll` emits a separate long-running service for
`radar telegram poll`.

Cron rendering is limited to hour-aligned intervals because cron cannot express
arbitrary second-level periods cleanly. Non-hour intervals fall back to systemd
`OnUnitActiveSec`.

Ship static examples under `examples/scheduling/` and document all config keys
in `docs/config.md`.

## Consequences

Operators can generate scheduler artifacts from the same TOML file the CLI
already uses, which keeps paths and intervals consistent. The trade-off is that
cron support is intentionally narrower than systemd; exotic intervals require
systemd or an external orchestrator.

`radar run` remains available for ad hoc loops and smoke tests. Production
scheduling should prefer `radar once` behind a host timer.
