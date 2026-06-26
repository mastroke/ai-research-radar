# ADR 0004: Model-Agnostic Synthesis Backend

## Context

Milestone r4 needs LLM-backed brief generation that works across OpenAI,
Anthropic, and Azure OpenAI with bring-your-own API keys. The product brief
requires compiling findings from two or more source families into a structured
summary, while keeping the existing deterministic compiler as a safe fallback
when credentials are missing or upstream calls fail.

## Decision

Add a `synthesis` package with:

- `SynthesisProvider` — injectable HTTP, best-effort `synthesize()` returning
  `StructuredBrief | None`
- Provider implementations for `openai`, `anthropic`, and `azure`
- `synthesize_brief()` — ranks findings, requires two or more source families
  before calling a provider, and falls back to `compile_brief` output otherwise
- `StructuredBrief` — summary, themes, synthesized items, and markdown renderer

Config exposes an optional `[synthesis]` table plus environment overrides:

- `RADAR_SYNTHESIS_PROVIDER`, `RADAR_SYNTHESIS_MODEL`
- `RADAR_SYNTHESIS_TIMEOUT_SECONDS`, `RADAR_SYNTHESIS_MIN_SOURCE_FAMILIES`
- Provider credentials: `RADAR_OPENAI_API_KEY`, `RADAR_ANTHROPIC_API_KEY`,
  `RADAR_AZURE_OPENAI_API_KEY`, `RADAR_AZURE_OPENAI_ENDPOINT`,
  `RADAR_AZURE_OPENAI_DEPLOYMENT`

The CLI routes all brief emission through `synthesize_brief`. Synthesis stays
disabled until a provider is configured. HTTP uses the standard library to keep
the core package dependency-free.

## Consequences

Cross-source briefs can include an LLM-generated summary and per-item synthesis
when credentials and source diversity are present. Single-source runs and
provider failures keep the prior deterministic markdown shape, so operators see
degraded output instead of a hard error.

The trade-off is a JSON response contract parsed without a schema validator.
Malformed model output triggers fallback rather than partial synthesis. Provider
timeouts share one configurable bound and do not retry across providers in this
milestone.
