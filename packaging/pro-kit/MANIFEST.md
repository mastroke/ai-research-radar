# Radar Pro manifest — free core vs paid kit

Open-core boundary for Gumroad packaging. The MIT repository ships everything
required to run a self-hosted radar. The Pro kit sells operational time-savers,
not runtime secrets.

## Free core (MIT, GitHub)

| Capability | Location |
| --- | --- |
| `radar once` / `radar run` CLI | `src/ai_research_radar/cli.py` |
| TOML config + `RADAR_*` env overrides | `src/ai_research_radar/config.py` |
| arXiv, HN, GitHub, Hugging Face connectors | `src/ai_research_radar/connectors/` |
| Deterministic brief compiler | `src/ai_research_radar/brief.py` |
| File-backed memory | `src/ai_research_radar/memory/` |
| Optional BYOK synthesis (OpenAI, Anthropic, Azure) | `src/ai_research_radar/synthesis/` |
| Telegram delivery + locked commands | `src/ai_research_radar/delivery/` |
| `radar schedule` cron/systemd helper | `src/ai_research_radar/schedule.py` |
| Quickstart examples | `examples/` |

No license key or network callback is required for any of the above.

## Radar Pro kit (paid, Gumroad)

| Asset | Why it is Pro |
| --- | --- |
| Persona configs (`builder`, `researcher`, `investor`) | Curated watch terms, limits, and schedule defaults |
| Prompt packs (`prompts/*.txt`) | Audience-specific synthesis instructions |
| Production scheduling bundle | Hardened systemd/cron templates with operator notes |
| Runbooks | Step-by-step Telegram and host deployment |

Pro does **not** gate connectors, synthesis, Telegram, or scheduling in code.
Buyers pay for curated configs, prompts, and runbooks that shorten setup.

## Upgrade path

1. Install or upgrade the free package from GitHub.
2. Copy Pro files into `~/.config/radar/` or `/etc/radar/` on the host.
3. Re-run `radar schedule` to regenerate timer units from the new config.

Future managed hosting is out of scope for this kit.
