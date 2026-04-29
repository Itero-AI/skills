---
name: upload-users
description: |
  Bulk-imports users into an Itero tenant from a CSV file. Walks the user
  through validation fixes, user-group decisions, duplicate detection, and a
  seat-count check before submitting. Triggers on:
  "/upload-users <path>", "upload these users", "import this CSV of users",
  "bulk-add users", "onboard these reps", "add this list of users to Itero",
  "import users from a spreadsheet", or any request to load a list of new
  Itero users (Managers or Representatives) from a CSV.
user-invocable: true
---

# Upload Users Skill

Walk a user through cleaning and uploading a CSV of new Itero users. Backed by
`scripts/upload_users.py`, which calls the Itero Tenant API
(`https://iterotenantapi.azurewebsites.net`).

The skill is designed for **non-technical users**. Explain every step in plain
English. Never make a destructive choice silently. Always dry-run first; only
hit `--live` after explicit `yes`.

---

## Getting Started (Customer Setup — One Time)

1. Drop the `upload-users/` folder into `.claude/skills/`.
2. Add `ITERO_API_KEY=<your-tenant-api-key>` to your `.env` file. The key must
   belong to a user with the **Manager** role.
3. (Optional) Add `ITERO_TENANT_SEATS=<number>` to your `.env` if you know
   your tenant's seat cap — enables the pre-flight seat check. Skip if
   unknown; the skill will run without it.

That's it. No other configuration needed.

---

## Why user groups matter (the user always sees this)

> User groups in Itero are how you assign learning paths and certifications.
> Each group can have its own training curriculum, scorecard requirements,
> and certification track. Putting your reps into the right group up front
> means they'll automatically see the right training when they log in.
> Skipping this just means you'll have to assign things one rep at a time
> later.

Render this paragraph at Step 3, every time, regardless of the input file's
state. Then list the existing groups so the user can decide whether to reuse
them or create new ones.

---

## The Flow

The skill always runs the eight steps below in order. The agent narrates each
step in plain English; the script handles the deterministic work.

### Step 1 — Open the file

- Resolve the CSV path: slash arg (`/upload-users path/to/file.csv`),
  attached file in chat, or ask the user to drop it in.
- If the file is `.xlsx` or anything other than `.csv`, stop and reply:
  *"This needs to be a CSV file. In Excel: File → Save As → CSV (Comma
  delimited). Then re-run."*
- Run:
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/upload-users/scripts/upload_users.py \
    inspect <csv-path> [--tenant TENANT]
  ```
- The script prints a row count, all detected issues grouped by category,
  and the first 3 rows. It writes `.tmp/users-import-plan.json`.

### Step 2 — Fix data-shape errors

Look at the `inspect` output. For every issue category present, walk the user
through it in plain English. Categories and how to handle each:

| Category | What to say to the user | What to do |
|---|---|---|
| `missing_column` | "The header row is missing a required column: {col}." | Ask user to fix the file's header row and re-run inspect. |
| `missing_value` (Name/Email/Role) | "Row {N} is missing {col}. What value should I put there, or should I drop the row?" | Update the plan or drop the row. |
| `bad_email` | "Row {N} has {value} in the Email column — that doesn't look like an email. What's the correct address?" | Update the plan. |
| `bad_role` | "Row {N} has Role={value}. Itero only supports `Manager` or `Representative`. Which one?" | Update the plan. |
| `bad_isactive` | "Row {N} has IsActive={value} — I'll need true or false. (Blank is fine; that means active.)" | Update the plan. |
| `too_long` | "Row {N}'s {col} is {length} chars; max is 100. What should I shorten it to?" | Update the plan. |

The agent edits `.tmp/users-import-plan.json` directly to apply the user's
answers. Re-run `inspect` only if the user wants a fresh validation pass after
edits — usually unnecessary.

The original CSV is **never modified**.

### Step 3 — Educate on user groups, then list existing groups

Always render the "Why user groups matter" paragraph above. Then run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/upload-users/scripts/upload_users.py \
  list-groups [--tenant TENANT]
```

Show the returned list to the user. If the tenant has zero groups, say so —
that's a real signal that the customer may need to think about cohorts before
proceeding.

### Step 4 — Resolve UserGroup column

Run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/upload-users/scripts/upload_users.py \
  suggest-groups [--tenant TENANT]
