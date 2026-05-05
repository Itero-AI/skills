---
name: personas
description: |
  Creates, edits, and deletes Itero personas (the AI counterparties used in
  practice scenarios) via the public API. Use when someone wants to: list the
  personas on the tenant, create a new persona archetype, update an existing
  persona's voice or default fields, or delete an unused persona. Triggers on:
  "create a persona", "list personas", "what personas do we have", "add a new
  archetype", "update the persona", "delete a persona", "list voices",
  "show available voices", or any request to configure Itero personas.
user-invocable: true
---

# Personas Skill

Manage Itero personas via the public API — list, fetch, create, update, delete.
Backed by `scripts/personas.py`.

---

## Critical rule: personas are archetypes, not individuals

A persona is a **behavioral archetype** — a reusable customer type. Examples:
`SaaS CFO Archetype`, `Field-Services Finance Manager`, `Procurement Manager`.

A persona is **NOT** a specific individual like "Fred Johnson" or "Raymond Ramirez".

When a scenario needs a specific person's name, age, family, accounts, or
emotional situation:

- Override the bot name per-scenario via `practiceScenario.personaBotName`
- Put the character's identity in `practiceScenario.keyBehaviorsOpinions`'s
  Context block (second-person, e.g. "You are Fred Johnson, 68, retired…")
- Use `personaCompany` and `personaTitle` for Enterprise per-scenario overrides

If you find yourself about to create a persona named after a specific person,
**stop**. Re-use an archetype and put the identity in the scenario.

---

## Authentication

Reads `ITERO_API_KEY` from `.env`. For multi-tenant repos, pass `--tenant <NAME>`
to use `ITERO_API_KEY_<NAME>` instead.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/personas/scripts/personas.py list [--tenant NAME]
```

---

## Flow 1: List the personas on a tenant

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/personas/scripts/personas.py list [--tenant NAME]
```

Output: id, type (Enterprise / Consumer), name, botName, title, company.

When a user asks "what personas do we have?", run this first. Show the list.
Then ask whether they want to use one of these or create a new archetype.

---

## Authoring rich-context fields (mandatory for Enterprise)

Three fields drive the bot's grounding when reps ask about its world:

- **`existingProcesses`** — How the persona handles things today. Policy enforcement, approval flows, manual tasks, FP&A, multi-entity reconciliation. H3 sections + nested bullets, persona's first-person voice ("I", "we", "our team").
- **`pains`** — Numbered Challenge / Impact narrative paired to each process area. Same H3-or-`<strong>` + bullet format, same first-person voice.
- **`generalCharacteristics`** — 2–4-sentence paragraph: posture, decision authority, motivations, what earns the persona's respect on a cold call.

**Hard rule: don't ship a persona without these filled.** Stub personas (only `name` / `botName` / `voiceId` / etc.) produce shallow, generic bot answers when reps ask "how do you handle that today?" or "what's painful about your current setup?" The bot can only invent details — it can't draw on grounded customer context.

**Hard rule: write at the archetype level, not the scenario level.** Personas are reusable across scenarios. If the persona's `pains` field says "I have 80 Chase Ink cards" and a different scenario reuses the persona with "you have 200 Wells Fargo cards", the bot has a conflict. The persona describes the **pattern**; the scenario's `keyBehaviorsOpinions.Context` carries the **instance**.

| Don't put on a persona | Do put on a persona |
|---|---|
| "Chase Ink", "Citi", "Concur", "NetSuite OneWorld", "Zip", "QBO" — specific vendor names | "Our company's commercial bank's card program", "a legacy expense tool", "our multi-entity ERP", "our procurement workflow tool" |
| "~80 cardholders", "20+ hours/month", "10–12 day close", "$1M cost mandate", "5+ month underwriting" | "dozens of cardholders", "significant time each month", "double-digit business days", "meaningful annual cost", "multi-month delays" |
| "Board presentation in 6 weeks", "PE pushing 4 new locations next quarter" | "Periodic board pressure on operational scalability", "PE-driven expansion creates persistent timeline pressure" |

**Source the patterns from authoritative customer docs**, not training-knowledge guesses or one specific scenario. Sales playbooks, AE discovery frameworks, ICP one-pagers, customer training materials, case studies, competitive differential docs. Read several scenarios across the buyer type to find the *shared* pattern — that's the archetype content.

