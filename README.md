# Itero Skills

A collection of skills for AI coding agents that lets you manage your Itero practice platform — scenarios, scorecards, personas, bulk user imports — directly from chat. Available as a plugin for Claude Code, Cursor, and OpenAI Codex; manual install for Google Antigravity.

## Contents

- [Skills](#skills)
- [Install](#install)
  - [Automatic — paste a prompt into your agent](#automatic-paste-a-prompt-into-your-agent)
  - [Manual — drag folders](#manual-drag-folders)
  - [Developer — five shell commands](#developer-five-shell-commands)
- [API key](#api-key)
- [Sanity check](#sanity-check)
- [Plugin manifests](#plugin-manifests)
- [Multi-tenant](#multi-tenant)
- [Support](#support)

## Skills

| Skill | What it does |
|---|---|
| `scenarios` | Create practice scenarios from playbooks, transcripts, or descriptions. |
| `scorecards` | Build evaluation rubrics from training docs or methodology guides. |
| `personas` | Author Enterprise/B2B and Consumer/B2C personas for practice calls. |
| `upload-users` | Bulk-import a CSV of users into your tenant. |

Every skill dry-runs changes and waits for your confirmation before writing.

## Install

Three paths — pick whichever fits your audience.

### Automatic — paste a prompt into your agent

Copy the block below, paste it into your AI assistant's chat, press Enter. The agent self-installs. **Your API key never enters chat.**

````
Please install the Itero skills for me. Do these steps in order, asking me to confirm before any step that needs my input:

1. Tell me which AI assistant you are (Claude Code, Cursor, OpenAI Codex, or Google Antigravity) and which OS I'm on (Mac or Windows). Confirm with me before continuing.

2. Download https://github.com/Itero-AI/skills/archive/refs/heads/main.zip and unzip it to a temporary location.

3. Copy the four folders inside the unzipped `skills/` directory (`scenarios`, `scorecards`, `personas`, `upload-users`) into the correct global skills folder for your agent on my OS, creating the destination folder if it doesn't exist:
   - Claude Code: `~/.claude/skills/` on Mac, `%USERPROFILE%\.claude\skills\` on Windows
   - Cursor or Codex: `~/.agents/skills/` on Mac, `%USERPROFILE%\.agents\skills\` on Windows
   - Antigravity: `~/.gemini/antigravity/skills/` on Mac, `%USERPROFILE%\.gemini\antigravity\skills\` on Windows

4. Run `pip3 install requests python-dotenv` and confirm both installed successfully. If `pip3` isn't installed, tell me to install Python from https://python.org first and pause.

5. Create a file called `.env` in my current working directory containing exactly this single line — leave the value blank, do NOT ask me for my API key in chat:

   ```
   ITERO_API_KEY=
   ```

   Then tell me the full path to the `.env` file you just created and instruct me to (a) open that file in my IDE's file explorer, (b) click after the equals sign, (c) paste my Itero API key, and (d) save the file.

6. After I confirm I've added my key, list the contents of the destination skills folder to verify all four skill folders are there. Then tell me to fully restart you and try the message: list my scorecards.
````

After step 5, open the `.env` the agent created in your IDE's file explorer (Cursor / VS Code / Antigravity all show dotfiles by default), paste your key after the `=`, save.

> *Screenshot: VS Code / Cursor with `.env` open, `ITERO_API_KEY=` and cursor positioned right after the equals sign.*

### Manual — drag folders

Non-technical, IDE-only, no terminal required. See [INSTALL.md](INSTALL.md) for the painfully-detailed step-by-step (Mac + Windows × four agents, with screenshots).

### Developer — five shell commands

```bash
git clone https://github.com/Itero-AI/skills.git /tmp/itero-skills

# Pick the destination for your agent:
DEST=~/.claude/skills                   # Claude Code
# DEST=~/.agents/skills                 # Cursor or Codex (one path covers both)
# DEST=~/.gemini/antigravity/skills     # Antigravity

mkdir -p "$DEST" && cp -r /tmp/itero-skills/skills/* "$DEST/"
pip3 install requests python-dotenv
echo "ITERO_API_KEY=$YOUR_KEY" > .env
```

Restart your agent. Done.

Alternative for Claude Code: `/plugin marketplace add Itero-AI/skills` then `/plugin install itero@itero-plugins`.

## API key

Get one at **Settings → API Keys** inside [your Itero account](https://app.iteroapp.ai).

**The key must belong to a user with the Manager role.** All four skills require Manager-level access against the public API.

## Sanity check

Restart your AI assistant and try:

> *list my scorecards*

If you see your scorecards (or "no scorecards yet"), you're done.

## Plugin manifests

This repo serves as a plugin for multiple agents:

- **Claude Code** — `.claude-plugin/marketplace.json` + `plugin.json`
- **Cursor** — `.cursor-plugin/marketplace.json` + `plugin.json`
- **OpenAI Codex** — `.codex-plugin/plugin.json` (no marketplace.json — Codex doesn't use one)
- **Google Antigravity** — no Antigravity-specific marketplace command exists; manual or developer install only

All marketplace manifests use `"source": "./"`. Skills live at `skills/<name>/SKILL.md`.

## Multi-tenant

Add per-tenant keys to `.env`:

```
ITERO_API_KEY_PROD=...
ITERO_API_KEY_STAGING=...
```

Then invoke skills with `--tenant PROD` or `--tenant STAGING`. Without the flag, skills use bare `ITERO_API_KEY`.

## Support

- Issues: https://github.com/Itero-AI/skills/issues
- Email: support@iteroapp.ai

## License

MIT — see [LICENSE](LICENSE).
