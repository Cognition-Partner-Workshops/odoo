# Recon summary: `s3.1-rehearsal-draft2` - **PASS**

- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging) | Target: `local` (local target: NOT a merge verdict)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping `map-draft-2` / tolerances `unt12-3` / seed `1`
- Generated: 2026-10-20T11:38:03.874287+00:00
- **WARNING: UNVERIFIED collection accountCashRounding: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection accountFullReconcile: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection accountJournalGroup: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection accountLockException: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection accountPayment: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection accountReconcileModelLineAccountTaxRel: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection accountReportExpression: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection accountReportExternalValue: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection productBaseUnit: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection productPricelist: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection productPricelistItem: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection productTag: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection stockPackageHistory: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection stockPutawayRule: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection stockScrapReasonTag: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection stockStorageCategoryCapacity: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection accountPartialReconcile: 0 source rows, key/shape/field rules unexercised**

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 142 | PASS |
| 2 per_field_aggregates | 776 | PASS |
| 3 keyed_diffs | 2516 | PASS |

Full evidence: result.json, report.md (linked from the PR, not pasted).
