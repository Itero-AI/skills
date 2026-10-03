---
name: scorecards
description: Manage Itero scorecard templates, categories, criteria, rubrics, agents, and publication through the public API. Use when someone asks to list scorecards, build a scorecard, add or change criteria, customize rubric descriptions, publish or unpublish a template, or delete scorecard content. Triggers include "create a scorecard," "publish this scorecard," "add scoring criteria," "update the rubric," "list evaluation agents," and "why won't this template publish?"
user-invocable: true
license: MIT
metadata:
  author: itero
  version: "2.3.0"
  homepage: https://iteroapp.ai
  source: https://github.com/Itero-AI/skills
inputs:
  - name: ITERO_API_KEY
    description: Itero public API key. A named tenant may use ITERO_API_KEY_<NAME>.
    required: true
references:
  - references/scorecards.md
---

> **Mandatory API confirmation:** Before every `POST`, `PUT`, `PATCH`, or `DELETE`, show the exact method, URL, and complete payload (`no body` when applicable), then wait for explicit confirmation. For a delete, also show the template, category, or criterion name and stable ID and require the user to confirm that target.

# Scorecards

Use `https://iterogatewayapi.azurewebsites.net` and send `X-API-Key: $ITERO_API_KEY`. Read the key from the environment; never display, log, or paste its value. Load [the generated scorecards reference](references/scorecards.md) for exact schemas, enum subsets, and operation examples.

## Quick start: list scorecards

Project collection fields instead of loading full templates into context.

```bash
curl --fail-with-body --silent --show-error \
  --header "X-API-Key: $ITERO_API_KEY" \
  "https://iterogatewayapi.azurewebsites.net/api/public/v1/scorecard" \
  | jq '(.items? // .) | map({id, name, status, callTypes, interactionType})'
```

## Publish through the API

Publishing is a supported API operation. After every intended category and criterion has been created successfully, preview and confirm this request:

```http
PATCH /api/public/v1/scorecard/{id}/status
Content-Type: application/json

{"status": 1}
```

`status: 0` means Draft and `status: 1` means Published. The template DTO includes `status`. The API rejects an empty template with `ScorecardTemplateCannotPublishEmpty`; publishing requires at least one active criterion inside an active category.

## What do you need?

| Goal | Operation | Guidance |
|---|---|---|
| Create a complete draft | `POST /api/public/v2/scorecard` | One atomic request with categories and criteria. |
| List templates or agents | `GET /api/public/v1/scorecard`, `GET /api/public/v1/agent` | Project agent IDs, names, agentType and interactionType. IDs are tenant-specific. |
| Edit an existing template | `PUT /api/public/v1/scorecard` | Preserve the current fields and nested IDs. |
| Edit categories | `/api/public/v1/scorecard-category` operations | V1 per-entity editing; create parents before children. |
| Edit criteria or rubrics | `/api/public/v1/scorecard-criteria` operations | Match returned rubric IDs by rubrikScale for later customization. |
| Publish or return to draft | `PATCH /api/public/v1/scorecard/{id}/status` | Use 1 to publish or 0 for Draft after a separate confirmation. |
| Delete a draft | `DELETE /api/public/v1/scorecard/{id}` | Delete only the confirmed template ID. |

