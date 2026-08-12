# Itero Skills

Manage your [Itero](https://iteroapp.ai) sales-practice platform from chat. Install these skills in Claude Code, Cursor, OpenAI Codex, or Google Antigravity, and your AI assistant can build practice scenarios and personas, design and publish scorecards, manage users and learning paths, and — new in v2 — search real conversations, read transcripts, and explain evaluation results criterion by criterion.

Seven skills talk to the Itero public API; two document-preparation skills run entirely on your computer (no API key needed) and prepare files for RAG and vector-store ingestion. MIT-licensed.

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

Do not copy v2 over an existing v1 install — a folder merge can leave the old v1 scripts active. Follow the step-by-step commands in [UPGRADING.md](UPGRADING.md); they back up your six v1 skill folders first, so the upgrade is fully reversible.

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
