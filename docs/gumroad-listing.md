# Agency Handoff Pack — Gumroad listing copy

## Product title

**Agency Handoff Pack — Deterministic agent sign-off for client delivery ($49)**

## Short description

Stop shipping AI agents on vibes. Run frozen multi-turn baselines, score four
regression layers, and hand clients a Markdown sign-off report — in minutes, from
the CLI.

## Long description

You built the agent. The client wants proof it still behaves after handoff.

The **Agency Handoff Pack** bundles everything an agency needs to close an AI
support-agent (or similar) engagement with a deterministic acceptance gate:

- **12+ curated scenarios** beyond the OSS sample (billing, auth, escalation, edge cases)
- **Branded sign-off report template** with executive summary and known-limitations section
- **Agency SOW snippet** and **procurement one-pager** ready to paste into contracts
- **Runbook**: baseline → report → client sign-off in under 15 minutes

The OSS [Agent Handoff Kit](https://github.com/mastroke/agent-handoff-kit) CLI is
free and MIT-licensed. This pack is for teams who want done-for-you scenarios and
delivery templates, not another framework to maintain.

### What you run

```bash
agent-handoff baseline run --config scenarios.yaml
agent-handoff report generate --client-name "Client Name"
```

Four regression layers, deterministic pass/fail:

1. **Prompt drift** — system prompt matches frozen baseline
2. **Tool call / schema** — calls and required args match fixture schema
3. **Memory bleed** — forbidden cross-session fragments absent from context
4. **Retrieval miss** — required knowledge sources present in frozen retrieval set

### What this is not

- Not a live LLM evaluation platform
- Not production observability or A/B testing
- Not a substitute for security review

We say that upfront because honest scope beats oversold AI QA tools.

## Price

**$49** — one-time purchase, updates for 12 months.

## FAQ

**Do I need an API key?**  
No. Everything replays frozen fixtures offline.

**Can I use this for non-support agents?**  
Yes. Scenarios are YAML — swap prompts, tools, and retrieval fixtures for your domain.

**How is this different from the free GitHub repo?**  
The OSS repo includes the CLI, tests, three sample scenarios, and basic templates.
The pack adds extended scenarios, branded report styling, and agency-ready contract snippets.

**What Python version?**  
3.11+

**Refund policy?**  
30-day refund if the pack does not run as documented on Python 3.11+.

**Who built this?**  
Masoob ([@mastroke](https://github.com/mastroke)) — CLI-first tooling for agent delivery teams.

## Screenshot placeholders

<!-- Replace with actual screenshots before publishing -->

![Baseline run terminal output](screenshots/baseline-run.png)

_Caption: `agent-handoff baseline run` showing PASS across four layers._

![Sign-off report preview](screenshots/handoff-report.png)

_Caption: Generated Markdown report with executive summary and per-scenario detail._

![Scenario YAML excerpt](screenshots/scenarios-yaml.png)

_Caption: Frozen multi-turn scenario with cross-layer checks._

## Tags (Gumroad)

agents, ai, agency, handoff, qa, cli, python, support-bot, deliverables

## License note for listing footer

OSS CLI: MIT. Pack content (extended scenarios + branded templates): licensed for
purchaser use on client projects; no redistribution.
