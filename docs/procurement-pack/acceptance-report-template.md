# Agent acceptance report (template)

> Copy this template or generate automatically via `aak baseline run --report-md`.

## Engagement metadata

| Field | Value |
| --- | --- |
| Vendor / agent product | _TBD_ |
| Evaluation owner | _TBD_ |
| Frozen probe version | _e.g. 1.0.0_ |
| Layer A (agent endpoint) | _URL + build ID_ |
| Layer B (raw pinned API) | _model name + snapshot date_ |
| Run date (UTC) | _ISO-8601_ |

## Executive summary

_One paragraph: overall verdict, pass rates, and whether agent layer adds value or
introduces regressions._

**Overall classification:** `_baseline_met | agent_value_add | agent_regression | shared_failure | partial_agent_`

## Cross-layer scorecard

| Metric | Layer A (agent) | Layer B (raw API) |
| --- | ---: | ---: |
| Pass rate | _0%_ | _0%_ |
| Baseline met (both pass) | _n_ | — |
| Agent value-add (A pass, B fail) | _n_ | — |
| Agent regression (B pass, A fail) | _n_ | — |
| Shared failure (both fail) | _n_ | — |
| Total probes | _n_ | _n_ |

## Suite results

### RAG (`rag` v1.0.0)

_Suite verdict and narrative._

| Probe | Layer A | Layer B | Attribution |
| --- | --- | --- | --- |
| rag-citation-001 | _pass/fail_ | _pass/fail_ | _classification_ |

### Tool use (`tool_use` v1.0.0)

| Probe | Layer A | Layer B | Attribution |
| --- | --- | --- | --- |
| tool-calendar-001 | _pass/fail_ | _pass/fail_ | _classification_ |

### Coding agent (`coding_agent` v1.0.0)

| Probe | Layer A | Layer B | Attribution |
| --- | --- | --- | --- |
| code-patch-001 | _pass/fail_ | _pass/fail_ | _classification_ |

## Layer attribution narrative

_Describe where the agent stack helped (retrieval, tools, multi-step coding) and
where it regressed versus the raw model._

## Acceptance recommendation

- [ ] **Accept** — baseline met, no agent regressions
- [ ] **Accept with conditions** — list remediation items
- [ ] **Reject** — shared failures or material agent regressions

## Sign-off

| Role | Name | Date |
| --- | --- | --- |
| Engineering | | |
| Security / compliance | | |
| Procurement | | |

---

_Generated with [agent-acceptance-kit](https://github.com/mastroke/agent-acceptance-kit). Not legal advice._