**If the user wants a stub for testing without doing the source-grounding work**, redirect them: create the persona in the Itero Scenario Studio UI with supporting materials attached — the AI enrichment pass auto-fills the three fields. The public API does not run that enrichment, so API-created stubs stay empty.

### Worked snippet — Enterprise / B2B archetype (CFO)

```html
<h3><strong>Receipt &amp; Expense Capture</strong></h3>
<ul>
<li>Employees capture receipts informally — photographs, emailed PDFs, sometimes paper into a shared folder. There's no point-of-swipe enforcement.</li>
<li>At month-end I reconcile against the bank statement, which shows merchant and amount but rarely itemization, so coding decisions get made from memory.</li>
<li><strong>Impact:</strong> Receipt-chasing eats meaningful hours every month. Coding errors are common because employees aren't trained on the chart of accounts, and I end up re-coding most submissions myself.</li>
</ul>
```

Note: no specific vendor name, no exact hour count, no exact close timeline — those vary scenario-to-scenario. The pattern stays.

`pains` mirrors this with `Challenge` / `Impact` sub-bullets:

```html
<ol>
<li><p><strong>Manual Receipt Chasing</strong>:</p>
<ul>
<li><strong>Challenge:</strong> Employees forget, lose, or submit receipts weeks late, and there's no enforcement at the moment of spend.</li>
<li><strong>Impact:</strong> Significant time every month chasing documentation, plus a close that drags because expense reports are the bottleneck.</li>
</ul></li>
</ol>
```

Reference shape for a production-grade Enterprise archetype: `personas fetch 105 --tenant <NAME>` (or 106) on a tenant where the personas pre-existed our API-create work.

## Authoring Consumer / B2C personas (different field set than Enterprise)

**Consumer personas use a different set of fields than Enterprise.** The `existingProcesses` and `pains` fields above are framed around enterprise-buyer concepts — policy enforcement, approval flows, FP&A, multi-entity reconciliation — that don't conceptually apply to a patient, member, or individual consumer. A Medicare member doesn't have "approval flows"; they have habits and dispositions.

For Consumer personas (`personaType: 1`):

- **Skip `existingProcesses` and `pains`.** They're Enterprise-conceptual. Leave them unset.
- **Put the disposition in `generalCharacteristics`.** This is where the rich content lives for Consumer. 4–6 sentences in the persona's first-person voice covering posture, decision style, what earns their respect, what loses them. Aim for a paragraph the bot can confidently draw on when asked open-ended questions about who they are.
- **Set `practiceScenarioCommunicationStyleId`** (REQUIRED for Consumer). Pick the closest match from `GET /api/public/v1/practice-scenario/communication-styles`. Common mappings:
  - `id: 2` Friendly and Receptive — cooperative, agreeable members
  - `id: 3` Reserved but Cooperative — anxious / cautious / hesitant members
  - `id: 4` Skeptical and Questioning — distrustful / verification-demanding members
  - `id: 5` Guarded and Reluctant — independent / refusal-prone members
  - `id: 6` Dismissive or Hostile — frustrated / blunt / will-hang-up members
  - `id: 8` Busy and Distracted — time-pressed / multitasking members

The same archetype-level discipline applies — and is *easier to violate* on Consumer personas, because objections, care contexts, conditions, and family situations all *feel* like part of "who the member is", but they're not. They're scenario-level.

**Don't put on a Consumer persona** | **Do put on a Consumer persona**
---|---
"I already saw my cardiologist last month" / "I had my A1c done" — *those are scenario openings* | "I trust my doctor and tend to view extra visits as redundant unless someone explains why they're different"
"I want in-home, not video" / "I'm not doing telehealth" — *modality preference is scenario-level* | "I get anxious about technology I'm not familiar with, and I'd rather have someone present than figure out a new format"
"I'm fine, I don't need this" — *that's an objection, not a personality* | "I'm independent and tend to refuse help reflexively until someone reframes it as something I'm choosing"
"I'm 67 and on Medicare Advantage with [carrier]" / "I have diabetes and high blood pressure" | "I'm an older adult who's been navigating the healthcare system for years" *(omit specific age, plan, conditions — let the scenario carry those)*
"I'm caring for my husband who had a stroke" — *specific family situation* | "I'm often juggling competing demands and don't have a lot of slack in my day"

