---
name: learning-paths
description: |
  Lists Itero learning paths and certifications and assigns or reassigns them
  to users via the public API. Use when someone wants to: see what learning
  paths or certifications exist on the tenant, see who a path is assigned to,
  assign a learning path or certification to one or more reps, reassign one
  (e.g. a retake after a failed certification), or set a due date. Triggers
  on: "assign the learning path", "assign the certification", "who has this
  path", "reassign", "give the new reps the onboarding path", "list learning
  paths", "set a due date for the certification".
user-invocable: true
references:
    - learning-path-api.md
---

# Learning Paths Skill

Assign and reassign Itero learning paths and certifications to tenant users via
the public API. Backed by `scripts/learning_paths.py`.

---

## Running the scripts

`<skill-dir>` below means the folder containing this SKILL.md (announced when the
skill loads). Under a Claude Code plugin install this is the `skills/learning-paths`
subfolder of the plugin root; under a manual install it is the skill folder
inside your agent's skills directory. All scripts run via `uv run` —
dependencies resolve automatically (PEP 723).

---

## Scope

**This skill assigns and reassigns. Creating or editing learning paths is
Studio-only; there is no public API for it — do not promise otherwise.**

---

## Authentication

Reads `ITERO_API_KEY` from `.env`. For multi-tenant repos, pass `--tenant <NAME>`
to use `ITERO_API_KEY_<NAME>` instead.

```bash
uv run "<skill-dir>/scripts/learning_paths.py" list [--tenant NAME]
```

---

## API reference

| Need | Where |
|---|---|
| Full response schemas / DTO fields | [learning-path-api.md](references/learning-path-api.md) — "Response Schemas" |
| Assign vs. reassign semantics | [learning-path-api.md](references/learning-path-api.md) — "Assign vs. Reassign Semantics" |
| `tenantUserId` vs `id` trap | [learning-path-api.md](references/learning-path-api.md) — "`tenantUserId` — not `id`" |
| Status enum meanings | [learning-path-api.md](references/learning-path-api.md) — "Enums" |
| Error codes | [learning-path-api.md](references/learning-path-api.md) — "Errors" |

---

## Flow 1 — List learning paths

```bash
uv run "<skill-dir>/scripts/learning_paths.py" list [--type 0|1] [--tenant NAME]
```

`--type` filters by kind:
- `0` — Learning Path (standard, untimed)
- `1` — Certification (pass thresholds enforced; may be retriable)

Omit `--type` to see everything. Output shows id, type label, title, stage
count, ordered flag, and retriable flag. Run this first whenever the user asks
what paths exist or before any assign/reassign operation.

---

## Flow 2 — Inspect assignments on a path

```bash
uv run "<skill-dir>/scripts/learning_paths.py" fetch <id> [--tenant NAME]
```

Returns the full details JSON: stages (ordered list of practice scenario
references) plus all current assignments with `tenantUserId`, `dueDate`, and
`status`. Status values (0–5) are integers; for what each means (New,
InProgress, Overdue, Completed, Failed, Canceled) route to the reference:
[learning-path-api.md](references/learning-path-api.md) — "Enums".

---

## Flow 3 — Assign users to a learning path

Follow these steps in order.

### Step 1 — List paths

```bash
uv run "<skill-dir>/scripts/learning_paths.py" list [--tenant NAME]
```

Confirm the path id with the user before proceeding.

### Step 2 — Resolve tenantUserId values

```bash
uv run "<skill-dir>/scripts/learning_paths.py" users [--role Representative|Manager] [--active true|false] [--tenant NAME]
```

**Critical — two-ID trap.** The tenant user record exposes two integers: `id`
and `tenantUserId`. Assignment requires `tenantUserId`, NOT `id`. Passing `id`
will silently target the wrong user or produce a `400`. The `users` subcommand
prints both side-by-side and labels the columns so there is no ambiguity.

### Step 3 — Show a preview and get approval

Before any API call, show the user a preview table:

| Path title | Users (name) | Due date |
|---|---|---|
| \<title from list\> | \<names from users output\> | \<YYYY-MM-DD or none\> |

Wait for explicit yes before continuing.

### Step 4 — Dry-run

```bash
uv run "<skill-dir>/scripts/learning_paths.py" assign <id> --user-ids <id1,id2,...> [--due YYYY-MM-DD] [--tenant NAME]
```

The script is dry-run by default (no `--live`). Review the printed payload and
confirm it looks correct.

### Step 5 — Go live

```bash
uv run "<skill-dir>/scripts/learning_paths.py" assign <id> --user-ids <id1,id2,...> [--due YYYY-MM-DD] [--tenant NAME] --live
```

**What happens after:**
- Users who are newly assigned receive an assignment email (set expectations
  with the user before going live).
- If a listed user already has an active assignment, only their due date is
  updated — their progress is preserved and no new email is sent. Use reassign
  if you need to restart them from scratch.

**Due date notes:**
- `--due` accepts a bare `YYYY-MM-DD`; the script sends it as end-of-day UTC
  (`T23:59:59Z`).
- The date must be in the future — past dates return `400`.
- Omit `--due` entirely to assign with no deadline.

---

## Flow 4 — Reassign users (retakes / restarts)

Use reassign when:
- A rep failed a retriable certification and needs a fresh attempt.
- A rep is partway through a path and needs to restart from scratch (remediation,
  role change, etc.).

**Warn the user before going live:** reassign cancels the active assignment and
starts a new one — all prior stage progress is lost and cannot be recovered.

```bash
# dry-run first
uv run "<skill-dir>/scripts/learning_paths.py" reassign <id> --user-ids <id1,id2,...> [--due YYYY-MM-DD] [--tenant NAME]

# live
uv run "<skill-dir>/scripts/learning_paths.py" reassign <id> --user-ids <id1,id2,...> [--due YYYY-MM-DD] [--tenant NAME] --live
```

The same `tenantUserId` rules and `--due` format from Flow 3 apply here.

---

## Error handling

| Error | What to do |
|---|---|
| `missing env var ITERO_API_KEY…` | Add `ITERO_API_KEY=<key>` to `.env` (or `ITERO_API_KEY_<NAME>` for `--tenant NAME`) |
| `404` on path id | Run `list` to confirm the id exists on this tenant |
| `400` validation error | Check that all `--user-ids` values are `tenantUserId` integers from the `users` output (not `id`), and that `--due` is a future date |
| `403` Forbidden | Learning-path endpoints need a Manager-role key; the `users` subcommand hits an Owner-documented tenant endpoint — if only `users` 403s, the key lacks Owner |
| `401` Unauthorized | Missing or invalid `X-API-Key` — verify the value in `.env` |
