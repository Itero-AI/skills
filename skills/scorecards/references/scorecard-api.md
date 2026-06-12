# Scorecard API Reference

A scorecard is a structured evaluation template applied to calls. It is a three-level hierarchy: **template** groups **categories**, which group **criteria**, which automatically spawn **rubrics** (one per scale level).

Full CRUD over all four levels is available via the public API on the practice API host.

## Conventions (all Itero public endpoints)

- Auth: `X-API-Key: <ITERO_API_KEY>` header on every request. Write endpoints need a Manager-role key unless noted.
- `POST`/`PUT`/`GET` return `200 OK` with the DTO; `DELETE` returns `200 OK` empty.
- Validation errors → `400` with per-field messages. After rotating a key, allow up to 5 minutes.
- Host for this resource: https://iteropracticeapi.azurewebsites.net

---

## Endpoints

### Template

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/public/v1/scorecard` | Create a template |
| `PUT` | `/api/public/v1/scorecard` | Update a template (id in body) |
| `GET` | `/api/public/v1/scorecard` | List templates for the current tenant |
| `DELETE` | `/api/public/v1/scorecard/{id}` | Delete a template |

### Category

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/public/v1/scorecard-category` | Create a category |
| `PUT` | `/api/public/v1/scorecard-category` | Update a category (id in body) |
| `GET` | `/api/public/v1/scorecard-category?scorecardTemplateId={id}&type={type}` | List categories, filtered by template and `ScorecardType` |
| `DELETE` | `/api/public/v1/scorecard-category/{id}` | Delete a category |

