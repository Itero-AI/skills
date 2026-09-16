*Last Edited: 2026-09-16 16:16*

# Persona Notes

<!-- gotchas -->
## Persona gotchas

<!-- fact:persona-voices-array -->
### Set the voice through `voices`, not the deprecated scalar fields

Personas now carry a `voices` array, where each entry pairs a `provider` with that provider's `voiceId`: `[{"provider": 2, "voiceId": "voice-001"}]`. At least one entry is required on a write, and each provider may appear only once.

The older scalar fields are deprecated. `voiceId` is the Retell id and `elevenLabsVoiceId` the ElevenLabs id; each is merged into `voices` as an entry for its provider, but only when that provider is not already present in the array. Sending both a scalar and a matching `voices` entry means the array wins and the scalar is silently ignored, so pick one — write `voices` and leave the scalars alone.

Read the voice from `voices` too. A persona configured through the array can carry a provider the scalar fields cannot express, in which case `voiceId` is empty even though the persona has a working voice; reporting "no voice set" from the scalar alone is wrong.

Providers are `0` Retell, `1` ElevenLabs, and `2` Itero. Resolve real IDs from `GET /api/public/v1/persona/voices` rather than guessing, and keep each `voiceId` with the provider it belongs to.

<!-- fact:persona-voiceid -->
### The scalar voice fields are the old shape

Before the `voices` array existed, a persona's voice was the scalar `voiceId`, and the verified tenant used it on 19 of its 20 live personas. That remains what older personas carry, so expect to read it — but write through `voices` instead, as described above. `elevenLabsVoiceId` was never a write field; it is a returned compatibility value.

On 2026-08-12, `GET /api/public/v1/persona/voices` returned 170 voices, each carrying `voiceId`, `elevenLabsVoiceId`, `voiceName`, `gender`, and `age`. Voice items now also carry a `voices` array of their own, so a catalogue entry describes the same providers the persona write accepts. The snapshot used to reference the wrong response type here, which is why older guidance listed only the five scalars.

<!-- fact:persona-delete-side-effects -->
### Deleting a persona affects more than the persona

Two sources disagree on what `DELETE /persona/{id}` does to the persona's scenarios. The current API documentation states deletion also removes associated scenarios and dialogue history (a cascade). Field testing (2026-04) observed the opposite: no cascade — the persona's auto-spawned scenarios were left orphaned at `personaId=0`, still visible in the Scenario Studio. Treat the cascade behavior as unverified and assume either outcome is possible.

Related: creating a persona auto-spawns ~18 default practice scenarios attached to it, asynchronously — they can take minutes to appear after `POST /persona`.

Before any persona delete: call `GET /practice-scenario`, project `id`, `practiceScenarioName`, and `personaId`, and list every scenario referencing the persona in the confirmation alongside the persona's name and ID. Tell the user those scenarios will be either deleted with it or orphaned. After a confirmed delete, re-list scenarios and offer to clean up any that were orphaned or left behind.

### Keep persona personality flat and non-conflicting

A talkative or "chatty" trait in `generalCharacteristics` fights per-scenario rules like "answer only what's asked," and the bot resolves the conflict by info-dumping — the single biggest observed realism defect, caused by a well-intentioned trait. Write `generalCharacteristics` as flat, warm phrasing ("warm, pleasant, and in no hurry") and let each scenario's behavior rules control how much the person reveals. The same conflict applies when choosing the scenario's communication style: avoid styles that push talkativeness when the scenario relies on reveal-only-when-asked facts.

### Keep the persona reusable

A persona is a reusable behavioral archetype, not one specific prospect. Put facts that change from one role-play to another—such as a person's exact age, employer, account details, or immediate objection—on the practice scenario instead.

Before creating a persona, list the existing personas and reuse one when it already fits. Before updating, start from the complete current object so required fields are not accidentally cleared.
<!-- /gotchas -->
