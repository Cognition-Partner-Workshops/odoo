run_id: UNT14-54
manifest_sha: ef5b8af24b0b

# w2-b04 independent verification: uomUom, productTemplateUomUomRel, accountFullReconcile, accountAccountTag, accountAccount

**Verdict: PASS** (live recon, `target_class: migration_cluster`, `merge_eligible: true` on all 5 units; probes past the gate PASS; MongoDB-storage tour PASS)

Batch PR [#143](https://github.com/Cognition-Partner-Workshops/odoo/pull/143), merged; batch evidence head `2b000c73d017e75f3f51320242cfb76aa52edc5f` (`result.batch.json`, base `2f68f21`, manifest `ef5b8af24b0b`). Verified on the merged base `573f2cd0e8ea4a9b5b5f89aa808e1dd226376b98` (tip of `mongo-run/unt13`), which contains that head. I migrated none of these units.
Plugin pin `2c1160efde323c570425953b7e38bcc3496c6053` (`.migration/plugin_sha`), harness run from a detached worktree at that commit.

## Source

- `odoo_src` rebuilt with `.migration/fixtures/build_source.sh` (source commit `63446015e3c1`, `total_wall_seconds=247`).
- `.migration/fixtures/source_fingerprint.py` (via `secret:personal:ODOO_PG_RO_DSN`, one-shot exec): `a100e84ee2fb6282f30b45c003fd1db47561317c739340a10564d9e869e56a4e`, exact match to the ticket and `.migration/source_fingerprint.json`.
- Every recon run records `source_db: odoo_src`, `source_server: hmac-sha256:545efbd0aca82e45` (`RECON_REDACT_SALT` bound from `secret:org:RECON_REDACT_SALT`), matching `.migration/connectivity.json`. `odoo_unt13` was not reloaded or reseeded.

## Recon (my runs, `<unit>/result.json` beside this report)

Each unit: `recon.cli run --mode live --family postgresql --unit <u> --collections <u> --target-db odoo_unt13 --target-class migration_cluster --allowed-targets-file .migration/allowed_targets.json --seed 1`, committed `mapping_spec.json` (map-draft-5, sha `c0b93dad…02a7`) and `recon_tolerances.json` (v1, sha `8c9b9e4c…5416`), canonicalization = the mapping's `canonicalization` block, Tier 4 = my own `verify-ops.json`. All runs: `git_head 573f2cd`, `git_dirty false`, no warnings, Tiers 1-4 passed.

| Unit | Verdict / merge_eligible | Checks T1 / T2 / T3 / T4 | Source rows (embeds) | T1-T3 stats = batch result.json | ops_sha256 mine vs batch | batch git_head |
|---|---|---|---|---|---|---|
| `uomUom` | PASS / True | 5 / 8 / 30 / 2 | 30 | yes | `cb15df269ac9…` vs `015639493d64…` | `7b38f56` |
| `productTemplateUomUomRel` | PASS / True | 3 / 0 / 2 / 2 | 2 | yes | `cda418f0695b…` vs `7d9ee1f67b53…` | `7b38f56` |
| `accountFullReconcile` | PASS / True | 1 / 2 / 42 / 2 | 42 | yes | `1897642d89d2…` vs `288bc9e21d6a…` | `7b38f56` |
| `accountAccountTag` | PASS / True | 7 / 6 / 68 / 3 | 15 (+accountMoveLineRel 51, accountTaxRepartitionLineRel 1, productTemplateRel 1) | yes | `452f777327e6…` vs `367616567a64…` | `7b38f56` |
| `accountAccount` | PASS / True | 15 / 8 / 461 / 3 | 213 (+resCompanyRel 213, accountTag 34, taxDefaultRel 1) | yes | `d1c02f78cef7…` vs `0a11e985e456…` | `7b38f56` |

Comparison with the batch evidence (`.migration/recon/<unit>/result.json`): same mapping and tolerance sha256, same source server fingerprint, identical Tier 1 counts, Tier 2 aggregate stats and Tier 3 keyed-diff stats (full diff of every row, 0 duplicate source keys); only `ops_sha256`, `git_head` and timestamps differ, as they must.

### Tier 4 ops (verifier-owned, not the batch's)

- `uomUom`: `verify_uomUom_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_uomUom_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id)
- `productTemplateUomUomRel`: `verify_productTemplateUomUomRel_links_ordered` (every link as the ORM's Many2many.read sees it, ordered by both ids); `verify_productTemplateUomUomRel_links_per_product_template_id` (link count per product_template_id (the owning side's record set size))
- `accountFullReconcile`: `verify_accountFullReconcile_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_accountFullReconcile_rows_per_create_uid` (record count per creating user (the 'created by' grouping of the list view))
- `accountAccountTag`: `verify_accountAccountTag_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_accountAccountTag_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id); `verify_accountAccountTag_embed_fanout_by_parent` (per-parent count of each embedded array (account_account_tag_account_move_line_rel, account_account_tag_accoun)
- `accountAccount`: `verify_accountAccount_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_accountAccount_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id); `verify_accountAccount_embed_fanout_by_parent` (per-parent count of each embedded array (account_account_res_company_rel, account_account_account_tag, account)

## Probes past the gate (`../probe_w2_unt14.py`, read-only; `<unit>/probe.json`)

Per unit: count; every mapped field (missing = source NULL count, no explicit nulls, BSON type = spec `bson_type`); no unmapped keys at the root or inside embedded elements; no duplicate `_id` / junction pair / natural key; every root row compared field by field with `odoo_src`; every embedded array compared element by element with its child table; declared indexes present with the same key order, unique flag and partial filter; raw-BSON sha256 of the collection before recon and after all probes and tours.

| Unit | Probes | Fields | Rows / junction | Embeds (source children = target elements) | Indexes | raw-BSON sha256 before = after (docs) |
|---|---|---|---|---|---|---|
| `uomUom` | PASS (11 probes) | 13 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 30 rows x 13 fields, 0 mismatches | none | 4 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `2ced47e0e426…` = `2ced47e0e426…` (30) |
| `productTemplateUomUomRel` | PASS (11 probes) | 0 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 2 source links = 2 target links; read back from `productTemplateId` (1 endpoints, 2 links, resolved in odoo_src.product_template (PostgreSQL-resident, wave 3)), `uomUomId` (2 endpoints, 2 links, resolved in odoo_unt13.uomUom._id (wave 2)) | none | 2 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 1 unique | `ccb6a7761f48…` = `ccb6a7761f48…` (2) |
| `accountFullReconcile` | PASS (9 probes) | 4 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 42 rows x 4 fields, 0 mismatches | none | 0 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `08e1e4ccb96d…` = `08e1e4ccb96d…` (42) |
| `accountAccountTag` | PASS (16 probes) | 9 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 15 rows x 9 fields, 0 mismatches | `accountMoveLineRel` 51=51; `accountTaxRepartitionLineRel` 1=1; `productTemplateRel` 1=1 | 3 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `6d0acdaa439e…` = `6d0acdaa439e…` (15) |
| `accountAccount` | PASS (19 probes) | 17 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 213 rows x 17 fields, 0 mismatches | `resCompanyRel` 213=213; `accountTag` 34=34; `taxDefaultRel` 1=1 | 11 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `40c60ea7e493…` = `40c60ea7e493…` (213) |

Index note: none of this batch's spec indexes declares a partial filter, so the partial-filter check has nothing to compare for the spec's own filters; the live unique indexes carry `{<key>: {$exists: true}}`, which is what `storage_mongodb._create_indexes` (`odoo/orm/storage_mongodb.py:736-742`) adds to every unique index so that omitted NULLs never collide, and the probe expects exactly that filter.

### References (resolved against the real FK parent in `odoo_src`, then located)

A parent that is a merged wave 1-2 collection (or an embedded child array of one) is resolved in `odoo_unt13`; everything else is PostgreSQL-resident (framework tables or units of waves 3+) and is resolved in `odoo_src`. No reference was resolved through an unmerged namespace.

| Unit | Field -> spec `to` | FK parent | Resolved in | Distinct values | Dangling | |
|---|---|---|---|---|---|---|
| `uomUom` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `uomUom` | `packageTypeId->stockPackageType` | `stock_package_type` | odoo_unt13.stockPackageType._id (merged wave 2, w2-b02) | 0 | 0 | PASS |
| `uomUom` | `relativeUomId->uomUom` | `uom_uom` | odoo_unt13.uomUom._id (merged wave 2, w2-b04) | 17 | 0 | PASS |
| `uomUom` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productTemplateUomUomRel` | `productTemplateId->productTemplate` | `product_template` | odoo_src.product_template (PostgreSQL-resident, wave 3) | 1 | 0 | PASS |
| `productTemplateUomUomRel` | `uomUomId->uomUom` | `uom_uom` | odoo_unt13.uomUom._id (merged wave 2, w2-b04) | 2 | 0 | PASS |
| `accountFullReconcile` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountFullReconcile` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountAccountTag` | `countryId->resCountry` | `res_country` | odoo_src.res_country (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountAccountTag` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountAccountTag` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountAccountTag` | `accountMoveLineRel.accountMoveLineId->accountMoveLine` | `account_move_line` | odoo_src.account_move_line (PostgreSQL-resident, wave 8) | 46 | 0 | PASS |
| `accountAccountTag` | `accountTaxRepartitionLineRel.accountTaxRepartitionLineId->accountTax` | `account_tax_repartition_line` | odoo_src.account_tax_repartition_line (PostgreSQL-resident, wave 3) | 1 | 0 | PASS |
| `accountAccountTag` | `productTemplateRel.productTemplateId->productTemplate` | `product_template` | odoo_src.product_template (PostgreSQL-resident, wave 3) | 1 | 0 | PASS |
| `accountAccount` | `accountStockExpenseId->accountAccount` | `account_account` | odoo_unt13.accountAccount._id (merged wave 2, w2-b04) | 0 | 0 | PASS |
| `accountAccount` | `accountStockVariationId->accountAccount` | `account_account` | odoo_unt13.accountAccount._id (merged wave 2, w2-b04) | 2 | 0 | PASS |
| `accountAccount` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountAccount` | `currencyId->resCurrency` | `res_currency` | odoo_src.res_currency (PostgreSQL-resident, framework table) | 0 | 0 | PASS |
| `accountAccount` | `parentId->accountAccount` | `account_account` | odoo_unt13.accountAccount._id (merged wave 2, w2-b04) | 10 | 0 | PASS |
| `accountAccount` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountAccount` | `resCompanyRel.resCompanyId->resCompany` | `res_company` | odoo_src.res_company (PostgreSQL-resident, framework table) | 2 | 0 | PASS |
| `accountAccount` | `accountTag.accountAccountTagId->accountAccountTag` | `account_account_tag` | odoo_unt13.accountAccountTag._id (merged wave 2, w2-b04) | 5 | 0 | PASS |
| `accountAccount` | `taxDefaultRel.taxId->accountTax` | `account_tax` | odoo_src.account_tax (PostgreSQL-resident, wave 3) | 1 | 0 | PASS |

## Tours

- Batch claim: PR #143 / `result.batch.json`: account tours (`addons/account/tests/test_tour.py`, 6 tests) 6/6 on PostgreSQL storage and 6/6 on MongoDB storage, no skips; merge/unmerge tests 2/2 on both storages.
- My re-run on MongoDB storage: scratch copy `odoo_v2b04r` (`createdb -T odoo_src`, admin password set only through `odoo-bin shell -d odoo_v2b04r --db_port=5433 --no-http`), all 25 merged wave 1-2 units loaded under `odoo_unt13.odoo_v2b04r__*` by the shared loader from the copy, then `odoo-bin -d odoo_v2b04r --db_port=5433 -u account,product,stock,uom,sale_stock --test-enable --test-tags /account:TestUi` with `ODOO_MONGODB_URI` bound to the migration cluster: **0 failed, 0 error(s) of 6 tests**. Copy dropped, scratch prefix 25 -> 0 collections.
- PostgreSQL-storage results were not re-run here (the ticket asks for one tour per batch on MongoDB storage); the PR's PostgreSQL-storage line above is the claim compared against.

## Branch

Committed on `recon/verify-w2-unt14` (new, flat branch; `recon/verify-w2-b01` / `-b02` on origin hold an earlier run's evidence and were left untouched). Files written through the harness's Python file tool (no file-edit tool was available in this session; no shell heredocs). No PR, no merge.

## Findings

None.

Coverage notes (not findings):
- First attempt of the batch tour on scratch copy `odoo_v2b04m` with only `-u account` errored in setUpClass (0 failed, 2 error(s) of 0 tests): the test's setup creates an opted-in record (`product.pricelist` from the test company, or `product.attribute`) and the storage path's shadow insert hit `NOT NULL` still present on `product_pricelist.currency_id` in the copy. `storage_mongodb.auto_init` (odoo/orm/storage_mongodb.py:577-601) drops those NOT NULLs when the module owning an opted-in model is updated, so the copy needs `-u` of the owning modules (`account,product,stock,uom,sale_stock`), as the batch PRs ran; with that the run above passed. Verifier setup, not a batch defect; recorded so the deployment step carries the same module update.
