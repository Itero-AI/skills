# Itero Skills for Claude Code

Official Itero plugin for Claude Code. Manage your practice platform from any Claude Code session — build scenarios from sales playbooks, design scorecards from training docs, author personas from customer materials, and bulk-import users from CSV.

## What's in the box

| Skill | What it does |
|---|---|
| **`/scenarios`** | Create, edit, delete practice scenarios. Build from a customer roleplay doc, sales playbook, or call transcript. Batch-create multiple scenarios from one source. |
| **`/scorecards`** | Build and edit scorecard templates, categories, criteria, and rubrics. Author from training materials or methodology docs. |
| **`/personas`** | Create and manage AI personas — the counterparties used in practice calls. Supports both Enterprise/B2B archetypes (CFO, VP Finance, Procurement) and Consumer/B2C archetypes (Medicare members, patients, individual buyers). |
| **`/upload-users`** | Bulk-import users into your tenant from a CSV. Walks through validation fixes, user-group decisions, duplicate detection, and a seat-count check before submitting. |

Every skill walks you through the workflow interactively, dry-runs every change, and only writes after explicit confirmation.

## Install

In Claude Code:

```
/plugin marketplace add Itero-AI/skills
/plugin install itero@itero-plugins
```

Then install the two Python dependencies the skills use:

```bash
pip3 install -r ${CLAUDE_PLUGIN_ROOT}/requirements.txt
```

If `${CLAUDE_PLUGIN_ROOT}` doesn't expand in your shell, run this instead:

```bash
pip3 install requests python-dotenv
```

## Setup

Create a `.env` file in your project's root directory and add your Itero API key:

```
ITERO_API_KEY=<your-api-key>
```

Optional — if you want the `upload-users` skill to pre-flight check your seat cap before importing, also add:

```
ITERO_TENANT_SEATS=<your-seat-count>
```

That's it. Run any `/itero:*` command in Claude Code and the skills will pick up the key automatically.

## Multiple tenants

If you manage more than one Itero tenant from the same project, use the `--tenant <NAME>` flag and add per-tenant keys to `.env`:

```
ITERO_API_KEY_PROD=<production-key>
ITERO_API_KEY_STAGING=<staging-key>
```

Then invoke skills with `--tenant PROD` or `--tenant STAGING`. Without the flag, the skills use bare `ITERO_API_KEY`.

## Where to get an API key

API keys are managed in the Itero web app under **Settings → API Keys**. The key needs to belong to a user with the **Manager** role for `upload-users` to work; the other three skills work with any role.

## Support

Questions, bugs, feature requests: **support@iteroapp.ai**

## License

MIT — see [LICENSE](LICENSE).
