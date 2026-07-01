# Sample clause snippets (not legal advice)

Engineering-oriented language you can adapt when requiring cross-layer agent
acceptance evidence in RFPs, pilot SOWs, or internal platform reviews.

---

## 1. Frozen probe baseline requirement

> Vendor shall execute the buyer-provided **Agent Acceptance Kit** probe suites
> (or equivalent frozen harness approved in writing) against **Layer A** (vendor's
> full agent endpoint as deployed for the pilot) and **Layer B** (a pinned raw
> model API specified by buyer). Both layers shall use the **identical probe set
> and version** without mid-evaluation changes to scoring rules.

## 2. Layer attribution deliverable

> Vendor shall deliver a machine-readable baseline JSON and human-readable
> acceptance report including **per-probe layer attribution** classifying outcomes
> as baseline met, agent value-add, agent regression, or shared failure. Reports
> shall be reproducible from documented CLI invocations (`aak baseline run`).

## 3. Starter capability coverage

> Minimum pilot coverage shall include three starter suites: **RAG** (context
> citation), **tool use** (external action affordances), and **coding agent**
> (patch + test awareness). Additional suites may be appended by buyer with
> version bumps to the frozen probe manifest.

## 4. Acceptance thresholds (example)

> Pilot acceptance requires: (a) zero **agent regression** probes, (b) at least
> 80% **baseline met** or **agent value-add** classifications overall, and (c) no
> **shared failure** on safety-tagged probes. Thresholds are illustrative — set
> numeric gates to match risk tier.

## 5. Evidence retention

> Vendor shall retain request/response traces for failed probes for **90 days**,
> redacted per buyer policy, sufficient for buyer to rerun attribution locally
> using agent-acceptance-kit or compatible tooling.

## 6. Model pin and change control

> Layer B shall use a **pinned model snapshot** documented in the acceptance
> report. Upgrades to Layer A or Layer B during evaluation require a **new
> baseline run** and written comparison to the prior frozen result.

---

**Disclaimer:** These snippets are sample engineering procurement text only. They
do not constitute legal advice. Consult qualified counsel before inclusion in
binding agreements.
