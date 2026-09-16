---
name: usage
description: Read Itero usage, limits, and billing history through the public API. Use when someone asks how much of their plan is left, how many units or evaluations they have used, whether they are into overage, what they were billed, or for an invoice history. Triggers include "how much usage do we have left," "are we over our limit," "what did we get billed last month," "show me our invoices," "how many voice practice minutes have we used," and "what's our current plan usage."
user-invocable: true
license: MIT
metadata:
  author: itero
  version: "2.2.0"
  homepage: https://iteroapp.ai
  source: https://github.com/Itero-AI/skills
inputs:
  - name: ITERO_API_KEY
    description: Itero public API key belonging to an Owner-role user. A named tenant may use ITERO_API_KEY_<NAME>.
    required: true
references:
  - references/usage.md
---

> **Read-only skill.** Both operations only read. Nothing here changes a plan, a contract, or an invoice — if the user wants a plan changed, direct them to Itero rather than attempting it through the API.

# Usage

Use `https://iterotenantapi.azurewebsites.net` — **not** the gateway — and send `X-API-Key: $ITERO_API_KEY`. Read the key from the environment; never display, log, or paste its value. Load [the generated usage reference](references/usage.md) for exact schemas and enums.

These two endpoints are not served by `iterogatewayapi`; that host returns `404` for them. Every other Itero operation still uses the gateway.

The key must belong to a user with the `Owner` role, and it can only ever read its own tenant's usage.

## Quick start: what's left this month

```bash
curl --fail-with-body --silent --show-error \
  --header "X-API-Key: $ITERO_API_KEY" \
  "https://iterotenantapi.azurewebsites.net/api/public/v1/usage/current-usage" \
  | jq 'map({productType, planType, includedUnits, usedUnits, remainingUnits, overageUnits, overageCost, isActive})'
```

## What do you need?

| Goal | Operation | Guidance |
|---|---|---|
| Usage so far this period | `GET /api/public/v1/usage/current-usage` | Live consumption against the open period. |
| Remaining allowance or overage | `GET /api/public/v1/usage/current-usage` | Read `remainingUnits` with `planType` — they mean different things per plan. |
| Past bills and invoices | `POST /api/public/v1/usage/get-usage-history` | Closed, invoiced periods only. Send `{"monthsBack": N}`. |
| Cost for one past month | `POST /api/public/v1/usage/get-usage-history` | Group rows by `periodStart`; a month can hold several invoices. |

## Workflow

1. Pick the endpoint from the question: "how much is left" is current usage, "what were we charged" is history.
2. Bound the history request with `monthsBack` (1–60) when the user named a window; omit it only when they genuinely want everything.
3. Read the operation in [the generated reference](references/usage.md) and translate every enum before reporting — `productType`, `planType`, and `invoiceStatus` are integers.
4. Report per product, not as one total. A tenant holds one contract per metered product, and their plans differ.
5. Give the plain answer — units used, units left, cost — rather than the raw JSON.

## Reading the numbers correctly

| Field | What it means |
|---|---|
| `planType: 0` (Prepaid) | `remainingUnits` counts down from `includedUnits`; overage starts once it hits zero. |
| `planType: 1` (PayAsYouGo) | `remainingUnits` is always `0`. That is not "exhausted" — every unit simply bills at `overageRate`. |
| `includedUnits: null` | The plan is unlimited or pay-as-you-go. Do not render it as zero included units. |
| `isActive: false` | The contract's period may have just rolled over and not yet renewed. Not necessarily cancelled. |
| `[]` from history | No invoiced periods yet. Not an error, and not "no usage" — check current usage instead. |

## Common Mistakes

| Mistake | Correct approach |
|---|---|
| Sending usage requests to the gateway | Use `https://iterotenantapi.azurewebsites.net` for these two operations only. |
| Reading `[]` as "no contract" or "no usage" | It means no invoiced periods; answer from `current-usage`. |
| Counting history rows as months | Rows are per invoice; one month can appear twice. Group by `periodStart`. |
| Reporting `remainingUnits: 0` as "out of credit" | On pay-as-you-go that is the normal steady state. |
| Reporting raw enum integers | Translate `productType`, `planType`, and `invoiceStatus` into names. |
| Summing every contract into one number | Report per product; the contracts meter different things. |
| Sending `monthsBack: 0` | The minimum is `1`. Omit the field to get everything. |
| Pasting invoice links into shared output | Report the figures; leave the billing URLs out. |

## Error quick reference

| Response | What to do |
|---|---|
| `400` | Check `monthsBack` is between 1 and 60, or omit it. |
| `401` | Confirm the key is available and valid without printing it. |
| `403` | The key is not an Owner-role key. Explain that and do not retry unchanged. |
| `404` | You are almost certainly calling the gateway. Switch to the tenant host. |
