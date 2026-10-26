run_id: UNT14-54
manifest_sha: ef5b8af24b0b

# w2-b03 independent verification: accountIncoterms, accountReport, productCategory, accountTaxGroup, accountPaymentTerm

**Verdict: PASS** (live recon, `target_class: migration_cluster`, `merge_eligible: true` on all 5 units; probes past the gate PASS; MongoDB-storage tour PASS)

Batch PR [#144](https://github.com/Cognition-Partner-Workshops/odoo/pull/144), merged; batch evidence head `49d18c451bd480e2febb1d977eded8d3de288837` (`result.batch.json`, base `2f68f21`, manifest `ef5b8af24b0b`). Verified on the merged base `573f2cd0e8ea4a9b5b5f89aa808e1dd226376b98` (tip of `mongo-run/unt13`), which contains that head. I migrated none of these units.
Plugin pin `2c1160efde323c570425953b7e38bcc3496c6053` (`.migration/plugin_sha`), harness run from a detached worktree at that commit.

## Source

- `odoo_src` rebuilt with `.migration/fixtures/build_source.sh` (source commit `63446015e3c1`, `total_wall_seconds=247`).
- `.migration/fixtures/source_fingerprint.py` (via `secret:personal:ODOO_PG_RO_DSN`, one-shot exec): `a100e84ee2fb6282f30b45c003fd1db47561317c739340a10564d9e869e56a4e`, exact match to the ticket and `.migration/source_fingerprint.json`.
- Every recon run records `source_db: odoo_src`, `source_server: hmac-sha256:545efbd0aca82e45` (`RECON_REDACT_SALT` bound from `secret:org:RECON_REDACT_SALT`), matching `.migration/connectivity.json`. `odoo_unt13` was not reloaded or reseeded.

## Recon (my runs, `<unit>/result.json` beside this report)

Each unit: `recon.cli run --mode live --family postgresql --unit <u> --collections <u> --target-db odoo_unt13 --target-class migration_cluster --allowed-targets-file .migration/allowed_targets.json --seed 1`, committed `mapping_spec.json` (map-draft-5, sha `c0b93dad…02a7`) and `recon_tolerances.json` (v1, sha `8c9b9e4c…5416`), canonicalization = the mapping's `canonicalization` block, Tier 4 = my own `verify-ops.json`. All runs: `git_head 573f2cd`, `git_dirty false`, no warnings, Tiers 1-4 passed.

| Unit | Verdict / merge_eligible | Checks T1 / T2 / T3 / T4 | Source rows (embeds) | T1-T3 stats = batch result.json | ops_sha256 mine vs batch | batch git_head |
|---|---|---|---|---|---|---|
| `accountIncoterms` | PASS / True | 2 / 4 / 11 / 2 | 11 | yes | `cf7569c5fc47…` vs `4cdaea958067…` | `1ee2491` |
| `accountReport` | PASS / True | 6 / 7 / 17 / 3 | 7 (+column 8, sectionRel 2) | yes | `5673f94fb156…` vs `2dd43185d9e2…` | `1ee2491` |
| `productCategory` | PASS / True | 9 / 6 / 24 / 3 | 20 (+stockPickingTypeRel 4) | yes | `02d4f8f3cb88…` vs `e410c5367439…` | `1ee2491` |
| `accountTaxGroup` | PASS / True | 3 / 6 / 27 / 2 | 27 | yes | `d8fdfc052e60…` vs `d12ee51d4821…` | `1ee2491` |
| `accountPaymentTerm` | PASS / True | 4 / 7 / 28 / 3 | 13 (+line 15) | yes | `953d4130cb4d…` vs `043ecb5ea586…` | `1ee2491` |

Comparison with the batch evidence (`.migration/recon/<unit>/result.json`): same mapping and tolerance sha256, same source server fingerprint, identical Tier 1 counts, Tier 2 aggregate stats and Tier 3 keyed-diff stats (full diff of every row, 0 duplicate source keys); only `ops_sha256`, `git_head` and timestamps differ, as they must.

### Tier 4 ops (verifier-owned, not the batch's)

- `accountIncoterms`: `verify_accountIncoterms_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_accountIncoterms_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id)
- `accountReport`: `verify_accountReport_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_accountReport_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id); `verify_accountReport_embed_fanout_by_parent` (per-parent count of each embedded array (account_report_column, account_report_section_rel) against the child-)
- `productCategory`: `verify_productCategory_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_productCategory_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id); `verify_productCategory_embed_fanout_by_parent` (per-parent count of each embedded array (product_category_stock_picking_type_rel) against the child-row count,)
- `accountTaxGroup`: `verify_accountTaxGroup_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_accountTaxGroup_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id)
- `accountPaymentTerm`: `verify_accountPaymentTerm_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_accountPaymentTerm_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id); `verify_accountPaymentTerm_embed_fanout_by_parent` (per-parent count of each embedded array (account_payment_term_line) against the child-row count, keyed by id)

## Probes past the gate (`../probe_w2_unt14.py`, read-only; `<unit>/probe.json`)

Per unit: count; every mapped field (missing = source NULL count, no explicit nulls, BSON type = spec `bson_type`); no unmapped keys at the root or inside embedded elements; no duplicate `_id` / junction pair / natural key; every root row compared field by field with `odoo_src`; every embedded array compared element by element with its child table; declared indexes present with the same key order, unique flag and partial filter; raw-BSON sha256 of the collection before recon and after all probes and tours.

| Unit | Probes | Fields | Rows / junction | Embeds (source children = target elements) | Indexes | raw-BSON sha256 before = after (docs) |
|---|---|---|---|---|---|---|
| `accountIncoterms` | PASS (9 probes) | 7 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 11 rows x 7 fields, 0 mismatches | none | 1 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `44d4f1aa0884…` = `44d4f1aa0884…` (11) |
| `accountReport` | PASS (17 probes) | 39 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 7 rows x 39 fields, 0 mismatches | `column` 8=8; `sectionRel` 2=2 | 3 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `af257c077f09…` = `af257c077f09…` (7) |
| `productCategory` | PASS (14 probes) | 22 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 20 rows x 22 fields, 0 mismatches | `stockPickingTypeRel` 4=4 | 7 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `f0cbc455ae9d…` = `f0cbc455ae9d…` (20) |
| `accountTaxGroup` | PASS (11 probes) | 10 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 27 rows x 10 fields, 0 mismatches | none | 2 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `1e11116f575b…` = `1e11116f575b…` (27) |
| `accountPaymentTerm` | PASS (13 probes) | 14 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 13 rows x 14 fields, 0 mismatches | `line` 15=15 | 2 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `973aeefee36b…` = `973aeefee36b…` (13) |

Index note: none of this batch's spec indexes declares a partial filter, so the partial-filter check has nothing to compare for the spec's own filters; the live unique indexes carry `{<key>: {$exists: true}}`, which is what `storage_mongodb._create_indexes` (`odoo/orm/storage_mongodb.py:736-742`) adds to every unique index so that omitted NULLs never collide, and the probe expects exactly that filter.

### References (resolved against the real FK parent in `odoo_src`, then located)

A parent that is a merged wave 1-2 collection (or an embedded child array of one) is resolved in `odoo_unt13`; everything else is PostgreSQL-resident (framework tables or units of waves 3+) and is resolved in `odoo_src`. No reference was resolved through an unmerged namespace.

| Unit | Field -> spec `to` | FK parent | Resolved in | Distinct values | Dangling | |
|---|---|---|---|---|---|---|
| `accountIncoterms` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountIncoterms` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountReport` | `countryId->resCountry` | `res_country` | odoo_src.res_country (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountReport` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountReport` | `rootReportId->accountReport` | `account_report` | odoo_unt13.accountReport._id (merged wave 2, w2-b03) | 1 | 0 | PASS |
| `accountReport` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountReport` | `column.createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountReport` | `column.customAuditActionId->irActWindow` | `ir_act_window` | odoo_src.ir_act_window (PostgreSQL-resident, framework table) | 0 | 0 | PASS |
| `accountReport` | `column.writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountReport` | `sectionRel.subReportId->accountReport` | `account_report` | odoo_unt13.accountReport._id (merged wave 2, w2-b03) | 2 | 0 | PASS |
| `productCategory` | `companyId->resCompany` | `res_company` | odoo_src.res_company (PostgreSQL-resident, framework table) | 0 | 0 | PASS |
| `productCategory` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productCategory` | `parentId->productCategory` | `product_category` | odoo_unt13.productCategory._id (merged wave 2, w2-b03) | 4 | 0 | PASS |
| `productCategory` | `removalStrategyId->productRemoval` | `product_removal` | odoo_unt13.productRemoval._id (merged wave 2, w2-b01) | 0 | 0 | PASS |
| `productCategory` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productCategory` | `stockPickingTypeRel.stockPickingTypeId->stockPickingType` | `stock_picking_type` | odoo_src.stock_picking_type (PostgreSQL-resident, wave 3) | 2 | 0 | PASS |
| `accountTaxGroup` | `companyId->resCompany` | `res_company` | odoo_src.res_company (PostgreSQL-resident, framework table) | 2 | 0 | PASS |
| `accountTaxGroup` | `countryId->resCountry` | `res_country` | odoo_src.res_country (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountTaxGroup` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountTaxGroup` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountPaymentTerm` | `companyId->resCompany` | `res_company` | odoo_src.res_company (PostgreSQL-resident, framework table) | 0 | 0 | PASS |
| `accountPaymentTerm` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountPaymentTerm` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountPaymentTerm` | `line.createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountPaymentTerm` | `line.writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |

## Tours

- Batch claim: PR #144 / `result.batch.json`: `purchase_stock.test_purchase_order_suggest_search_panel_ux` PASS 1/1 and `sale.TestSaleMailComposerUI` PASS 2/2 on PostgreSQL storage (tree 2f68f21) and on MongoDB storage (tree 1ee2491, re-run on the merged head), 0 skipped.
- My re-run on MongoDB storage: scratch copy `odoo_v2b03r` (`createdb -T odoo_src`, admin password set only through `odoo-bin shell -d odoo_v2b03r --db_port=5433 --no-http`), all 25 merged wave 1-2 units loaded under `odoo_unt13.odoo_v2b03r__*` by the shared loader from the copy, then `odoo-bin -d odoo_v2b03r --db_port=5433 -u account,product,stock,uom,sale_stock,purchase_stock --test-enable --test-tags /purchase_stock:TestPurchaseOrderSuggest.test_purchase_order_suggest_search_panel_ux` with `ODOO_MONGODB_URI` bound to the migration cluster: **0 failed, 0 error(s) of 1 tests**. Copy dropped, scratch prefix 25 -> 0 collections.
- PostgreSQL-storage results were not re-run here (the ticket asks for one tour per batch on MongoDB storage); the PR's PostgreSQL-storage line above is the claim compared against.

## Branch

Committed on `recon/verify-w2-unt14` (new, flat branch; `recon/verify-w2-b01` / `-b02` on origin hold an earlier run's evidence and were left untouched). Files written through the harness's Python file tool (no file-edit tool was available in this session; no shell heredocs). No PR, no merge.

## Findings

None.

Coverage notes (not findings):
- First attempt of the batch tour on scratch copy `odoo_v2b03m` with only `-u purchase_stock` errored in setUpClass (0 failed, 2 error(s) of 0 tests): the test's setup creates an opted-in record (`product.pricelist` from the test company, or `product.attribute`) and the storage path's shadow insert hit `NOT NULL` still present on `product_pricelist.currency_id` in the copy. `storage_mongodb.auto_init` (odoo/orm/storage_mongodb.py:577-601) drops those NOT NULLs when the module owning an opted-in model is updated, so the copy needs `-u` of the owning modules (`account,product,stock,uom,sale_stock`), as the batch PRs ran; with that the run above passed. Verifier setup, not a batch defect; recorded so the deployment step carries the same module update.
