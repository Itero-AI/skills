---
name: upload-users
description: Bulk-import Itero users from a CSV with local validation, group review, duplicate detection, seat checks, a dry-run preview, and explicit confirmation. Use when someone asks to upload users, import a CSV or spreadsheet of users, bulk-add users, onboard a list of reps or managers, or run `/upload-users <path>`. Use manage-users for one or a few individual records.
user-invocable: true
license: MIT
metadata:
  author: itero
  version: "2.0.0"
  homepage: https://iteroapp.ai
  source: https://github.com/Itero-AI/skills
inputs:
  - name: ITERO_API_KEY
    description: Itero public API key. A named tenant may use ITERO_API_KEY_<NAME>.
    required: true
references:
  - references/upload-users.md
---

> **Mandatory upload confirmation:** Before the multipart `POST`, show the exact method and gateway URL, the `file` field and filename, the final row and group summaries, and the first five CSV lines from `preview`. Explain that successful creation sends invitation emails, then wait for an explicit `yes`. Never infer approval from earlier cleanup or group decisions.

# Upload Users

Use the bundled script to validate and import a CSV through the unified gateway. It is dry-run by default; add `--live` only after the final confirmation. Read [the generated upload reference](references/upload-users.md) for the multipart schema, limits, and verified role guidance.

`<skill-dir>` means the directory containing this file. Run commands with `uv run`; dependencies come from the script's inline declaration.

## Quick start: inspect the CSV

```bash
uv run "<skill-dir>/scripts/upload_users.py" inspect path/to/users.csv
```

Add `--tenant NAME` to use `ITERO_API_KEY_<NAME>`. Never print the resolved key.

## What do you need?

| Goal | Command | Result |
|---|---|---|
| Validate a CSV | `inspect <csv>` | Reports issues and writes `.tmp/users-import-plan.json`. |
| Review existing groups | `list-groups` | Reads `/api/public/v1/get-user-groups`. |
| Review current users | `list-users` | Reads canonical `/api/public/v1/user`. |
| Suggest and classify groups | `suggest-groups` | Marks each planned group as existing or new. |
| Check duplicate emails | `check-duplicates` | Stops before an all-or-nothing import can fail. |
| Check seats | `check-seats` | Compares active representatives with the configured seat cap. |
| Review exact upload | `preview` | Shows counts and the first five CSV lines to confirm. |
| Import | `import --live` | Uploads multipart field `file` after confirmation. |

## Required workflow

### 1. Inspect without changing the source

- Accept only `.csv`; ask the user to export a spreadsheet as CSV when needed.
- Reject files over 1 MB.
- Run `inspect`; never modify the original CSV.
- Resolve missing columns or values, malformed email addresses, unsupported roles, invalid active flags, and values over 100 characters in the generated plan.

### 2. Review user groups

Explain that user groups control learning-path and certification assignment. Then run:

```bash
uv run "<skill-dir>/scripts/upload_users.py" list-groups [--tenant NAME]
uv run "<skill-dir>/scripts/upload_users.py" suggest-groups [--tenant NAME]
```

Group names are case-sensitive. Ask for an explicit `yes` for each new group because the import auto-creates unknown names.

### 3. Stop for duplicates

```bash
uv run "<skill-dir>/scripts/upload_users.py" check-duplicates [--tenant NAME]
```

If duplicates exist, stop. Ask whether the user will fix the source and restart, or wants those rows removed from the plan. Run `drop-duplicates` only after that choice. Do not imply that duplicate users will be updated.

### 4. Stop for seat overflow

```bash
uv run "<skill-dir>/scripts/upload_users.py" check-seats [--tenant NAME]
```

If the configured seat cap would be exceeded, stop and let the user choose which planned representatives become inactive or whether to abort. Re-run the check after edits. If no seat-cap environment variable exists, state that the local check was skipped; do not claim capacity is available.

### 5. Preview and confirm

```bash
uv run "<skill-dir>/scripts/upload_users.py" preview
```

Show the role, status, and group counts plus the first five CSV lines printed by the script. State that the request is `POST https://iterogatewayapi.azurewebsites.net/api/public/v1/user/import-csv`, multipart field `file`, and that invitations are sent for created users. Wait for explicit `yes`.

### 6. Import once

```bash
uv run "<skill-dir>/scripts/upload_users.py" import [--tenant NAME] --live
```

Report the imported row count and auto-created groups. On a server error, report the response without credentials and return to the relevant validation step instead of retrying blindly.

## Common Mistakes

| Mistake | Correct approach |
|---|---|
| Uploading `.xlsx` | Export it as CSV first. |
| Editing the source during cleanup | Edit only `.tmp/users-import-plan.json`. |
| Skipping group review | Confirm every new, case-sensitive group name. |
| Continuing with duplicate emails | Stop and remove or resolve them first. |
| Assuming an unknown seat cap means room exists | State that the local capacity check was skipped. |
| Running `--live` after a general approval | Require a final `yes` for the exact CSV upload. |

## Error quick reference

| Error | What to do |
|---|---|
| Missing `ITERO_API_KEY` | Add the environment variable without exposing its value. |
| File is not CSV or exceeds 1 MB | Export or split the source and inspect again. |
| `400 CSVFileValidation` | Return to `inspect`; the content or shape is invalid. |
| `400 NotEnoughSeats` | Re-run the seat check because tenant state may have changed. |
| `401` | Confirm the key is present and valid without printing it. |
| `403` | Follow the verified role guidance in the generated reference. |
