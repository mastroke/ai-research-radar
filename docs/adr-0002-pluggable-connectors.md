# ADR 0002: Pluggable Source Connectors

## Context

Roadmap milestone r2 needs live discovery from arXiv, Hacker News, GitHub, and
Hugging Face without coupling the brief compiler to any one API shape. Connectors
must fail gracefully when upstream services are slow or unavailable.

## Decision

Add a `SourceConnector` interface with one implementation per upstream source.
Each connector:

- builds a query from configured `watch_terms`
- fetches with `urllib` and an explicit timeout
- parses into existing `Finding` records
- returns an empty list on network or parse failure

A small registry maps config `sources` names to connector instances. The CLI
merges connector findings with manual seed items before compiling the brief.
HTTP is injectable so unit tests run against recorded fixtures without network
calls.

## Consequences

The brief path can now include live items when sources are configured, while CI
stays deterministic via fixtures. Connectors remain best-effort: one failing
source does not block others or manual seeds.

The trade-off is no deduplication or seen-store yet. Repeated items across runs
are expected until milestone r3 adds file-backed memory.
