# User API Reference

Single-user lifecycle management (list, create, update, activate/deactivate, delete) for the current tenant. Bulk CSV import belongs to a separate surface — see the `upload-users` skill and its [user-import-api.md](../../upload-users/references/user-import-api.md).

## Conventions (all Itero public endpoints)

- Auth: `X-API-Key: <ITERO_API_KEY>` header on every request. Write endpoints need a Manager-role key unless noted.
- `POST`/`PUT`/`GET` return `200 OK` with the DTO; `DELETE` returns `200 OK` empty.
- Validation errors → `400` with per-field messages. After rotating a key, allow up to 5 minutes.
- Host for this resource: https://iterotenantapi.azurewebsites.net

> **Role deviation: every endpoint in this reference requires an Owner-role API key.** The conventions block above states the Manager default; it does not apply here. All four `/api/public/v1/user` endpoints are documented as requiring Owner.

---

## Endpoints

| Method | Path | Auth Role | Description |
|---|---|---|---|
| `GET` | `/api/public/v1/user` | Owner | List users in the caller's tenant. Accepts optional `?role=` and `?isActive=` filters. |
| `POST` | `/api/public/v1/user` | Owner | Create a single user. Sends an invitation email. |
| `PUT` | `/api/public/v1/user` | Owner | Update an existing user. The user `id` is passed in the request body (no path param). |
| `DELETE` | `/api/public/v1/user/{id}` | Owner | Delete a user. See the warning below on `{id}` semantics. |

**Legacy listing endpoints:** `/api/Public/v1/get-users` and `/api/Public/v1/get-user-groups` (note capital-P `Public`) are a separate, older listing surface. They are documented in the `upload-users` skill's reference and are not covered here.

---

## Response Schema — `UserPublicDto`

Returned by `GET`, `POST`, and `PUT`.

| Field | Type | Notes |
|---|---|---|
| `id` | integer | The listing identifier (what the bundled CLI accepts on every subcommand). **Not** what `PUT` takes in its `id` body field — that is `tenantUserId` (verified live 2026-06-12). For `DELETE`, see the warning below — which value the path takes is unconfirmed. |
| `tenantUserId` | integer | The tenant-scoped user identifier. This is the value consumed by the learning-paths skill (`POST /api/public/v1/learning-path/{id}/assign`). Do not confuse it with `id`. |
| `createdDate` | string (ISO 8601 UTC) | Date the user record was created. May appear as `0001-01-01T00:00:00` for older records where the field was never populated — treat that value as unknown. |
| `name` | string | Full name of the user. |
| `role` | string | One of the four `Role` enum values. |
| `email` | string | Email address. Immutable after creation — PUT does not accept an `email` field. |
| `isActive` | boolean | Whether the user is active. |
| `groups` | `UserPublicGroupDto[]` | Groups the user belongs to (may be empty). |

**`UserPublicGroupDto`**

| Field | Type | Notes |
|---|---|---|
| `id` | integer | Unique group ID. |
| `name` | string | Display name of the group. |

### `id` vs `tenantUserId`

Every user object exposes two integer identifiers:

