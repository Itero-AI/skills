# Persona API Reference

A persona represents a buyer or consumer profile used as the AI counterparty in practice calls. Full CRUD is available via the public API.

## Conventions (all Itero public endpoints)

- Auth: `X-API-Key: <ITERO_API_KEY>` header on every request. Write endpoints need a Manager-role key unless noted.
- `POST`/`PUT`/`GET` return `200 OK` with the DTO; `DELETE` returns `200 OK` empty.
- Validation errors → `400` with per-field messages. After rotating a key, allow up to 5 minutes.
- Host for this resource: https://iterotalktrackapi.azurewebsites.net

---

## Architecture: personas are archetypes, not individuals

A persona is a **behavioral archetype** — a reusable customer type that defines the default voice, gender, communication style, and general disposition. It is **not** a specific individual (e.g. "Fred Johnson") and equally not a scenario-specific instance (e.g. "uses a card program with 80 cardholders").

**Two kinds of specifics belong at the scenario layer, not the persona:**

- **Individual identity** — name, age, family, accounts, the specific emotional situation. Put these in `practiceScenario.keyBehaviorsOpinions`'s Context subheading.
- **Scenario-instance details** — specific vendor names, exact counts, exact timelines, dollar amounts, named tools. Put these in the scenario's `keyBehaviorsOpinions` Context block. They vary scenario-to-scenario; baking them into the persona causes conflicts when the persona is reused.

Override mechanisms for per-scenario specifics:

- `practiceScenario.personaBotName` — bot name override (e.g. `"Raymond"`, `"Fred Johnson"`).
- `practiceScenario.personaCompany` and `personaTitle` (Enterprise only) — per-scenario company/title overrides.
- `practiceScenario.keyBehaviorsOpinions` — everything else: identity, vendor names, counts, timelines, dollar amounts.

