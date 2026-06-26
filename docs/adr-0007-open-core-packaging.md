# ADR 0007: Open-core packaging and Radar Pro kit

## Context

Milestone r7 needs public docs, example briefs, and a Gumroad-ready Pro kit
without hiding connectors, synthesis, or Telegram behind a license gate in code.

## Decision

- Ship the full CLI under MIT on GitHub (free core).
- Package paid value as `packaging/pro-kit/`: persona configs, prompt packs,
  production runbooks, and hardened scheduling templates.
- Document the boundary in `packaging/pro-kit/MANIFEST.md` and the README.
- Build Gumroad archives with `packaging/pro-kit/build-archive.sh` (no secrets).

Pro buyers install the same PyPI/GitHub package; they overlay curated files.

## Consequences

- No runtime license check or feature flags in this milestone.
- Pro prompt packs are files today; a future `prompt_pack` config hook can load
  them without changing the monetization boundary.
- Example briefs live under `examples/briefs/` (not gitignored runtime `briefs/`).
- Screenshots in `docs/screenshots/` are static SVG for README portability.

## Alternatives considered

- Gating Telegram or synthesis in code — rejected; contradicts open-core distribution goals.
- Shipping Pro as a private repo — rejected; harder to keep in sync with the MIT core.
