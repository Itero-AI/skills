# Itero Skills

A public, MIT-licensed collection of skills for AI coding agents. The seven Itero platform skills use the unified API gateway at `https://iterogatewayapi.azurewebsites.net`; two document-preparation skills run entirely on your computer.

Install the collection in Claude Code, Cursor, OpenAI Codex, or Google Antigravity to manage Itero from chat, review conversations and transcripts, or prepare documents for RAG and vector-store ingestion.

## Contents

- [Skills](#skills)
- [Install](#install)
- [API key](#api-key)
- [Upgrade from v1](#upgrade-from-v1)
- [Sanity check](#sanity-check)
- [Plugin manifests](#plugin-manifests)

## Skills

| Skill | What it does |
|---|---|
| `personas` | Create and manage Enterprise/B2B and Consumer/B2C personas. |
| `scenarios` | Create and manage practice scenarios from playbooks, transcripts, or descriptions. |
| `scorecards` | Build, inspect, and publish evaluation scorecards. |
| `learning-paths` | Inspect learning paths and certifications, then assign or reassign them. |
| `manage-users` | List, create, update, activate, deactivate, and delete individual users. |
| `upload-users` | Validate and bulk-import a CSV of users. |
| `conversations` | Search calls, read transcripts and evaluation results, tag calls, and start evaluations. |
| `doc-optimizer` | Turn one PDF, DOCX, or TXT file into chunk-independent Markdown for RAG. |
| `doc-consolidator` | Collapse related documents into fewer topic-grouped Markdown files for RAG. |

Before any API write, the Itero platform skills show the exact request and wait for explicit confirmation. The document-preparation skills also confirm before merging files or removing temporary work.

## Install

Choose any of these three paths. If you already installed v1, use [Upgrade from v1](#upgrade-from-v1) so the old HTTP clients are not merged into v2.

### Automatic — paste a prompt into your agent

Copy the block below into your AI assistant. Your API key never enters chat.

````text
Please install the Itero skills for me. Follow these steps in order and ask me before anything needs my input:

1. Identify which assistant you are (Claude Code, Cursor, OpenAI Codex, or Google Antigravity) and whether this is Mac or Windows. Confirm that with me.
2. Download https://github.com/Itero-AI/skills/archive/refs/heads/main.zip and unzip it in a temporary location.
3. Copy all nine folders from the downloaded `skills/` directory into the correct global skills directory, creating it if needed:
   - Claude Code: `~/.claude/skills/` on Mac or `%USERPROFILE%\.claude\skills\` on Windows
   - Cursor or Codex: `~/.agents/skills/` on Mac or `%USERPROFILE%\.agents\skills\` on Windows
   - Antigravity: `~/.gemini/antigravity/skills/` on Mac or `%USERPROFILE%\.gemini\antigravity\skills\` on Windows
4. Check `uv --version` only if I plan to use `scorecards`, `upload-users`, `doc-optimizer`, or `doc-consolidator`. If uv is missing, help me install it from https://docs.astral.sh/uv/getting-started/installation/ and verify the installation.
5. If it does not already exist, create `.env` in my current working directory with this line, leaving the value blank. Never ask me to paste the key into chat:

   ```text
   ITERO_API_KEY=
   ```

   Tell me the full path and ask me to paste my Itero API key after the equals sign in my editor, save the file, and confirm when that is done.
6. Verify that the destination contains these nine folders: `personas`, `scenarios`, `scorecards`, `learning-paths`, `manage-users`, `upload-users`, `conversations`, `doc-optimizer`, and `doc-consolidator`. Then ask me to restart the assistant and try: list my scorecards.
````

### Manual — drag folders

Follow the beginner-friendly [manual installation guide](INSTALL.md) for Mac and Windows. It covers all four supported assistants without requiring terminal experience.

### Developer — Bash shell commands

Run this in Bash on macOS or Linux. On Windows, use Git Bash or choose the automatic or manual path above. Set the destination to the global skills directory for your assistant, then run:

```bash
git clone https://github.com/Itero-AI/skills.git /tmp/itero-skills
ITERO_SKILLS_SOURCE="/tmp/itero-skills"
ITERO_SKILLS_DEST="/absolute/path/to/your/agent/skills"
mkdir -p "$ITERO_SKILLS_DEST"
cp -R "$ITERO_SKILLS_SOURCE/skills/." "$ITERO_SKILLS_DEST/"
test -e .env || printf 'ITERO_API_KEY=\n' > .env
```

Use `~/.claude/skills`, `~/.agents/skills`, or `~/.gemini/antigravity/skills` as the destination on macOS, Linux, or Git Bash. Git Bash accepts paths beneath `/c/Users/<your-name>/`; PowerShell and Command Prompt do not run this block.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) only if you use `scorecards`, `upload-users`, `doc-optimizer`, or `doc-consolidator`. Their scripts declare dependencies inline and uv resolves them on first run.

Claude Code can alternatively install the plugin with `/plugin marketplace add Itero-AI/skills` followed by `/plugin install itero@itero-plugins`.

## API key

Get a key from **Settings → API Keys** in [Itero](https://app.iteroapp.ai), then save it as `ITERO_API_KEY` in the `.env` file for the project where you use your agent. The skills send it to the unified gateway in the `X-API-Key` header and never print it.

Role note: Manager keys can use most platform workflows; user create, update, and delete operations have been observed to require an Owner key.

The `doc-optimizer` and `doc-consolidator` skills do not use an Itero API key.

## Upgrade from v1

Do not copy v2 over an existing v1 install. A folder merge can leave the six old HTTP-client copies active. The commands below first move exactly the six v1 API-skill folders to reversible backups, then copy clean v2 replacements plus the new `conversations` skill. The two document-preparation skills are unchanged and stay in place.

Open a Bash or Zsh shell in your current v2 clone. Set `ITERO_SKILLS_DEST` to the absolute skills-directory path for your assistant before running the block.

```bash
set -eu
ITERO_SKILLS_SOURCE="$(git rev-parse --show-toplevel)"
ITERO_SKILLS_DEST="/absolute/path/to/your/agent/skills"

test -f "$ITERO_SKILLS_SOURCE/README.md"
test -d "$ITERO_SKILLS_DEST"
test "$ITERO_SKILLS_DEST" != "/"
test ! -e "$ITERO_SKILLS_DEST/personas.v1.bak"
test ! -e "$ITERO_SKILLS_DEST/scenarios.v1.bak"
test ! -e "$ITERO_SKILLS_DEST/scorecards.v1.bak"
test ! -e "$ITERO_SKILLS_DEST/learning-paths.v1.bak"
test ! -e "$ITERO_SKILLS_DEST/manage-users.v1.bak"
test ! -e "$ITERO_SKILLS_DEST/upload-users.v1.bak"
test ! -e "$ITERO_SKILLS_DEST/conversations"

mv "$ITERO_SKILLS_DEST/personas" "$ITERO_SKILLS_DEST/personas.v1.bak"
mv "$ITERO_SKILLS_DEST/scenarios" "$ITERO_SKILLS_DEST/scenarios.v1.bak"
mv "$ITERO_SKILLS_DEST/scorecards" "$ITERO_SKILLS_DEST/scorecards.v1.bak"
mv "$ITERO_SKILLS_DEST/learning-paths" "$ITERO_SKILLS_DEST/learning-paths.v1.bak"
mv "$ITERO_SKILLS_DEST/manage-users" "$ITERO_SKILLS_DEST/manage-users.v1.bak"
mv "$ITERO_SKILLS_DEST/upload-users" "$ITERO_SKILLS_DEST/upload-users.v1.bak"

cp -R "$ITERO_SKILLS_SOURCE/skills/personas" "$ITERO_SKILLS_DEST/personas"
cp -R "$ITERO_SKILLS_SOURCE/skills/scenarios" "$ITERO_SKILLS_DEST/scenarios"
cp -R "$ITERO_SKILLS_SOURCE/skills/scorecards" "$ITERO_SKILLS_DEST/scorecards"
cp -R "$ITERO_SKILLS_SOURCE/skills/learning-paths" "$ITERO_SKILLS_DEST/learning-paths"
cp -R "$ITERO_SKILLS_SOURCE/skills/manage-users" "$ITERO_SKILLS_DEST/manage-users"
cp -R "$ITERO_SKILLS_SOURCE/skills/upload-users" "$ITERO_SKILLS_DEST/upload-users"
cp -R "$ITERO_SKILLS_SOURCE/skills/conversations" "$ITERO_SKILLS_DEST/conversations"
```

Confirm that the six backups exist before removing or replacing anything else:

```bash
ls -d "$ITERO_SKILLS_DEST"/*.v1.bak
```

To restore v1, first print and inspect `ITERO_SKILLS_DEST`, verify that it is the intended skills directory, and verify all six backup folders exist. Then run these exact restore commands:

```bash
set -eu
printf '%s\n' "$ITERO_SKILLS_DEST"
test -n "$ITERO_SKILLS_DEST" && test "$ITERO_SKILLS_DEST" != "/"
test -d "$ITERO_SKILLS_DEST/personas.v1.bak"
test -d "$ITERO_SKILLS_DEST/scenarios.v1.bak"
test -d "$ITERO_SKILLS_DEST/scorecards.v1.bak"
test -d "$ITERO_SKILLS_DEST/learning-paths.v1.bak"
test -d "$ITERO_SKILLS_DEST/manage-users.v1.bak"
test -d "$ITERO_SKILLS_DEST/upload-users.v1.bak"

rm -rf "$ITERO_SKILLS_DEST/personas" && mv "$ITERO_SKILLS_DEST/personas.v1.bak" "$ITERO_SKILLS_DEST/personas"
rm -rf "$ITERO_SKILLS_DEST/scenarios" && mv "$ITERO_SKILLS_DEST/scenarios.v1.bak" "$ITERO_SKILLS_DEST/scenarios"
rm -rf "$ITERO_SKILLS_DEST/scorecards" && mv "$ITERO_SKILLS_DEST/scorecards.v1.bak" "$ITERO_SKILLS_DEST/scorecards"
rm -rf "$ITERO_SKILLS_DEST/learning-paths" && mv "$ITERO_SKILLS_DEST/learning-paths.v1.bak" "$ITERO_SKILLS_DEST/learning-paths"
rm -rf "$ITERO_SKILLS_DEST/manage-users" && mv "$ITERO_SKILLS_DEST/manage-users.v1.bak" "$ITERO_SKILLS_DEST/manage-users"
rm -rf "$ITERO_SKILLS_DEST/upload-users" && mv "$ITERO_SKILLS_DEST/upload-users.v1.bak" "$ITERO_SKILLS_DEST/upload-users"
```

The restore commands leave `conversations` installed because v1 has no folder to restore for it. Remove that folder only after verifying the destination path if you want an exact v1-only set.

## Sanity check

Restart your AI assistant and ask:

> *list my scorecards*

If you see your scorecards, or a message saying there are none yet, installation is complete.

## Plugin manifests

Claude Code can install this repository as a plugin today. Cursor and Codex manifests are included for their plugin systems; manual installation works everywhere.

- Claude Code uses `.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json`.
- Cursor uses `.cursor-plugin/marketplace.json` and `.cursor-plugin/plugin.json`.
- OpenAI Codex uses `.codex-plugin/plugin.json`.
- Google Antigravity uses the manual or developer path.

All plugin sources point at the repository root. Skills live at `skills/<name>/SKILL.md`.

## License

MIT — see [LICENSE](LICENSE).
