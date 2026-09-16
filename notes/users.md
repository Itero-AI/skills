*Last Edited: 2026-09-16 16:08*

# User and CSV Import Notes

<!-- gotchas -->
## User gotchas

<!-- fact:user-role-enum -->
### The role field accepts exactly four values

`role` is typed as a bare nullable `string` everywhere it appears — request schemas, response DTOs, and the `role` query filter — and the specification enumerates nothing. The API accepts exactly these four values, spelled and capitalized this way:

| Value | Who it is |
|---|---|
| `Owner` | Full administrative access. This is what the old `Manager` role was renamed to. |
| `Coach` | Added in the September 2026 release. |
| `Manager` | Now a narrower front-line role, not the former administrative one. |
| `Representative` | The practising rep. |

Two consequences follow, and both have already caused real bugs:

- **Never assume the old two-value `{Manager, Representative}` set.** Code that filters or switches on those two silently drops every `Owner` and every `Coach`. One tool lost 212 users across 9 tenants this way before anyone noticed, because the users simply did not appear rather than erroring.
- **`Manager` no longer means administrator.** Creating an administrator means sending `Owner`. Code carrying the old meaning refuses to create one, or creates a front-line user while reporting success.

Because the field is an open string, a misspelled or retired role does not necessarily fail loudly. Verify the role on the returned record after a write instead of trusting the request. To see which roles a tenant actually uses, project the field from `GET /api/public/v1/user` rather than assuming. (Field-verified 2026-09-16: a live tenant returned all four values across 40 users.)

<!-- fact:user-write-owner-role -->
### User writes can require the Owner role

User write endpoints were observed to return `403 Forbidden` for API keys that did not belong to an Owner-role user, although the public specification does not state this requirement. If a user write returns `403`, retry with a key created by someone in that role.

<!-- fact:get-users-alias -->
### Use the canonical user endpoint

The older duplicate user-list route was verified byte-for-byte identical to `/api/public/v1/user`, including its `role` and `isActive` query parameters and response DTO. It adds no capability. Document and call only `GET /api/public/v1/user`; do not expose the legacy route in generated guidance.

### Keep the two user IDs distinct

User responses can include both `id` and `tenantUserId`. Use the identifier required by the specific operation instead of assuming they are interchangeable. Learning-path assignment is the important exception that explicitly requires `tenantUserId`.

### Validate bulk imports before sending them

Send bulk imports to `POST /api/public/v1/user/import-csv` as multipart form data with the CSV in a field named `file`. The upload must be a `.csv` file no larger than 1 MB. Validate required columns, email shape, roles, active status, duplicate emails, and group spelling before the user confirms the upload.

The import does not create duplicate users. Successful creation sends invitation emails, so tell the user before the write. Treat the import as one confirmed operation and report server validation errors without retrying blindly.
<!-- /gotchas -->

<!-- lifecycle -->
## User lifecycle

List and identify the current user before any update or delete. Preview the complete write payload, including role, active status, and groups. Prefer deactivation when the user wants a reversible offboarding action; require a separate explicit confirmation before deletion.
<!-- /lifecycle -->
