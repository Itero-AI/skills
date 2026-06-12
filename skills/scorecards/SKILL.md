---
name: scorecards
description: |
  Creates, edits, and deletes Itero scorecard templates, categories, criteria, and rubrics
  via the public API. Use when someone wants to: create a new scorecard (from training
  materials, methodology docs, a verbal description, or an existing scorecard in another
  format); edit an existing scorecard (add a category, add a criterion, rename anything,
  update rubric descriptions, change criterion text); or delete a criterion, category, or
  full template. Triggers on: "create a scorecard", "build a scorecard", "add a category",
  "add a criterion", "rename the scorecard", "delete a criterion", "delete a category",
  "update the rubric", "edit the scorecard", "set up scoring", "what should we grade them on",
  "build a scorecard from this playbook", or any request to configure Itero's evaluation
  criteria or scoring system.
user-invocable: true
references:
    - scorecard-api.md
---

# Scorecards Skill

Manage Itero scorecard templates via the public API — create, edit, and delete at any level
(templates, categories, criteria, rubrics). Backed by `scripts/scorecard.py`.

---

## Running the scripts

`<skill-dir>` below means the folder containing this SKILL.md (announced when the
skill loads). Under a Claude Code plugin install this is the `skills/scorecards`
subfolder of the plugin root; under a manual install it is the skill folder
inside your agent's skills directory. All scripts run via `uv run` —
dependencies resolve automatically (PEP 723).

---

## API reference

| Need | Where |
|---|---|
| Full payload tables, enums, hosts, auth | [scorecard-api.md](references/scorecard-api.md) |
| Lifecycle: draft → publish (Studio-only) | [scorecard-api.md](references/scorecard-api.md) — "Lifecycle: Draft → Published" |
| Agent IDs / config seeding (tenant-scoped) | [scorecard-api.md](references/scorecard-api.md) — "Agent IDs" |
| Soft-delete read lag after DELETE | [scorecard-api.md](references/scorecard-api.md) — "Soft-Delete Read Lag" |
| Unexpected 400/500 | [scorecard-api.md](references/scorecard-api.md) — "Errors" |

---

## Scorecard Type Guide

When creating a new template, determine the call type — it drives which AI agent evaluates
the calls.

| Type | Use for |
|---|---|
| `cold_call` | Outbound cold call scorecards |
| `discovery` | Discovery calls, first meetings, intro calls |
| `b2c` | B2C, advisory, insurance-style, or relationship-based calls |
| `other` | Falls back to any available agent |

---

## Authoring Rules

Apply these rules whenever creating or modifying criteria.

### QA criteria (`scorecardType: 1` on the category)

Binary evaluation — phrased so **true = good**:

- Good: `"Did the rep deliver the required call-recording disclosure before any substantive question?"`
- Bad: `"Did the rep skip the recording disclosure?"` ← inverted; rewrite before creating
- Use for: compliance items, required actions, observable yes/no behaviors
- A scorer can answer yes or no by watching the call — no judgment needed

### Qualitative criteria (`scorecardType: 0` on the category)

Graded on a 5-level rubric — start with "How effectively..." or "How well...":

- Good: `"How effectively did the rep use open-ended questions to uncover the prospect's situation?"`
- Bad: `"Did the rep probe?"` ← too binary, rewrite as a quality assessment
- Use for: tone, rapport, probing quality, objection handling, clarity, empathy

### Quick decision

Can two reasonable reviewers disagree on the answer? → Qualitative.
Can you answer yes/no just by watching the call? → QA.

### One concept per binary QA criterion

A QA criterion must check exactly one observable behavior — never bundle two checks into a single criterion. If you catch yourself writing "and" in a QA criterion, stop and split it.

- **Bad:** `"Did the rep deliver the recording disclosure and confirm the prospect's name before proceeding?"` — two checks; either can fail independently.
- **Good (split):** `"Did the rep deliver the required call-recording disclosure before any substantive question?"` AND `"Did the rep confirm the prospect's name at the start of the call?"`

Bundled QA criteria produce ambiguous scores (true if both? true if either?) and make coaching conversations harder because you cannot tell which behavior the rep failed.

### Categories must be distinct concepts — one concept per category

Categories exist to keep clearly distinct evaluation concepts separate. Don't merge two distinct concepts into one category for convenience.

**Bad:** `"Discovery & Objection Handling"` — discovery questions and objection-handling techniques are different rep skills evaluated against different bot behaviors. They get smashed together in reporting.

**Good:** `"Discovery"` (open-ended questions, layered follow-ups, probing) AND `"Objection Handling"` (Josh Braun framework, validate/mirror/neutral, language patterns) — two categories, each with criteria scoped to one concept.

