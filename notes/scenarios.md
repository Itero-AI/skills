*Last Edited: 2026-08-12 15:08*

# Practice Scenario Notes

<!-- gotchas -->
## Practice scenario gotchas

### Write behavior from the simulated person's point of view

Use `keyBehaviorsOpinions` to describe what the simulated person knows, believes, and tends to do. Keep stable archetype traits on the persona and scenario-specific facts on the scenario. A useful structure is a short `Context` section followed by `Key Behaviors and Opinions`, written in second person.

For a live-call simulation (`practiceScenarioType: 2`), provide the transcript and do not invent a separate behavior script that conflicts with it. For other scenario types, provide enough behavioral direction to make the practice specific and winnable.

### Treat updates as complete-object writes

Fetch the current scenario before an update and carry forward fields that should remain unchanged. Review linked persona, call type, communication style, scorecard, dialogue-start setting, and persona override fields before sending the complete payload.

List responses can be very large. Follow the shared context-safety rule: project IDs and names for selection, and save the full JSON to a file only when a detailed edit requires it.
<!-- /gotchas -->
