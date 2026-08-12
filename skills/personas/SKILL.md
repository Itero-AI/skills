---
name: personas
description: Manage Itero personas through the public API. Use when someone asks to list or inspect personas, create a reusable customer archetype, change a persona, choose a voice, or delete a persona. Triggers include "create a persona," "list personas," "what personas do we have," "update the persona," "delete a persona," "list voices," and "show available voices."
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
  - references/personas.md
---

> **Mandatory API confirmation:** Before every `POST`, `PUT`, `PATCH`, or `DELETE`, show the exact method, URL, and complete payload (`no body` when applicable), then wait for explicit confirmation. For a delete, also show the persona name and stable ID and require the user to confirm that target. This rule also applies when a non-GET operation appears harmless.

# Personas

Use `https://iterogatewayapi.azurewebsites.net` and send `X-API-Key: $ITERO_API_KEY`. Read the key from the environment; never display, log, or paste its value. For complete schemas and examples, open [the generated personas reference](references/personas.md) only when needed.

## Quick start: list personas

Keep collection responses small. Project the fields needed for selection instead of loading the raw response into the conversation.

```bash
curl --fail-with-body --silent --show-error \
  --header "X-API-Key: $ITERO_API_KEY" \
  "https://iterogatewayapi.azurewebsites.net/api/public/v1/persona" \
  | jq '(.items? // .) | map({id, name, personaType, botName, voiceId})'
```

## What do you need?

| Goal | Operation | Guidance |
|---|---|---|
| Find or reuse an archetype | `GET /api/public/v1/persona` | Project IDs and names before choosing. |
| Choose a voice | `GET /api/public/v1/persona/voices` | Filter by `voiceName`, `gender`, or `age`. |
| Create a persona | `POST /api/public/v1/persona` | List existing personas and voices first. |
| Change a persona | `PUT /api/public/v1/persona` | Start from the current complete object. |
| Remove a persona | `DELETE /api/public/v1/persona/{id}` | List its scenarios first; deletion affects them too. See the workflow below. |

## Workflow

1. List existing personas and reuse one when its behavioral archetype fits.
2. Read the relevant operation in [the generated reference](references/personas.md) for exact fields, types, and enums.
3. Use `voiceId` from the voices endpoint in create and update payloads.
4. Keep the persona reusable. Put prospect-specific facts, immediate objections, and one-off circumstances on the scenario.
5. Show the exact request and wait for confirmation before sending a write.
6. Before a delete: fetch `GET /practice-scenario`, project `id`, `practiceScenarioName`, and `personaId`, and list every scenario referencing this persona in the confirmation along with the persona's name and ID. Warn that those scenarios will be deleted with it or orphaned — documentation and field testing disagree on which (see the reference). After a confirmed delete, re-list scenarios and offer to clean up leftovers.
6. Report the returned ID and summarize only the fields that changed.

## Common Mistakes

| Mistake | Correct approach |
|---|---|
| Sending `elevenLabsVoiceId` | Send `voiceId`; the other field is returned for compatibility. |
| Creating a persona for one named prospect | Create a reusable archetype and place instance details on the scenario. |
| Inventing rich context | Ground behavior in the user's playbook or source material. |
| Sending a partial update | Fetch the current object and carry forward fields that must remain. |
| Reading a full list into context | Project the few fields needed or save raw JSON to a file. |

## Error quick reference

| Response | What to do |
|---|---|
| `400` | Compare the payload with the generated request schema, especially enum and required fields. |
| `401` | Confirm the environment variable exists and the key is valid without printing it. |
| `403` | Explain that the key lacks permission; do not retry unchanged. |
| `404` | Re-list personas and verify the stable ID. |
| `500` | Stop, preserve the response details without secrets, and retry only after checking the payload. |