When you find yourself naming a category `"X & Y"`, stop — split it into two categories before you add criteria to it. The cost of fixing later (delete + recreate criteria in new categories) is much higher than fixing at create time.

### What NOT to set

- **Rubric descriptions** — Itero populates them automatically on creation. Only use
  `update-rubric` for tenant-specific overrides after the fact.
- **Category weights** — Itero defaults to equal weights. Omit `weight` from all category
  payloads unless a custom distribution is explicitly required.
- Each category is one type (QA OR Qualitative). Mixed-type categories are not supported.
  Use separate categories for each type within the same scorecard.

### Typical scorecard size

- 3–6 categories
- 2–5 criteria per category
- 8–20 total criteria
- Roughly 40–60% QA / 40–60% Qualitative

---

## Preview Format

**Always render a preview before making any API calls.** Structure: QA section first, then
Qualitative. Within each section, group by category.

Category header (one per section it appears in):
```
Discovery & Trust Building
```

QA criterion (`[QA]` label is OUTSIDE the backtick block — not part of the paste text):

[QA]
```
Did the rep deliver the required call-recording disclosure before any substantive question?
```

Qualitative criterion:

[Qual]
```
How effectively did the rep use open-ended questions to uncover the prospect's situation?
```

For surgical edits, only show the affected entity labeled with the operation:

[ADD] — new entity being added  
[RENAME] — name changing  
[UPDATE] — content changing  
[DELETE] — entity being removed  

**Wait for explicit user approval before calling any script with `--live`.**

---

## Flow 1: Create a New Scorecard

### Step 1 — Gather intent and materials

If the user provides training docs, a playbook, methodology materials, or call transcripts:
read them and infer the category and criterion structure. Look for: named frameworks (SPIN,
MEDDIC, custom), required behaviors, call stages, skills explicitly evaluated.

If no materials are provided, ask about the sales process:
- What stages does a call go through?
- What behaviors separate great reps from average ones?
- Are there compliance or required-disclosure items?

### Step 2 — Determine scorecard type (if not obvious from context)

Ask once: "What type of calls is this scorecard for — cold call, discovery, B2C, or
something else?"

### Step 3 — Render the preview and iterate

Show the full proposed scorecard in preview format. Present QA and Qualitative sections
separately. Ask: "Does this look right? Any changes before I create it?"

Iterate until the user approves.

### Step 4 — Build plan.json

Write the approved scorecard to `.tmp/scorecard-plan.json`:

```json
{
  "name": "<scorecard name>",
  "agentType": "<cold_call | discovery | b2c | other>",
  "callTypes": [2],
  "categories": [
    {
      "name": "<category name>",
      "scorecardType": 1,
      "criteria": [
        {
          "title": "<short title (5–8 words)>",
          "criteria": "<full criterion text as it will appear in Itero>"
        }
      ]
    },
    {
      "name": "<another category>",
      "scorecardType": 0,
      "criteria": [
        {
          "title": "<short title>",
          "criteria": "<How effectively / How well...>"
        }
      ]
    }
  ]
}
```

`callTypes` values: `0` = Activity, `1` = Meeting, `2` = Practice. Omit the field entirely
if it should apply to all call types.

### Step 5 — Dry-run, then live

```bash
uv run "<skill-dir>/scripts/scorecard.py" create .tmp/scorecard-plan.json [--tenant TENANT]
```

Review the dry-run output. If it looks correct, run with `--live`:

```bash
uv run "<skill-dir>/scripts/scorecard.py" create .tmp/scorecard-plan.json [--tenant TENANT] --live
```

Report the created template ID, category count, and criterion count.

Tell the user verbatim, or close to it:

> The template is now in **draft state**. To activate scoring, open the template in the Itero Studio and publish it there — there is no API endpoint to publish. The skill cannot do this step for you.

---

## Flow 2: Surgical Edit

### Step 1 — Find the template

```bash
uv run "<skill-dir>/scripts/scorecard.py" list [--tenant TENANT]
```

Match by name. If ambiguous, show the list and ask the user to confirm.

### Step 2 — Load the full hierarchy

```bash
uv run "<skill-dir>/scripts/scorecard.py" fetch <template_id> [--tenant TENANT]
```

Parse the JSON to locate the target entity (category, criterion, or rubric) by name.

### Step 3 — Preview and confirm

Show a minimal preview with the operation label. Wait for user approval.

### Step 4 — Execute the minimal change

