# Practice Scenario API Reference

A practice scenario pairs a persona with a situation — discovery call, objection handling, live-call simulation, etc. — that a rep practices against. Full CRUD is available via the public API.

## Conventions (all Itero public endpoints)

- Auth: `X-API-Key: <ITERO_API_KEY>` header on every request. Write endpoints need a Manager-role key unless noted.
- `POST`/`PUT`/`GET` return `200 OK` with the DTO; `DELETE` returns `200 OK` empty.
- Validation errors → `400` with per-field messages. After rotating a key, allow up to 5 minutes.
- Host for this resource: https://iterotalktrackapi.azurewebsites.net

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/public/v1/practice-scenario` | Create a scenario |
| `PUT` | `/api/public/v1/practice-scenario` | Update a scenario (id in body) |
| `GET` | `/api/public/v1/practice-scenario` | List scenarios for the current tenant |
| `DELETE` | `/api/public/v1/practice-scenario/{id}` | Delete a scenario |
| `GET` | `/api/public/v1/practice-scenario/call-types` | Catalog of call types |
| `GET` | `/api/public/v1/practice-scenario/communication-styles` | Catalog of communication styles |

---

## Create and Update Payload

Update requests include the fields below plus a required `id`. The `id` is in the request body, not the URL path.

| Field | Type | Required | Notes |
|---|---|---|---|
| `personaId` | int | Yes | Must reference an existing persona. |
| `practiceScenarioName` | string | Yes | Max 500 characters. |
| `practiceScenarioDescription` | string | Yes | Max 1,000 characters. Rep-facing "what to expect" summary — what the rep will walk through, what is in scope, what is out of scope, and how the scenario ends. Do **not** fill with internal bot-behavior notes, design rationale, or scoring commentary — those belong in `keyBehaviorsOpinions` or separate internal docs. |
| `personaBotName` | string | No | Overrides the persona's bot name for this scenario. Correct place to attach a specific individual's name (e.g. `"Raymond"`, `"Fred Johnson"`) to an archetype persona — do not create a new persona per individual. |
| `personaCompany` | string | No | Enterprise personas only. Overrides the persona's company. |
| `personaTitle` | string | No | Enterprise personas only. Overrides the persona's title. |
| `practiceScenarioCallTypeId` | int | Yes | Obtain IDs from `GET /practice-scenario/call-types`. Always fetch at runtime; do not hardcode. |
| `practiceScenarioCommunicationStyleId` | int | Yes | Must be `> 0`. Obtain IDs from `GET /practice-scenario/communication-styles`. GET responses on older scenarios may return `0` — PUT validators reject `0`, so any update flow must supply a valid ID (never echo back the zero). |
| `endCallFunctionExpression` | string | No | Expression defining when the call ends. |
| `practiceScenarioType` | int | Yes | See [`PracticeScenarioType`](#practicescenarotype) enum. Cannot be changed after the scenario is saved. |
| `keyBehaviorsOpinions` | string | Required when `practiceScenarioType` is `0`, `1`, or `3` | Hard limit: **4,000 characters** — check length before every write. Describes the **bot** (the customer/prospect counterparty), not the rep. See [Authoring `keyBehaviorsOpinions`](#authoring-keybehaviorsopinions). Must be `null` when type is `2` (LiveCallSimulation). |
| `transcript` | string | Required when `practiceScenarioType` is `2` | Required for LiveCallSimulation; leave `null` otherwise. |
| `omitFromScoring` | bool | Yes | Default `false`. |
| `dialogueStartSetting` | int | Yes | See [`DialogueStartSetting`](#dialoguestartsetting) enum. |
| `starterLine` | string | No | Max 500 characters. Used only when `dialogueStartSetting` is `1` (ProspectPredefined). |
| `activityHistories` | array | No | Array of `PracticeScenarioActivityHistoryDto`. |
| `internalSystems` | array | No | Array of `PracticeScenarioInternalSystemDto`. See [internalSystems](#internalsystems) section. |
| `scorecardTemplateId` | int | No | Must be positive if provided. Links this scenario to a scorecard template. |

---

## Enums

### `PracticeScenarioType`

| Value | Name | Description |
|---|---|---|
| `0` | CommonScenario | End-to-end conversation. The default scenario shape — rep practices a full call from open to close. |
| `1` | ObjectionHandling | Batting-cage drill. Prospect throws one objection, rep responds, scenario ends shortly after the response. **Not a full conversation** — scope it tight. |
| `2` | LiveCallSimulation | Driven by a pasted transcript rather than `keyBehaviorsOpinions`. The `transcript` field is **required**; `keyBehaviorsOpinions` must be `null`. |
| `3` | FocusScenario | A slice of a call (one transition, one talk-track section) — not end-to-end. Use when reps need to drill a specific moment without context-switching through a whole call. |

> **Note:** `practiceScenarioType` cannot be changed after a scenario is saved. Pick deliberately.

### `DialogueStartSetting`

| Value | Name | Behavior |
|---|---|---|
| `0` | ProspectDynamic | AI goes first. AI generates a dynamic opening line. (default) |
| `1` | ProspectPredefined | AI goes first. AI says the exact text in `starterLine`. |
| `2` | Representative | User goes first. AI stays silent until the user speaks. |

---

## Authoring `keyBehaviorsOpinions`

`keyBehaviorsOpinions` is the **single most important field** for scenario quality. Hard limit: **4,000 characters** — check before every write. It is a plain string with a required two-subheading structure and a required voice.

### Who it describes

`keyBehaviorsOpinions` describes **the bot** — the AI persona the rep practices against (the customer, prospect, objection-raiser, etc.). It does **not** describe the rep, the script the rep follows, or how the rep should behave.

> **Test:** if a line starts with "The rep should…" or "Your job is to explain…", it's in the wrong field. Rewrite from the bot's perspective or delete it.

### Required structure

The string contains two subheadings, in this order:

1. **Context** — numbered list of facts the persona knows about itself and its situation. Things the bot can truthfully say when asked (identity, age, family, accounts, prior interactions, emotional state, what has and has not been disclosed). Write in second-person ("You are Fred Johnson, 68, retired from…").

2. **Key Behaviors and Opinions** — numbered list of behavioral rules governing how the bot acts during the call. Write in second-person ("You speak bluntly and directly…", "You refuse to share account balances until the rep has…"). These rules shape the bot's replies; the Context block is raw material the rules draw on.

### Required voice

Second-person throughout both subheadings: "You are…", "You react…", "You do not…". Not third-person ("Fred is skeptical…"), not first-person ("I am Fred…"), not imperative ("Be skeptical…").

### Worked example

```
Context:
1. You are Fred Johnson, 68, retired from a middle-management role in Sacramento.
2. Your wife Maria, 66, is also retired. You have two adult children.
3. You attended a $799 estate-planning seminar last month and bought a revocable living trust.
4. Your current advisor is Gary at Edward Jones — you have worked with him for 15 years and you trust him.
5. You have roughly $400–600K in investable assets plus $80K at the credit union. You have not disclosed these numbers to the rep.

