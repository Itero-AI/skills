---
name: scenarios
description: |
  Creates, edits, and deletes Itero practice scenarios via the public API. Use
  when someone wants to: build a new practice scenario (from a customer
  roleplay doc, a sales playbook, a transcript, or a verbal description); batch-
  create multiple scenarios from one source; attach a scorecard to existing
  scenarios; update or delete a scenario. Triggers on: "create a scenario",
  "build scenarios", "make a roleplay", "add an objection-handling drill",
  "build a scenario from this playbook", "attach the scorecard to these
  scenarios", "update the scenario", "delete the scenario", "list the call
  types", "list communication styles", or any request to configure Itero's
  practice scenarios.
user-invocable: true
---

# Scenarios Skill

Manage Itero practice scenarios via the public API — list, fetch, create
(single or batch), update, attach scorecards, delete. Backed by
`scripts/scenarios.py`.

API-created scenarios show up in the Scenario Studio in **draft state** until
the user clicks "Enable testing" in the UI. The skill seeds the bots; the
Scenario Studio is where the bot behavior gets refined through testing.

---

## Authentication

Reads `ITERO_API_KEY` from `.env`. For multi-tenant repos, pass `--tenant <NAME>`.

---

## The most important field: `keyBehaviorsOpinions`

`keyBehaviorsOpinions` is the single most important field on a scenario — it's
what actually shapes how the bot acts during the call. Required structure:

Two subheadings, in order:

1. **Context** — numbered list of facts the persona knows about itself and its
   situation. Things the bot can truthfully say when asked. Write in second-
   person ("You are Fred Johnson, 68, retired from…").