### Criteria and Rubrics

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/public/v1/scorecard-criteria` | Create a criterion (automatically creates one rubric per scale level) |
| `PUT` | `/api/public/v1/scorecard-criteria` | Update a criterion (id in body) |
| `GET` | `/api/public/v1/scorecard-criteria?templateCategoryId={id}` | List criteria within a category |
| `DELETE` | `/api/public/v1/scorecard-criteria/{id}` | Delete a criterion |
| `GET` | `/api/public/v1/scorecard-criteria/rubrics?criteriaId={id}` | List rubrics for a criterion |
| `PUT` | `/api/public/v1/scorecard-criteria/rubric` | Update a rubric description (path is singular) |

### Related Catalog Endpoints (other services)

These endpoints resolve IDs needed in template payloads. Fetch at runtime; do not hardcode.

| Method | Host | Path | Description |
|---|---|---|---|
| `GET` | `iterotenantapi.azurewebsites.net` | `/api/public/v1/agent` | Agent catalog — resolves `qualitiveAgentId` / `qaAgentId` |
| `GET` | `iterotenantapi.azurewebsites.net` | `/api/Public/v1/get-user-groups` | User groups — resolves `userGroupIds` (note capital P) |
| `GET` | `iterotalktrackapi.azurewebsites.net` | `/api/public/v1/practice-scenario/call-types` | Practice-scenario call types — resolves `practiceScenarioCallTypeIds` |

---

## Template Payload

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | Yes | Display name of the template. |
| `qualitiveAgentId` | int | Yes | Must reference an existing agent. Field is spelled `qualitive` (not `qualitative`) — match exactly. Tenant-scoped; see Agent ID section below. |
| `qaAgentId` | int | Yes | Must reference an existing agent. Tenant-scoped. |
| `callTypes` | array of `CallType` | No | Each element must be a valid `CallType` int. Omit to apply to all call types. |
| `practiceScenarioCallTypeIds` | array of int | No | Filters scoring to specific practice-scenario call types. |
| `meetingKeywords` | array of string | No | Keyword filter for meeting calls. |
| `callTags` | array of `CallTagDto` | No | Each element: `{ "id": int, "name": string }`. |
| `maxCallDurationSeconds` | number | No | |
| `minCallDurationSeconds` | number | No | |
| `userGroupIds` | array of int | No | User groups allowed to use this template. |

Update requests include all the fields above plus a required `id`. The `id` is in the request body, not the URL path.

---

## Category Payload

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | Yes | |
| `scorecardTemplateId` | int | Yes | Parent template. |
| `scorecardType` | int | Yes | See `ScorecardType` enum. Each category is one type — mixed-type categories are not supported. |
| `weight` | int | No | **Omit entirely when authoring** — do not include this field in category payloads (matches SKILL.md: "Omit weight from all category payloads"). Itero defaults to equal weights across categories. Only include when a custom distribution is explicitly required. Qualitative only; must not be negative; maximum `1000`. |

Update requests include all the fields above plus a required `id`.

---

## Criterion Payload

| Field | Type | Required | Notes |
|---|---|---|---|
| `title` | string | Yes | Short label (5–8 words). |
| `criteria` | string | Yes | Full criterion text as it will appear in Itero. |
| `scorecardTemplateCategoryId` | int | Yes | Parent category. |

Update requests include all the fields above plus a required `id`.

Creating a criterion automatically spawns one rubric per scoring scale (`Poor` through `Excellent`, i.e. `RubrikScale` values `0`–`4`). `NotApplicable` (value `5`) is not auto-spawned. Rubrics cannot be created directly — only their descriptions can be updated.

**Rubric descriptions are managed by Itero automatically** — do not PUT rubric descriptions when authoring a new scorecard via API. The platform sets initial state to the literal string `"Empty"` and fills descriptions in via its own enrichment process. The rubric `PUT` endpoint exists for tenant-specific customization after the fact, not for initial authoring.

---

## Rubric

### Returned by `GET /scorecard-criteria/rubrics`

| Field | Type | Notes |
|---|---|---|
| `id` | int | |
| `description` | string | Defaults to the literal string `"Empty"` on creation. |
| `rubrikScale` | int | See `RubrikScale` enum. |
| `scorecardTemplateCriteriaId` | int | Parent criterion. |

### Update Payload for `PUT /scorecard-criteria/rubric`

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | int | Yes | |
| `description` | string | Yes | Must not be empty. |

---

## Enums

### `CallType`

| Value | Name |
|---|---|
| `0` | Activity |
| `1` | Meeting |
| `2` | Practice |

### `ScorecardType`

| Value | Name | Description |
|---|---|---|
| `0` | Qualitative | Weighted subjective scoring with categories and rubrics. |
| `1` | Qa | Quality-assurance checklist. |
| `2` | Screen | Screening variant. |

> **Scope note:** This skill covers Qualitative (0) and QA (1) only. The bundled script iterates `scorecardType` values `(0, 1)` in its category-fetch and delete loops and does not manage Screen-type (2) categories.

### `RubrikScale`

Spelled `RubrikScale` (with a `k`) in payloads — match exactly.

| Value | Name |
|---|---|
| `0` | Poor |
| `1` | NeedsImprovement |
| `2` | Neutral |
| `3` | Good |
| `4` | Excellent |
| `5` | NotApplicable |

---

## Authoring Convention — QA vs Qualitative

When authoring a scorecard via API, the job is to define the template, categories, and criteria. **Rubric descriptions and category weights are managed by Itero automatically** and must not be set via API during authoring.

The distinction between QA and Qualitative is a **content convention** in the criterion text itself:

### Qualitative criteria (`scorecardType: 0`)

Subjective, graded scoring across a 5-level rubric spread. Use for judgment calls: tone, rapport, probing quality, clarity, empathy. Start with "How effectively..." or "How well...".

- Good: `"How effectively did the rep use open-ended questions to uncover the prospect's situation?"`
- Bad: `"Did the rep probe?"` — too binary; rewrite as a quality assessment.

### QA criteria (`scorecardType: 1`)

Binary true/false evaluation — the UI surfaces these as yes/no items. **Phrase the criterion so that true = good and false = bad.** A rep passes the item when the statement is true.

- Good: `"Did the rep deliver the required call-recording disclosure before any substantive question?"`
- Bad: `"Did the rep skip the recording disclosure?"` — inverted; rewrite before creating.
- Use for: compliance items, required actions, observable yes/no behaviors.

### Quick decision

> Can two reasonable reviewers disagree on the answer? → **Qualitative**.
> Can you answer yes/no just by watching the call? → **QA** (binary, true = good).

---

## Lifecycle: Draft → Published

Templates created via the API land in **draft state**. The following lifecycle facts govern when scoring activates:

- **Publish is Studio-only** — there is no API endpoint to publish a template. The user must open the template in the Itero web Studio and publish it there. Confirmed by the platform team as of 2026-06; no publish endpoint is planned.
- **The template DTO carries no status field** — publish state is not verifiable via the API. An API client cannot determine whether a template is draft or published from any `GET /scorecard` response field.
- **Attaching a template to a scenario succeeds while draft** — `POST /practice-scenario` or `PUT /practice-scenario` with a `scorecardTemplateId` referencing a draft template does not fail. The link is created; scoring is just inactive until publish.
- **Scoring activates on publish** — calls against a scenario that references a draft template will not be scored until the template is published in Studio.
- **Recommended sequence:** `POST /scorecard` → publish in Studio → verify scoring → then optionally attach to scenarios via `scorecardTemplateId`. (Attaching while still in draft is legitimate — scoring simply activates on publish regardless of when the scenario link was created.)
- **Renaming a template does not detach scenarios** — updating a template's `name` via `PUT /scorecard` does not affect any scenario that references it by ID.

---

## Agent IDs

`qualitiveAgentId` and `qaAgentId` are **tenant-scoped** — the same integer may refer to different agents across different tenants. Do not share or hardcode IDs across tenant environments.

Resolution order (automated by `scripts/scorecard.py`):

1. Config cache in `.scorecard-config.json`, keyed by tenant name (`DEFAULT` for single-tenant installs).
2. Donor scan — borrows IDs from any existing template in the same tenant. Saves to config so future runs use the cache.
3. Agent-catalog fallback — calls `GET /api/public/v1/agent` on `iterotenantapi` to present the tenant's full agent list for manual selection.

**`.scorecard-config.json` structure.** The file is tenant-keyed at the top level. Each tenant entry holds `qaAgentId` (int) and `qualitiveAgentIds` (a dict keyed by `agentType` string, with `"other"` as the catch-all default). Note the asymmetry: the config stores a **dict** under `qualitiveAgentIds` (plural) so different agent types can map to different qual agents per tenant, while the API payload field is the singular `qualitiveAgentId` — the script resolves the correct integer before posting.

```json
{
  "DEFAULT": {
    "qaAgentId": 14,
    "qualitiveAgentIds": {
      "other": 12
    }
  },
  "ACME": {
    "qaAgentId": 27,
    "qualitiveAgentIds": {
      "other": 25,
      "discovery": 26
    }
  }
}
```

- `DEFAULT` is used when `--tenant` is omitted (single-tenant installs).
- Named keys (e.g., `ACME`) are upper-cased tenant names passed via `--tenant acme`.
- `qualitiveAgentIds.other` is the fallback when the requested `agentType` has no explicit entry.
- The `DEFAULT` key is also where legacy flat-format files (top-level `qaAgentId`/`qualitiveAgentIds`) are migrated on first read.

The agent catalog response shape (for `GET /api/public/v1/agent`):

```json
[
  { "id": 12, "name": "Insurance Qual Agent", "agentType": "...", "tenantId": 5 }
]
```

> The rows above are illustrative. Fetch the live catalog to obtain actual IDs for the tenant.

Legacy flat-format `.scorecard-config.json` files (top-level `qaAgentId`/`qualitiveAgentIds` without tenant keys) are auto-migrated into the `DEFAULT` entry on first read — no manual intervention needed.

---

## Typical Creation Flow

Building a scorecard from scratch:

1. `POST /api/public/v1/scorecard` — create the template with resolved `qualitiveAgentId` and `qaAgentId`.
2. `POST /api/public/v1/scorecard-category` — repeat per category. Set `scorecardType` to `0` (Qualitative) or `1` (Qa) per the convention above. Omit `weight`.
3. `POST /api/public/v1/scorecard-criteria` — repeat per criterion in each category. For QA categories, phrase criteria so true = good.
4. **Publish in Studio** — open the template in the Itero web app and publish it.

Rubric descriptions and category weights are managed by Itero automatically — no further API calls are required after step 3. Only hit `PUT /scorecard-criteria/rubric` or set a custom `weight` when a tenant explicitly needs to override the defaults.

---

## Web App Behavior

Unlike persona and scenario creation, scorecard creation in the Itero web app does not use AI enrichment — it is manual configuration. The UI surfaces drawer dialogs for templates, categories, and criteria that map directly onto the payloads above.

API-created templates appear in the Itero Studio in draft state; the UI is where publish happens.

---

## Soft-Delete Read Lag

After a successful `DELETE /scorecard-criteria/{id}` (`200 OK`), the soft-deleted criterion may still appear in `GET /scorecard-criteria?templateCategoryId=X` responses for some time after deletion — but the UI shows it gone, and a category-level fetch confirms it's gone. Trust the UI / category fetch, not the criteria-list endpoint, when verifying deletion.

---

## Errors

| Symptom | Cause | Fix |
|---|---|---|
| `400` — per-field validation messages | Invalid or missing required field | Read the per-field messages; correct the offending fields |
| `400` on category create | `scorecardTemplateId` references a non-existent template | Run `GET /scorecard` to confirm the template ID |
| `400` on criterion create | `scorecardTemplateCategoryId` references a non-existent category | Run `GET /scorecard-category?scorecardTemplateId={id}&type={type}` to confirm |
| `500` on template create | `qualitiveAgentId` or `qaAgentId` references a non-existent or cross-tenant agent | Fetch the live agent catalog from `iterotenantapi`; do not share agent IDs across tenants |
| Soft-deleted criterion still appears in GET | Read lag after DELETE | Trust the UI / category fetch as authoritative — see Soft-Delete Read Lag above |
| `No existing template with agent IDs found` (script message, not an API error) | Fresh tenant — no donor template carries both agent IDs | The bundled script falls back to printing the tenant agent catalog; pick the qual + QA agents and seed `.scorecard-config.json` — see Agent IDs above |

---

## Request / Response Examples

### Create a template

```http
POST /api/public/v1/scorecard
X-API-Key: <ITERO_API_KEY>
Content-Type: application/json

