# Changelog

## 2.1.0 — 2026-08-27

- `scenarios`: added field-tested authoring guidance for `keyBehaviorsOpinions` — a reusable conversation-discipline template for voice scenarios, fact-block design rules (one fact per line revealed only when asked, absolute dates, dates in words, digit-grouped numbers, synthetic-only identity and payment values, facts covering the scorecard's probing questions, internal records mirroring the call type), and behavior-rule design rules (no conflicting instructions, trigger-based break conditions, deflections are not exits, difficulty through vagueness, quoted negative examples).
- `personas`: documented keeping persona personality flat and non-conflicting so scenario reveal rules are not overridden by talkative traits.
- Restored the observed ~4,000-character `keyBehaviorsOpinions` limit note (unverified against the current API).

## 2.0.0 — 2026-08-12

- Added `conversations` for searching calls, reading transcripts and evaluations, tagging calls, and starting evaluations.
- Moved all Itero API skills to the unified gateway, with the documented practice-host exception for individual evaluation reads and deletes.
- Generated API references from committed OpenAPI snapshots and verified notes so endpoint, schema, enum, and known-behavior documentation stays in sync.
- Consolidated the scorecard builder and HTTP client into one journaled, dry-run-first script, and removed duplicated HTTP clients from knowledge-only skills.
- Updated the user-upload client to use the unified gateway and retained local scripts only where they provide meaningful workflow logic.

## 1.4.0 — 2026-06-11

- New skill: `learning-paths` — list learning paths/certifications, assign and reassign to users.
- New skill: `manage-users` — create, update, activate/deactivate, delete individual users.
- All four Itero API skills now ship an in-skill API reference (`references/` folder).
- Folded in field-tested guidance: internalSystems merge semantics and CRM defaults, keyBehaviorsOpinions calibration rules and 4,000-char limit, scorecard draft→publish lifecycle, fresh-tenant agent-ID bootstrap.
- Fixed: install docs (marketplace name, step naming, broken anchors), script paths under manual/non-Claude installs.

## 1.3.0 — 2026-05-05

- Added doc-prep skills (doc-optimizer, doc-consolidator); switched all skills to uv.
