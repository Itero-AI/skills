*Last Edited: 2026-08-12 15:08*

# Persona Notes

<!-- gotchas -->
## Persona gotchas

<!-- fact:persona-voiceid -->
### Send `voiceId`, not `elevenLabsVoiceId`

Use `voiceId` when creating or updating a persona. The verified tenant used `voiceId` on 19 of its 20 live personas. `elevenLabsVoiceId` is a returned compatibility field; do not send it in a write payload.

On 2026-08-12, `GET /api/public/v1/persona/voices` returned 170 voices. Each voice item used these fields: `voiceId`, `elevenLabsVoiceId`, `voiceName`, `gender`, and `age`.

### Keep the persona reusable

A persona is a reusable behavioral archetype, not one specific prospect. Put facts that change from one role-play to another—such as a person's exact age, employer, account details, or immediate objection—on the practice scenario instead.

Before creating a persona, list the existing personas and reuse one when it already fits. Before updating, start from the complete current object so required fields are not accidentally cleared.
<!-- /gotchas -->
