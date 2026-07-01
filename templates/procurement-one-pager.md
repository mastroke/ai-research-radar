# Agent Handoff Baseline — Procurement one-pager

## What you are buying

A **deterministic acceptance gate** for AI agent handoffs: frozen multi-turn
scenarios, pass/fail regression scoring, and a client-ready sign-off report.

| Item | OSS (free) | Agency Handoff Pack ($49) |
| --- | --- | --- |
| CLI baseline runner | Yes | Yes + curated scenario library |
| Sign-off report generator | Yes | Yes + branded report template |
| Sample support-agent scenarios | 3 scenarios | 12+ scenarios + SOW snippets |
| Live LLM / tool replay | No | No |
| Production monitoring | No | Optional services engagement |

## Why it exists

Agencies ship agents; clients need proof the handoff did not regress prompts,
tools, memory isolation, or retrieval. This kit turns that proof into a repeatable
CLI workflow instead of a one-off demo.

## How acceptance works

```bash
pip install agent-handoff-kit
agent-handoff baseline run --config scenarios/support-agent/scenarios.yaml
agent-handoff report generate --client-name "Acme Corp"
```

Exit code 0 = all layers pass. Non-zero = blocked until fixed or waived.

## Honest limits

- Replays **frozen transcripts**, not live model calls.
- Retrieval checks compare fixture source lists, not embedding quality.
- Memory bleed uses heuristic substring checks, not formal isolation proofs.

## Vendor

Built by Masoob ([github.com/mastroke](https://github.com/mastroke)). MIT-licensed OSS
core; paid pack adds templates and extended scenarios for agency workflows.