Creating a new persona should be rare: only when a genuinely new behavioral type is needed. If you find yourself creating a persona named after a specific person, stop — reuse an archetype and move the specifics to the scenario.

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/public/v1/persona` | Create a persona |
| `GET` | `/api/public/v1/persona` | List personas for the current tenant |
| `PUT` | `/api/public/v1/persona` | Update a persona (id in body, NOT in URL) |
| `DELETE` | `/api/public/v1/persona/{id}` | Delete a persona |
| `GET` | `/api/public/v1/persona/voices` | List available voices (required for `voiceId`) |

> **`GET /api/public/v1/persona/{id}` is not supported.** The server returns `405 Method Not Allowed` with `Allow: DELETE` (verified 2026-04-20). To retrieve a single persona, call `GET /api/public/v1/persona` and filter client-side by `id`. Similarly, `PUT /api/public/v1/persona/{id}` returns `405` — always send the `id` in the request body, not the URL.

---

## Create and Update Payload

Update requests include all the fields below plus a required `id`. The `id` is in the request body, not the URL path.

| Field | Type | Required | Notes |
|---|---|---|---|
| `personaType` | int | Yes | `0` = Enterprise, `1` = Consumer. |
| `name` | string | Yes | Max 255 characters. Archetype label (e.g. `"SaaS CFO Archetype"`). |
| `botName` | string | Yes | Max 255 characters. Default name the bot uses on calls (overridable per-scenario). |
| `title` | string | Required when `personaType: 0` | Max 255 characters. |
| `companyName` | string | Required when `personaType: 0` | Max 255 characters. |
| `voiceId` | string | Yes | Use a value from `GET /api/public/v1/persona/voices`. Filter by gender before selecting. |
| `gender` | string | Yes | `"Male"` or `"Female"`. |
| `language` | string | Yes | One of `en-US`, `en-GB`, `es-ES`, `es-419`. |
| `email` | string | No | Must be a valid email. Max 255 characters. |
| `mobile` | string | No | Phone number string. |
| `existingProcesses` | string (HTML) | Enterprise — functionally critical | Describes the buyer's current-state professional workflows (policy enforcement, approval flows, manual tasks, FP&A, multi-entity reconciliation). **Does not conceptually apply to Consumer** — leave unset for Consumer personas. Format: H3 sections with `<strong>` titles, nested `<ul>` bullets, `<strong>Impact:</strong>` summary at the end of each section. Voice: persona's first-person. Drives the bot's grounding when reps ask about its work-world. |
| `pains` | string (HTML) | Enterprise — functionally critical | Numbered Challenge/Impact narrative paired to each process area in `existingProcesses`. **Does not conceptually apply to Consumer** — leave unset. Format: `<ol>` with `<strong>`-tagged items, each containing `<strong>Challenge</strong>` + `<strong>Impact</strong>` sub-bullets. Same first-person voice. Drives the persona's complaints during a call. |
| `generalCharacteristics` | string (HTML) | See notes | **Enterprise:** optional supplement to `existingProcesses`/`pains`. **Consumer: this is the primary rich-context field** — put the entire disposition here (4–6 sentences) since Consumer personas skip `existingProcesses`/`pains`. Captures posture, decision style, motivations, and what earns the persona's respect on a cold call. Empty `<p>None</p>` is acceptable for Enterprise when the scenario's `keyBehaviorsOpinions` already covers it. |
| `practiceScenarioCommunicationStyleId` | int | Required when `personaType: 1` | Obtain IDs from `GET /api/public/v1/practice-scenario/communication-styles`. The communication style together with `generalCharacteristics` carries the full disposition for Consumer personas (since `existingProcesses`/`pains` are skipped). |

### Enterprise vs Consumer field summary

| Field | Enterprise (`personaType: 0`) | Consumer (`personaType: 1`) |
|---|---|---|
| `title` | Required | Optional |
| `companyName` | Required | Optional |
| `existingProcesses` | Functionally critical | Leave unset |
| `pains` | Functionally critical | Leave unset |
| `generalCharacteristics` | Optional supplement | Primary rich-context field (4–6 sentences) |
| `practiceScenarioCommunicationStyleId` | Optional | **Required** |

---

## Voices Endpoint

`GET /api/public/v1/persona/voices` returns a bare JSON array (not wrapped in `data` or `items`). Each entry:

| Field | Type | Notes |
|---|---|---|
| `voiceId` | string | Pass this value as `voiceId` on create/update (e.g. `"cartesia-Adam"`). Not `id`. |
| `voiceName` | string | Human-readable label (e.g. `"Adam"`). Not `name`. |
| `gender` | string | `"Male"` or `"Female"`. Filter on this to match the persona's `gender`. |
| `age` | string | Qualitative bucket, e.g. `"Middle Aged"`. |

> **Note:** voices use `voiceId`/`voiceName` rather than the generic `id`/`name`. Helper utilities that look up catalog IDs by a shared `id` field (e.g. a `pick_id` helper in `itero_client.py`) will miss them — extract `voiceId` explicitly when resolving the voices catalog.

---

## Communication Styles (Consumer)

Fetch from `GET /api/public/v1/practice-scenario/communication-styles`. Common mappings for Consumer personas:

| ID | Style name | Use for |
|---|---|---|
| `2` | Friendly and Receptive | Cooperative, agreeable members |
| `3` | Reserved but Cooperative | Anxious, cautious, or hesitant members |
| `4` | Skeptical and Questioning | Distrustful, verification-demanding members |
| `5` | Guarded and Reluctant | Independent, refusal-prone members |
| `6` | Dismissive or Hostile | Frustrated, blunt, or will-hang-up members |
| `8` | Busy and Distracted | Time-pressed, multitasking members |

The rows above are illustrative — verify against the live catalog before using these IDs. Fetch the catalog at runtime via `GET /api/public/v1/practice-scenario/communication-styles`.

---

## Response

A created or retrieved persona returns the full payload plus an auto-generated integer `id`. Fields not provided on create come back as `null`.

```json
{
  "id": 12345,
  "personaType": 0,
  "name": "Alex Stone",
  "botName": "Alex",
  "title": "VP of Sales",
  "companyName": "Acme Corp",
  "voiceId": "cartesia-James",
  "gender": "Male",
  "language": "en-US",
  "email": null,
  "mobile": null,
  "existingProcesses": null,
  "pains": null,
  "generalCharacteristics": null,
  "practiceScenarioCommunicationStyleId": null
}
```

List (`GET /api/public/v1/persona`) returns an array of the same shape.

---

## Side Effects of Persona CRUD

### Auto-spawned scenario catalog

When a persona is created (via `POST /api/public/v1/persona`), the platform automatically creates 18 default `practiceScenario` records attached to that persona — a mix of Common, Objection-handling, and Focus-type templates (e.g. "The Warm-Up", "I'm Busy", "The Elevator Pitch"). These are not returned in the create response; they appear on a subsequent `GET /practice-scenario`.

**The spawn is asynchronous — delayed by minutes.** Do NOT expect the 18 scenarios to exist immediately after `POST /persona` returns. A `GET /practice-scenario` seconds after creation may return 0 spawned scenarios; the full 18 materialize a few minutes later. Cleanup logic that lists-and-deletes immediately after create will find nothing and silently leave 18 orphans. Either poll until the count stabilizes or defer cleanup to the end of a multi-step build and re-verify the scenario count before finishing.

### DELETE does not cascade

`DELETE /api/public/v1/persona/{id}` does not cascade to the auto-spawned scenarios. Deleting a persona leaves those 18 scenarios orphaned at `personaId=0`. They remain listable and renderable in the Scenario Studio UI until explicitly deleted via `DELETE /practice-scenario/{id}`.

**Implication:** if you create a persona and later delete it (e.g. a test persona), you must enumerate and delete its spawned scenarios in a separate pass. A client that only calls `DELETE /persona/{id}` leaves 18 orphan scenarios per persona.

---

## Web App Behavior

Customers creating personas in the Itero web app get single-click generators for `botName`, `companyName` (Enterprise), `email`, and `mobile`. The web app also accepts supporting materials (sales playbooks, ICP docs, training material) and runs an AI enrichment pass that auto-fills `existingProcesses`, `pains`, and `generalCharacteristics`. Both the generators and the enrichment pass are **not exposed via the public API**. An API client must supply these values in the create payload.

Voices are filtered by selected gender in the UI. Client code should call `GET /api/public/v1/persona/voices`, filter by gender, and select a matching voice rather than hardcoding a voice ID.

---

## Errors

| Symptom | Cause | Fix |
|---|---|---|
| `400` — `missing required field(s): title, companyName` | Enterprise persona created without `title`/`companyName` | Add both fields to the payload |
| `400` — `missing required field(s): practiceScenarioCommunicationStyleId` | Consumer persona created without communication style | Fetch the communication-styles catalog and supply a valid ID |
| `400` — bad `voiceId` | Voice ID not in the catalog | Re-run `GET /persona/voices` and pick a valid `voiceId` |
| `400` — `personaType must be 0 or 1` | Unexpected value for `personaType` | Use `0` (Enterprise) or `1` (Consumer) |
| `405 Method Not Allowed` on GET or PUT with `{id}` in URL | `GET /persona/{id}` and `PUT /persona/{id}` are not supported | Use `GET /persona` and filter client-side; send `id` in the body on PUT |
| `404` on delete | Persona ID does not exist | Run `GET /persona` to confirm the ID before deleting |

---

## Request / Response Examples

### Minimal Enterprise payload

```http
POST /api/public/v1/persona
X-API-Key: <ITERO_API_KEY>
Content-Type: application/json

