# Wave 3 close: full-scope recon (UNT12-52)

**Verdict: FAIL**, `merge_eligible: false`, `target_class: migration_cluster`, mode `live`, 45 collections (waves 1-3) in one run against `odoo_unt12`; T1 counts_through_mapping 371 PASS, T2 per_field_aggregates 394 PASS, T3 keyed_diffs 1647 **FAIL (3 findings)**, T4 app_level_parity 46 **FAIL (1 finding)**. Redaction unsalted (`RECON_REDACT_SALT` unavailable, as in every prior run). Nothing was fixed, reloaded or changed on the target.

**Run:** `mongo-run/unt12` @ `1f281459775` (merge of PR #73, contains verified head `a261dbceaa5`); mapping `map-draft-2` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc`, tolerances `unt12-3` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea`, plugin `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (worktree of exactly that SHA, unpatched). Source: `odoo_src` rebuilt with `.migration/fixtures/build_source.sh` (marker 3, 70 modules, 21 crons active, left untouched); `createdb -T odoo_src odoo_unt12_w3close`, seeded in run-branch order with `seed_uom_packaging.py`, the whole committed `seed_scenario_rows.py` (w1 blocks, w1-b06 account chart, w2-b02 product catalog with its sequence pins, forward-only w3-b01 stock-config block) and `seed_account_journal.py`, via the pre-opt-in tree's `odoo-bin shell --no-http` (all three exit 0, no "already past" sequence-pin warning, crons 1,19-23 deactivated on the clone only: 15 active). Harness run 05:26:59Z-05:29:45Z, `--unit wave-3-close --seed 0`, 46 Tier-4 ops (`ops.json` = wave-2 close's 41 + stock-config's 5). `load_unit.py` was not run; Odoo was never started against the target or with `mongodb_migration_db` set.

**Target read-only proof:** 45 collections, 920 docs; per-collection `countDocuments`, max `writeDate` and a sha256 over every document's raw BSON (ordered by `_id`) are identical before (`target_before.json`, 05:26:44Z), after the main run (`target_after.json`, 05:30:04Z) and after both diagnostics (`target_after_diagnostic.json`, 05:36:52Z); `target_snapshot.py` is the read-only script that took them.

## Findings (Tier 3 / Tier 4)

| collection | tier | key | differing fields | what the clone has |
|---|---|---|---|---|
| `productPricelist` (wave 2, w2-b02) | 3 | `tuple:24a6ade6d35f` = pricelist 7 "Seeded wholesale" | `active`, `write_date -> writeDate` | `active = false`, `write_date` 2026-10-21 05:25:53 (live: active, pinned to 2026-10-20 00:00:00) |
| `productProduct` (wave 2, w2-b02) | 3 | `tuple:666aa17826ad` = product 5 "Office Chair" | `write_date -> writeDate` | `write_date` 2026-10-21 05:25:53 (live: pinned) |
| `productPricelist` | 4 | op `pricelist_list` | 1 source row unmatched / 1 target row unmatched | the same archived pricelist 7 |

**This is a seeding difference, and the culprit is the w3-b01 stock-config seed block (PR #73).** `seed_scenario_rows.py` lines 310-374 create the archived "Seeded Depot" warehouse. `stock.warehouse.create` -> `_check_multiwarehouse_group` (`addons/stock/models/stock_warehouse.py:308-326`) sees two active warehouses and runs `res.config.settings({'group_stock_multi_locations': True}).execute()`; product's `res.config.settings.set_values` (`addons/product/models/res_config_settings.py:38-46`) then archives every active pricelist because `group_product_pricelist` is off on the fixture. On the fully seeded clone that transaction (05:25:53.287898) archived pricelist 7 and bumped `write_date` on pricelist 7 and product 5 (and wrote `res_config_settings` 1, `res_groups` 1/41/42, `res_company` 1, `res_partner` 1, `ir_default` 37-38, `ir_config_parameter` 28-55, none of them migrated collections). The block's re-pin loop covers `product_template`/`product_category` but not `product_pricelist`/`product_product`. Live `productPricelist`/`productProduct` were loaded by w2-b02 (PR #71) from a clone seeded before this block and were never reloaded with it; the w3-b01 batch verifier graded only the 8 stock-config collections, so the cross-batch effect was invisible until this run. The depot itself (`stockWarehouse` 3, archived) and all 8 wave-3 collections match live.

## Diagnostics (clone `odoo_unt12_w3close_diag`: identical seeding minus `seed_scenario_rows.py` lines 310-end)

On that clone pricelist 7 is active and pinned, product 5 is pinned, and no `res_config_settings` row exists.

- `diagnostic-no-w3b01-seed/`: all 37 wave-1/2 collections, 41 ops -> T1 FAIL on `stockPackageType` only (`embed_cardinality rows(stock_package_type_stock_putaway_rule_rel)=2 vs sum(len(stockPutawayRuleRel))=4`), the harness stops there. Expected: live `stockPackageType.stockPutawayRuleRel` was reloaded **with** the w3-b01 putaway rules 2-3 (`recon/w3-pkg-reload`, PR #73), so it needs the block the diagnostic removes; in the main run it PASSes all four tiers.
- `diagnostic-no-w3b01-seed-excl-pkgtype/`: the other 36 wave-1/2 collections, 38 ops -> **PASS** (T1 254, T2 268, T3 1523, T4 38 checks, 0 findings), 05:33:20Z-05:36:28Z.

So without the w3-b01 seed block every wave-1/2 collection except the deliberately co-reloaded `stockPackageType` still matches live; with it, two w2-b02 collections no longer do. No other batch broke another batch's data.

## Per-collection tiers (main run; last column = diag-2 on the no-w3-b01 clone)

| collection | wave | source rows (seeded clone) | target docs before / after | T1 | T2 | T3 | T4 ops | diagnostic (no w3-b01 seed) |
|---|---|---|---|---|---|---|---|---|
| `stockStorageCategory` | 1 | 6 | 6 / 6 | PASS | PASS | PASS | 1 PASS | PASS |
| `stockScrapReasonTag` | 1 | 3 | 3 / 3 | PASS | PASS | PASS | 1 PASS | PASS |
| `returnReason` | 1 | 5 | 5 / 5 | PASS | PASS | PASS | 1 PASS | PASS |
| `productCategory` | 1 | 7 | 7 / 7 | PASS | PASS | PASS | 2 PASS | PASS |
| `productRemoval` | 1 | 4 | 4 / 4 | PASS | PASS | PASS | 1 PASS | PASS |
| `productTag` | 1 | 3 | 3 / 3 | PASS | PASS | PASS | 2 PASS | PASS |
| `productDocument` | 1 | 2 | 2 / 2 | PASS | PASS | PASS | 1 PASS | PASS |
| `productBaseUnit` | 1 | 2 | 2 / 2 | PASS | PASS | PASS | 1 PASS | PASS |
| `uomUom` | 1 | 30 | 30 / 30 | PASS | PASS | PASS | 1 PASS | PASS |
| `stockPackageType` | 1 | 3 | 3 / 3 | PASS | PASS | PASS | 3 PASS | T1 FAIL in diag-1 (expected: live array reloaded with the w3-b01 rules), excluded from diag-2 |
| `accountPaymentTerm` | 1 | 11 | 11 / 11 | PASS | PASS | PASS | 1 PASS | PASS |
| `accountIncoterms` | 1 | 11 | 11 / 11 | PASS | PASS | PASS | 1 PASS | PASS |
| `accountCashRounding` | 1 | 2 | 2 / 2 | PASS | PASS | PASS | 1 PASS | PASS |
| `accountJournalGroup` | 1 | 2 | 2 / 2 | PASS | PASS | PASS | - | PASS |
| `accountLockException` | 1 | 1 | 1 / 1 | PASS | PASS | PASS | - | PASS |
| `accountReport` | 1 | 5 | 5 / 5 | PASS | PASS | PASS | 1 PASS | PASS |
| `accountReportExpression` | 1 | 3 | 3 / 3 | PASS | PASS | PASS | 1 PASS | PASS |
| `accountReportExternalValue` | 1 | 1 | 1 / 1 | PASS | PASS | PASS | - | PASS |
| `productAttribute` | 1 | 14 | 14 / 14 | PASS | PASS | PASS | 3 PASS | PASS |
| `accountAccount` | 1 | 184 | 184 / 184 | PASS | PASS | PASS | 1 PASS | PASS |
| `accountAccountTag` | 1 | 10 | 10 / 10 | PASS | PASS | PASS | 1 PASS | PASS |
| `accountTax` | 1 | 58 | 58 / 58 | PASS | PASS | PASS | 1 PASS | PASS |
| `accountTaxGroup` | 1 | 26 | 26 / 26 | PASS | PASS | PASS | 1 PASS | PASS |
| `accountTaxRepartitionLine` | 1 | 232 | 232 / 232 | PASS | PASS | PASS | 1 PASS | PASS |
| `accountFiscalPosition` | 1 | 4 | 4 / 4 | PASS | PASS | PASS | 1 PASS | PASS |
| `accountJournal` | 2 | 14 | 14 / 14 | PASS | PASS | PASS | 2 PASS | PASS |
| `accountPaymentMethod` | 2 | 2 | 2 / 2 | PASS | PASS | PASS | 1 PASS | PASS |
| `accountReconcileModel` | 2 | 8 | 8 / 8 | PASS | PASS | PASS | 1 PASS | PASS |
| `accountReconcileModelLineAccountTaxRel` | 2 | 1 | 1 / 1 | PASS | PASS | PASS | 1 PASS | PASS |
| `productTemplate` | 2 | 37 | 37 / 37 | PASS | PASS | PASS | 1 PASS | PASS |
| `productProduct` | 2 | 47 | 47 / 47 | PASS | PASS | **FAIL** (1) | 1 PASS | PASS |
| `productTemplateAttributeValue` | 2 | 24 | 24 / 24 | PASS | PASS | PASS | 1 PASS | PASS |
| `productAttributeValueProductTemplateAttributeLineRel` | 2 | 24 | 24 / 24 | PASS | PASS | PASS | 1 PASS | PASS |
| `productCombo` | 2 | 3 | 3 / 3 | PASS | PASS | PASS | 1 PASS | PASS |
| `productSupplierinfo` | 2 | 28 | 28 / 28 | PASS | PASS | PASS | 1 PASS | PASS |
| `productPricelist` | 2 | 2 | 2 / 2 | PASS | PASS | **FAIL** (2) | 1 **FAIL** | PASS |
| `productPricelistItem` | 2 | 2 | 2 / 2 | PASS | PASS | PASS | 1 PASS | PASS |
| `stockWarehouse` | 3 | 3 | 3 / 3 | PASS | PASS | PASS | 1 PASS | not graded (wave 3) |
| `stockLocation` | 3 | 38 | 38 / 38 | PASS | PASS | PASS | 1 PASS | not graded (wave 3) |
| `stockPickingType` | 3 | 24 | 24 / 24 | PASS | PASS | PASS | 1 PASS | not graded (wave 3) |
| `stockRoute` | 3 | 9 | 9 / 9 | PASS | PASS | PASS | - | not graded (wave 3) |
| `stockRule` | 3 | 15 | 15 / 15 | PASS | PASS | PASS | 1 PASS | not graded (wave 3) |
| `stockPutawayRule` | 3 | 3 | 3 / 3 | PASS | PASS | PASS | - | not graded (wave 3) |
| `stockStorageCategoryCapacity` | 3 | 2 | 2 / 2 | PASS | PASS | PASS | - | not graded (wave 3) |
| `stockWarehouseOrderpoint` | 3 | 5 | 5 / 5 | PASS | PASS | PASS | 1 PASS | not graded (wave 3) |