{
  "name": "Discovery Call Scorecard",
  "qualitiveAgentId": 12,
  "qaAgentId": 14,
  "callTypes": [2]
}
```

> `callTypes: [2]` restricts this template to Practice calls only. Omit `callTypes` entirely to apply the template to all call types.

**Response `200 OK`:**

```json
{
  "id": 301,
  "name": "Discovery Call Scorecard",
  "qualitiveAgentId": 12,
  "qaAgentId": 14,
  "callTypes": [2]
}
```

### Create a category

```http
POST /api/public/v1/scorecard-category
X-API-Key: <ITERO_API_KEY>
Content-Type: application/json

{
  "name": "Discovery",
  "scorecardTemplateId": 301,
  "scorecardType": 0
}
```

**Response `200 OK`:**

```json
{
  "id": 820,
  "name": "Discovery",
  "scorecardTemplateId": 301,
  "scorecardType": 0,
  "weight": null
}
```

### Create a criterion

```http
POST /api/public/v1/scorecard-criteria
X-API-Key: <ITERO_API_KEY>
Content-Type: application/json

{
  "title": "Open-Ended Probing",
  "criteria": "How effectively did the rep use open-ended questions to uncover the prospect's situation?",
  "scorecardTemplateCategoryId": 820
}
```

**Response `200 OK`:**

```json
{
  "id": 4501,
  "title": "Open-Ended Probing",
  "criteria": "How effectively did the rep use open-ended questions to uncover the prospect's situation?",
  "scorecardTemplateCategoryId": 820
}
```

> Rubrics (scales 0–4) are auto-spawned; no further API calls are needed for initial authoring.

### Update a rubric description (post-publish tenant override only)

```http
PUT /api/public/v1/scorecard-criteria/rubric
X-API-Key: <ITERO_API_KEY>
Content-Type: application/json