**Add a category:**
```bash
uv run "<skill-dir>/scripts/scorecard.py" add-category \
  '{"name":"<name>","scorecardTemplateId":<template_id>,"scorecardType":<0 or 1>}' \
  [--tenant TENANT] --live
```

**Add a criterion:**
```bash
uv run "<skill-dir>/scripts/scorecard.py" add-criteria \
  '{"title":"<title>","criteria":"<text>","scorecardTemplateCategoryId":<category_id>}' \
  [--tenant TENANT] --live
```

**Update a template, category, or criterion** — pass the COMPLETE object (all required fields
plus `id`). Required fields per entity:

- `template`: `id`, `name`, `qualitiveAgentId`, `qaAgentId`
- `category`: `id`, `name`, `scorecardTemplateId`, `scorecardType`
- `criteria`: `id`, `title`, `criteria`, `scorecardTemplateCategoryId`

```bash
uv run "<skill-dir>/scripts/scorecard.py" update <template|category|criteria> <id> \
  '<complete json payload>' [--tenant TENANT] --live
```

**Update a rubric description:**
```bash
uv run "<skill-dir>/scripts/scorecard.py" update-rubric <rubric_id> \
  "<description text>" [--tenant TENANT] --live
```

To find rubric IDs for a criterion, look inside the `rubrics` array in `fetch` output.
Each rubric has a `rubrikScale` (0=Poor, 1=NeedsImprovement, 2=Neutral, 3=Good, 4=Excellent).

---

## Flow 3: Delete

> **Verification gotcha**: After a successful `DELETE /scorecard-criteria/{id}` (200 OK), the soft-deleted criterion may still appear in `GET /scorecard-criteria?templateCategoryId=X` responses for some time. The UI is authoritative — if the user reports "it's gone in the UI," the delete worked. Trust the UI / category-level fetch, not the criteria-list endpoint, when verifying.

**The safety gate is non-negotiable.** Always show the full scope before deleting anything.

### Step 1 — Load and describe what will be destroyed

```bash
uv run "<skill-dir>/scripts/scorecard.py" list [--tenant TENANT]
# If deleting a category or criteria:
uv run "<skill-dir>/scripts/scorecard.py" fetch <template_id> [--tenant TENANT]
```

Show the user the exact scope:

- Deleting a criterion: *"This will permanently delete the criterion **'{title}'** (id={id}).
  Type `yes` to confirm."*
- Deleting a category: *"This will permanently delete the category **'{name}'** and its
  {N} criteria. Type `yes` to confirm."*
- Deleting a template: *"This will permanently delete the template **'{name}'** and all
  {N} categories, {M} total criteria. Type `yes` to confirm."*

### Step 2 — Execute only after explicit `yes`

```bash
uv run "<skill-dir>/scripts/scorecard.py" delete <criteria|category|template> <id> \
  [--tenant TENANT] --live
```

The script handles safe ordering automatically: criteria are deleted before their parent
category; categories are deleted before their parent template.

---

## Authentication

Default: the skill reads `ITERO_API_KEY` from your `.env` file. That's the only setup needed for a single-tenant install.

If you manage multiple Itero tenants from one repo, add the optional `--tenant <NAME>` flag; the skill will resolve `ITERO_API_KEY_<NAME>` from `.env` instead. Example:

```bash
uv run "<skill-dir>/scripts/scorecard.py" list --tenant <NAME>
uv run "<skill-dir>/scripts/scorecard.py" create .tmp/plan.json --tenant <NAME> --live
```

Omit `--tenant` for the common single-key case.

### Agent-ID cache is tenant-keyed

The skill caches `qualitiveAgentId` / `qaAgentId` per tenant in `.scorecard-config.json` (tenant names upper-cased, `DEFAULT` for the no-tenant case). Agent IDs are tenant-scoped on the Itero practice API, so sharing one cache across tenants causes 500s on create. Legacy flat-format configs (without tenant keys at the top level) auto-migrate into the `DEFAULT` entry on first read; no manual intervention needed.

---

## Error Handling

| Error message | What to do |
|---|---|
| `missing env var ITERO_API_KEY` | Add `ITERO_API_KEY=<key>` to `.env` |
| `template id=X not found` | Run `list` to see available templates; pick the right ID |
| `No existing templates found` | Create any template in the Itero web app first, then retry |
| `No existing template with agent IDs found` | The script falls back to the tenant agent catalog; pick the qual + QA agents from the printed list (purpose-built agents like an 'Insurance' qual agent may exist). IDs are cached per-tenant in `.scorecard-config.json`. |
| API 400 error | The response body contains per-field validation errors — fix the payload |
| `plan file not found` | Check the path to your `.tmp/scorecard-plan.json` |