### Three Consumer worked examples

#### Example 1: Warm Cooperator (high-trust, agreeable disposition)

```json
{
  "personaType": 1,
  "name": "Warm Cooperator",
  "botName": "Margaret",
  "voiceId": "cartesia-Susan",
  "gender": "Female",
  "language": "en-US",
  "practiceScenarioCommunicationStyleId": 2,
  "generalCharacteristics": "<p>I'm an older adult who's always trusted the people who help me with my health — my doctor, my insurance, the folks who call to confirm appointments. I don't see why I'd be rude to someone who's just doing their job. If you tell me what we need to do and when, I'll usually say yes. I'm not going to make you jump through hoops, but I do appreciate it when someone takes the time to read back the date and time so I know I've got it right.</p>"
}
```

Note: no care gap, no health plan, no condition, no specific age. The disposition (cooperative, trusting, mildly inattentive to operational detail) is the only durable trait — and it's expressed entirely through `generalCharacteristics` paired with the "Friendly and Receptive" communication style.

#### Example 2: Defensive Skeptic (low-trust, distrustful disposition)

```json
{
  "personaType": 1,
  "name": "Defensive Skeptic",
  "botName": "Robert",
  "voiceId": "cartesia-James",
  "gender": "Male",
  "language": "en-US",
  "practiceScenarioCommunicationStyleId": 4,
  "generalCharacteristics": "<p>I get unsolicited calls every week and most of them are scams. I've learned to be careful — I don't give out my information to strangers, I don't agree to things in the first sixty seconds, and I'll hang up on anyone who sounds rushed or pushy. If you're calling on behalf of my health plan, fine, but you'd better be ready to prove it without acting offended that I asked. I'll respect a calm, professional tone. I won't respect someone who flinches the moment I push back.</p>"
}
```

Note: skepticism here is *dispositional* — it's about how the member screens any caller, not about a specific objection like "is this a scam?" being raised on a specific call.

#### Example 3: Anxious Hesitator (cautious, family-deferring disposition)

```json
{
  "personaType": 1,
  "name": "Anxious Hesitator",
  "botName": "Eleanor",
  "voiceId": "cartesia-Joan",
  "gender": "Female",
  "language": "en-US",
  "practiceScenarioCommunicationStyleId": 3,
  "generalCharacteristics": "<p>I worry about getting things wrong. I'm not comfortable with technology I haven't used before, and I don't like to commit to something on the phone without talking it through with my spouse or one of my adult children first. If you ask me to schedule something today, I'll often ask you to call me back — not to put you off, but because I really do want to think it through. The thing that helps me most is when someone slows down, explains things in plain words, and tells me I can change my mind if I need to.</p>"
}
```

Note: family-deference and tech-anxiety are *dispositional*. Specific tech (Zoom, a particular SMS link) and specific family members (husband Tom, daughter Linda) belong on the scenario, not the persona.

### Conflict-check for Consumer personas

Walk every sentence of `generalCharacteristics` and ask: "If this same persona were reused in a scenario with a different care gap, a different health plan, a different condition, a different family situation, a different specific objection — would this sentence still hold true?"

If a sentence names a specific care type, an exact age, a named tool/product/plan, a specific family member, a specific medical condition, or any other instance-level detail — **move it to the scenario's `keyBehaviorsOpinions.Context`** and replace it on the persona with a pattern-level phrasing. The persona is the disposition; the scenario is the situation.

### Conflict-check before signing off (mandatory)

Before approving the persona payload, walk every line of `existingProcesses` and `pains` and ask:

> "If this same persona were reused tomorrow in a scenario where the prospect has a different vendor, a different cardholder count, a different close timeline, or a different cost mandate — would this line still hold true?"

If a line names a specific tool, an exact count, an exact timeline, an exact dollar figure, or any other specific that varies between real prospects of this archetype — **move it to the scenario's `keyBehaviorsOpinions.Context`** and replace it on the persona with a pattern-level phrasing. No exceptions; the bot's grounding gets noisier the more conflicts it has to reconcile.

---

## Flow 2: Create a persona

### Step 0 — Gather source material before drafting

