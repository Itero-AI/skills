# User Import API Reference

The User resource covers tenant-user listing and bulk-create via CSV upload. Reading users and user groups is supported alongside bulk import. There is no endpoint to create or update an individual user one-at-a-time via the public API — onboarding is bulk-import driven.

Single-user create/update/deactivate/delete: see the `manage-users` skill.

## Conventions (all Itero public endpoints)

- Auth: `X-API-Key: <ITERO_API_KEY>` header on every request. Write endpoints need a Manager-role key unless noted.
- `POST`/`PUT`/`GET` return `200 OK` with the DTO; `DELETE` returns `200 OK` empty.
- Validation errors → `400` with per-field messages. After rotating a key, allow up to 5 minutes.
- Host for this resource: https://iterotenantapi.azurewebsites.net

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET`  | `/api/Public/v1/get-users`       | List users in the caller's tenant. Note capital P in `Public`. |
| `GET`  | `/api/Public/v1/get-user-groups` | List user groups in the caller's tenant. Note capital P. |
| `POST` | `/api/public/v1/user/import-csv` | Bulk-create users in the caller's tenant from a CSV file. Sends invitation emails. Manager role required. |

Path-case quirk: the read endpoints use `/api/Public/v1/...` (capital P); the import endpoint uses `/api/public/v1/...` (lowercase). Routing is case-insensitive on the host, but match the documented case so logs and traces stay clean.

A cross-tenant admin variant of the import endpoint exists for internal Itero use (requires `AdminAccess`); it is not supported by this skill.

---

## GET /api/Public/v1/get-users

Returns a bare JSON array of all users in the caller's tenant.

```json
[
  {
    "id": 1757,
    "tenantUserId": 1942,
    "createdDate": "0001-01-01T00:00:00",
    "name": "Jane Doe",
    "role": "Manager",
    "email": "jane.doe@example.com",
    "isActive": true
  }
]
```

`createdDate` may come back as `0001-01-01T00:00:00` (.NET `DateTime.MinValue`) for older users where the field was never populated — treat that value as "unknown."

Seat consumption is based on active Representatives (`isActive == true && role == "Representative"`). The public API does not expose the tenant's seat cap directly — the skill reads it from `ITERO_TENANT_SEATS` (or `ITERO_TENANT_SEATS_<TENANT>`) in `.env` and uses the user list to count currently active reps.

---

## GET /api/Public/v1/get-user-groups

Returns a bare JSON array of group objects (`[]` on tenants with no groups).

```json
[
  {
    "id": 12,
    "name": "Sales Team"
  }
]
```

> **Field-name casing note:** this is a legacy endpoint with inconsistent casing. The script reads both `id`/`Id` and `name`/`Name` defensively — consumers should do the same.

Use this to discover existing group titles before authoring an import CSV — the import auto-creates a group on miss, and you usually do not want that side-effect. Group name matching on import is **case-sensitive**.

---

## POST /api/public/v1/user/import-csv

Accepts `multipart/form-data` with a single `file` field containing the CSV. Returns `200 OK` with an empty body on success. Unlike the convention above, this endpoint returns an empty body — not a DTO — on success.

### CSV constraints

| Constraint | Value |
|---|---|
| Extension | `.csv` (case-insensitive) |
| Max size | 1 MB (1,048,576 bytes) |
| Min size | > 0 bytes (must be non-empty) |
| Encoding | UTF-8 |
| Delimiter | `,` |
| Header row | Required (first row = column names) |
| Whitespace | Auto-trimmed from every field |
| Culture | `InvariantCulture` (decimal/date parsing rules) |

### Columns

Header row is required. Headers match property names case-insensitively; column order does not matter.

| Column | Type | Required | Validation |
|---|---|---|---|
| `Name` | string | Yes | Non-empty, max 100 chars |
| `Email` | string | Yes | Non-empty, max 100 chars, valid email; **lowercased server-side** before persistence |
| `Role` | enum string | Yes | `Manager` or `Representative` (parsed by name; integers do not work) |
| `IsActive` | bool | No | `true` / `false` (case-insensitive). Integers `1` / `0` are not accepted — use `true` or `false`. Defaults to `true` when column is omitted or value is blank. |
| `UserGroup` | string | No | Group title; auto-created on miss (see below) |

### Role enum

Use the string names verbatim in the CSV:

| Value | Integer |
|---|---|
| `Manager` | 0 |
| `Representative` | 1 |

### UserGroup behavior

| Input | Effect |
|---|---|
| Blank or column omitted | User is created with no group. |
| Exact-case match against an existing group title | User is added to that group. |
| No match (case-sensitive) | A new group is created with that title and the canned description `"This User Group has been created from a CSV file. Please update the description."` |

To avoid accidental group creation, list existing groups first with `GET /api/Public/v1/get-user-groups` and reuse a returned title verbatim.

### Example CSV

```csv
Name,Email,Role,IsActive,UserGroup
Jane Doe,jane.doe@example.com,Manager,true,Sales Team
John Smith,john.smith@example.com,Representative,true,Sales Team
Mary Jones,mary.jones@example.com,Representative,false,
```

> The rows above are illustrative.

### Server-side import flow

1. Parse the CSV. Any parse failure aborts with `400 CSVFileValidation`.
2. Count active reps in the file (`IsActive == true && Role == Representative`).
3. Reject if `currentActiveReps + activeRepsInCsv > tenant.NumberOfSeats` → `400 NotEnoughSeats` with body `"Not enough seats. Available: {N}, requested: {M}."`.
4. Validate every row with FluentValidation. **All-or-nothing**: a single invalid row aborts the entire import.
5. For each row, resolve or create the user group, then create the user. `Email` is lowercased.
6. After every row succeeds, the server fires an invitation email per created user.

### Duplicate-email semantics (open)

The controller's documentation says "Existing users will not be duplicated; the service handles conflicts internally." The actual conflict behavior on a duplicate email lives downstream in the create call — confirm whether it is a no-op, an error, or an update before relying on this guarantee in production. The skill runs `check-duplicates` upstream to avoid hitting this path.

### Response codes

| Code | Meaning |
|---|---|
| `200 OK` | All records imported. Empty body. |
| `400 Bad Request` | Validation subtype: `FileRequired`, `OnlyCsvAllowed`, `FileSizeExceeded`, `CSVFileValidation`, or `NotEnoughSeats`. Body is `ProblemDetails`. |
| `401 Unauthorized` | Missing or invalid API key. |
| `403 Forbidden` | API key lacks the Manager role. |
| `500 Internal Server Error` | Unhandled exception. |

---

## Errors

| Symptom | Cause | Fix |
|---|---|---|
| `missing env var ITERO_API_KEY` (script message) | API key not set | Add `ITERO_API_KEY=<key>` to `.env`. |
| `file is '.xlsx', not .csv` (script message) | Wrong file format | Save as CSV in Excel and re-run. |
| `file is N bytes, over the 1 MB import limit` (script message) | File exceeds the 1 MB limit | Split into smaller batches and run the skill once per batch. |
| `plan not found at .tmp/...` (script message) | Plan file missing | Run `inspect <csv>` first to create the plan. |
| `seat_check.ok is False` (script message, on import) | Seat overflow not resolved | Re-run `check-seats` after deactivating rows or increasing seats. |
| `400 NotEnoughSeats` | Tenant seat count changed between check and import | Re-run `check-seats`. |
| `400 CSVFileValidation` | Row count or CSV shape changed after inspect | Re-run `inspect` to see the current issues. |
| `403 Forbidden` | API key does not have the Manager role | Have an Itero admin promote the key's user. |

---

## Source

- DTO: `itero-tenant-api/.../CsvUserRecordDto.cs`
- Validator: `CsvUserRecordDtoValidator.cs`
- Controller: `PublicUserController.cs`
- Service: `TenantUserApplicationService.cs`
- Role enum: `UserRole.cs`
