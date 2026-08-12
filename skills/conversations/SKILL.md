---
name: conversations
description: Search and review Itero conversations, fetch transcripts, log external calls, tag calls, start evaluations, and explain evaluation results through the public API. Use for transcripts, conversations, call reviews, coaching, evaluation results, "why did this rep score low," Gong or Outreach imported calls, evaluable scorecards, and evaluation deletion. Triggers include "find this call," "show the transcript," "review this conversation," "evaluate this call," "explain the score," "tag these calls," and "log an external call."
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
  - references/conversations.md
---

> **Mandatory API confirmation:** Before every `POST`, `PUT`, `PATCH`, or `DELETE`, show the exact method, URL, and complete payload (`no body` when applicable), then wait for explicit confirmation. This includes the read-only call search because it uses `POST`. For evaluation deletion, show the stable evaluation ID and require the user to confirm that exact ID.

# Conversations

Use `https://iterogatewayapi.azurewebsites.net` for every operation except the two evaluation-by-ID operations described below. Send `X-API-Key: $ITERO_API_KEY`; read the key from the environment and never display, log, or paste its value. Load [the generated conversations reference](references/conversations.md) for all fields and examples.

## Quick start: list evaluable scorecards

```bash
curl --fail-with-body --silent --show-error \
  --header "X-API-Key: $ITERO_API_KEY" \
  "https://iterogatewayapi.azurewebsites.net/api/public/v1/call/scorecard-templates" \
  | jq '(.items? // .) | map({id, name, callTypes})'
```

## What do you need?

| Goal | Operation | Guidance |
|---|---|---|
| Search conversations | `POST /api/public/v1/call/get-calls` | Start at page 0 and read `totalCount`. |
| Fetch a transcript | `GET /api/public/v1/call/get-call?callId=` | Save the full response, then project transcript fields. |
| Log an external call | `POST /api/public/v1/call/add-call` | Preview transcript, participants, dates, and tags. |
| Start an evaluation | `POST /api/public/v1/call/evaluate-call` | Check existing evaluations first. |
| Read the score breakdown | `GET /api/public/v1/evaluation/{id}` | Use the practice-host exception in the reference. |
| Delete an evaluation | `DELETE /api/public/v1/evaluation/{id}` | Use the same exception and confirm the ID. |
| Add tags in bulk | `POST /api/public/v1/call-tag/add-tags-to-calls` | Confirm call IDs and exact tag spellings. |
| List evaluable templates | `GET /api/public/v1/call/scorecard-templates` | Project IDs, names, and types. |

## Search and fetch workflow

1. Build a call-search payload. The endpoint supports 16 filters plus pagination and sorting; read the field table in [the generated reference](references/conversations.md#post-apipublicv1callget-calls).
2. Use `pageNumber: 0` for the first page. It is 0-indexed despite incorrect specification prose. Read `totalCount` before requesting more pages.
3. Know the matching rules: `callTags` is a case-insensitive substring filter, while prospect and company filters are exact.
4. Show the exact search payload and wait for confirmation because the read uses `POST`.
5. Project the results to IDs, title, owner, date, source, tags, and evaluation summaries.
6. Fetch only the selected `callId`. Save the full response to a file, then extract `transcriptions[]` fields `content`, `speaker`, `start`, and `end`; do not load a long transcript into the main context.

## Evaluate and explain workflow

1. Search for the call and inspect its existing evaluation summaries. Do not start another evaluation while one is already evaluating.
2. List evaluable templates and select the intended `scorecardTemplateId`.
3. Preview and confirm the exact `evaluate-call` payload, then send it once. The response is `200` with no body — it does not return an evaluation ID.
4. Poll `GET /call/get-call?callId=...` until the new entry appears in `evaluations[]` (match `scorecardTemplateId`, take the newest `evaluationDate`) and its `status` reaches 2 (Success) or 3 (Error). Then read the breakdown by that `evaluationId` through the practice host documented in the reference. The gateway currently returns `503` for `GET` and `DELETE` evaluation-by-ID; only those two operations use the exception.
5. Explain the result from `categories[]` and nested `criteria[]`, including score, result, and justification. Tie a low overall result to the specific criteria rather than guessing.
6. If deletion is requested, show and confirm the stable evaluation ID before using the practice-host delete operation.

## Log or tag calls

- Validate external-call dates, owner email, transcript order, participants, and any external URL before previewing `add-call`.
- Treat tag spelling as data. Unknown tag names on `add-call` or bulk add-tags are created automatically, so a typo creates a new tag.
- Bulk add-tags **replaces** the entire tag list on any call that already has tags. To keep existing tags, fetch each call's current tags and send the union.
- Project IDs from search results before a bulk tag request, then show every selected call ID and the **final tag list each call will end up with** before confirmation.

## Common Mistakes

| Mistake | Correct approach |
|---|---|
| Starting call search at page 1 | Start at `pageNumber: 0`; page 1 skips the newest page. |
| Expecting `evaluate-call` to return the evaluation ID | The response has no body; poll `get-call` for the new `evaluations[]` entry. |
| Adding tags on top of existing tags with bulk add-tags | It replaces the list; send the union of current + new tags per call. |
| Loading a raw transcript into context | Save the response and extract only the needed transcript fields. |
| Using a partial prospect or company name | Use exact matching; only `callTags` uses substring matching. |
| Retrying an already-running evaluation | Inspect current evaluation status and wait. |
| Reading evaluation-by-ID through the gateway | Use the documented practice-host exception for GET and DELETE only. |
| Sending an unreviewed tag | Confirm exact spelling because unknown tags are auto-created. |

## Error quick reference

| Response | What to do |
|---|---|
| `400` | Check IDs, date-times, required transcript fields, and whether evaluation is already running. |
| `401` | Confirm the key is available and valid without printing it. |
| `403` | Explain that the key lacks permission; do not retry unchanged. |
| `404` | Re-run a projected search and verify the call or evaluation ID. |
| `503` on evaluation-by-ID | Use the practice-host exception documented in the reference. |
| `500` | Stop and preserve non-secret response details before retrying. |
