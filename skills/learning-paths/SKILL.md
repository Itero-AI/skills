---
name: learning-paths
description: Manage Itero learning paths, certifications, assignments, and reassignments through the public API. Use when someone asks to list or inspect learning paths, assign training, change a due date, restart a learner's attempt, or work with learning-path or certification records. Triggers include "assign this learning path," "list learning paths," "change the due date," "reassign training," "restart their attempt," and "who should receive this certification?"
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
  - references/learning-paths.md
---

> **Mandatory API confirmation:** Before every `POST`, `PUT`, `PATCH`, or `DELETE`, show the exact method, URL, and complete payload (`no body` when applicable), then wait for explicit confirmation. For a delete, also show the learning-path name and stable ID and require the user to confirm that target. For assignment and reassignment, name every affected learner in the preview.

# Learning Paths

Use `https://iterogatewayapi.azurewebsites.net` and send `X-API-Key: $ITERO_API_KEY`. Read the key from the environment; never display, log, or paste its value. Load [the generated learning-paths reference](references/learning-paths.md) for exact schemas and examples.

## Quick start: list learning paths

Project only the fields needed for selection.

```bash
curl --fail-with-body --silent --show-error \
  --header "X-API-Key: $ITERO_API_KEY" \
  "https://iterogatewayapi.azurewebsites.net/api/public/v1/learning-path" \
  | jq '(.items? // .) | map({id, title, type, isOrdered, stagesAmount})'
```

## What do you need?

| Goal | Operation | Guidance |
|---|---|---|
| Find a learning path | `GET /api/public/v1/learning-path` | Project IDs and names. |
| Inspect one path | `GET /api/public/v1/learning-path/{id}` | Read details before assigning. |
| Assign learners | `POST /api/public/v1/learning-path/{id}/assign` | Use each user's `tenantUserId`. |
| Start a fresh attempt | `POST /api/public/v1/learning-path/{id}/reassign` | Explain that progress does not continue. |
| Work with path or certification records | Relevant generated operation | Follow the exact schema; detailed CRUD guidance lives in the reference. |
| Delete a path | `DELETE /api/public/v1/learning-path/{id}` | Confirm name and ID. |

## Assignment workflow

1. List the learning paths with a projection and identify the intended path.
2. List users through `GET /api/public/v1/user`, showing name, `id`, and `tenantUserId` for selection.
3. Copy `tenantUserId`—not `id`—into every assignment or reassignment item. The wrong value can target another user or return `400`.
4. Choose assign to create or adjust an assignment while preserving progress. Choose reassign only when the user intends a fresh attempt.
5. Validate any due date as a future UTC date-time.
6. Preview the path, each learner, due date, and exact payload; then wait for confirmation.

## Common Mistakes

| Mistake | Correct approach |
|---|---|
| Sending the user record's `id` | Send `tenantUserId` for assignment and reassignment. |
| Treating reassign as a due-date edit | Use it only when a fresh attempt is intended. |
| Guessing a path or person from a name | List and show stable identifiers before previewing the write. |
| Sending a local time or past due date | Convert to a future UTC date-time. |
| Loading complete collections into context | Project names and IDs or save raw JSON to a file. |

## Error quick reference

| Response | What to do |
|---|---|
| `400` | Check `tenantUserId`, path ID, due date, required fields, and enum values. |
| `401` | Confirm the key is available and valid without printing it. |
| `403` | Explain that the key lacks permission; do not retry unchanged. |
| `404` | Refresh the path and user lists and verify both identifiers. |
| `500` | Stop and preserve the response details without credentials. |
