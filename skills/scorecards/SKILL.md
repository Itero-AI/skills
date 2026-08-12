---
name: scorecards
description: Manage Itero scorecard templates, categories, criteria, rubrics, agents, and publication through the public API. Use when someone asks to list scorecards, build a scorecard, add or change criteria, customize rubric descriptions, publish or unpublish a template, or delete scorecard content. Triggers include "create a scorecard," "publish this scorecard," "add scoring criteria," "update the rubric," "list evaluation agents," and "why won't this template publish?"
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
  - references/scorecards.md
---

> **Mandatory API confirmation:** Before every `POST`, `PUT`, `PATCH`, or `DELETE`, show the exact method, URL, and complete payload (`no body` when applicable), then wait for explicit confirmation. For a delete, also show the template, category, or criterion name and stable ID and require the user to confirm that target. This applies both to direct requests and to `build_scorecard.py --live`.

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

| Goal | Operation or tool | Guidance |
|---|---|---|
| List templates or agents | `GET /scorecard`, `GET /agent` | Project IDs and names. Agent IDs are tenant-specific. |
| Build a complete template | `scripts/build_scorecard.py` | Validate, dry-run, confirm, then run live. |
| Create or update a template | `POST /scorecard`, `PUT /scorecard` | Use the schema's exact field spelling. |
| Manage categories | `/scorecard-category` operations | Create the template first and retain its returned ID. |
| Manage criteria or rubrics | `/scorecard-criteria` operations | Create the category and criterion before editing rubrics. |
| Publish or return to draft | `PATCH /scorecard/{id}/status` | Use `1` to publish or `0` for draft. |
| Delete scorecard content | Relevant `DELETE` operation | Delete only the confirmed target; child cleanup runs in reverse order. |

All paths above are under `/api/public/v1`; see [the endpoint map](references/scorecards.md#endpoint-map).

## Build a scorecard safely

1. Prepare a plan with this shape. Omit agent IDs to resolve them from the current tenant; explicit IDs win.

   ```json
   {
     "name": "Discovery Call",
     "callTypes": [0, 1],
     "interactionType": 0,
     "userGroupIds": [123],
     "qualitiveAgentId": 456,
     "qaAgentId": 789,
     "categories": [
       {
         "name": "Discovery",
         "scorecardType": 0,
         "criteria": [
           {
             "title": "Find the business impact",
             "criteria": "The rep connects the problem to a measurable impact.",
             "rubrics": [{"scale": 4, "description": "Clear, quantified impact"}]
           }
         ]
       }
     ],
     "publish": false
   }
   ```

   Use [the generated scorecards reference](references/scorecards.md) to select valid enum values. Omit `weight` (the platform assigns equal weights; a custom override must be 1–1000, qualitative categories only) and omit `rubrics` during initial authoring — rubric descriptions are platform-managed and the update endpoint is for later tenant-specific customization. Only scales 0–4 exist on a new criterion.
2. Validate without credentials or network access:

   ```bash
   uv run "<skill-dir>/scripts/build_scorecard.py" --validate plan.json
   ```

3. Run the default dry-run. It may make `GET` requests to resolve agents or rubrics, but it must not send a write.

   ```bash
   uv run "<skill-dir>/scripts/build_scorecard.py" plan.json
   ```

4. Show the complete plan, including whether `publish` is true, and wait for explicit confirmation.
5. Run with `--live` only after confirmation. Keep the generated journal; it records every successful ID.
6. If cleanup is requested, preview `--cleanup <journal>` first, show each reverse-order delete target, obtain a new confirmation, and only then add `--live`.

## Common Mistakes

| Mistake | Correct approach |
|---|---|
| Claiming a template cannot be published by API | Use `PATCH /scorecard/{id}/status` with `{"status": 1}`. |
| Publishing before child writes finish | Create template, categories, criteria, and rubrics first. |
| Publishing an empty template | Add an active criterion inside an active category first. |
| Correcting `qualitiveAgentId` spelling | Preserve that exact API field spelling. |
| Treating `rubrikScale` as a typo | Preserve the API spelling and match scales to returned rubric IDs. |
| Reusing an agent ID from another tenant | Resolve it from `GET /api/public/v1/agent`. |

## Error quick reference

| Response | What to do |
|---|---|
| `400 ScorecardTemplateCannotPublishEmpty` | Add and activate at least one category and criterion, then confirm a new publish request. |
| `400` | Compare required fields and per-operation enum values with the generated schema. |
| `401` | Confirm the key exists and is valid without printing it. |
| `403` | Explain that the key lacks permission; do not retry unchanged. |
| `404` | Re-list the relevant parent resource and verify ID threading. |
| `500` | Stop the chain; preserve and report the builder journal without secrets. |
