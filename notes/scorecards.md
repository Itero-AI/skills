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
<!-- /gotchas -->
