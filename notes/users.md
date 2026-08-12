*Last Edited: 2026-08-12 15:08*

# User and CSV Import Notes

<!-- gotchas -->
## User gotchas

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
