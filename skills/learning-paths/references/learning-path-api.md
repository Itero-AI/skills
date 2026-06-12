# Learning Path API Reference

Learning Paths and Certifications are structured training sequences assigned to tenant users. The public API provides read access plus assign/reassign operations. **There is no public API for creating, editing, or deleting learning paths — those are authored exclusively in the Itero Studio.**

## Conventions (all Itero public endpoints)

- Auth: `X-API-Key: <ITERO_API_KEY>` header on every request. Write endpoints need a Manager-role key unless noted.
- `POST`/`PUT`/`GET` return `200 OK` with the DTO; `DELETE` returns `200 OK` empty.
- Validation errors → `400` with per-field messages. After rotating a key, allow up to 5 minutes.
- Host for this resource: https://iteropracticeapi.azurewebsites.net

---

## Endpoints

All four endpoints require a Manager-role API key.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/public/v1/learning-path` | List all learning paths and certifications for the current tenant. Accepts optional `?type=` filter. |
| `GET` | `/api/public/v1/learning-path/{id}` | Retrieve full details of a single learning path, including its stages and current assignments. |
| `POST` | `/api/public/v1/learning-path/{id}/assign` | Assign one or more users to a learning path. Updates due date only when the user already has an active assignment. |
| `POST` | `/api/public/v1/learning-path/{id}/reassign` | Reassign one or more users, canceling any active assignment and starting a fresh one. |

**Note on assign/reassign responses:** Both `POST` endpoints return `200 OK` with **no response body**. This is a deviation from the general convention above, which states that `POST` returns `200 OK` with the DTO.

---

## Enums

### `LearningPathType`

Used as the `?type=` query parameter on the list endpoint and returned in every response as the `type` field.

| Value | Name | Description |
|---|---|---|
| `0` | Learning Path | Standard, untimed learning path |
| `1` | Certification | Certification — pass thresholds are enforced and a failed run can be retried if `isRetriable` is `true` |

### `LearningPathAssignmentStatus`

Returned in `PublicLearningPathAssignmentDto.status` (details endpoint) and determined by the assign/reassign operations.

| Value | Name | Description |
|---|---|---|
| `0` | New | Assignment created; no stage started yet |
| `1` | InProgress | At least one stage has been started or completed |
| `2` | Overdue | Past `dueDate` and not finished |
| `3` | Completed | All stages finished and pass thresholds met |
| `4` | Failed | All stages finished but pass thresholds were not met |
| `5` | Canceled | Assignment was canceled (e.g., via the reassign endpoint) |

---

## Response Schemas

### `PublicLearningPathDto` (list endpoint)

| Field | Type | Notes |
|---|---|---|
| `id` | integer | Unique identifier of the learning path |
| `title` | string | Display name |
| `description` | string | Optional long description |
| `isOrdered` | boolean | Whether stages must be completed in order |
| `isRetriable` | boolean | Whether a failed Certification can be retried |
| `requiredTalkTime` | number or null | Required cumulative talk time across all stages, in seconds. `null` when not set. |
| `stagesAmount` | integer | Number of stages in the learning path |
| `qualitativeScoreThreshold` | integer or null | Minimum qualitative score required to pass. `null` when not set. |
| `qaScoreThreshold` | integer or null | Minimum QA score required to pass. `null` when not set. |
| `type` | `LearningPathType` | See enum table above |

### `PublicLearningPathDetailsDto` (details endpoint)

All fields from `PublicLearningPathDto` except `stagesAmount`, plus:

| Field | Type | Notes |
|---|---|---|
| `stages` | `PublicLearningPathStageDto[]` | Ordered list of stages in the learning path |
| `assignments` | `PublicLearningPathAssignmentDto[]` | Users currently assigned to this learning path |

#### `PublicLearningPathStageDto`

| Field | Type | Notes |
|---|---|---|
| `id` | integer | Unique identifier of the stage |
| `orderIndex` | integer | Zero-based position of this stage within the learning path |
| `practiceScenarioId` | integer | ID of the practice scenario the stage runs |

#### `PublicLearningPathAssignmentDto`

| Field | Type | Notes |
|---|---|---|
| `tenantUserId` | integer | ID of the assigned user within the tenant |
| `dueDate` | string (ISO 8601 UTC) or null | UTC due date for the assignment. `null` when no due date was set. |
| `status` | `LearningPathAssignmentStatus` | See enum table above |

---

## Request Schema (assign and reassign)

Both `POST /{id}/assign` and `POST /{id}/reassign` accept the same body shape.

**Model:** `AssignLearningPathPublicRequest`

| Field | Type | Required | Notes |
|---|---|---|---|
| `assignments` | `AssignLearningPathItem[]` | **Required** | Must be non-empty |

**`AssignLearningPathItem`**

| Field | Type | Required | Notes |
|---|---|---|---|
| `tenantUserId` | integer | **Required** | Must be > 0. See warning below. |
| `dueDate` | string (ISO 8601 UTC) | Optional | Required when provided to be in the future. See date format note below. |

### `tenantUserId` — not `id`

The value for `tenantUserId` comes from the **tenant API user list's `tenantUserId` field**, not its `id` field. The tenant user object exposes two integer identifiers: `id` (the global user record ID) and `tenantUserId` (the tenant-scoped assignment identifier). Passing the `id` value instead of `tenantUserId` will silently target the wrong user or produce a `400`. Use `GET /api/public/v1/user` on `iterotenantapi.azurewebsites.net` to look up users; the `tenantUserId` column is the one to pass here. (Note: that tenant-API lookup endpoint is documented as requiring an Owner-role key, unlike the learning-path endpoints themselves, which need Manager.)

### `dueDate` format

`dueDate` is optional. When provided:

- Format: ISO 8601 UTC date-time string, e.g., `"2026-07-15T23:59:59Z"`.
- The value **must be in the future** at the time of the request; past dates return `400`.
- The bundled script's `--due` flag accepts a bare `YYYY-MM-DD` date and normalizes it to `T23:59:59Z` (end-of-day UTC) before sending. If you pass a full ISO 8601 timestamp directly, the script forwards it unchanged.

---

## Assign vs. Reassign Semantics

### `POST /{id}/assign`

- For each user in the request:
  - If the user has **no active (non-finished) assignment**: creates a new assignment in status `0 New`. An **assignment email is sent** to the newly assigned user.
  - If the user **already has an active assignment**: only the `dueDate` is updated and status is recomputed — `1 InProgress` if any stage is already started or completed, `0 New` otherwise. Progress is preserved. No new assignment email is sent.
- Use this endpoint for first-time assignments or due-date adjustments.

### `POST /{id}/reassign`

- For each user in the request:
  - Any existing non-finished assignment is set to `5 Canceled`. **Progress on the canceled assignment is not preserved.**
  - A brand-new assignment is created in status `0 New`.
  - The cancel-and-create happens in a single transaction.
- Use this endpoint when a user is already partway through a learning path and you need to restart them from scratch (e.g., retakes, remediation).

---

## No Public CRUD

Learning paths and certifications are authored exclusively in the Itero Studio. There are no public API endpoints to create, update, or delete learning paths. The four endpoints above cover read access and user assignment only.

---

## Errors

| Code | Trigger | Notes |
|---|---|---|
| `400` | `assignments` list is empty | Non-empty list is required for assign/reassign |
| `400` | `tenantUserId` is invalid or not found | Fetch users from the tenant API to confirm valid `tenantUserId` values |
| `400` | `dueDate` is in the past | Provide a future UTC date-time or omit `dueDate` |
| `400` | Invalid `type` query param value | Must be `0` or `1` |
| `401` | Missing or invalid API key | Check the `X-API-Key` header value |
| `403` | API key lacks Manager permissions | All four endpoints require a Manager-role key |
| `404` | Learning path ID not found | Verify the ID using `GET /api/public/v1/learning-path` |
| `500` | Internal server error | Transient; retry after a brief delay |

---

## Examples

### List all learning paths

```http
GET /api/public/v1/learning-path
X-API-Key: <ITERO_API_KEY>
```

**Response `200 OK`:**

```json
[
  {
    "id": 12,
    "title": "Discovery Call Certification",
    "description": "Final certification before going live",
    "isOrdered": true,
    "isRetriable": true,
    "requiredTalkTime": 600,
    "stagesAmount": 3,
    "qualitativeScoreThreshold": 70,
    "qaScoreThreshold": 80,
    "type": 1
  }
]
```

> The row above is illustrative. Fetch the live list to obtain actual IDs for the tenant.

### List certifications only

```http
GET /api/public/v1/learning-path?type=1
X-API-Key: <ITERO_API_KEY>
```

### Get learning path details

```http
GET /api/public/v1/learning-path/12
X-API-Key: <ITERO_API_KEY>
```

**Response `200 OK`:**

```json
{
  "id": 12,
  "title": "Discovery Call Certification",
  "description": "Final certification before going live",
  "isOrdered": true,
  "isRetriable": true,
  "requiredTalkTime": 600,
  "qualitativeScoreThreshold": 70,
  "qaScoreThreshold": 80,
  "type": 1,
  "stages": [
    { "id": 101, "orderIndex": 0, "practiceScenarioId": 5001 },
    { "id": 102, "orderIndex": 1, "practiceScenarioId": 5002 }
  ],
  "assignments": [
    { "tenantUserId": 123, "dueDate": "2026-07-01T00:00:00Z", "status": 1 },
    { "tenantUserId": 124, "dueDate": null, "status": 0 }
  ]
}
```

> Values above are illustrative. `tenantUserId` integers are tenant-scoped and must not be shared across tenants.

### Assign users — with and without due date

```http
POST /api/public/v1/learning-path/12/assign
X-API-Key: <ITERO_API_KEY>
Content-Type: application/json

{
  "assignments": [
    { "tenantUserId": 123, "dueDate": "2026-07-15T23:59:59Z" },
    { "tenantUserId": 124 }
  ]
}
```

**Response `200 OK` (empty body)**

> User 123 gets a due date; user 124 is assigned with no deadline. Both receive assignment emails if they are newly assigned. If either already has an active assignment, only the due date is updated.

### Reassign a user

```http
POST /api/public/v1/learning-path/12/reassign
X-API-Key: <ITERO_API_KEY>
Content-Type: application/json

{
  "assignments": [
    { "tenantUserId": 123, "dueDate": "2026-08-01T23:59:59Z" }
  ]
}
```

**Response `200 OK` (empty body)**

> User 123's existing assignment (if any) is set to `5 Canceled` and a fresh assignment is created. Prior stage progress is not carried over.

---

## Source

Controllers: `itero-practice-api/Itero.Practice/Itero.Practice.Api/Controllers/v1/LearningPath/PublicLearningPath*Controller.cs`
DTOs: `itero-practice-api/Itero.Practice/Application/Dtos/PublicApi/v1/LearningPaths/**`