```

Three branches, picked by the script based on plan state:

- **Column missing or fully blank** — script suggests groupings (e.g., by
  email domain). Agent asks: *"Here's what I'm thinking — does this look
  right? Tell me any rows you'd like to move to a different group."* User
  edits in chat; agent updates the plan.
- **Column populated, all values match existing groups exactly** — agent
  shows the table and asks *"Ready to proceed?"*.
- **Column populated, one or more values are NEW** — script flags each new
  group. Agent must ask explicit `yes` per new group:
  > *"This will create a NEW group called 'Sales East' with the description
  > 'This User Group has been created from a CSV file. Please update the
  > description.' Type `yes` to confirm, or tell me a different name (which
  > must match an existing group exactly — they're case-sensitive)."*

After this step every distinct group in the plan is tagged `existing` or
`new`.

### Step 5 — Duplicate check (STOP)

Run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/upload-users/scripts/upload_users.py \
  check-duplicates [--tenant TENANT]
```

If duplicates are found, **STOP**. The script prints them. Render to the
user:

> *"These N email(s) already exist in your tenant: {list}. Itero's import is
> all-or-nothing, so I won't submit until we resolve these. Two options:*
> *(a) you edit the file to remove these rows and we re-run the skill, or*
> *(b) I drop them from the planned import and continue with the others.*
> *Which do you want?"*

If (a), exit. If (b), run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/upload-users/scripts/upload_users.py \
  drop-duplicates [--tenant TENANT]
```

### Step 6 — Seat-count check (STOP)

Run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/upload-users/scripts/upload_users.py \
  check-seats [--tenant TENANT]
```

If the seat cap is unknown (`ITERO_TENANT_SEATS_<NAME>` not set), the script
warns and continues. Tell the user the script is skipping the check and
why, then move on.

If the seat cap is known and would be exceeded, the script prints the math.
**STOP** and render:

> *"Your tenant has {N} seats. {M} are already filled. This import would add
> {K} more active reps, putting you at {total} — that's {over} over. Two
> options:*
> *(a) I'll set IsActive=false on {over} of the new rep rows so they're
> created as inactive (you can activate them later from the Itero app), or*
> *(b) abort and contact Itero to add seats. Which?"*

If (a), ask the user which rows to deactivate, edit the plan, then re-run
`check-seats`. If (b), exit.

### Step 7 — Final preview + confirm

Run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/upload-users/scripts/upload_users.py preview
```

The script prints role mix, status mix, group mix, and the first 5 lines of
the exact CSV that will be uploaded.

Show this to the user, then ask:

> *"Type `yes` to upload, or tell me what to change."*

### Step 8 — Live import

Only after explicit `yes`, run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/upload-users/scripts/upload_users.py \
  import [--tenant TENANT] --live
```

Without `--live` the script dry-runs and reports what would have been sent.
With `--live` it does the multipart POST and reports row count plus the list
of groups the server auto-created. Relay both to the user.

If the server returns `400`, the script prints the `ProblemDetails` body
verbatim. Common subtypes (`CSVFileValidation`, `NotEnoughSeats`) should be
rare since steps 5 and 6 ran upstream — if they appear here, something
changed in the tenant between checks. Investigate before retrying.

---

## Authentication

Default: skill reads `ITERO_API_KEY` from your `.env` file. That's the only
setup needed for a single-tenant install.

If you manage multiple Itero tenants from one repo, add the optional
`--tenant <NAME>` flag; the skill will resolve `ITERO_API_KEY_<NAME>` from
`.env` instead. Example:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/upload-users/scripts/upload_users.py \
  inspect ~/Downloads/users.csv --tenant ACME
```

Omit `--tenant` for the common single-key case.

---

## Out of scope (v1)

- The Admin endpoint `POST /api/public/v1/admin/user/import-csv?tenantId=...`
  — this skill only uses the Manager endpoint for the caller's own tenant.
- `.xlsx` auto-conversion — reject with a clear "save as CSV" message.
- Updating existing users — there is no public PUT endpoint for users.

---

## Error Handling

| Error message | What to do |
|---|---|
| `missing env var ITERO_API_KEY` | Add `ITERO_API_KEY=<key>` to `.env`. |
| `file is '.xlsx', not .csv` | Save the file as CSV in Excel and re-run. |
| `file is N bytes, over the 1 MB import limit` | Split into smaller batches and run the skill once per batch. |
| `plan not found at .tmp/...` | Run `inspect <csv>` first to create the plan. |
| `seat_check.ok is False` (on import) | Re-run `check-seats` after deactivating rows or increasing seats. |
| `400 NotEnoughSeats` (from server) | Tenant seat count changed between check and import. Re-run `check-seats`. |
| `400 CSVFileValidation` (from server) | Re-run `inspect` to see what's wrong; the row count or shape changed. |
| `403 Forbidden` | API key does not have Manager role. Have an Itero admin promote the key's user. |
