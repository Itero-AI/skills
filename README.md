# Itero Skills

A collection of skills for AI coding agents — manage your Itero practice platform (scenarios, scorecards, personas, bulk user imports) AND prep documents for RAG / vector-store ingestion, directly from chat. Installable as a Claude Code plugin; manifest files for Cursor and Codex are included for when those tools support marketplace installs; manual install works everywhere today.

## Contents

- [Skills](#skills)
- [Install](#install)
  - [Automatic — paste a prompt into your agent](#automatic--paste-a-prompt-into-your-agent)
  - [Manual — drag folders](#manual--drag-folders)
  - [Developer — five shell commands](#developer--five-shell-commands)
- [API key](#api-key)
- [Sanity check](#sanity-check)
- [Plugin manifests](#plugin-manifests)

## Skills

| Skill | What it does |
|---|---|
| `learning-paths` | Assign and reassign learning paths and certifications. |
| `manage-users` | Create, update, deactivate, and delete individual users. |
| `personas` | Author Enterprise/B2B and Consumer/B2C personas for practice calls. |
| `scenarios` | Create practice scenarios from playbooks, transcripts, or descriptions. |
| `scorecards` | Build evaluation rubrics from training docs or methodology guides. |
| `upload-users` | Bulk-import a CSV of users into your tenant. |
| `doc-optimizer` | Turn a single PDF / DOCX / TXT into chunk-independent Markdown for RAG. |
| `doc-consolidator` | Collapse many related docs into fewer topic-grouped Markdown files for RAG. |

The Itero skills (`learning-paths`, `manage-users`, `personas`, `scenarios`, `scorecards`, `upload-users`) dry-run changes and wait for your confirmation before writing. The doc-prep skills (`doc-optimizer`, `doc-consolidator`) pause for confirmation before merging or destructive cleanup.

## Install

Three paths — pick whichever fits your audience.

### Automatic — paste a prompt into your agent

Copy the block below, paste it into your AI assistant's chat, press Enter. The agent self-installs. **Your API key never enters chat.**

````
Please install the Itero skills for me. Do these steps in order, asking me to confirm before any step that needs my input:

1. Tell me which AI assistant you are (Claude Code, Cursor, OpenAI Codex, or Google Antigravity) and which OS I'm on (Mac or Windows). Confirm with me before continuing.

2. Download https://github.com/Itero-AI/skills/archive/refs/heads/main.zip and unzip it to a temporary location.

3. Copy every folder inside the unzipped `skills/` directory into the correct global skills folder for your agent on my OS, creating the destination folder if it doesn't exist:
   - Claude Code: `~/.claude/skills/` on Mac, `%USERPROFILE%\.claude\skills\` on Windows
   - Cursor or Codex: `~/.agents/skills/` on Mac, `%USERPROFILE%\.agents\skills\` on Windows
   - Antigravity: `~/.gemini/antigravity/skills/` on Mac, `%USERPROFILE%\.gemini\antigravity\skills\` on Windows

4. Check whether `uv` is installed by running `uv --version`. If it's missing, install it: on Mac/Linux run `brew install uv` (or follow the [official instructions](https://docs.astral.sh/uv/getting-started/installation/)); on Windows run `winget install --id=astral-sh.uv -e` in PowerShell. Confirm `uv --version` prints a version number before continuing. (uv reads each script's inline dependency declaration and creates an isolated environment automatically — there is no separate dependency-install step, and uv will install Python itself if it's missing.)

5. Create a file called `.env` in my current working directory containing exactly this single line — leave the value blank, do NOT ask me for my API key in chat:

   ```
   ITERO_API_KEY=
   ```

   Then tell me the full path to the `.env` file you just created and instruct me to (a) open that file in my IDE's file explorer, (b) click after the equals sign, (c) paste my Itero API key, and (d) save the file.

6. After I confirm I've added my key, list the contents of the destination skills folder to verify all eight skill folders are there. Then tell me to fully restart you and try the message: list my scorecards.
````

After step 5, open the `.env` the agent created in your IDE's file explorer (Cursor / VS Code / Antigravity all show dotfiles by default), paste your key after the `=`, save.

### Manual — drag folders

Non-technical, IDE-only, no terminal required. See [INSTALL.md](INSTALL.md) for the painfully-detailed step-by-step (Mac + Windows × four agents).

> Note: the `doc-optimizer` and `doc-consolidator` skills don't need an API key — they run locally. They DO need `uv` installed (one-time, per machine) so the bundled scripts can fetch their own dependencies.

### Developer — five shell commands

```bash
git clone https://github.com/Itero-AI/skills.git /tmp/itero-skills

# Pick the destination for your agent:
DEST=~/.claude/skills                   # Claude Code
# DEST=~/.agents/skills                 # Cursor or Codex (one path covers both)
# DEST=~/.gemini/antigravity/skills     # Antigravity

mkdir -p "$DEST" && cp -r /tmp/itero-skills/skills/* "$DEST/"
brew install uv 2>/dev/null || true     # install uv if you don't have it
echo "ITERO_API_KEY=$YOUR_KEY" > .env
```

Restart your agent. Done. Each script declares its own Python dependencies inline (PEP 723) and uv resolves them on first run — no global pip pollution, no `requirements.txt` to keep in sync.

Alternative for Claude Code: `/plugin marketplace add Itero-AI/skills` then `/plugin install itero@itero-plugins`.

## API key

Get one at **Settings → API Keys** inside [your Itero account](https://app.iteroapp.ai).

**The key must belong to a user with the Manager role.** The Itero skills (`learning-paths`, `personas`, `scenarios`, `scorecards`, `upload-users`) require Manager-level access against the public API. The doc-prep skills (`doc-optimizer`, `doc-consolidator`) don't need an API key — they run locally. User create/update/delete (the `manage-users` skill) requires an Owner-role key — see that skill's reference.

## Sanity check

Restart your AI assistant and try:

> *list my scorecards*

If you see your scorecards (or "no scorecards yet"), you're done.

## Plugin manifests

This repo is installable as a Claude Code plugin today. Manifest files for Cursor and Codex are included for when those tools support marketplace installs; manual install works everywhere today.

- **Claude Code** — `.claude-plugin/marketplace.json` + `plugin.json` (marketplace install works now)
- **Cursor** — `.cursor-plugin/marketplace.json` + `plugin.json` (manifest included; marketplace install not yet supported by Cursor)
- **OpenAI Codex** — `.codex-plugin/plugin.json` (manifest included; no marketplace.json — Codex doesn't use one yet)
- **Google Antigravity** — no Antigravity-specific marketplace command exists; manual or developer install only

All marketplace manifests use `"source": "./"`. Skills live at `skills/<name>/SKILL.md`.

## License

MIT — see [LICENSE](LICENSE).