Ask the user for the customer's sales playbook, AE discovery framework, ICP/persona one-pager, training docs, or case studies. If none are available and the persona is for production use, redirect to the Scenario Studio UI (where the enrichment pass fills `existingProcesses` / `pains` / `generalCharacteristics` from supporting materials automatically). Do NOT proceed with API create on invented content for an Enterprise persona.

### Step 1 — Confirm a new archetype is actually needed

Run `list` first. Show existing archetypes. Ask: "Does one of these fit, or do
you genuinely need a new behavioral type?" If they hesitate, default to reusing
an existing one. New archetypes should be rare.

### Step 2 — Pick a voice

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/personas/scripts/personas.py voices [--tenant NAME]
```

Show the list, ask the user to pick (or pick the first matching voice for the
specified gender/language and confirm).

### Step 3 — Draft rich-context fields from source material

Per [Authoring rich-context fields](#authoring-rich-context-fields-mandatory-for-enterprise), write the three fields drawing from the customer docs gathered in Step 0. Cite source-doc + section per major fact in your scratch draft. Voice: persona's first-person, not Brex/product perspective. HTML format mirrors `personas fetch 105 --tenant <NAME>` (or 106) on a tenant that already has rich personas.

### Step 4 — Build plan.json

Write to `.tmp/persona-plan.json`:

```json
{
  "personaType": 0,
  "name": "SaaS CFO Archetype",
  "botName": "CFO",
  "title": "CFO",
  "companyName": "Acme",
  "voiceId": "<from voices command>",
  "gender": "Male",
  "language": "en-US",
  "existingProcesses": "<h3><strong>...</strong></h3>...",
  "pains": "<ol><li>...</li></ol>",
  "generalCharacteristics": "<p>...</p>"
}
```

| `personaType` | Use for |
|---|---|
| `0` Enterprise | B2B buyer (CFO, VP Finance, Procurement, etc.) — `title` + `companyName` required |
| `1` Consumer | B2C / advisory / individual buyer — `title` + `companyName` optional |

### Step 5 — Render preview, get approval

Show the user a preview of the full payload — type, name, botName, voiceId, gender, language, title/companyName for Enterprise, plus the rich-context fields (print the HTML so they can sanity-check the H3 sections, the Challenge/Impact bullets, and the persona-perspective voice). Wait for approval before any API call.

### Step 6 — Dry-run, then live

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/personas/scripts/personas.py create .tmp/persona-plan.json [--tenant NAME]
# review output, then:
uv run ${CLAUDE_PLUGIN_ROOT}/skills/personas/scripts/personas.py create .tmp/persona-plan.json [--tenant NAME] --live
```

Report the new persona id.

---

## Flow 3: Update a persona

`PUT /api/public/v1/persona/{id}` requires the **complete** payload, not a partial.
Fetch first:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/personas/scripts/personas.py fetch <id> [--tenant NAME]
```

(Note: Itero returns 405 on `GET /persona/{id}`. The `fetch` subcommand lists
all personas and filters client-side — it works around the API limitation.)

Modify the JSON, then update:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/personas/scripts/personas.py update <id> '<complete json payload>' [--tenant NAME] --live
```

---

## Flow 4: Delete a persona

**Safety gate.** Before deleting, list scenarios using this persona. If any are
in active learning paths or certifications, stop and ask the user to confirm.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/personas/scripts/personas.py delete <id> [--tenant NAME] --live
```

---

## When to use other skills instead

- Creating a scenario? Use `/scenarios`. The scenarios skill offers an inline
  "simple persona" shortcut so you don't have to context-switch for archetype
  reuse — only come here when you genuinely need full persona configuration.
- Configuring a scorecard? Use `/scorecards`.

---

## Error Handling

| Error | What to do |
|---|---|
| `missing env var ITERO_API_KEY` | Add `ITERO_API_KEY=<key>` to `.env` |
| `persona id=X not found` | Run `list` to see available IDs |
| `personaType must be 0 or 1` | Set `personaType: 0` (Enterprise) or `1` (Consumer) |
| `missing required field(s): ...` | Fill in the listed fields. Enterprise requires `title` and `companyName`. |
| API 400 on create | Most often a bad `voiceId` — re-run `voices` and pick from the list |
| API 405 on fetch | Expected: `GET /persona/{id}` is not supported. The `fetch` subcommand handles this. |
