# Wave 2 close: full-scope recon (UNT12-46)

**Verdict: FAIL** (one collection, `accountTax`, Tier 1 `embed_cardinality`, caused by a seeding difference, see below). `merge_eligible: false`, `target_class: migration_cluster`, mode `live`, redaction unsalted (`RECON_REDACT_SALT` unavailable, same as every prior run).
**Diagnostic run without the w2-b02 seed block: PASS**, 29 collections (wave 1 + account-journal), Tiers 1-4, `merge_eligible: true` (`diagnostic-no-w2b02-seed/result.json`).
**Target read-only proof:** 37 collections, 821 docs, counts and max writeDate/createDate identical before (`target_before.json`, 22:38:11Z), after the main run (`target_after.json`, 22:38:49Z) and after the diagnostic (`target_after_diagnostic.json`, 22:41:54Z). Nothing wrote to `odoo_unt12` during this ticket; `load_unit.py` was not run and Odoo was never started against the target.

## Recipe (both runs)
- `mongo-run/unt12` @ `9287c2116cd0d98a3ee6f89fbfef4e8a4300e2b7`; `mapping_spec.json` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc` (map-draft-2), `recon_tolerances.json` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea` (unt12-3), both exact matches.
- Plugin `mongo-migration-plugin` @ `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (detached worktree, unpatched), harness `mongo-recon-harness 0.3.3`, canonicalization `skills/mongo-migration/profiles/postgresql.md`.
- Source: `odoo_src` rebuilt with `.migration/fixtures/build_source.sh` (marker 3, 70 modules), left untouched (crons 1,19-23 still active: 21 active crons). `createdb -T odoo_src odoo_unt12_w2close`, seeded with the whole committed `.migration/load/seed_scenario_rows.py` (incl. the w1-b06 account-chart block and the w2-b02 product-catalog block with its sequence pins) + `seed_uom_packaging.py` + `seed_account_journal.py`, via `../odoo-unt12-src/odoo-bin shell --no-http`; crons 1,19-23 deactivated on the clone only (15 active).
- Target: `odoo_unt12` on `MONGODB_ATLAS_URI`, `--target-class migration_cluster`, `--allowed-targets-file .migration/allowed_targets.json`, read only.
- Tier 4 ops: `ops.json` = wave-1 close ops (28, `recon/wave-1-close`) + `.migration/recon/account-journal/ops.json` (5) + `.migration/recon/product-catalog/ops.json` (8) = 41 ops, no duplicate names.
- Main run: one invocation, `--collections` = all 37, `--seed 0`, 22:38:30Z-22:38:39Z. `result.json`, `report.md`, `recon.summary.md` are the harness's own output.

## Per-collection
| collection | wave | source rows (seeded clone) | target docs | T1 (main run) | T2-T4 (main run) | diagnostic run (no w2-b02 seed) |
|---|---|---|---|---|---|---|
| `stockStorageCategory` | 1 | 6 | 6 | PASS | halted at T1 | PASS T1-T4 |
| `stockScrapReasonTag` | 1 | 3 | 3 | PASS | halted at T1 | PASS T1-T4 |
| `returnReason` | 1 | 5 | 5 | PASS | halted at T1 | PASS T1-T4 |
| `productCategory` | 1 | 7 | 7 | PASS | halted at T1 | PASS T1-T4 |
| `productRemoval` | 1 | 4 | 4 | PASS | halted at T1 | PASS T1-T4 |
| `productTag` | 1 | 3 | 3 | PASS | halted at T1 | PASS T1-T4 |
| `productDocument` | 1 | 2 | 2 | PASS | halted at T1 | PASS T1-T4 |
| `productBaseUnit` | 1 | 2 | 2 | PASS | halted at T1 | PASS T1-T4 |
| `uomUom` | 1 | 30 | 30 | PASS | halted at T1 | PASS T1-T4 |
| `stockPackageType` | 1 | 3 | 3 | PASS | halted at T1 | PASS T1-T4 |
| `accountPaymentTerm` | 1 | 11 | 11 | PASS | halted at T1 | PASS T1-T4 |
| `accountIncoterms` | 1 | 11 | 11 | PASS | halted at T1 | PASS T1-T4 |
| `accountCashRounding` | 1 | 2 | 2 | PASS | halted at T1 | PASS T1-T4 |
| `accountJournalGroup` | 1 | 2 | 2 | PASS | halted at T1 | PASS T1-T4 |
| `accountLockException` | 1 | 1 | 1 | PASS | halted at T1 | PASS T1-T4 |
| `accountReport` | 1 | 5 | 5 | PASS | halted at T1 | PASS T1-T4 |
| `accountReportExpression` | 1 | 3 | 3 | PASS | halted at T1 | PASS T1-T4 |
| `accountReportExternalValue` | 1 | 1 | 1 | PASS | halted at T1 | PASS T1-T4 |
| `productAttribute` | 1 | 14 | 14 | PASS | halted at T1 | PASS T1-T4 |
| `accountAccount` | 1 | 184 | 184 | PASS | halted at T1 | PASS T1-T4 |
| `accountAccountTag` | 1 | 10 | 10 | PASS | halted at T1 | PASS T1-T4 |
| `accountTax` | 1 | 58 | 58 | FAIL (2 embed_cardinality findings) | halted at T1 | PASS T1-T4 |
| `accountTaxGroup` | 1 | 26 | 26 | PASS | halted at T1 | PASS T1-T4 |
| `accountTaxRepartitionLine` | 1 | 232 | 232 | PASS | halted at T1 | PASS T1-T4 |
| `accountFiscalPosition` | 1 | 4 | 4 | PASS | halted at T1 | PASS T1-T4 |
| `accountJournal` | 2 | 14 | 14 | PASS | halted at T1 | PASS T1-T4 |
| `accountPaymentMethod` | 2 | 2 | 2 | PASS | halted at T1 | PASS T1-T4 |
| `accountReconcileModel` | 2 | 8 | 8 | PASS | halted at T1 | PASS T1-T4 |
| `accountReconcileModelLineAccountTaxRel` | 2 | 1 | 1 | PASS | halted at T1 | PASS T1-T4 |
| `productTemplate` | 2 | 37 | 37 | PASS | halted at T1 | not graded (its rows need the w2-b02 seed block) |
| `productProduct` | 2 | 47 | 47 | PASS | halted at T1 | not graded (its rows need the w2-b02 seed block) |
| `productTemplateAttributeValue` | 2 | 24 | 24 | PASS | halted at T1 | not graded (its rows need the w2-b02 seed block) |
| `productAttributeValueProductTemplateAttributeLineRel` | 2 | 24 | 24 | PASS | halted at T1 | not graded (its rows need the w2-b02 seed block) |
| `productCombo` | 2 | 3 | 3 | PASS | halted at T1 | not graded (its rows need the w2-b02 seed block) |
| `productSupplierinfo` | 2 | 28 | 28 | PASS | halted at T1 | not graded (its rows need the w2-b02 seed block) |
| `productPricelist` | 2 | 2 | 2 | PASS | halted at T1 | not graded (its rows need the w2-b02 seed block) |
| `productPricelistItem` | 2 | 2 | 2 | PASS | halted at T1 | not graded (its rows need the w2-b02 seed block) |

Diagnostic tiers: T1 counts_through_mapping 177 checks, T2 per_field_aggregates 202 checks, T3 keyed_diffs 1308 checks, T4 app_level_parity 33 checks; 0 findings, 0 warnings.

## The FAIL, and why it is a seeding difference
Tier 1 findings (main run, both on `accountTax`):
- `rows(account_tax_purchase_order_line_rel)=32 vs sum(len(purchaseOrderLineRel))=31`
- `rows(account_tax_sale_order_line_rel)=51 vs sum(len(saleOrderLineRel))=50`

Clone vs `odoo_src`: `odoo_src` has 50 / 31 rows in those two junction tables, the fully seeded clone has 51 / 32. The extra rows are `(tax 3, sale_order_line 52)` and `(tax 4, purchase_order_line 33)`, and those two order lines are created by the **w2-b02 product-catalog seed block** of `seed_scenario_rows.py` (lines 224-308: `sale 26 line [52]`, `purchase 18 line [33]`), which attaches the products' default taxes to them. Live `accountTax` (wave 1, unit account-chart, w1-b06, reloaded in UNT12-38 from `recon/w1-b06-reload` @ `86122d8`) was loaded from a clone seeded **before** that block existed, so the live docs for taxes 3 and 4 are missing one `saleOrderLineRel` / `purchaseOrderLineRel` element each.

Culprit batch: **w2-b02 product-catalog (PR #71)**: its seed block reaches into a wave-1 collection (`accountTax.saleOrderLineRel` / `.purchaseOrderLineRel`) that was never reloaded with it, and the batch verifier graded only the 8 product-catalog collections, so the cross-batch effect was invisible until this full-scope run. The diagnostic clone (`odoo_unt12_w2close_diag`: identical seeding minus lines 224-308) passes all four tiers over the 29 non-product-catalog collections, so nothing else in either wave broke another batch's data. Nothing was fixed, reloaded or changed on the target; the manager decides between reloading `accountTax` from a fully seeded clone (as UNT12-38 did for the account chart) or detaching the taxes from the two seeded order lines in the w2-b02 block (then the 8 product-catalog collections would need a reload too, as their live docs reflect those taxed lines).

## Plugin notes (pinned 9a584b4c, not patched)
- `report.md` says "Merge eligible: no (fixture/continuous evidence never merges)" for a `live` FAIL; the reason text is misleading (it is the FAIL that blocks, not the mode). Cosmetic.
- `RECON_REDACT_SALT` is not provisioned for this engagement; both runs are unsalted (harness warning), as every prior UNT12 run.
