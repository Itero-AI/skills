*Last Edited: 2026-08-12 15:08*

# Shared Itero API Notes

<!-- gotchas -->
## Shared API gotchas

<!-- fact:auth-header -->
### Authenticate without exposing the key

Use `https://iterogatewayapi.azurewebsites.net` for Itero public API operations unless a resource note names a verified exception. Send the key in this header:

```http
X-API-Key: <key>
```

Read the default key from `ITERO_API_KEY`. For a named tenant, read `ITERO_API_KEY_<NAME>`, with the tenant name upper-cased. Never paste the key into a command that will be saved, print it, log it, or include it in an error message.

<!-- fact:context-safety-projection -->
### Keep large collections out of the agent context

Do not read a full collection response into the conversation when a few fields will answer the question. Save large responses to a file or project them to the smallest useful shape first.

This matters most for `GET /api/public/v1/practice-scenario`: the verified tenant returned 596 scenarios, about 535 KB or 152,000 tokens. Projecting each item to its ID, display name, and `personaId` reduced the response to about 48 KB. It also matters for `GET /api/public/v1/call/get-call`: save the full call to a file and extract only the needed transcript fields instead of loading the entire response.

Apply the same rule to every list operation: filter on the server when possible, select only fields the user needs, and redirect raw JSON to a file when detail must be preserved.
<!-- /gotchas -->

## Canonical enum supersets

These tables contain the union of values found across the committed schemas. They are validation supersets, not permission to send every value to every operation. Generated documentation must show the narrower enum from that operation's request schema when one exists.

### CallType

| Value | Name | Notes |
|---:|---|---|
| 0 | Activity | Supported by the canonical enum. |
| 1 | Meeting | Supported by the canonical enum. |
| 2 | Practice | Supported by the canonical enum, including the add-call request. |

### ConversationStatus

| Value | Name |
|---:|---|
| 0 | Informational |
| 2 | PositiveOutcome |
| 3 | NoAnswer |
| 4 | NegativeOutcome |
| 5 | FollowUpRequired |
| 6 | Transferred |
| 7 | Abandoned |
| 8 | InvalidData |
| 9 | DoNotContact |

There is no value `1` in the schema.

### Source

| Value | Name | Notes |
|---:|---|---|
| 0 | None | Documented label. |
| 1 | Outreach | Documented label. |
| 2 | Gong | Documented label. |
| 3 | Frontspin | Documented label. |
| 4 | Undocumented | Present in the schema; the public specification gives no label. |
| 5 | Undocumented | Present in the schema; the public specification gives no label. |
| 6 | Undocumented | Present in the schema; the public specification gives no label. |

### ConversationIntegrationType

| Value | Name | Notes |
|---:|---|---|
| 0 | None | Documented label. |
| 1 | Outreach | Documented label. |
| 2 | Gong | Documented label. |
| 3 | Frontspin | Documented label. |
| 4 | Undocumented | Present in the schema; the public specification gives no label. |
| 5 | Undocumented | Present in the schema; the public specification gives no label. |
| 6 | Undocumented | Present in the schema; the public specification gives no label. |

### InteractionType

| Value | Name |
|---:|---|
| 0 | Voice |
| 1 | Chat |

### ScorecardType

| Value | Name | Notes |
|---:|---|---|
| 0 | Qualitative | Supported by the canonical enum. |
| 1 | QA | Supported by the canonical enum. |

### EvaluationStatus

| Value | Name |
|---:|---|
| 0 | NotStarted |
| 1 | InProgress |
| 2 | Success |
| 3 | Error |

### RubrikScale

The API spells this enum `RubrikScale`.

| Value | Name |
|---:|---|
| 0 | Poor |
| 1 | NeedsImprovement |
| 2 | Neutral |
| 3 | Good |
| 4 | Excellent |
| 5 | NotApplicable |

### ScorecardTemplateStatus

| Value | Name |
|---:|---|
| 0 | Draft |
| 1 | Published |

### PersonaType

| Value | Name |
|---:|---|
| 0 | Enterprise |
| 1 | Consumer |

### PracticeScenarioType

| Value | Name |
|---:|---|
| 0 | CommonScenario |
| 1 | ObjectionHandling |
| 2 | LiveCallSimulation |
| 3 | FocusScenario |

### ScorecardAppliedStatus

| Value | Name |
|---:|---|
| 0 | Not applied |
| 1 | Applied |
