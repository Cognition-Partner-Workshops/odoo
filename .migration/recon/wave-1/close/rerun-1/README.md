# Wave 1 close: full-scope recon, rerun-1 (after the #64 account-chart reload)

Rerun of `../` (first run, FAIL on the #64 seed gap) after account chart was reloaded from a seeded clone (UNT12-38, `recon/w1-b06-reload` @ `86122d8`). Same recipe, same pinned bytes, same 25 collections, now with the full committed seed including the w1-b06 account-chart block.

- Run branch `mongo-run/unt12` @ `7fee6d9d335fba6b392b2658159eb9f47714c0ec`; plugin `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (pinned, unpatched)
- Mapping `map-draft-2` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc`; tolerances `unt12-3` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea` (verified against the pinned values)
- Mode `live`, target `odoo_unt12`, `target_class: migration_cluster`; generated 2026-10-20T20:00:20.353915+00:00
- Source: `odoo_src` (marker 3, crons 1,19-23 all still active) -> `createdb -T odoo_src odoo_w1close_r1`; clone seeded with the whole committed `.migration/load/seed_scenario_rows.py` (incl. the account-chart block: tags 9,10; tax 58; repartition lines 229-232; the 7 junction rows) + `.migration/load/seed_uom_packaging.py`; crons 1,19-23 deactivated on the clone only
- Tier 4 ops = `../ops.json` (six batches' committed ops merged, 28 ops)

## Verdict

**PASS, merge_eligible=True**, warnings: 0, findings: 0 on all four tiers.

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 141 | PASS |
| 2 per_field_aggregates | 164 | PASS |
| 3 keyed_diffs | 1267 | PASS |
| 4 app_level_parity | 28 | PASS |

No batch broke another batch's data: all 25 collections pass Tiers 1-4 together over one seeded clone, and the seven previously 0-row account-chart arrays are now graded over seeded rows (see `embeds_graded` below).

## Per-collection tier table

| collection | batch | source rows (clone) | target docs | T1 | T2 | T3 (keyed diff population) | T4 ops |
|---|---|---|---|---|---|---|---|
| `accountAccount` | #64 | 184 | 184 | PASS | PASS | PASS (184) | 1 |
| `accountAccountTag` | #64 | 10 | 10 | PASS | PASS | PASS (10) | 1 |
| `accountCashRounding` | #60 | 2 | 2 | PASS | PASS | PASS (2) | 1 |
| `accountFiscalPosition` | #64 | 4 | 4 | PASS | PASS | PASS (4) | 1 |
| `accountIncoterms` | #60 | 11 | 11 | PASS | PASS | PASS (11) | 1 |
| `accountJournalGroup` | #60 | 2 | 2 | PASS | PASS | PASS (2) | 0 |
| `accountLockException` | #60 | 1 | 1 | PASS | PASS | PASS (1) | 0 |
| `accountPaymentTerm` | #60 | 11 | 11 | PASS | PASS | PASS (11) | 1 |
| `accountReport` | #60 | 5 | 5 | PASS | PASS | PASS (5) | 1 |
| `accountReportExpression` | #60 | 3 | 3 | PASS | PASS | PASS (3) | 1 |
| `accountReportExternalValue` | #60 | 1 | 1 | PASS | PASS | PASS (1) | 0 |
| `accountTax` | #64 | 58 | 58 | PASS | PASS | PASS (58) | 1 |
| `accountTaxGroup` | #64 | 26 | 26 | PASS | PASS | PASS (26) | 1 |
| `accountTaxRepartitionLine` | #64 | 232 | 232 | PASS | PASS | PASS (232) | 1 |
| `productAttribute` | #59 | 14 | 14 | PASS | PASS | PASS (14) | 3 |
| `productBaseUnit` | #61 | 2 | 2 | PASS | PASS | PASS (2) | 1 |
| `productCategory` | #61 | 7 | 7 | PASS | PASS | PASS (7) | 2 |
| `productDocument` | #61 | 2 | 2 | PASS | PASS | PASS (2) | 1 |
| `productRemoval` | #61 | 4 | 4 | PASS | PASS | PASS (4) | 1 |
| `productTag` | #61 | 3 | 3 | PASS | PASS | PASS (3) | 2 |
| `returnReason` | #56 | 5 | 5 | PASS | PASS | PASS (5) | 1 |
| `stockPackageType` | #62 | 3 | 3 | PASS | PASS | PASS (3) | 3 |
| `stockScrapReasonTag` | #56 | 3 | 3 | PASS | PASS | PASS (3) | 1 |
| `stockStorageCategory` | #56 | 6 | 6 | PASS | PASS | PASS (6) | 1 |
| `uomUom` | #62 | 30 | 30 | PASS | PASS | PASS (30) | 1 |

T1-T3 are graded per collection; a tier is marked PASS for a collection when the run's tier passed with 0 findings for it (the harness records findings per collection, none here). T4 ops is the number of merged `ops.json` operations touching the collection (28 ops over 22 collections; `accountReportExternalValue`, `accountLockException`, `accountCashRounding`-type collections without ops are covered by Tiers 1-3 only, as in the batches).

### Embedded arrays graded (Tier 3 `embeds_graded`)

```json
{
 "accountAccount.accountTag": 13,
 "accountAccount.resCompanyRel": 184,
 "accountAccount.taxDefaultRel": 1,
 "accountAccountTag.accountMoveLineRel": 1,
 "accountAccountTag.accountTaxRepartitionLineRel": 1,
 "accountAccountTag.productTemplateRel": 1,
 "accountCashRounding.accountPaymentMethodLineRel": 3,
 "accountCashRounding.resCurrencyRel": 1,
 "accountCashRounding.resPartnerCategoryRel": 3,
 "accountFiscalPosition.account": 1,
 "accountFiscalPosition.accountTaxRel": 50,
 "accountFiscalPosition.resCountryStateRel": 2,
 "accountPaymentTerm.line": 13,
 "accountReport.column": 8,
 "accountReport.line": 2,
 "accountReport.sectionRel": 2,
 "accountTax.alternatives": 2,
 "accountTax.filiationRel": 2,
 "accountTax.productSupplierTaxesRel": 72,
 "accountTax.productTaxesRel": 72,
 "accountTax.purchaseOrderLineRel": 31,
 "accountTax.saleOrderLineRel": 50,
 "productAttribute.productTemplateRel": 9,
 "productAttribute.value": 101,
 "productCategory.stockPickingTypeRel": 3,
 "productTag.productProductRel": 3,
 "productTag.productTemplateRel": 3,
 "stockPackageType.stockPutawayRuleRel": 2,
 "stockPackageType.stockRouteRel": 2
}
```

## Read-only proof (target `odoo_unt12`)

`target_before.json` taken 2026-10-20T19:59:04.882857+00:00 and `target_after.json` taken 2026-10-20T20:00:21.035099+00:00: `countDocuments` and max `writeDate`/`createDate` identical for all 25 collections: **True**. Max `writeDate` is `2026-10-20T00:00:00` everywhere; the account-chart reload (UNT12-38) predates the before snapshot.

| collection | count before | count after | max writeDate before | max writeDate after |
|---|---|---|---|---|
| `accountAccount` | 184 | 184 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountAccountTag` | 10 | 10 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountCashRounding` | 2 | 2 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountFiscalPosition` | 4 | 4 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountIncoterms` | 11 | 11 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountJournalGroup` | 2 | 2 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountLockException` | 1 | 1 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountPaymentTerm` | 11 | 11 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountReport` | 5 | 5 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountReportExpression` | 3 | 3 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountReportExternalValue` | 1 | 1 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountTax` | 58 | 58 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountTaxGroup` | 26 | 26 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountTaxRepartitionLine` | 232 | 232 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `productAttribute` | 14 | 14 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `productBaseUnit` | 2 | 2 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `productCategory` | 7 | 7 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `productDocument` | 2 | 2 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `productRemoval` | 4 | 4 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `productTag` | 3 | 3 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `returnReason` | 5 | 5 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `stockPackageType` | 3 | 3 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `stockScrapReasonTag` | 3 | 3 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `stockStorageCategory` | 6 | 6 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `uomUom` | 30 | 30 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |

Not run: `load_unit.py`, any Odoo process against the target, any Odoo with `mongodb_migration_db` set. Redaction unsalted (`RECON_REDACT_SALT` unset, same as the batches). Nothing in `.migration/` outside this directory was changed.
