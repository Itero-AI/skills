---
name: scenarios
description: Manage Itero practice scenarios through the public API. Use when someone asks to list, create, update, connect a scorecard to, or delete a practice scenario, or needs call types or communication styles. Triggers include "create a scenario," "build a roleplay," "make an objection-handling drill," "attach this scorecard," "update the scenario," "delete the scenario," and "list communication styles."
user-invocable: true
license: MIT
metadata:
  author: itero
  version: "2.1.0"
  homepage: https://iteroapp.ai
  source: https://github.com/Itero-AI/skills
inputs:
  - name: ITERO_API_KEY
    description: Itero public API key. A named tenant may use ITERO_API_KEY_<NAME>.
    required: true
references:
  - references/scenarios.md
---

> **Mandatory API confirmation:** Before every `POST`, `PUT`, `PATCH`, or `DELETE`, show the exact method, URL, and complete payload (`no body` when applicable), then wait for explicit confirmation. For a delete, also show the scenario name and stable ID and require the user to confirm that target. This rule also applies when a non-GET operation appears harmless.

# Scenarios

Use `https://iterogatewayapi.azurewebsites.net` and send `X-API-Key: $ITERO_API_KEY`. Read the key from the environment; never display, log, or paste its value. Load [the generated scenarios reference](references/scenarios.md) for exact schemas and enums.

## Quick start: list scenarios safely

Scenario lists can be extremely large. Project only selection fields or redirect the raw JSON to a file; never load the full list into the conversation.

```bash
curl --fail-with-body --silent --show-error \
  --header "X-API-Key: $ITERO_API_KEY" \
  "https://iterogatewayapi.azurewebsites.net/api/public/v1/practice-scenario" \
  | jq '(.items? // .) | map({id, practiceScenarioName, personaId, practiceScenarioType, scorecardTemplateId})'
```

## What do you need?

| Goal | Operation | Guidance |
|---|---|---|
| Find a scenario | `GET /api/public/v1/practice-scenario` | Project fields before selecting a record. |
| List call types | `GET /api/public/v1/practice-scenario/call-types` | Use the returned IDs rather than guessing. |
| List communication styles | `GET /api/public/v1/practice-scenario/communication-styles` | Use the returned IDs in payloads. |
| Create a scenario | `POST /api/public/v1/practice-scenario` | Resolve persona and related IDs first. |
| Update or attach a scorecard | `PUT /api/public/v1/practice-scenario` | Start from the complete current record. |
| Delete a scenario | `DELETE /api/public/v1/practice-scenario/{id}` | Confirm the name and ID. |

## Workflow

1. List scenarios with a projection and identify the intended record or confirm a new one is needed.
2. Resolve the persona, call type, communication style, and scorecard IDs before drafting.
3. Read the exact operation in [the generated reference](references/scenarios.md).
4. Write `keyBehaviorsOpinions` from the simulated person's point of view, following the authoring rules in [the generated reference](references/scenarios.md): conversation-discipline template, fact-block design, and behavior-rule design.
5. Fetch the complete object for an update and change only what the user requested — but never trust the fetched persona overrides: GET can return synthesized `personaBotName`, `personaCompany`, and `personaTitle` values that were never stored. Set `personaBotName` to the intended value and null `personaCompany`/`personaTitle` unless a B2B override is genuinely wanted.
6. Show the exact request — including those three override fields — and wait for confirmation before sending it.

## Common Mistakes

| Mistake | Correct approach |
|---|---|
| Loading hundreds of full scenarios into context | Project IDs, names, and relationship IDs, or save the response to a file. |
| Putting stable personality traits on every scenario | Keep reusable traits on the persona and situation-specific facts on the scenario. |
| Writing behavior from the rep's point of view | Describe what the simulated customer knows, believes, and does. |
| Bundling several facts on one line | One fact per line under a "reveal each fact only when asked" header. |
| Giving the persona a chatty trait alongside reveal rules | Keep personality flat; conflicting instructions make the bot info-dump. |
| Numeric dates or ungrouped digit strings in facts | Write dates in words and long numbers in comma-separated spoken groups. |
| Judgment-based break conditions ("a genuine reason") | Use generous triggers: "when they make a reasonable attempt, let it go." |
| Round-tripping fetched persona overrides in a PUT | GET can synthesize `personaBotName`/`personaCompany`/`personaTitle`; set them deliberately, nulling company/title unless intended. |
| Guessing related IDs or enum values | Read the list endpoints and generated schema first. |
| Sending a partial `PUT` | Carry forward all fields that should remain unchanged. |

## Error quick reference

| Response | What to do |
|---|---|
| `400` | Check required fields, enum values, and referenced persona or scorecard IDs. |
| `401` | Confirm the key is available and valid without printing it. |
| `403` | Explain that the key lacks permission; do not retry unchanged. |
| `404` | Refresh the projected scenario list and verify the ID. |
| `500` | Check the complete payload against the schema, then stop if the service still fails. |