{
  "personaType": 0,
  "name": "Alex Stone",
  "botName": "Alex",
  "title": "VP of Sales",
  "companyName": "Acme Corp",
  "voiceId": "cartesia-James",
  "gender": "Male",
  "language": "en-US"
}
```

**Response `200 OK`:**

```json
{
  "id": 12345,
  "personaType": 0,
  "name": "Alex Stone",
  "botName": "Alex",
  "title": "VP of Sales",
  "companyName": "Acme Corp",
  "voiceId": "cartesia-James",
  "gender": "Male",
  "language": "en-US",
  "email": null,
  "mobile": null,
  "existingProcesses": null,
  "pains": null,
  "generalCharacteristics": null,
  "practiceScenarioCommunicationStyleId": null
}
```

### Minimal Consumer payload

```http
POST /api/public/v1/persona
X-API-Key: <ITERO_API_KEY>
Content-Type: application/json

{
  "personaType": 1,
  "name": "Warm Cooperator",
  "botName": "Margaret",
  "voiceId": "cartesia-Susan",
  "gender": "Female",
  "language": "en-US",
  "practiceScenarioCommunicationStyleId": 2,
  "generalCharacteristics": "<p>I'm an older adult who's always trusted the people who help me with my health. If you tell me what we need to do and when, I'll usually say yes.</p>"
}
```

### Update a persona (fetch first, then PUT)

```http
PUT /api/public/v1/persona
X-API-Key: <ITERO_API_KEY>
Content-Type: application/json

{
  "id": 12345,
  "personaType": 0,
  "name": "Alex Stone",
  "botName": "Alex",
  "title": "VP of Sales",
  "companyName": "Acme Corp",
  "voiceId": "cartesia-James",
  "gender": "Male",
  "language": "en-US",
  "existingProcesses": "<h3><strong>Updated process content</strong></h3><ul><li>Detail here.</li></ul>",
  "pains": "<ol><li><p><strong>Pain area</strong></p><ul><li><strong>Challenge:</strong> description</li><li><strong>Impact:</strong> description</li></ul></li></ol>",
  "generalCharacteristics": "<p>Updated characteristics.</p>",
  // …all other fields carried forward from the fetched persona
}
```

> PUT requires the **complete** payload, not a partial patch. Fetch the persona first with `GET /api/public/v1/persona`, filter by id, modify the fields you want to change, and send the full object.

> For Enterprise personas, omit `practiceScenarioCommunicationStyleId` entirely on PUT (behavior with an explicit `null` is unverified).

### Delete a persona

```http
DELETE /api/public/v1/persona/12345
X-API-Key: <ITERO_API_KEY>
```

**Response `200 OK` (empty body)**

> Remember: after DELETE, enumerate and delete the auto-spawned scenarios separately — they are not cascaded.

---

## Source

Controller: `itero-talk-track-api/IteroTalkTrack/IteroTalkTrackApi/Controllers/V1/PublicPersonaController.cs`
DTOs: `itero-talk-track-api/IteroTalkTrack/Application/Dtos/PublicApi/PublicPersona*.cs`