Key Behaviors and Opinions:
1. You speak bluntly and directly. You do not fill silence for the rep.
2. You react skeptically to any fiduciary statement until the rep explains specifically what they mean.
3. You protectively defend Gary whenever the rep implies their firm would serve you better.
4. You do not share account balances, statements, or income numbers on the first appointment.
5. You warm up if the rep takes time to ask about your grandchildren before getting into numbers.
```

### Relationship to `activityHistories` and `internalSystems`

In practice, most production scenarios leave `activityHistories` and `internalSystems` as empty arrays and carry all context inside the `keyBehaviorsOpinions` string's Context subheading. The two structured arrays exist for CRM-integration scenarios where prior activity or system-of-record attributes are fed in programmatically; for standard persona-driven practice they are redundant with the Context block.

---

## Response

Created or retrieved scenarios return the full payload plus an integer `id`. List returns an array of the same shape.

---

## Nested Types

### `PracticeScenarioActivityHistoryDto`

| Field | Type | Rules |
|---|---|---|
| `id` | int | Required. `id` semantics are not separately verified for this array; send `id: 0` for new entries (matching the `internalSystems` attribute pattern). In practice this array is usually omitted — `keyBehaviorsOpinions` covers the same ground for standard scenarios. |
| `date` | DateTime | Required. |
| `activity` | string | Required. |

### `internalSystems`

`internalSystems` is an array of `PracticeScenarioInternalSystemDto`.

| Field | Type | Rules |
|---|---|---|
| `systemName` | string | Required. Default to `"CRM"` — the rep's system of record (what's on the agent's screen at connect time). |
| `attributes` | array of attribute objects | Required. |

#### Attribute object (nested in `internalSystems[].attributes`)

The API names this type `PracticeScenarionInternalSystemAttributeDto` (note the typo: `Scenarion`). Match the spelling in payloads that reference the type explicitly.

| Field | Type | Rules |
|---|---|---|
| `id` | int | Server-managed database PK. See "Attribute id semantics" below. |
| `attribute` | string | Required. Attribute name. |
| `value` | string | Required. Attribute value. |

#### Attribute id semantics

- **On POST and on PUT for new attributes:** send `id: 0`. The server assigns the real PK on insert.
- **On PUT for existing attributes:** send the server-assigned PK from a prior fetch to overwrite the value/name in place.
- **PUT semantics on the `internalSystems` array are MERGE, not REPLACE.** Sending `internalSystems: []` in a PUT does **not** clear existing attributes — it's a no-op.
- **Stale id > 0** (an id not currently on the scenario) → API returns `500 InternalServerError` with no detail. If a batch mixes existing and new attributes, supply the live IDs for existing slots and `id: 0` for new ones.
- **Deleting a single attribute is Studio-only** — there is no public API path for single-attribute delete.
- **Full overhaul:** prefer `DELETE` + `CREATE` over `PUT` for scenarios that need a complete attribute overhaul. Merge semantics mean stale attributes will otherwise linger.

#### `systemName` content guidance

Default `systemName` to `"CRM"` (the rep's system of record — what's on the agent's screen at connect time). Scale the attributes to the customer type:

| Customer type | Attribute density | Key fields to include |
|---|---|---|
| New lead | Sparse | Lead source, product interest, `"Existing Policies: None"`, quote status — no policy number |
| Existing customer | Rich | Policy numbers, coverage/limits, premium, `"Customer Since"` date, open opportunity |

Instance facts (what a rep would see in their CRM for this specific contact) live in `internalSystems`, not on the persona. Persona carries the archetype; `internalSystems` carries the per-scenario contact record.

---

## Persona Override Fields and Auto-Defaulting

The backend silently auto-populates `personaBotName`, `personaCompany`, and `personaTitle` on scenarios where those fields are `null`, at list/fetch time:

- `personaBotName` is overwritten with the linked persona's `botName`.
- `personaCompany` is overwritten with an AI-generated fake tech company name ("NovaTech Solutions", "Nexora Technologies", "Nimbus Innovations", "NovaCore Technologies").
- `personaTitle` is similarly auto-filled in some cases.

**Practical rule for any fetch+modify+PUT workflow:** before the PUT, explicitly re-set `personaBotName` to the intended value and explicitly null `personaCompany` and `personaTitle` (unless the scenario is genuinely B2B and you want company/title populated). A naive fetch + PUT round-trip persists the auto-defaulted values as real scenario data, clobbering whatever was set at create time.

---

## Web App Behavior

The Itero Scenario Studio accepts supporting materials (PDF, CSV, TXT, or MD files — up to five, 20 MB each, or a pasted transcript) and runs an AI pass that pre-fills `practiceScenarioName`, `practiceScenarioDescription`, `keyBehaviorsOpinions`, `activityHistories`, and `internalSystems`. These enrichment steps are **not exposed via the public API** — an API client must supply the final values directly.

Additional UI behaviors:

- Once a scenario has been saved, `practiceScenarioType` cannot be changed.
- `starterLine` is shown only when `dialogueStartSetting` is `1` (ProspectPredefined).
- Always fetch `/call-types` and `/communication-styles` before creating — never hardcode IDs.
- Some communication styles in the catalog are intentionally negative (hostile, dismissive, aggressive). Picking one makes a scenario excessively difficult — the bot will cut the rep off, refuse to engage, or get visibly angry. Surface style names before creating; warn when a negative one is selected.
- API-created scenarios land in **draft state** in the Scenario Studio until the user clicks "Enable testing" in the UI.
- The Studio's AI enrichment pass writes `keyBehaviorsOpinions` in the same two-subheading, second-person format described above. Hand-authored API payloads should match that format so the Studio UI renders the field as expected.

---

## Errors

| Symptom | Cause | Fix |
|---|---|---|
| `400` — `practiceScenarioCommunicationStyleId must be > 0` | Echoing back a `0` from an older GET response | Fetch the communication-styles catalog and supply a valid ID |
| `400` — `transcript` required | `practiceScenarioType: 2` without `transcript` | Add the `transcript` field |
| `400` — `keyBehaviorsOpinions` required | `practiceScenarioType: 0/1/3` with `keyBehaviorsOpinions: null` | Add the Context + Key Behaviors block |
| `400` — field-level messages | Various validation failures | Read the per-field messages; correct the offending fields |
| `500 InternalServerError` (no detail) on PUT | `internalSystems` contains an `id > 0` that doesn't exist on the scenario (stale or invented) | Fetch the scenario fresh, use the live PKs for existing attributes, `id: 0` for new ones |
| `500` on PUT after fetch+modify | Auto-defaulted persona override fields persisted | Before PUT, re-set `personaBotName` to intended value; null `personaCompany`/`personaTitle` unless B2B |

---

## Request / Response Examples

### Create a scenario

```http
POST /api/public/v1/practice-scenario
X-API-Key: <ITERO_API_KEY>
Content-Type: application/json

