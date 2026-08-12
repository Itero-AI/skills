*Last Edited: 2026-08-12 15:08*

# Conversation and Evaluation Notes

<!-- gotchas -->
## Conversation gotchas

<!-- fact:pagination-zero-indexed -->
### Call-search pages start at zero

`pageNumber` on `POST /api/public/v1/call/get-calls` is 0-indexed. The specification prose says it is 1-based, but that prose is wrong. Pages 0, 1, and 2 returned disjoint results in live verification; starting at `pageNumber: 1` silently skips the newest page. Use `pageNumber: 0` for the first page and read `totalCount` to plan later pages.

<!-- fact:evaluation-host-exception -->
### Use the practice host for two evaluation operations

`GET /api/public/v1/evaluation/{id}` and `DELETE /api/public/v1/evaluation/{id}` hang for about 90 seconds and then return `503` through the gateway, even for a nonexistent ID. Call only those two operations on `https://iteropracticeapi.azurewebsites.net`; they completed in under 0.5 seconds during live verification. Keep every other public operation on the gateway.

<!-- fact:tags-autocreate -->
### Check new tag names before writing

Unknown tag names sent to add-call or add-tags are created automatically. Show the final tag names before the write so a spelling or capitalization mistake does not create an unwanted tag.

<!-- fact:add-tags-replaces -->
### Bulk tagging replaces the whole tag list

`POST /api/public/v1/call-tag/add-tags-to-calls` overwrites: on any call that already has tags, the provided list fully replaces the existing tags. Sending `["follow-up"]` to a call tagged `vip` leaves it tagged only `follow-up`.

To append instead of replace, fetch each selected call's current tags first and send the union of current + new tags per call. Always show the final tag list each call will end up with — not just the tags being added — in the confirmation.

<!-- fact:evaluate-call-no-body -->
### `evaluate-call` returns no body — poll for the new evaluation ID

`POST /api/public/v1/call/evaluate-call` returns `200` with an empty response. There is no evaluation ID in the reply. To find the new evaluation, poll `GET /api/public/v1/call/get-call?callId=...` until a new entry appears in `evaluations[]` (match on `scorecardTemplateId` and the newest `evaluationDate`), and check its `status` (0=NotStarted, 1=InProgress, 2=Success, 3=Error) before reading the breakdown. Evaluation runs asynchronously — allow for a wait, and stop polling on status 2 or 3.

<!-- fact:calltags-substring-match -->
### Know which call-search filters are fuzzy

The `callTags` filter uses case-insensitive substring matching. Prospect and company filters use exact matching. Use a precise tag fragment when broad matches would be surprising, and do not expect partial prospect or company names to match.

### Keep transcripts out of the main context

`GET /api/public/v1/call/get-call?callId=...` can return a large record. Save the response to a file, then project only the needed `transcriptions[]` fields such as content, speaker, start, and end.
<!-- /gotchas -->

<!-- lifecycle -->
## Conversation and evaluation lifecycle

Search calls first, select a stable `callId`, and fetch the transcript only when needed. Logging an external call, adding tags, and starting an evaluation are writes, so preview the exact payload and wait for explicit confirmation.

Starting an evaluation returns no identifier — poll the call record until the new evaluation summary appears, then use that `evaluationId` to read the category and criterion breakdown. If an evaluation is already running, do not submit a duplicate request. Before deleting an evaluation, show its stable ID and require the user to confirm that exact ID.
<!-- /lifecycle -->
