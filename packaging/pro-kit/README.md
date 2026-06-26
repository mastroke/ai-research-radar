# Radar Pro kit

Paid extras for [AI Research Radar](https://github.com/mastroke/ai-research-radar).
Install the free MIT core first, then overlay this directory.

## What you get

| Asset | Purpose |
| --- | --- |
| `configs/` | Persona presets (builder, researcher, investor) with synthesis and schedule blocks |
| `prompts/` | Curated synthesis prompt packs tuned per audience |
| `scheduling/` | Production systemd and cron templates with hardening notes |
| `runbooks/` | Telegram setup and host deployment steps |

See [MANIFEST.md](MANIFEST.md) for the free-core boundary.

## Install

```bash
# 1. Install the free core from GitHub
python -m pip install "git+https://github.com/mastroke/ai-research-radar.git"

# 2. Copy a persona config
mkdir -p ~/.config/radar
cp packaging/pro-kit/configs/builder.toml ~/.config/radar/radar.toml

# 3. Set credentials (BYOK)
export RADAR_OPENAI_API_KEY="..."
# optional delivery
export RADAR_TELEGRAM_BOT_TOKEN="..."
export RADAR_TELEGRAM_CHAT_ID="123456789"

# 4. Smoke test
radar once --config ~/.config/radar/radar.toml
```

Full host steps: [runbooks/production-deploy.md](runbooks/production-deploy.md).

## Prompt packs

Pro prompt files under `prompts/` are drop-in replacements for the default
synthesis instruction. Wire them by copying the text into your provider
workflow or a future `prompt_pack` config hook. Each file documents audience,
ranking bias, and JSON output shape.

## Gumroad archive

From the repository root:

```bash
./packaging/pro-kit/build-archive.sh
```

Produces `dist/radar-pro-kit.tar.gz` for upload.