{
  "id": 9103,
  "description": "Rep asked 3+ layered open-ended questions and reflected answers back."
}
```

**Response `200 OK`:**

```json
{
  "id": 9103,
  "description": "Rep asked 3+ layered open-ended questions and reflected answers back.",
  "rubrikScale": 4,
  "scorecardTemplateCriteriaId": 4501
}
```

### Delete a criterion

```http
DELETE /api/public/v1/scorecard-criteria/4501
X-API-Key: <ITERO_API_KEY>
```

**Response `200 OK` (empty body)**

> After deletion, the criterion may still appear in `GET /scorecard-criteria?templateCategoryId=820` for some time. See Soft-Delete Read Lag above.

### List templates

```http
GET /api/public/v1/scorecard
X-API-Key: <ITERO_API_KEY>
```

**Response `200 OK`:**

```json
[
  {
    "id": 301,
    "name": "Discovery Call Scorecard",
    "qualitiveAgentId": 12,
    "qaAgentId": 14,
    "callTypes": [2],
    // …
  }
]
```

---

## Source

Controllers: `itero-practice-api/Itero.Practice/Itero.Practice.Api/Controllers/v1/Scorecard/PublicScorecard*Controller.cs`
DTOs: `itero-practice-api/Itero.Practice/Application/Dtos/PublicApi/v1/Scorecards/**`
