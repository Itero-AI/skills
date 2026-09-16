*Last Edited: 2026-09-16 16:08*

# Usage and Billing Notes

<!-- gotchas -->
## Usage gotchas

<!-- fact:usage-host-exception -->
### Call usage on the tenant host, not the gateway

The usage endpoints are the second verified exception to the gateway rule. They are not published in the gateway's aggregated specification and the gateway does not proxy them: `GET https://iterogatewayapi.azurewebsites.net/api/public/v1/usage/current-usage` returns `404`, while the same path on `https://iterotenantapi.azurewebsites.net` returns `200` with the same key.

Send both usage operations to `https://iterotenantapi.azurewebsites.net` with the usual `X-API-Key` header. Every other tenant operation — users, groups, agents — stays on the gateway. (Host-verified 2026-09-16.)

<!-- fact:usage-owner-role -->
### Usage reads require an Owner-role key

Both usage operations require a key belonging to a user with the `Owner` role. The tenant is resolved from the key itself; there is no `tenantId` parameter and no way to read another tenant's usage. A key for a `Coach`, `Manager`, or `Representative` cannot read billing data, so treat `403` here as a role problem rather than a bad key, and do not retry unchanged.

<!-- fact:usage-history-empty -->
### An empty history means no invoices, not no usage

`POST /usage/get-usage-history` returns an empty array for a tenant that has no invoiced billing periods. This is a normal `200`, not an error and not a `404`.

Do not read `[]` as "this tenant has no contract" or "this tenant has no usage" — it means neither. A verified tenant returned `[]` from `get-usage-history` while `GET /usage/current-usage` returned an active contract (`isActive: true`) with 150.28 units already consumed in the open period. The tenant was on contract and actively consuming; it simply had no closed period that had been invoiced yet.

When history is empty, say that no invoiced periods exist yet and answer the usage question from `current-usage` instead. (Field-verified across two tenants 2026-09-16.)

<!-- fact:usage-history-per-invoice -->
### History rows are per invoice, not per month

The history array carries one record per invoice, and a single billing period can be invoiced more than once. A verified tenant asked for `monthsBack: 13` and received 14 records covering 13 distinct months, because March 2026 appeared twice under two separate invoice IDs.

Never treat the array length as a month count, and never key records by `periodStart` alone. Group by `periodStart` and sum across the group when reporting a month's cost, or report each invoice separately with its `invoiceId`. (Field-verified 2026-09-16.)
<!-- /gotchas -->

<!-- lifecycle -->
## Reading usage correctly

Pick the endpoint by the question. "How much is left this month?" is `current-usage` — live consumption against the open period's allowance. "What were we billed?" is `get-usage-history` — closed periods that have been invoiced. The two never cover the same period: history excludes the month still in progress, so `monthsBack: 1` returns last month, not this one.

Both endpoints return one row per contract, and a tenant normally holds several contracts at once — one per metered product. Report the product from `productType` rather than collapsing the rows into a single number, because the plans differ: a `Prepaid` contract counts `remainingUnits` down from `includedUnits`, while a `PayAsYouGo` contract always reports `remainingUnits: 0` and bills every unit at `overageRate`. `includedUnits` is `null` when the plan is unlimited or pay-as-you-go.

`monthsBack` accepts 1 through 60. Sending `0` fails validation with `400 GreaterThanValidator`. Omit the field, or send `{}`, for every available period — a verified tenant returned 30 records reaching back to March 2024, so bound the request when the user asked about a specific window.

Read `isActive` carefully in `current-usage`: records are selected by contract status, and `isActive` additionally requires the current time to fall inside `periodStart`/`periodEnd`. A contract whose period has just rolled over can appear with `isActive: false` until it renews, so do not report that as a cancelled contract.

Usage responses contain billing figures and invoice links. Report the figures the user asked for; do not paste invoice URLs into shared output.
<!-- /lifecycle -->
