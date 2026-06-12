---
name: manage-users
description: |
  Creates, updates, activates/deactivates, and deletes individual Itero users
  via the public API. Use when someone wants to: add one or two users (not a
  bulk CSV), change a user's role, move a user between user groups, fix a
  user's name, deactivate a rep who left, re-activate a returning rep, or
  delete a user. Triggers on: "add a user", "create a user", "change their
  role", "deactivate", "offboard this rep", "remove a user", "move them to
  the Sales East group", "promote to manager". For bulk CSV imports use
  upload-users instead.
user-invocable: true
references:
    - user-api.md
---

# Manage Users Skill

Add, update, deactivate, or remove individual Itero users via the public API.
Backed by `scripts/manage_users.py`. This skill is designed for **non-technical
users** — explain each step in plain English, never take a destructive action
silently, and always dry-run before going live.

> **Adding ~5 or more users at once?** Use the `upload-users` skill (bulk CSV
> import) instead — it handles validation, duplicate detection, and seat-count
> checks across a file at once.

---

## Running the scripts

`<skill-dir>` below means the folder containing this SKILL.md (announced when
the skill loads). Under a Claude Code plugin install this is the
`skills/manage-users` subfolder of the plugin root; under a manual install it
is the skill folder inside your agent's skills directory. All scripts run via
`uv run` — dependencies resolve automatically (PEP 723).

---

## Authentication

The script reads `ITERO_API_KEY` from `.env`. For multi-tenant repos, pass
`--tenant <NAME>` to use `ITERO_API_KEY_<NAME>` instead.

```bash
uv run "<skill-dir>/scripts/manage_users.py" list [--tenant NAME]
```

> **Owner-role key required.** Every endpoint covered by this skill
> (`GET`, `POST`, `PUT`, `DELETE /api/public/v1/user`) is documented as
> requiring an Owner-role API key — not Manager. A `403 Forbidden` almost
> always means the key in `.env` is a Manager key. Have an Owner generate a
> new key and replace the value in `.env`.

---

## API reference

| Need | Where |
|---|---|
| `id` vs `tenantUserId` — which to use where | [user-api.md](references/user-api.md) — "`` `id` vs `tenantUserId` ``" |
| Role values and which consume a billable seat | [user-api.md](references/user-api.md) — "Enums" |
| Create request schema (`PublicUserCreateRequest`) | [user-api.md](references/user-api.md) — "POST /api/public/v1/user" |
| Update request schema (`PublicUserUpdateRequest`) | [user-api.md](references/user-api.md) — "PUT /api/public/v1/user" |
| Delete — pending-confirmation warning | [user-api.md](references/user-api.md) — "DELETE /api/public/v1/user/{id}" |
| Error codes and remediation | [user-api.md](references/user-api.md) — "Errors" |

---

## Flow 1 — List and inspect users

### List all users

```bash
uv run "<skill-dir>/scripts/manage_users.py" list [--role ROLE] [--active true|false] [--tenant NAME]
```

`--role` accepts one of: `Representative`, `Manager`, `Coach`, `Owner`.
`--active` filters by active status. Omit both to see everyone.

Output prints `id`, `tenantUserId`, role, active flag, name, email, and group
membership side-by-side. Use the `id` column (not `tenantUserId`) for all
subcommands in this skill.

### Inspect a single user

```bash
uv run "<skill-dir>/scripts/manage_users.py" fetch <id> [--tenant NAME]
```

Returns the full JSON record. Run this before any update to capture the current
field values you need to carry forward.

---

## Flow 2 — Create a user

### Step 1 — List existing groups first

```bash
uv run "<skill-dir>/scripts/manage_users.py" list-groups [--tenant NAME]
```

Group names are **case-sensitive**. A near-miss (e.g., `"sales east"` instead
of `"Sales East"`) creates a new group instead of joining the existing one. Run
`list-groups` and confirm the exact title before building the plan.

### Step 2 — Build a plan.json

Prepare a JSON file with the user's details:

```json
{
  "name": "Jane Smith",
  "email": "jane.smith@example.com",
  "role": "Representative",
  "isActive": true,
  "groups": ["Sales East"]
}
```

Required fields: `name`, `email`, `role`. Optional: `isActive` (defaults to
`true`) and `groups` (string array of exact group names).

Valid roles: `Representative`, `Manager`, `Coach`, `Owner`.

> **Seat warning.** Creating a `Representative` or `Manager` with
> `isActive: true` consumes a billable seat. If the tenant is at its seat
> limit, the API returns `400 NotEnoughSeats`.

