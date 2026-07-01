# Agency SOW snippet — Agent handoff acceptance

Include the following acceptance block in your Statement of Work when delivering
an AI support agent to a client.

---

## Deliverable: Agent handoff baseline pack

**Scope.** Vendor delivers a frozen multi-turn baseline (`scenarios.yaml`) covering
at least three production-representative flows, plus a deterministic regression run
and client sign-off report.

**Acceptance criteria.**

1. `agent-handoff baseline run --config scenarios.yaml` exits 0 with all scenarios
   passing across four layers: prompt drift, tool call/schema, memory bleed, retrieval.
2. `agent-handoff report generate` produces a Markdown sign-off report with executive
   summary, per-layer results, and known limitations.
3. Client receives editable scenario fixtures and documentation to extend baselines
   without vendor lock-in.

**Out of scope (unless separately scoped).** Live LLM latency tuning, production
observability, security penetration testing, and custom connector development.

**Sign-off.** Client approves handoff when baseline run is green and report is
delivered. Failures block release until remediated or explicitly waived in writing.

---

_Customize dollar amounts, SLA windows, and scenario count to match your engagement._
