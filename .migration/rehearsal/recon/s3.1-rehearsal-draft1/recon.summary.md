# Recon summary: `s3.1-rehearsal-draft1` - **FAIL**

- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging) | Target: `local` (local target: NOT a merge verdict)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping `map-draft-1` / tolerances `unt12-2` / seed `1`
- Generated: 2026-10-20T04:09:16.660678+00:00
- **WARNING: index_missing: accountMove index [('journalId', 1), ('_id', 1), ('sequencePrefix', 1)] unique=False**
- **WARNING: index_missing: accountMove index [('accountPayment.paymentId', 1)] unique=False**
- **WARNING: index_missing: accountMove index [('purchaseOrderRel.purchaseOrderId', 1)] unique=False**
- **WARNING: index_missing: accountMove index [('adjustingEntriesAccountMove.moveId', 1)] unique=False**

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 142 | PASS |
| 2 per_field_aggregates | 764 | FAIL (2) |
| 3 keyed_diffs | 2516 | PASS |

Top findings (2 of 2; full list in result.json):
- T2 `accountBankStatementLine` aggregate_sum: field amount_residual->amountResidual
- T2 `purchaseOrderLine` aggregate_sum: field technical_price_unit->technicalPriceUnit

Full evidence: result.json, report.md (linked from the PR, not pasted).
