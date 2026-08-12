---
name: manage-users
description: Manage individual Itero users through the public API. Use when someone asks to list or find users, create one or a few users, change a name, role, active status, or group membership, deactivate or reactivate someone, or delete a user. Triggers include "add a user," "change their role," "move them to this group," "deactivate this rep," "offboard this user," and "delete this user." Use upload-users for a CSV or larger batch.
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
  - references/users.md
---

> **Mandatory API confirmation:** Before every `POST`, `PUT`, `PATCH`, or `DELETE`, show the exact method, URL, and complete payload (`no body` when applicable), then wait for explicit confirmation. For a delete, also show the user's name, email, and stable ID and require the user to confirm that target. Creating a user can send an invitation email, so include that effect in the confirmation.

# Manage Users

Use `https://iterogatewayapi.azurewebsites.net` and send `X-API-Key: $ITERO_API_KEY`. Read the key from the environment; never display, log, or paste its value. Use only the canonical `/api/public/v1/user` endpoint for user records. Load [the generated users reference](references/users.md) for exact schemas and verified role behavior.

For a CSV or roughly five or more users, use the `upload-users` skill instead.

## Quick start: list users

Filter on the server when possible and project only identification fields.

```bash
curl --fail-with-body --silent --show-error \
  --header "X-API-Key: $ITERO_API_KEY" \
  "https://iterogatewayapi.azurewebsites.net/api/public/v1/user?isActive=true" \
  | jq '(.items? // .) | map({id, tenantUserId, name, email, role, isActive})'
```

## What do you need?

| Goal | Operation | Guidance |
|---|---|---|
| List or filter users | `GET /api/public/v1/user` | Use `role` and `isActive`, then project fields. |
| List groups | `GET /api/public/v1/get-user-groups` | Copy exact group names. |
| Create a user | `POST /api/public/v1/user` | Check the email and explain the invitation first. |
| Update, deactivate, or reactivate | `PUT /api/public/v1/user` | Start from the complete current record. |
| Delete a user | `DELETE /api/public/v1/user/{id}` | Prefer reversible deactivation unless deletion is explicit. |

## Workflow

1. List users through the canonical endpoint and show enough fields to disambiguate the person.
2. List user groups before changing membership; preserve the exact spelling and capitalization.
3. Read the selected operation in [the generated reference](references/users.md).
4. For updates, start from the current complete object and change only the requested fields.
5. Preview the exact request and its effects, then wait for confirmation.
6. Re-list or inspect the response to verify the result without dumping the full collection.

## Common Mistakes

| Mistake | Correct approach |
|---|---|
| Using a duplicate list route | Use only `GET /api/public/v1/user`. |
| Treating `id` and `tenantUserId` as interchangeable | Follow the identifier required by the specific operation. |
| Sending a partial update | Carry forward fields that must not change. |
| Silently creating a user | Explain that successful creation sends an invitation email. |
| Deleting when deactivation meets the goal | Prefer the reversible update unless deletion is explicit. |
| Guessing why a write returned `403` | Read the verified role note in the generated reference. |

## Error quick reference

| Response | What to do |
|---|---|
| `400 NotEnoughSeats` | Do not retry; ask the user to free a seat or change the plan. |
| `400` | Check required fields, role values, group names, and identifier choice. |
| `401` | Confirm the key is available and valid without printing it. |
| `403` | Follow the verified role guidance in the generated reference. |
| `404` | Re-list users and verify the operation's required identifier. |
