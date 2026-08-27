*Last Edited: 2026-08-27 12:00*

# Practice Scenario Notes

<!-- gotchas -->
## Practice scenario gotchas

### Write behavior from the simulated person's point of view

Use `keyBehaviorsOpinions` to describe what the simulated person knows, believes, and tends to do. Keep stable archetype traits on the persona and scenario-specific facts on the scenario. A useful structure is a short `Context` section, a fact block, and behavior rules, written in second person.

For a live-call simulation (`practiceScenarioType: 2`), provide the transcript and do not invent a separate behavior script that conflicts with it. For other scenario types, follow the field-tested authoring rules below to make the practice specific, realistic, and winnable.

An observed (unverified against the current API) limit of about 4,000 characters applies to `keyBehaviorsOpinions`; keep the template and facts concise enough to fit together.

### Conversation-discipline rules (reusable template)

Include a block like this in `keyBehaviorsOpinions` for every scenario type except live-call simulation (`practiceScenarioType: 2`, which follows its transcript) and adapt it to the situation. Each rule prevents an observed realism defect.

- Raise one issue at a time; never stack two concerns in the same turn.
- Answer only one question at a time, then stop.
- Do not volunteer facts — even related ones — until asked.
- You do not know your plan's limits, terms, or technical specifics — guess or say you are not sure, and accept corrections without defending your numbers. You do know the identifiers listed in your facts (account number, date of birth, phone) and can read them back when asked.
- Never say a flat no at a decision point — decline in the future tense ("I'll think about it"). During explanations, respond with "okay" or a question.
- When the rep makes a reasonable attempt to address a concern of yours, let it go — err on the side of letting them succeed. When you decide to move forward, ask a process question: "So what do I need to do?"
- Stay polite and human. Give payment details without fuss once you have consented. Never hang up — stay on the line until the rep ends the call.
- When asked for consent, or whether you understand and agree, answer with one word: "Yes." Never repeat the rep's wording back.
- You only ever speak aloud. Never narrate, no parentheses, no stage directions.

### Fact-block design (the "what you know" section)

- All identity and payment values must be fictional and non-live. Never copy real personal information from source material, and never use usable card or account numbers or real security codes — use clearly synthetic values (for example, a test-range card number).
- One fact per line, under a header ending in "(reveal each fact only when asked)". Bundled facts on one line get spoken in one breath, leaking several answers to one question.
- Absolute dates, never durations: "You bought in 2015," not "11 years ago" — the model botches the arithmetic.
- Write dates in words everywhere they appear (November 27, 2024 — never 11/27/24); numeric formats get spoken absurdly.
- Write every long number in comma-separated groups matching its spoken rhythm, grouped according to the number's actual format: a common card format is four groups of four (4111, 1111, 1111, 1111 — a published test number, not a live BIN); phone numbers use their natural groups; the same applies to account, plan, and reference numbers. Ungrouped digit runs get mangled or looped.
- Identity facts must be present — own date of birth, family birthdays, phone number, email (all synthetic) — or vagueness bleeds into them and the person cannot answer basic verification questions.
- Always supply full payment details (grouped digits, expiry in words, security code — a synthetic card, never a real one) with an instruction to read them steadily when asked. Without them the bot invents a number and can loop digits.
- Cover the attached scorecard's probing questions with facts — each area the rep is scored on probing needs its own line — or the bot has nothing coherent to answer with.
- Internal-record contents mirror the call type. An existing-customer call gets a full record in `internalSystems` that the rep verifies. A fresh or web lead gets a contact stub only, with everything else in the person's own knowledge, plus a line that they do not know technical details and should guess.

### Behavior-rule design

- No conflicting instructions. A "chatty" or talkative trait fights "answer only what's asked," and the bot resolves the conflict by info-dumping. Keep personality flat: "warm, pleasant, and in no hurry."
- Break conditions are triggers or generosity, never judgments. "When they make a reasonable attempt, let it go" works; "when they give a genuine reason" fails closed and creates an unwinnable wall that repeats one deflection forever.
- Deflections are statements, not exits. "Just email me the quote" must not end the call.
- Difficulty is vagueness, not combat. Real held objections shrink over turns, stay polite through the no, and hide the real blocker until directly asked. Hostile personas do not match real calls.
- One negative example beats three positive rules. When banning a behavior, quote the exact forbidden sentence.

### Treat updates as complete-object writes

Fetch the current scenario before an update and carry forward fields that should remain unchanged. Review linked persona, call type, communication style, scorecard, dialogue-start setting, and persona override fields before sending the complete payload.

<!-- fact:scenario-roundtrip-overrides -->
### Do not round-trip synthesized persona overrides

`GET /practice-scenario` can return synthesized values in `personaBotName`, `personaCompany`, and `personaTitle` — auto-filled placeholders (for example an invented company name), not stored scenario data. A naive fetch-then-PUT persists those generated values as real overrides, silently clobbering what was set at create time.

Before any PUT: explicitly set `personaBotName` to the intended value, and set `personaCompany` and `personaTitle` to `null` unless the scenario genuinely needs a B2B company/title override. Show these three fields in the confirmation preview so the user sees exactly what will be stored. (Field-verified 2026-04; re-encoded 2026-08-12.)

List responses can be very large. Follow the shared context-safety rule: project IDs and names for selection, and save the full JSON to a file only when a detailed edit requires it.
<!-- /gotchas -->