2. **Key Behaviors and Opinions** — numbered list of behavioral rules. Write in
   second-person ("You speak bluntly and directly.", "You refuse to share
   account balances until the rep has earned it.").

Voice: **second-person throughout**. Not third-person ("Fred is skeptical…"),
not first-person ("I am Fred…"), not imperative ("Be skeptical…").

**Test:** if a line starts with "The rep should…" or "Your job is to explain…",
it's in the wrong field — that's rep-side guidance, not bot behavior. Rewrite
from the bot's perspective or delete it.

---

## Interactive flow: creating scenarios from source materials

When a user wants to build scenarios from a roleplay guide, playbook, or call
transcript, walk them through the choices below. Don't skip steps — the
defaults the user accepts here drive the bot behavior they'll experience later.

### Step 1 — Read the source

Ask for the document, transcript, or playbook. If multiple scenarios are
described in one source (e.g. a six-scenario certification guide), surface that
upfront and confirm the user wants all of them in one batch.

### Step 2 — Persona

Run `personas list` and show the existing archetypes. Ask:

> "Use one of these existing personas, create a simple one inline, or open
> `/personas` for full configuration?"

**Inline simple persona create — STUB ONLY.** Gather: `name`, `botName`, `personaType`
(0=Enterprise, 1=Consumer); for Enterprise, also `title` + `companyName`;
for Consumer, also `practiceScenarioCommunicationStyleId` (required by the API —
pick a sensible default like `id 7` "Conversational and Professional" if the
user doesn't specify; resolve from `scenarios communication-styles`).
Default `voiceId` to the first available voice matching gender + language;
default `gender` to "Male"; default `language` to "en-US". Build a small
plan.json and call `personas create`.

**Critical friction note.** This shortcut produces a STUB persona — `existingProcesses`, `pains`, and `generalCharacteristics` will be empty. The bot will then have nothing to draw on when reps ask "how do you handle that today?" or "what's painful about your current setup?" — answers will be shallow and generic. Stub personas are acceptable ONLY for fast prototyping where the rich-context fields will be backfilled before the persona is used in a real learning path or certification.

Default the user toward one of two paths instead:

> "Two better options: (1) run `/personas` and walk through the full Flow 2 — we'll source the rich-context fields from your customer docs (sales playbook, AE discovery framework, ICP one-pager, etc.) and produce a production-grade persona. (2) Create the persona in the Itero Scenario Studio UI with supporting materials attached — the AI enrichment pass auto-fills the three rich-context fields. Want me to proceed with the inline stub anyway, or take one of those paths?"

If the user explicitly accepts the stub, proceed and flag in the post-create summary that the persona needs enrichment before production use.

### Step 3 — Call type

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/scenarios/scripts/scenarios.py call-types [--tenant NAME]
```

Show the catalog. Ask the user which one fits.

### Step 4 — Communication style

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/scenarios/scripts/scenarios.py communication-styles [--tenant NAME]
```

**Warn the user** before they pick one of the negative styles (hostile,
dismissive, aggressive, etc.). These produce a bot that cuts the rep off,
refuses to engage, or gets visibly angry. Picking one of these accidentally
makes a scenario excessively difficult — only pick a negative style on purpose.

### Step 5 — `practiceScenarioType`

Walk through all four options with what each is actually for:

| Value | Name | What it is |
|---|---|---|
| `0` | Common | End-to-end conversation. The default — full call from open to close. |
| `1` | ObjectionHandling | Batting cage. Prospect throws one objection, rep responds, scenario ends shortly after. **Not a full conversation.** |
| `2` | LiveCallSimulation | Driven by a pasted transcript. **Requires `transcript`** and **must leave `keyBehaviorsOpinions` null.** |
| `3` | FocusScenario | A slice of a call — one transition, one talk-track section, not end-to-end. |

Once a scenario is saved, `practiceScenarioType` cannot be changed. Pick
deliberately.

### Step 6 — `dialogueStartSetting` (who opens the call)

| Value | Name | Behavior |
|---|---|---|
| `0` | ProspectDynamic | AI goes first. AI generates a dynamic opening line. (default) |
| `1` | ProspectPredefined | AI goes first. AI says the exact text in `starterLine`. |
| `2` | Representative | User goes first. AI stays silent until the user speaks. |

If the user picks `1`, ask for the exact `starterLine` text (max 500 chars).

### Step 7 — Scorecard

Ask which scorecard template to attach (or none). Resolve by name in the plan
file via `scorecardName`. The skill cross-resolves to `scorecardTemplateId` by
calling the Scorecard API.

### Step 8 — Tell the user what the skill is auto-generating

Say this verbatim, or close to it:

> I'll generate the `practiceScenarioName`, `practiceScenarioDescription`, and
> `keyBehaviorsOpinions` from your source. The most important field by far is
> `keyBehaviorsOpinions` — that's where you actually drive bot behavior. After
> we create the scenarios, the real iteration happens in the Scenario Studio
> UI: enable testing, talk to the bot, tweak the rules, repeat. The skill
> seeds; the studio refines.

### Step 9 — Build the plan file

Write to `.tmp/<topic>-scenarios.json`. Single-scenario plans use a bare
object; multi-scenario plans use the `defaults` + `scenarios` shape.

**Single scenario:**

```json
{
  "personaName": "SaaS CFO Archetype",
  "practiceScenarioName": "Ramp Displacement (SaaS CFO)",
  "practiceScenarioDescription": "<rep-facing summary of what to expect>",
  "callType": "Cold Call",
  "communicationStyle": "Professional",
  "practiceScenarioType": 0,
  "dialogueStartSetting": 0,
  "scorecardName": "Enhanced Cold Call Scorecard",
  "personaBotName": "CFO",
  "keyBehaviorsOpinions": "Context:\n1. ...\n\nKey Behaviors and Opinions:\n1. ..."
}
```

**Batch with shared defaults:**

```json
{
  "defaults": {
    "personaName": "SaaS CFO Archetype",
    "scorecardName": "Enhanced Cold Call Scorecard",
    "callType": "Cold Call",
    "communicationStyle": "Professional",
    "practiceScenarioType": 0,
    "dialogueStartSetting": 0
  },
  "scenarios": [
    {
      "practiceScenarioName": "Ramp Displacement (SaaS CFO)",
      "practiceScenarioDescription": "...",
      "personaBotName": "CFO",
      "keyBehaviorsOpinions": "Context:\n1. ...\n\nKey Behaviors and Opinions:\n1. ..."
    }
  ]
}
```

Names resolve via API: `personaName` → `personaId`, `callType` →
`practiceScenarioCallTypeId`, `communicationStyle` →
`practiceScenarioCommunicationStyleId`, `scorecardName` →
`scorecardTemplateId`. Raw IDs (`personaId`, `practiceScenarioCallTypeId`,
etc.) pass through unchanged.

### Step 10 — Preview

Render each scenario in this format:

```
[1/6] Ramp Displacement (SaaS CFO)
  persona: SaaS CFO Archetype  (botName: CFO)
  call type: Cold Call    | comm style: Professional
  scenario type: Common (end-to-end)
  dialogue start: ProspectDynamic (AI goes first, dynamic line)
  scorecard: Enhanced Cold Call Scorecard
  description: <one-line summary>

  keyBehaviorsOpinions:
  -----
  Context:
  1. ...
  Key Behaviors and Opinions:
  1. ...
  -----
```

Wait for the user's approval. The full `keyBehaviorsOpinions` print matters —
it's what the user is sanity-checking.

### Step 11 — Dry-run, then `--live`

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/scenarios/scripts/scenarios.py create .tmp/<topic>-scenarios.json [--tenant NAME]
# dry-run output shows resolved IDs and the POST payload
uv run ${CLAUDE_PLUGIN_ROOT}/skills/scenarios/scripts/scenarios.py create .tmp/<topic>-scenarios.json [--tenant NAME] --live
```

Report the new scenario IDs.

### Step 12 — Tell the user what's next (in the UI, not here)

Tell the user verbatim, or close to it:

> Your scenarios are now in the Scenario Studio in **draft state**. To finish:
>
> 1. Open the Scenario Studio.
> 2. For each scenario, click **Enable testing**.
> 3. Talk to the bot once or twice. Notice where the bot's behavior doesn't
>    match what you wanted.
> 4. Tweak `keyBehaviorsOpinions` (and the description) inline. The studio's
>    fast feedback loop is where the real refinement happens — the skill can't
>    do that for you.
> 5. When the bot feels right, you're done. Drop the scenarios into a learning
>    path or certification.

---

## Other flows

### List scenarios

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/scenarios/scripts/scenarios.py list [--tenant NAME]
```

### Fetch one

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/scenarios/scripts/scenarios.py fetch <id> [--tenant NAME]
```

### Update a scenario

`PUT` requires the **complete** payload plus `id`. Fetch first, modify the
JSON, then:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/scenarios/scripts/scenarios.py update <id> '<complete json>' [--tenant NAME] --live
```

GET responses on older scenarios may return `practiceScenarioCommunicationStyleId: 0`.
PUT validators reject `0`, so you must supply a valid ID — don't echo back
the zero.

### Attach a scorecard to an existing scenario

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/scenarios/scripts/scenarios.py attach-scorecard <scenario_id> <template_id> [--tenant NAME] --live
```

### Delete a scenario

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/scenarios/scripts/scenarios.py delete <id> [--tenant NAME] --live
```

---

## Common Failure Modes

These mirror what good roleplay scenarios punish (from the Brex SDR guide and
others). When authoring `keyBehaviorsOpinions`, encode rules that punish:

- Asking multiple closed-ended yes/no questions back-to-back
- Pitch-slapping (hearing one piece of pain and immediately pitching)
- Trashing the prospect's current vendor
- Proposing rip-and-replace without earning the right
- Pushing for a meeting before real pain has been revealed
- Generic value props not tied to anything the prospect actually said

And reward:

- Open-ended questions framed around the prospect's world
- Layered follow-ups that build on a prior answer
- Patience — not pitching on the first piece of pain
- Acknowledging the existing vendor without trashing it
- Tying value statements to specific things the prospect said
- Asking about decision process and other stakeholders

---

## When to use other skills

- Configuring a scorecard? Use `/scorecards`.
- Creating a persona archetype with full configuration? Use `/personas`. The
  Scenarios skill handles simple inline persona create as a shortcut, but
  defers richer configuration.

---

## Error Handling

| Error | What to do |
|---|---|
| `missing env var ITERO_API_KEY` | Add `ITERO_API_KEY=<key>` to `.env` |
| `persona name 'X' not found` | Run `personas list` to see available archetypes |
| `callType 'X' not found` | Run `scenarios call-types` to see the catalog |
| `communicationStyle 'X' not found` | Run `scenarios communication-styles` to see the catalog |
| `scorecardName 'X' not found` | Run `scorecards list` to see templates |
| `LiveCallSimulation (type=2) requires non-empty 'transcript'` | Add a `transcript` field to the scenario |
| `practiceScenarioType=0/1/3 requires 'keyBehaviorsOpinions'` | Add the Context + Key Behaviors block |
| API 400 with `practiceScenarioCommunicationStyleId must be > 0` | The UI's older scenarios sometimes return `0`. Re-resolve from the catalog. |
