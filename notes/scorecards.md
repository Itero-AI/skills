*Last Edited: 2026-08-12 15:08*

# Scorecard Notes

<!-- lifecycle -->
## Scorecard lifecycle

Create the template first, then its categories, then each category's criteria. Add or update rubric descriptions only after the criterion exists. Do not publish until every intended child write has succeeded.

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

Create parents before children and keep every returned ID. When a partially created scorecard must be removed, delete only the entities recorded for that run and work in reverse order: criteria, categories, then the template.

The rubric response uses the API spelling `rubrikScale`. Match a requested scale to the returned rubric ID before updating its description.

<!-- fact:scorecard-authoring-defaults -->
### Let the platform own weights and rubric text when authoring

Omit `weight` from category payloads when authoring — Itero defaults to equal weights across categories, and weights apply to qualitative categories only. Include a weight only when a custom distribution is explicitly required; a supplied weight must be between 1 and 1000 (zero and negatives are rejected).

Creating a criterion auto-spawns one rubric per scale `0`–`4` (Poor through Excellent) with the placeholder description `"Empty"`, which the platform fills via its own enrichment. Scale `5` (NotApplicable) is not auto-spawned, and rubrics cannot be created directly. Do not PUT rubric descriptions during initial authoring — the rubric update endpoint exists for tenant-specific customization afterward. (Field-verified 2026-04; re-encoded 2026-08-12.)
<!-- /gotchas -->
