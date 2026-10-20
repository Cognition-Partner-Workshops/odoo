# Wave 2 close: full-scope recon, rerun-1 (UNT12-46)

Rerun of `../` (FAIL on `accountTax` embed cardinality, the w2-b02 seed gap) after `accountTax` was reloaded from a fully seeded clone (UNT12-49, `recon/w2-tax-reload` @ `6229b36`). Same recipe, same pinned bytes, same 37 collections, same 41 Tier-4 ops, fresh clone.

**Verdict: PASS**, `merge_eligible: true`, `target_class: migration_cluster`, mode `live`, T1 counts_through_mapping 260 checks, T2 per_field_aggregates 280 checks, T3 keyed_diffs 1530 checks, T4 app_level_parity 41 checks; 0 findings, 0 warnings; redaction unsalted (`RECON_REDACT_SALT` unavailable, as in every prior run).
**Target read-only proof:** 37 collections, 821 docs; per-collection counts and max writeDate/createDate identical before (`target_before.json`, 2026-10-20T22:55:53.660471+00:00) and after (`target_after.json`, 2026-10-20T22:58:07.345242+00:00); also identical to the first run's `../target_before.json` (the UNT12-49 reload changed accountTax contents, not its count or audit timestamps). Nothing wrote to `odoo_unt12` during this rerun; `load_unit.py` was not run, Odoo was never started against the target.

Recipe deltas vs `../README.md`: fresh `createdb -T odoo_src odoo_unt12_w2close_r1` (odoo_src marker 3 unchanged, 21 crons active), seeded with the whole committed `seed_scenario_rows.py` + `seed_uom_packaging.py` + `seed_account_journal.py` (crons 1,19-23 off on the clone only, 15 active; junction rows account_tax_sale/purchase_order_line_rel 51/32 as before). Harness run 22:56:02Z-22:58:07Z, `--unit wave-2-close-rerun-1`, `--seed 0`, mapping sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc`, tolerances sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea`, plugin `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c`.

No batch broke another batch's data: all 37 collections of waves 1 and 2 pass Tiers 1-4 together over one fully seeded clone.

| collection | wave | source rows (seeded clone) | target docs before / after | T1 | T2 | T3 | T4 ops |
|---|---|---|---|---|---|---|---|
| `stockStorageCategory` | 1 | 6 | 6 / 6 | PASS | PASS | PASS | 1 PASS |
| `stockScrapReasonTag` | 1 | 3 | 3 / 3 | PASS | PASS | PASS | 1 PASS |
| `returnReason` | 1 | 5 | 5 / 5 | PASS | PASS | PASS | 1 PASS |
| `productCategory` | 1 | 7 | 7 / 7 | PASS | PASS | PASS | 2 PASS |
| `productRemoval` | 1 | 4 | 4 / 4 | PASS | PASS | PASS | 1 PASS |
| `productTag` | 1 | 3 | 3 / 3 | PASS | PASS | PASS | 2 PASS |
| `productDocument` | 1 | 2 | 2 / 2 | PASS | PASS | PASS | 1 PASS |
| `productBaseUnit` | 1 | 2 | 2 / 2 | PASS | PASS | PASS | 1 PASS |
| `uomUom` | 1 | 30 | 30 / 30 | PASS | PASS | PASS | 1 PASS |
| `stockPackageType` | 1 | 3 | 3 / 3 | PASS | PASS | PASS | 3 PASS |
| `accountPaymentTerm` | 1 | 11 | 11 / 11 | PASS | PASS | PASS | 1 PASS |
| `accountIncoterms` | 1 | 11 | 11 / 11 | PASS | PASS | PASS | 1 PASS |
| `accountCashRounding` | 1 | 2 | 2 / 2 | PASS | PASS | PASS | 1 PASS |
| `accountJournalGroup` | 1 | 2 | 2 / 2 | PASS | PASS | PASS | 0 PASS |
| `accountLockException` | 1 | 1 | 1 / 1 | PASS | PASS | PASS | 0 PASS |
| `accountReport` | 1 | 5 | 5 / 5 | PASS | PASS | PASS | 1 PASS |
| `accountReportExpression` | 1 | 3 | 3 / 3 | PASS | PASS | PASS | 1 PASS |
| `accountReportExternalValue` | 1 | 1 | 1 / 1 | PASS | PASS | PASS | 0 PASS |
| `productAttribute` | 1 | 14 | 14 / 14 | PASS | PASS | PASS | 3 PASS |
| `accountAccount` | 1 | 184 | 184 / 184 | PASS | PASS | PASS | 1 PASS |
| `accountAccountTag` | 1 | 10 | 10 / 10 | PASS | PASS | PASS | 1 PASS |
| `accountTax` | 1 | 58 | 58 / 58 | PASS | PASS | PASS | 1 PASS |
| `accountTaxGroup` | 1 | 26 | 26 / 26 | PASS | PASS | PASS | 1 PASS |
| `accountTaxRepartitionLine` | 1 | 232 | 232 / 232 | PASS | PASS | PASS | 1 PASS |
| `accountFiscalPosition` | 1 | 4 | 4 / 4 | PASS | PASS | PASS | 1 PASS |
| `accountJournal` | 2 | 14 | 14 / 14 | PASS | PASS | PASS | 2 PASS |
| `accountPaymentMethod` | 2 | 2 | 2 / 2 | PASS | PASS | PASS | 1 PASS |
| `accountReconcileModel` | 2 | 8 | 8 / 8 | PASS | PASS | PASS | 1 PASS |
| `accountReconcileModelLineAccountTaxRel` | 2 | 1 | 1 / 1 | PASS | PASS | PASS | 1 PASS |
| `productTemplate` | 2 | 37 | 37 / 37 | PASS | PASS | PASS | 1 PASS |
| `productProduct` | 2 | 47 | 47 / 47 | PASS | PASS | PASS | 1 PASS |
| `productTemplateAttributeValue` | 2 | 24 | 24 / 24 | PASS | PASS | PASS | 1 PASS |
| `productAttributeValueProductTemplateAttributeLineRel` | 2 | 24 | 24 / 24 | PASS | PASS | PASS | 1 PASS |
| `productCombo` | 2 | 3 | 3 / 3 | PASS | PASS | PASS | 1 PASS |
| `productSupplierinfo` | 2 | 28 | 28 / 28 | PASS | PASS | PASS | 1 PASS |
| `productPricelist` | 2 | 2 | 2 / 2 | PASS | PASS | PASS | 1 PASS |
| `productPricelistItem` | 2 | 2 | 2 / 2 | PASS | PASS | PASS | 1 PASS |