{
  "personaId": 541,
  "practiceScenarioName": "Discovery Call — New Lead",
  "practiceScenarioDescription": "You will walk through a first discovery call with a new lead. The prospect is curious but guarded. Your goal is to surface their pain and book a follow-up. This scenario ends after the call close or the prospect disengages.",
  "personaBotName": "Raymond",
  "practiceScenarioCallTypeId": 1,
  "practiceScenarioCommunicationStyleId": 7,
  "practiceScenarioType": 0,
  "dialogueStartSetting": 0,
  "omitFromScoring": false,
  "keyBehaviorsOpinions": "Context:\n1. You are Raymond, 54, owner of a mid-size insurance agency.\n2. You took a cold call from this rep two weeks ago and agreed to a discovery call.\n3. You have three reps who struggle with cross-sell conversations.\n4. Your current training approach is monthly in-person role-play that most reps find repetitive.\n\nKey Behaviors and Opinions:\n1. You are politely skeptical — you've seen software demos before and most don't pan out.\n2. You ask about integration with your existing AMS before talking about anything else.\n3. You warm up noticeably once the rep demonstrates they understand the insurance agency workflow specifically.",
  "scorecardTemplateId": 169,
  "internalSystems": [
    {
      "systemName": "CRM",
      "attributes": [
        { "id": 0, "attribute": "Lead Source", "value": "Inbound web form" },
        { "id": 0, "attribute": "Product Interest", "value": "AI role-play platform" },
        { "id": 0, "attribute": "Existing Policies", "value": "None" },
        { "id": 0, "attribute": "Quote Status", "value": "Not started" }
      ]
    }
  ]
}
```

**Response `200 OK`:**

```json
{
  "id": 892,
  "personaId": 541,
  "practiceScenarioName": "Discovery Call — New Lead",
  ...
}
```

### Update an existing scenario (fetch first, then PUT)

```http
PUT /api/public/v1/practice-scenario
X-API-Key: <ITERO_API_KEY>
Content-Type: application/json

{
  "id": 892,
  "personaId": 541,
  "practiceScenarioName": "Discovery Call — New Lead (v2)",
  "practiceScenarioCommunicationStyleId": 7,
  "personaBotName": "Raymond",
  "personaCompany": null,
  "personaTitle": null,
  "internalSystems": [
    {
      "systemName": "CRM",
      "attributes": [
        { "id": 1045, "attribute": "Lead Source", "value": "Inbound web form" },
        { "id": 1046, "attribute": "Product Interest", "value": "AI role-play platform" },
        { "id": 0, "attribute": "Last Contact Date", "value": "2026-05-15" }
      ]
    }
  ]
  // …all other create fields carried forward unchanged (required on PUT — see payload table above)
}
```

> In the PUT above: IDs `1045` and `1046` are the live PKs from a fresh GET; the new `Last Contact Date` attribute uses `id: 0`.

---

## Source

Controller: `itero-talk-track-api/IteroTalkTrack/IteroTalkTrackApi/Controllers/V1/PublicPracticeScenarioController.cs`
DTOs: `itero-talk-track-api/IteroTalkTrack/Application/Dtos/PublicApi/PublicPracticeScenario*.cs`
