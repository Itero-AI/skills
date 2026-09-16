# Changelog

## 2.2.0 — 2026-09-16

Covers the September 2026 Itero API release.

- New skill: `usage` — current plan usage, remaining limits, overage, and invoiced billing history. These two endpoints are **not** served by the gateway; they are a verified host exception on `https://iterotenantapi.azurewebsites.net`, and they require an Owner-role key.
- `scenarios`: added `POST /practice-scenario/duplicate` (copies persona fields, agents, internal systems, and activity histories — but not attached files; the copy is always a draft) and `PATCH /practice-scenario/{id}/status` for publish and return-to-draft.
- **Breaking, and new in this release: only draft scenarios can be updated.** `PUT /practice-scenario` now returns `400` for a published scenario — the previous specification carried no such restriction, so an existing fetch-modify-PUT breaks on any live scenario. Updating one is now unpublish, update, republish, and it is out of practice in between.
- Corrected the create default: a `POST` that omits `status` creates a **draft**. Publishing at create time needs an explicit `status: 0`, which validates every field and provisions voice agents; draft requires only `practiceScenarioName`. `PUT` has no `status` field and never changes the publish state.
- `scenarios`: documented `requiresScreenRecording`, the Scenario Studio screen-recording toggle, on create, update, and read — including that a `PUT` omitting it turns recording off.
- **Scenario publish status is inverted relative to scorecards**: a scenario is published at `0` and draft at `1`, while a scorecard template is draft at `0` and published at `1`. Sending the scorecard convention to a scenario silently does the opposite of what was intended.
- `manage-users` / `upload-users`: documented the `role` enum, which the specification types as a bare string. The four values are `Owner`, `Coach`, `Manager`, and `Representative`. `Owner` is what the old `Manager` role was renamed to, `Coach` is new, and `Manager` is now a narrower front-line role — code assuming the old two-value set silently drops Owners and Coaches.
- `personas`: documented the new `voices` array, which pairs a `provider` (`0` Retell, `1` ElevenLabs, `2` Itero) with that provider's voice ID. The scalar `voiceId` and `elevenLabsVoiceId` fields are now deprecated; at least one `voices` entry is required on a write.
- Recorded verified usage behavior: an empty history array means no invoiced periods, not a missing contract and not zero usage — a tenant with an active contract and live consumption returned `[]`. History rows are one per invoice rather than one per month, so a single month can appear twice.
- Added canonical enum tables for `ProductType`, `PlanType`, `InvoiceStatus`, `VoiceProvider`, and `PracticeScenarioStatus`.
- `tools/fetch-specs.py`: added the tenant-API usage source, narrowed to the usage paths and the schemas they reach, and added `--only` to refresh a subset of snapshots when one upstream document is unavailable.
- Fixed: worked examples for a state-changing operation with no request body now include its query parameters. The scenario status example previously rendered without `?status=`, which would have done nothing if copied.

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