- `id` — the global user record identifier. Use it to find users in `GET` output (it is the id the bundled CLI accepts everywhere).
- `tenantUserId` — the tenant-scoped identifier. This is what BOTH write surfaces actually consume: `PUT /api/public/v1/user` requires it in the `id` body field (**verified live 2026-06-12** — sending the DTO `id` returns `404` "user not found"; Itero's endpoint docs are misleading on this in their example data), and learning-path assignment requires it as `tenantUserId`. The bundled CLI hides the trap: you pass the DTO `id`, the script resolves `tenantUserId` before any `PUT`.

---

## Enums

### `Role`

| Value | Billable seat | Notes |
|---|---|---|
| `Representative` | Yes — when `isActive: true` | Standard sales representative. |
| `Manager` | Yes — when `isActive: true` | Manager role. |
| `Coach` | No | Coach role. |
| `Owner` | No | Tenant owner. Also the required API key role for all endpoints in this reference. |

### Per-endpoint role requirements

| Endpoint | Caller's key role required |
|---|---|
| `GET /api/public/v1/user` | Owner |
| `POST /api/public/v1/user` | Owner |
| `PUT /api/public/v1/user` | Owner |
| `DELETE /api/public/v1/user/{id}` | Owner |

---

## GET /api/public/v1/user

Returns all users in the caller's tenant as a JSON array. Both query parameters are optional.

### Query Parameters

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `role` | string | Optional | Filter by role. Must be one of the four `Role` enum values. |
| `isActive` | boolean | Optional | Filter by active status (`true` or `false`). |

---

## POST /api/public/v1/user

Creates a single user in the caller's tenant.

### Request Schema — `PublicUserCreateRequest`

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | **Required** | Full name of the user. |
| `email` | string | **Required** | Email address. Lowercased server-side before persistence. Immutable after creation. |
| `role` | string | **Required** | One of the four `Role` enum values. |
| `isActive` | boolean | Optional | Whether the user should be active on creation. Defaults to `true`. |
| `groups` | string[] | Optional | Group names to assign to the user. Groups that do not yet exist are created automatically. Matching is **case-sensitive** — a near-miss name creates a new group rather than joining an existing one. Run `GET /api/Public/v1/get-user-groups` first to confirm exact titles. |

### Behavior notes

- If a user with the same email already exists in the tenant, the existing record is reused — no error is returned.
- An invitation email is sent to the user upon creation.
- Activating a `Representative` or `Manager` (`isActive: true` with either of those roles) consumes a billable seat. Creating one when the tenant has reached its seat limit returns `400`.

---

## PUT /api/public/v1/user

Updates an existing user. The target user is identified by the `id` field in the request body — there is no path parameter.

### Request Schema — `PublicUserUpdateRequest`

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | integer | **Required** | The `tenantUserId` value from `UserPublicDto` — NOT the DTO `id` (verified live 2026-06-12; the DTO `id` returns `404` "user not found"). Itero's endpoint docs label this field "Tenant-user identifier", which is literally correct even though their example data suggests otherwise. |
| `name` | string | **Required** | Updated full name. |
| `role` | string | **Required** | Updated role. One of the four `Role` enum values. |
| `isActive` | boolean | Optional | Whether the user should be active. Defaults to `true`. |
| `groups` | string[] | Optional | Updated group names. Groups that do not yet exist are created automatically. Matching is case-sensitive. |

### PUT requires the complete object

`PUT` replaces the user's fields with what you send. Omitting `isActive` defaults it to `true` (documented behavior) — so if the user is currently deactivated and you omit `isActive`, they will be reactivated. Always carry the current `isActive` forward explicitly. Similarly for `groups`: auto-create-on-miss is documented, but what happens when the field is omitted entirely is not. Out of caution, always send the current groups list to avoid unintended changes — fetch the user first with `GET` and carry existing values forward.

To deactivate or reactivate a user without touching other fields, use the `activate`/`deactivate` subcommands in the bundled script (they fetch-then-write automatically).

---

## DELETE /api/public/v1/user/{id}

Deletes a user from the caller's tenant.

> **Pending confirmation — do not use in production without verifying these three points:**
>
> 1. **Which `id` does the path take?** Itero's endpoint docs describe `{id}` as the "Tenant-user identifier of the user to delete," which corresponds to the DTO's `tenantUserId` field — but their example data is ambiguous about which of the two identifiers is meant. `PUT`'s body `id` was verified live (2026-06-12) to take `tenantUserId`, which strengthens the `tenantUserId` reading here — but `DELETE` itself remains unverified; passing the wrong value could silently target the wrong user.
>
> 2. **Hard delete or soft delete?** It is not documented whether the record is permanently removed or merely deactivated at the data layer. This is unverified.
>
> 3. **Immediate seat release?** Whether a deleted Representative or Manager immediately frees a billable seat is undocumented.
>
> **Recommended alternative: deactivate instead.** Set `isActive: false` via `PUT` (or the bundled script's `deactivate` subcommand). Deactivation is reversible, has no ambiguity around seat release, and is safe to call from automation. The bundled script refuses live deletes entirely until platform confirms the three points above.

### Path Parameter

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `{id}` | integer | **Required** | Documented as "Tenant-user identifier" (i.e., `tenantUserId`), but the identifier semantics are pending confirmation — see warning above. |

---

## Errors

| Code | Trigger | Notes |
|---|---|---|
| `400` | Missing required fields, invalid email, user not found, or seat limit reached | Per-field validation messages. Seat limit: `400 NotEnoughSeats` for Representative or Manager activation that exceeds the tenant cap. |
| `401` | Missing or invalid API key | Check the `X-API-Key` header value. After rotating a key, allow up to 5 minutes. |
| `403` | API key lacks Owner permissions | All endpoints in this reference require an Owner-role key, not Manager. |
| `500` | Internal server error | Transient — retry after a brief delay. |

---

## Examples

### List users

```http
GET /api/public/v1/user?role=Representative&isActive=true
X-API-Key: <ITERO_API_KEY>
```

**Response `200 OK`:**

```json
[
  {
    "id": 1,
    "tenantUserId": 25,
    "createdDate": "2026-06-11T10:15:00Z",
    "name": "John Doe",
    "role": "Representative",
    "email": "john.doe@example.com",
    "isActive": true,
    "groups": [
      { "id": 4, "name": "Sales East" }
    ]
  },
  {
    "id": 2,
    "tenantUserId": 26,
    "createdDate": "2026-06-10T08:00:00Z",
    "name": "Jane Smith",
    "role": "Manager",
    "email": "jane.smith@example.com",
    "isActive": true,
    "groups": []
  }
]
```

> Values above are illustrative. `id` and `tenantUserId` are tenant-scoped integers and must not be shared across tenants.

### Create a user

```http
POST /api/public/v1/user
X-API-Key: <ITERO_API_KEY>
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "role": "Representative",
  "isActive": true,
  "groups": ["Sales East"]
}
```

**Response `200 OK`:**

```json
{
  "id": 1,
  "tenantUserId": 25,
  "createdDate": "2026-06-11T10:15:00Z",
  "name": "John Doe",
  "role": "Representative",
  "email": "john.doe@example.com",
  "isActive": true,
  "groups": [
    { "id": 4, "name": "Sales East" }
  ]
}
```

> An invitation email is sent automatically. If a user with this email already exists, the existing record is reused.

### Update a user (complete object required)

```http
PUT /api/public/v1/user
X-API-Key: <ITERO_API_KEY>
Content-Type: application/json

{
  "id": 1,
  "name": "John Doe",
  "role": "Manager",
  "isActive": true,
  "groups": ["Sales East"]
}
```

**Response `200 OK`:** Returns the updated `UserPublicDto` (same shape as the create response above).

> Always send the full object. Omitting `isActive` defaults it to `true`. Fetch the current record first and carry all fields forward.

---

## Source

- Controller: `itero-tenant-api/.../Controllers/PublicUserController.cs`
- DTOs: `itero-tenant-api/.../Dtos/PublicApi/UserPublicDto.cs`, `PublicUserCreateRequest.cs`, `PublicUserUpdateRequest.cs`