See [the endpoint map](references/scorecards.md#endpoint-map) for the v1 editing operations.

## Create a scorecard with v2

1. Pick agents from `GET /api/public/v1/agent` by `agentType` plus `interactionType`, never by name. Voice needs qualitative type 0 and QA type 3, both interactionType 0. Chat needs types 4 and 5, both interactionType 1. Never use types 1 or 2. If several coaching agents qualify, ask which one. No agent type is verified for ScreenRecording: add neither that category nor screenRecordingAgentId unless the user supplies the agent ID.
2. Draft a complete payload. Replace the placeholder IDs below with the selected tenant's voice agents. Omit weight for equal weights; an explicit qualitative weight should be 1–1000 (v2 documents 0–1000, but v1 rejected zero). Qualitative rubrics can be omitted for platform AI generation or supplied as all five scales 0–4. QA criteria have neither rubrics nor weight.

   ```json
   {
     "name": "Discovery Call",
     "interactionType": 0,
     "qualitiveAgentId": 123,
     "qaAgentId": 456,
     "categories": [
       {
         "name": "Compliance",
         "scorecardType": 1,
         "criteria": [
           {
             "title": "Disclosed recording",
             "criteria": "Did the rep state that the call is recorded?"
           }
         ]
       },
       {
         "name": "Discovery",
         "scorecardType": 0,
         "criteria": [
           {
             "title": "Identified pain points",
             "criteria": "How well did the rep uncover the prospect pain points?",
             "rubrics": [
               {
                 "rubrikScale": 0,
                 "description": "No pain points identified."
               },
               {
                 "rubrikScale": 1,
                 "description": "One pain point touched on but not explored."
               },
               {
                 "rubrikScale": 2,
                 "description": "Some pain points surfaced."
               },
               {
                 "rubrikScale": 3,
                 "description": "Most pain points surfaced and explored."
               },
               {
                 "rubrikScale": 4,
                 "description": "All key pain points clearly identified."
               }
             ]
           }
         ]
       }
     ]
   }
   ```

   Each category needs a criterion with title and criteria. Chat rejects min/max duration and ScreenRecording categories. interactionType must match both agents. Feedback language values are 0 (Same as transcript), 1 (English) and 2 (Spanish). Send callTags with id and name.
3. Show the exact method, URL and complete payload and wait for confirmation.
4. Send one `POST /api/public/v2/scorecard`. It creates a Draft atomically.
5. On a 400, nothing was saved and no cleanup is needed. Fix the payload, show the revised request, obtain confirmation and resend. For an ambiguous transport error or 500, stop and inspect the outcome before attempting another create.
6. Keep every returned template, category, criterion and rubric ID for later v1 edits.
7. Review the complete draft, then publish with a separately confirmed `PATCH /api/public/v1/scorecard/{id}/status` and `{"status":1}`. Remove an unwanted draft only with a confirmed DELETE of its stable template ID.

## Common Mistakes

| Mistake | Correct approach |
|---|---|
| Claiming a template cannot be published by API | Use `PATCH /scorecard/{id}/status` with `{"status": 1}`. |
| Publishing before review | Review the complete draft and confirm publication separately. |
| Publishing an empty template | Add an active criterion inside an active category first. |
| Correcting `qualitiveAgentId` spelling | Preserve that exact API field spelling. |
| Treating `rubrikScale` as a typo | Preserve the API spelling and match scales to returned rubric IDs. |
| Reusing an agent ID from another tenant | Resolve it from `GET /api/public/v1/agent`. |
| Choosing agents by name | Match agentType and interactionType; ask when several coaching agents qualify. |
| Sending partial, duplicate or NotApplicable rubrics | Omit qualitative rubrics or supply each rubrikScale 0–4 exactly once. |
| Sending rubrics or weight on QA | Both are qualitative only. |
| Sending duration or ScreenRecording on chat | Omit min/max duration and ScreenRecording categories. |
| Mismatching interactionType and agents | Match voice 0 or chat 1 on both agents. |
| Cleaning up after a failed v2 create with 400 | Nothing was saved; correct and confirm a new request. |

## Error quick reference

| Response | What to do |
|---|---|
| `400 ScorecardTemplateCannotPublishEmpty` | Add and activate at least one category and criterion, then confirm a new publish request. |
| `400` | Compare required fields and per-operation enum values with the generated schema. |
| `401` | Confirm the key exists and is valid without printing it. |
| `403` | Explain that the key lacks permission; do not retry unchanged. |
| `404` | Re-list the relevant parent resource and verify ID threading. |
| `400 CallDurationNotAllowedForChat` | Remove min/max duration from chat scorecards. |
| `400 ScreenRecordingNotAllowedForChat` | Remove ScreenRecording categories from chat scorecards. |
| `400` for a partial rubric set | Omit qualitative rubrics or supply all five scales 0–4 exactly once. |
| `500` or ambiguous transport error | Stop; preserve the response without secrets and verify whether a draft exists before another create. |
