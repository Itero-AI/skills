*Last Edited: 2026-08-12 15:08*

# Practice Scenario Notes

<!-- gotchas -->
## Practice scenario gotchas

### Write behavior from the simulated person's point of view

Use `keyBehaviorsOpinions` to describe what the simulated person knows, believes, and tends to do. Keep stable archetype traits on the persona and scenario-specific facts on the scenario. A useful structure is a short `Context` section followed by `Key Behaviors and Opinions`, written in second person.

For a live-call simulation (`practiceScenarioType: 2`), provide the transcript and do not invent a separate behavior script that conflicts with it. For other scenario types, provide enough behavioral direction to make the practice specific and winnable.

### Treat updates as complete-object writes

Fetch the current scenario before an update and carry forward fields that should remain unchanged. Review linked persona, call type, communication style, scorecard, dialogue-start setting, and persona override fields before sending the complete payload.

<!-- fact:scenario-roundtrip-overrides -->
### Do not round-trip synthesized persona overrides

`GET /practice-scenario` can return synthesized values in `personaBotName`, `personaCompany`, and `personaTitle` — auto-filled placeholders (for example an invented company name), not stored scenario data. A naive fetch-then-PUT persists those generated values as real overrides, silently clobbering what was set at create time.

Before any PUT: explicitly set `personaBotName` to the intended value, and set `personaCompany` and `personaTitle` to `null` unless the scenario genuinely needs a B2B company/title override. Show these three fields in the confirmation preview so the user sees exactly what will be stored. (Field-verified 2026-04; re-encoded 2026-08-12.)

List responses can be very large. Follow the shared context-safety rule: project IDs and names for selection, and save the full JSON to a file only when a detailed edit requires it.
<!-- /gotchas -->
