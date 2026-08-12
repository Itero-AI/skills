*Last Edited: 2026-08-12 15:08*

# Learning Path Notes

<!-- gotchas -->
## Learning path gotchas

<!-- fact:tenantuserid-not-id -->
### Assign with `tenantUserId`

A user record contains both `id` and `tenantUserId`. Learning-path assignment and reassignment payloads require `tenantUserId`, not `id`. Sending `id` can silently target the wrong user or return `400`.

List users through `GET /api/public/v1/user`, show both identifiers beside the person's name, and copy only `tenantUserId` into each assignment object.

When a due date is included, send a future UTC date-time. Explain the effect of reassignment before writing because it starts a new attempt rather than continuing the current progress.
<!-- /gotchas -->

<!-- lifecycle -->
## Assignment lifecycle

Use the assign operation for a new assignment or a due-date change that should preserve current progress. Use reassign only when the user intends to start a fresh attempt. Preview the learning path, people, and due date together before either write.
<!-- /lifecycle -->
