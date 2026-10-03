*Last Edited: 2026-10-02 19:24*

# Usage and Billing Notes

<!-- gotchas -->
## Usage gotchas

<!-- fact:usage-host-exception -->
### Choose the host for the operation

The two billing operations, `GET /api/public/v1/usage/current-usage` and `POST /api/public/v1/usage/get-usage-history`, use `https://iterotenantapi.azurewebsites.net` and return 404 on the gateway. The six practice and evaluation summary, by-user and per-day report operations use `https://iterogatewayapi.azurewebsites.net` and return 404 on the tenant host. A 404 means the wrong host for that operation. (Host-verified 2026-09-29.)

<!-- fact:usage-owner-role -->
### All eight usage reads require an Owner-role key

The tenant is resolved from the key itself; there is no tenantId parameter or way to read another tenant's usage. Both billing operations require Owner. The Owner requirement for the six report operations is spec-documented, and all six returned 200 with an Owner key on 2026-10-02. Treat 403 as a role problem and do not retry unchanged.

<!-- fact:usage-history-empty -->
### An empty history means no invoices, not no usage

`POST /usage/get-usage-history` returns an empty array for a tenant that has no invoiced billing periods. This is a normal `200`, not an error and not a `404`.

Do not read `[]` as "this tenant has no contract" or "this tenant has no usage" — it means neither. A verified tenant returned `[]` from `get-usage-history` while `GET /usage/current-usage` returned an active contract (`isActive: true`) with 150.28 units already consumed in the open period. The tenant was on contract and actively consuming; it simply had no closed period that had been invoiced yet.

Scope the wording to what was actually asked. `monthsBack` filters the result, so `[]` from a bounded request only means *no invoiced periods in that window* — the tenant may well have older invoices. Say "nothing invoiced in the last N months" there, and reserve "no invoiced periods yet" for an unfiltered request that also came back empty. Either way, answer the usage question from `current-usage`. (Field-verified across two tenants 2026-09-16.)

<!-- fact:usage-history-per-invoice -->
### History rows are per invoice, not per month

The history array carries one record per invoice, and a single billing period can be invoiced more than once. A verified tenant asked for `monthsBack: 13` and received 14 records covering 13 distinct months, because March 2026 appeared twice under two separate invoice IDs.

Never treat the array length as a month count, and never key records by `periodStart` alone. Group by `periodStart` and sum across the group when reporting a month's cost, or report each invoice separately with its `invoiceId`. (Field-verified 2026-09-16.)

<!-- fact:usage-practice-per-day-unordered -->
### Fetch the complete practice page and sort dates

Practice per-day is paged and zero-based, with default page size 10. Rows are not date-ordered: sort by `date` after fetching. Fetch in one page with `pageSize` at least `totalCount`, or narrow with `from`/`to`. A request with pageNumber 0 and pageSize 1000 returned all totalCount rows on 2026-10-02. Days with no practice are omitted. Returned dates have no time-zone suffix, unlike the specification's example ending in `Z`. (Live-verified 2026-10-02.)

<!-- fact:usage-evaluation-per-day-sentinel -->
### Drop the evaluation sentinel row

Evaluation per-day is unpaged and newest first. It ends with a junk row dated `0001-01-01`; drop that row before totals or charts. (Live-verified 2026-10-02.)

<!-- fact:usage-duration-timespan-string -->
### Parse summary durations as strings

The evaluation summary's `averageQaEvaluationDuration` and `averageQualitativeEvaluationDuration` are strings such as `00:00:08.5990566`, or null, even though the schema shows a TimeSpan object. Do not access object fields or treat null as zero. (Live-verified 2026-10-02.)
<!-- /gotchas -->

<!-- lifecycle -->
## Choose activity reports or billing

Use the practice and evaluation summary, by-user and per-day reports for activity. `from`/`to` are optional and inclusive. Practice reports count only call type Practice. By-user reports exclude unlinked sessions and identify people only by `userId`: the specification does not say whether that is `id` or `tenantUserId`, so confirm an unambiguous match in `GET /api/public/v1/user` before naming anyone.

Practice minute values were whole numbers in the saved summary, by-user and per-day responses, although the schema allows `number (double)` values. (Live-verified 2026-10-02.) Activity counts are not billing units. Answer billing questions from `current-usage`. Save by-user and per-day responses to a file, then project only the fields needed.

## Reading billing correctly

Pick the endpoint by the question. "How much is left this month?" is `current-usage` — live consumption against the open period's allowance. "What were we billed?" is `get-usage-history` — closed periods that have been invoiced. The two never cover the same period: history excludes the month still in progress, so `monthsBack: 1` returns last month, not this one.

The two endpoints do not share a shape. `current-usage` returns a flat array with **one row per contract**. `get-usage-history` returns **one row per invoice**, each carrying its own `periodStart`, `totalCost`, and `invoiceStatus`, with the per-contract figures nested underneath in `contracts[]` — so `productType` and `planType` live one level down there, not on the top-level row.

A tenant normally holds several contracts at once, one per metered product. Report the product from `productType` rather than collapsing the rows into a single number, because the plans differ: a `Prepaid` contract counts `remainingUnits` down from `includedUnits`, while a `PayAsYouGo` contract always reports `remainingUnits: 0` and bills every unit at `overageRate`. `includedUnits` is `null` when the plan is unlimited or pay-as-you-go.

`monthsBack` accepts 1 through 60. Sending `0` fails validation with `400 GreaterThanValidator`. Omit the field, or send `{}`, for every available period — a verified tenant returned 30 records reaching back to March 2024, so bound the request when the user asked about a specific window.

Read `isActive` carefully in `current-usage`: records are selected by contract status, and `isActive` additionally requires the current time to fall inside `periodStart`/`periodEnd`. A contract whose period has just rolled over can appear with `isActive: false` until it renews, so do not report that as a cancelled contract.

Usage responses contain billing figures and invoice links. Report the figures the user asked for; do not paste invoice URLs into shared output.
<!-- /lifecycle -->
