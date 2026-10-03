*Last Edited: 2026-10-02 20:00*

# Scorecard Notes

<!-- lifecycle -->
## Scorecard lifecycle

Create a new scorecard with one atomic `POST /api/public/v2/scorecard`. It is created as Draft. Keep its returned nested IDs, review the complete scorecard, then publish with a separately confirmed status PATCH. The v1 per-entity operations are for editing existing scorecards.

<!-- fact:scorecard-publish-api -->
### Publish through the API

Publish a scorecard with:

```http
PATCH /api/public/v1/scorecard/{id}/status
Content-Type: application/json

{"status": 1}
```

`ScorecardTemplateStatus` is `0` for Draft and `1` for Published, and the template DTO includes its `status`. Publishing is rejected with `ScorecardTemplateCannotPublishEmpty` unless the template contains at least one active criterion inside an active category.
<!-- /lifecycle -->

<!-- gotchas -->
## Scorecard gotchas

The template field is spelled `qualitiveAgentId`; use that exact API spelling. Resolve omitted qualitative and QA agent IDs from `GET /api/public/v1/agent`, and never reuse an agent ID merely because it worked in another tenant.

For v1 per-entity edits, create parents before children and keep every returned ID. When partially created v1 content must be removed, delete only entities recorded for that run in reverse order: criteria, categories, then the template.

The rubric response uses the API spelling `rubrikScale`. Match a requested scale to the returned rubric ID before updating its description.

<!-- fact:scorecard-authoring-defaults -->
### Let the platform own default weights and rubric text

Omit `weight` by default for equal weights. Weights apply only to qualitative categories. The v2 specification says 0–1000, but v1 category writes rejected zero and negative values (field-verified 2026-04). Send 1–1000 on either version when an explicit weight is needed.

For v2 qualitative rubrics, omit them or send all five scales 0–4. On v1, a new criterion auto-spawns scales 0–4 with the placeholder `"Empty"`; NotApplicable is not spawned. Rubrics cannot be created directly. The rubric PUT is for later tenant-specific customization. (V1 behavior field-verified 2026-04.)

<!-- fact:scorecard-v2-create -->
### Create a complete draft atomically with v2

`POST /api/public/v2/scorecard` is atomic: on a 400 nothing is saved and no cleanup is needed. Required fields are `name`, `qualitiveAgentId`, `qaAgentId`, `interactionType` and `categories`. Each category needs at least one criterion with a `title` and `criteria`.

Rubrics are qualitative only. Omit them to let the platform AI-generate five levels, or send exactly one rubric for each `rubrikScale` 0–4. Partial, duplicated or NotApplicable sets return 400. QA criteria never carry rubrics. `weight` is qualitative only.

Chat scorecards reject min/max duration (`CallDurationNotAllowedForChat`) and ScreenRecording categories (`ScreenRecordingNotAllowedForChat`). `interactionType` must match the agents. `outputLanguageForScorecardFeedback` values are 0 (Same as transcript), 1 (English) and 2 (Spanish). `callTags` sends `id` and `name`.

Keep returned nested IDs for later v1 edits. Remove a draft with `DELETE /api/public/v1/scorecard/{id}`. (Live-verified 2026-10-02: voice create returned HTTP 200, status 0 Draft, two categories, five explicit rubrics on the qualitative criterion and none on QA; deleting the returned draft ID returned HTTP 200.)

<!-- fact:scorecard-agent-selection -->
### Select agents by type and interaction

Choose agents by `agentType` plus `interactionType` from `GET /api/public/v1/agent`, never by name. Voice uses qualitative type 0 and QA type 3, both interactionType 0. Chat uses qualitative type 4 and QA type 5, both interactionType 1. Never use types 1 (Ask Itero) or 2 (Data Capture). When several coaching agents qualify, ask the user which one to use. (Types 3–5 field-verified 2026-10-02 on one tenant.)

No verified agent type serves ScreenRecording. Do not add a ScreenRecording category or set `screenRecordingAgentId` unless the user supplies the agent ID.
<!-- /gotchas -->
