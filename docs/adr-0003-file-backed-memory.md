# ADR 0003: File-Backed Memory Store

## Context

Milestone r3 needs cross-run deduplication so repeated connector fetches do not
re-surface the same links in every brief. The system also needs durable finding
memory so the radar accumulates discovered items instead of treating each run as
stateless.

## Decision

Add a small `MemoryStore` interface with two implementations:

- `FileMemoryStore` — JSON file with `findings` and `seen_urls`
- `NullMemoryStore` — no persistence when `memory_path` is unset

Findings are keyed by normalized URL (trimmed, lowercased, no trailing slash).
The CLI merges incoming findings into the store, compiles the brief from unseen
entries only, marks briefed URLs as seen, and persists atomically via a temp file
rename.

Config exposes optional `memory_path` plus `RADAR_MEMORY_PATH` for environment
overrides. Memory stays disabled by default to preserve pre-r3 behavior.

## Consequences

Repeated runs with the same seed or connector output now emit a "no new items"
brief instead of duplicate signal. Findings remain on disk for future ranking
even after they are marked seen.

The trade-off is a single JSON file per radar instance with no concurrency
locking. Concurrent `radar run` processes against one store can race; a small
deployment should use one writer or separate memory paths.
