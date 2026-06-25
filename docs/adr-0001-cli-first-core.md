# ADR 0001: Start With a CLI-First Core

## Context

AI Research Radar needs connectors, memory, synthesis, scheduling, and Telegram
delivery. Building those all at once would make the first version hard to test
and easy to overfit around external services.

The first roadmap milestone asks for a standalone package and CLI skeleton with
config via environment or file. That boundary can be useful immediately if it
produces a deterministic brief from seed items.

## Decision

The first version exposes a `radar` CLI with two commands:

- `radar once` compiles one markdown brief from configured seed items.
- `radar run` repeats the same operation on the configured interval.

Configuration is loaded from a TOML file and `RADAR_*` environment variables.
The brief compiler is standard-library only, deterministic, and does not call
network services or LLM APIs.

## Consequences

This keeps the MVP runnable in CI and useful for local research notes without
credentials. It also leaves clean extension points for source connectors,
file-backed memory, model-agnostic synthesis, and Telegram delivery.

The trade-off is that this release is not yet an autonomous scout. It is the
production-shaped command and package boundary that future milestones build on.
