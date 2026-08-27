*Last Edited: 2026-08-27 12:00*

# Persona Notes

<!-- gotchas -->
## Persona gotchas

<!-- fact:persona-voiceid -->
### Send `voiceId`, not `elevenLabsVoiceId`

Use `voiceId` when creating or updating a persona. The verified tenant used `voiceId` on 19 of its 20 live personas. `elevenLabsVoiceId` is a returned compatibility field; do not send it in a write payload.

On 2026-08-12, `GET /api/public/v1/persona/voices` returned 170 voices. Each voice item used these fields: `voiceId`, `elevenLabsVoiceId`, `voiceName`, `gender`, and `age`.

<!-- fact:persona-delete-side-effects -->
### Deleting a persona affects more than the persona

Two sources disagree on what `DELETE /persona/{id}` does to the persona's scenarios. The current API documentation states deletion also removes associated scenarios and dialogue history (a cascade). Field testing (2026-04) observed the opposite: no cascade — the persona's auto-spawned scenarios were left orphaned at `personaId=0`, still visible in the Scenario Studio. Treat the cascade behavior as unverified and assume either outcome is possible.

Related: creating a persona auto-spawns ~18 default practice scenarios attached to it, asynchronously — they can take minutes to appear after `POST /persona`.

Before any persona delete: call `GET /practice-scenario`, project `id`, `practiceScenarioName`, and `personaId`, and list every scenario referencing the persona in the confirmation alongside the persona's name and ID. Tell the user those scenarios will be either deleted with it or orphaned. After a confirmed delete, re-list scenarios and offer to clean up any that were orphaned or left behind.

### Keep persona personality flat and non-conflicting

A talkative or "chatty" trait on the persona fights per-scenario rules like "answer only what's asked," and the bot resolves the conflict by info-dumping — the single biggest observed realism defect, caused by a well-intentioned trait. Prefer flat, warm phrasing ("warm, pleasant, and in no hurry") and let each scenario's behavior rules control how much the person reveals.

### Keep the persona reusable

A persona is a reusable behavioral archetype, not one specific prospect. Put facts that change from one role-play to another—such as a person's exact age, employer, account details, or immediate objection—on the practice scenario instead.

Before creating a persona, list the existing personas and reuse one when it already fits. Before updating, start from the complete current object so required fields are not accidentally cleared.
<!-- /gotchas -->
