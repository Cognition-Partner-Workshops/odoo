# Wave 3 close — full-scope recon, rerun-1

**Verdict: PASS** — `merge_eligible: true`, `target_class: migration_cluster`, mode `live`, 45 collections (wave 1: 25, wave 2: 12, wave 3: 8), 46 Tier-4 ops (`ops.json`, byte-identical to run 1's). Zero findings in all four tiers.

Rerun after the w3-b01 seed fix (PR #75) that caused run 1's FAIL (`../README.md`: the depot settings run archived pricelist 7 and bumped `write_date` on pricelist 7 / product 5 on a fully seeded clone, while live wave-2 data was never reloaded). No target reload happened between run 1 and rerun-1: the before snapshot here is identical to run 1's (`../target_before.json`, same 45 counts / max `writeDate` / BSON sha256 per collection).

**Run:** `mongo-run/unt12` @ `c33ddec7cef` (merge of PR #75, contains PR #73's merge `1f281459775`); mapping `map-draft-2` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc`, tolerances `unt12-3` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea` (both re-verified at this tip), plugin `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (worktree of exactly that SHA, unpatched). Source: `odoo_src` dropped and rebuilt fresh with `.migration/fixtures/build_source.sh` from `63446015e3c` (marker 3, 70 modules, 21 crons active, left untouched); `createdb -T odoo_src odoo_unt12_w3close_r1`, crons 1,19-23 deactivated on the clone only (15 active), seeded in run-branch order from `c33ddec` with `seed_uom_packaging.py`, the whole committed `seed_scenario_rows.py` (w1 blocks, w1-b06 account chart, w2-b02 product catalog with its sequence pins, forward-only w3-b01 stock-config block as fixed by PR #75) and `seed_account_journal.py` via the pre-opt-in tree's `odoo-bin shell --no-http`; all three exit 0, no "already past" sequence-pin warning. After seeding the clone has pricelist 7 "Seeded wholesale" active and pricelist 8 inactive, both at `2026-10-20 00:00:00`, and product 5 at `2026-10-20 00:00:00` (the fixed block logged `product_product: 1 rows re-pinned` and `product_pricelist: 1 rows re-pinned`), which is what live holds. Harness run 06:09:38Z-06:12:29Z, `--unit wave-3-close --seed 0`, same CLI as run 1 (`--mode live --target-class migration_cluster --target-db odoo_unt12 --allowed-targets-file .migration/allowed_targets.json`). `load_unit.py` was not run; Odoo was never started against the target or with `mongodb_migration_db` set.

**Target read-only proof** (`target_snapshot.py`, `MONGODB_ATLAS_URI` by name, `odoo_unt12`, reads only): `target_before.json` taken 2026-10-21T06:09:31Z, `target_after.json` taken 2026-10-21T06:12:30Z; both 45 collections / 920 documents, and per collection `countDocuments`, max `writeDate` and the sha256 over the raw BSON of all documents sorted by `_id` are identical before and after (0 differing collections), and identical to run 1's before snapshot (05:26:44Z).

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 371 | PASS |
| 2 | per_field_aggregates | 394 | PASS |
| 3 | keyed_diffs | 1647 | PASS |
| 4 | app_level_parity | 46 | PASS |

Harness output: `result.json` (redacted, unsalted: `RECON_REDACT_SALT` not set), `report.md`, `recon.summary.md`.

## Per-collection tier table

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
| `accountJournalGroup` | 1 | 2 | 2 / 2 | PASS | PASS | PASS | - |
| `accountLockException` | 1 | 1 | 1 / 1 | PASS | PASS | PASS | - |
| `accountReport` | 1 | 5 | 5 / 5 | PASS | PASS | PASS | 1 PASS |
| `accountReportExpression` | 1 | 3 | 3 / 3 | PASS | PASS | PASS | 1 PASS |
| `accountReportExternalValue` | 1 | 1 | 1 / 1 | PASS | PASS | PASS | - |
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
| `stockWarehouse` | 3 | 3 | 3 / 3 | PASS | PASS | PASS | 1 PASS |
| `stockLocation` | 3 | 38 | 38 / 38 | PASS | PASS | PASS | 1 PASS |
| `stockPickingType` | 3 | 24 | 24 / 24 | PASS | PASS | PASS | 1 PASS |
| `stockRoute` | 3 | 9 | 9 / 9 | PASS | PASS | PASS | - |
| `stockRule` | 3 | 15 | 15 / 15 | PASS | PASS | PASS | 1 PASS |
| `stockPutawayRule` | 3 | 3 | 3 / 3 | PASS | PASS | PASS | - |
| `stockStorageCategoryCapacity` | 3 | 2 | 2 / 2 | PASS | PASS | PASS | - |
| `stockWarehouseOrderpoint` | 3 | 5 | 5 / 5 | PASS | PASS | PASS | 1 PASS |