> **Invitation email.** An invitation email is sent to the user on creation.
> Set expectations with the user before going live.

> **Duplicate email.** If a user with the same email already exists in the
> tenant, the existing record is reused — no error is returned.

### Step 3 — Dry-run, then go live

```bash
# dry-run first (no --live)
uv run "<skill-dir>/scripts/manage_users.py" create plan.json [--tenant NAME]

# go live after explicit yes
uv run "<skill-dir>/scripts/manage_users.py" create plan.json [--tenant NAME] --live
```

Dry-run prints the payload and skips the POST. Only add `--live` after the user
has confirmed the preview looks correct.

---

## Flow 3 — Update a user

> **PUT requires the complete object.** The API replaces all user fields with
> what you send. Omitting `isActive` silently defaults it to `true` — so if the
> user is currently deactivated and you omit `isActive`, they will be
> reactivated. Always fetch first and carry every field forward.

### Step 1 — Fetch the current record

```bash
uv run "<skill-dir>/scripts/manage_users.py" fetch <id> [--tenant NAME]
```

Note the current values for `name`, `role`, `isActive`, and `groups` (as a
list of name strings).

### Step 2 — Build the updated payload

Construct the complete JSON object with all fields, changing only what the user
asked to change:

```json
{
  "name": "Jane Smith",
  "role": "Manager",
  "isActive": true,
  "groups": ["Sales East"]
}
```

`email` cannot be changed — do not include it in the payload.

### Step 3 — Dry-run, then go live

```bash
# dry-run first (no --live)
uv run "<skill-dir>/scripts/manage_users.py" update <id> '{"name":"Jane Smith","role":"Manager","isActive":true,"groups":["Sales East"]}' [--tenant NAME]

# go live after explicit yes
uv run "<skill-dir>/scripts/manage_users.py" update <id> '{"name":"Jane Smith","role":"Manager","isActive":true,"groups":["Sales East"]}' [--tenant NAME] --live
```

The `id` argument is the integer from the `list` or `fetch` output (not
`tenantUserId`).

---

## Flow 4 — Deactivate or activate a user

**Prefer deactivate over delete.** Deactivation frees the user's billable seat
(active Representatives and Managers consume seats; deactivated users do not)
and is fully reversible. All history, call recordings, and scores are preserved.

```bash
# deactivate — frees the seat; recommended for reps who have left
uv run "<skill-dir>/scripts/manage_users.py" deactivate <id> [--tenant NAME] --live

# reactivate — reclaims a seat
uv run "<skill-dir>/scripts/manage_users.py" activate <id> [--tenant NAME] --live
```

Both subcommands fetch the current record and write back a complete object
with only `isActive` changed — other fields are preserved automatically.
Dry-run by default; add `--live` to execute.

---

## Flow 5 — Delete a user

**The script currently refuses live deletes.** Three things about the DELETE
endpoint are pending platform confirmation:

1. Whether the path `{id}` takes the DTO `id` or `tenantUserId`.
2. Whether delete is a hard delete or a soft delete.
3. Whether it immediately frees a billable seat.

Until these are confirmed, `--live` on the `delete` subcommand raises an error
and no API call is made. Relay this refusal to the user honestly — do not
attempt to work around it.

Dry-run still works and shows the target identity so you can verify you have
the right user:

```bash
uv run "<skill-dir>/scripts/manage_users.py" delete <id> [--tenant NAME]
```

`--confirm-email` exists in the CLI but is reserved for when the platform
confirms delete semantics — it does not bypass the live-delete guard.

**Recommended path today:** deactivate the user (Flow 4). This frees the seat,
is reversible, and is unambiguous.

---

## Error table

| Error | Cause | What to do |
|---|---|---|
| `403 Forbidden` | API key lacks Owner role | Have an Owner generate a new key and update `.env`; Manager keys are rejected by all endpoints in this skill |
| `400 NotEnoughSeats` | Activating a Rep or Manager when the tenant is at its seat limit | Deactivate another active Rep/Manager first, or contact Itero to add seats |
| `400` validation | Missing required field, invalid role string, or malformed payload | Check that `role` is exactly one of `Representative`, `Manager`, `Coach`, `Owner`; check that `name` and `email` are present for create; check that `name` and `role` are present for update |
| `missing env var ITERO_API_KEY…` | Key not in `.env` | Add `ITERO_API_KEY=<key>` to `.env` (or `ITERO_API_KEY_<NAME>=<key>` for `--tenant NAME`) |
| `user id=N not found` | Wrong id passed | Run `list` to see current ids; note that `id` and `tenantUserId` are different integers |
