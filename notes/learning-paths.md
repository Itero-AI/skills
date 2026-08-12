*Last Edited: 2026-08-12 15:08*

# Learning Path Notes

<!-- gotchas -->
## Learning path gotchas

<!-- fact:tenantuserid-not-id -->
### Assign with `tenantUserId`

A user record contains both `id` and `tenantUserId`. Learning-path assignment and reassignment payloads require `tenantUserId`, not `id`. Sending `id` can silently target the wrong user or return `400`.

List users through `GET /api/public/v1/user`, show both identifiers beside the person's name, and copy only `tenantUserId` into each assignment object.

When a due date is included, send a future UTC date-time. Explain the effect of reassignment before writing because it starts a new attempt rather than continuing the current progress.

<!-- fact:learning-path-put-reconciles -->
### `PUT /learning-path/{id}` reconciles assignments — omissions unassign people

The update endpoint treats `assignments` as the complete desired set, not a patch. Users omitted from the list have their active assignment removed, and omitting the `assignments` field entirely removes every active assignment on the path. The same replace semantics apply to `stages`.

To change anything else (rename, description, ordering), first call `GET /api/public/v1/learning-path/{id}`, then echo the current `assignments` (each `tenantUserId` with its `dueDate`) and current `stages` back verbatim in the PUT body. Show the user how many assignments the payload preserves before sending; a metadata-only edit that shows `0 assignments preserved` on a path that has assignees is a bug, not a rename.
<!-- /gotchas -->

<!-- lifecycle -->
## Assignment lifecycle

Use the assign operation for a new assignment or a due-date change that should preserve current progress. Use reassign only when the user intends to start a fresh attempt. Preview the learning path, people, and due date together before either write.
<!-- /lifecycle -->
