run_id: UNT14-54
manifest_sha: ef5b8af24b0b

# w2-b05 independent verification: productTag, stockReference, productAttribute, productAttributeValueProductTemplateAttributeLineRel

**Verdict: PASS** (live recon, `target_class: migration_cluster`, `merge_eligible: true` on all 4 units; probes past the gate PASS; MongoDB-storage tour PASS)

Batch PR [#145](https://github.com/Cognition-Partner-Workshops/odoo/pull/145), merged; batch evidence head `53b5dabb6a030af99a3b647a4e8c6ca734539bbe` (`result.batch.json`, base `2f68f21`, manifest `ef5b8af24b0b`). Verified on the merged base `573f2cd0e8ea4a9b5b5f89aa808e1dd226376b98` (tip of `mongo-run/unt13`), which contains that head. I migrated none of these units.
Plugin pin `2c1160efde323c570425953b7e38bcc3496c6053` (`.migration/plugin_sha`), harness run from a detached worktree at that commit.

## Source

- `odoo_src` rebuilt with `.migration/fixtures/build_source.sh` (source commit `63446015e3c1`, `total_wall_seconds=247`).
- `.migration/fixtures/source_fingerprint.py` (via `secret:personal:ODOO_PG_RO_DSN`, one-shot exec): `a100e84ee2fb6282f30b45c003fd1db47561317c739340a10564d9e869e56a4e`, exact match to the ticket and `.migration/source_fingerprint.json`.
- Every recon run records `source_db: odoo_src`, `source_server: hmac-sha256:545efbd0aca82e45` (`RECON_REDACT_SALT` bound from `secret:org:RECON_REDACT_SALT`), matching `.migration/connectivity.json`. `odoo_unt13` was not reloaded or reseeded.

## Recon (my runs, `<unit>/result.json` beside this report)

Each unit: `recon.cli run --mode live --family postgresql --unit <u> --collections <u> --target-db odoo_unt13 --target-class migration_cluster --allowed-targets-file .migration/allowed_targets.json --seed 1`, committed `mapping_spec.json` (map-draft-5, sha `c0b93dad…02a7`) and `recon_tolerances.json` (v1, sha `8c9b9e4c…5416`), canonicalization = the mapping's `canonicalization` block, Tier 4 = my own `verify-ops.json`. All runs: `git_head 573f2cd`, `git_dirty false`, no warnings, Tiers 1-4 passed.

| Unit | Verdict / merge_eligible | Checks T1 / T2 / T3 / T4 | Source rows (embeds) | T1-T3 stats = batch result.json | ops_sha256 mine vs batch | batch git_head |
|---|---|---|---|---|---|---|
| `productTag` | PASS / True | 6 / 4 / 487 / 3 | 10 (+productProductRel 1, productTemplateRel 476) | yes | `b5b307915cf7…` vs `3c2cb729c906…` | `8098a41` |
| `stockReference` | PASS / True | 7 / 3 / 524 / 3 | 121 (+moveRel 281, purchaseRel 8, saleRel 114) | yes | `792c4e5d0fee…` vs `c326ab61859a…` | `8098a41` |
| `productAttribute` | PASS / True | 7 / 6 / 853 / 3 | 40 (+productTemplateRel 410, value 403) | yes | `2998c58bad7e…` vs `d97ad10689b8…` | `8098a41` |
| `productAttributeValueProductTemplateAttributeLineRel` | PASS / True | 3 / 0 / 1642 / 2 | 1642 | yes | `4a99c24bb176…` vs `dff99825de17…` | `8098a41` |

Comparison with the batch evidence (`.migration/recon/<unit>/result.json`): same mapping and tolerance sha256, same source server fingerprint, identical Tier 1 counts, Tier 2 aggregate stats and Tier 3 keyed-diff stats (full diff of every row, 0 duplicate source keys); only `ops_sha256`, `git_head` and timestamps differ, as they must.

### Tier 4 ops (verifier-owned, not the batch's)

- `productTag`: `verify_productTag_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_productTag_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id); `verify_productTag_embed_fanout_by_parent` (per-parent count of each embedded array (product_tag_product_product_rel, product_tag_product_template_rel) ag)
- `stockReference`: `verify_stockReference_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_stockReference_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id); `verify_stockReference_embed_fanout_by_parent` (per-parent count of each embedded array (stock_reference_move_rel, stock_reference_purchase_rel, stock_referen)
- `productAttribute`: `verify_productAttribute_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_productAttribute_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id); `verify_productAttribute_embed_fanout_by_parent` (per-parent count of each embedded array (product_attribute_product_template_rel, product_attribute_value) agai)
- `productAttributeValueProductTemplateAttributeLineRel`: `verify_productAttributeValueProductTemplateAttributeLineRel_links_ordered` (every link as the ORM's Many2many.read sees it, ordered by both ids); `verify_productAttributeValueProductTemplateAttributeLineRel_links_per_product_attribute_value_id` (link count per product_attribute_value_id (the owning side's record set size))

## Probes past the gate (`../probe_w2_unt14.py`, read-only; `<unit>/probe.json`)

Per unit: count; every mapped field (missing = source NULL count, no explicit nulls, BSON type = spec `bson_type`); no unmapped keys at the root or inside embedded elements; no duplicate `_id` / junction pair / natural key; every root row compared field by field with `odoo_src`; every embedded array compared element by element with its child table; declared indexes present with the same key order, unique flag and partial filter; raw-BSON sha256 of the collection before recon and after all probes and tours.

| Unit | Probes | Fields | Rows / junction | Embeds (source children = target elements) | Indexes | raw-BSON sha256 before = after (docs) |
|---|---|---|---|---|---|---|
| `productTag` | PASS (13 probes) | 8 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 10 rows x 8 fields, 0 mismatches | `productProductRel` 1=1; `productTemplateRel` 476=476 | 3 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 1 unique | `3153d3be1f6c…` = `3153d3be1f6c…` (10) |
| `stockReference` | PASS (15 probes) | 5 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 121 rows x 5 fields, 0 mismatches | `moveRel` 281=281; `purchaseRel` 8=8; `saleRel` 114=114 | 3 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `cf3f102ca5b9…` = `cf3f102ca5b9…` (121) |
| `productAttribute` | PASS (14 probes) | 9 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 40 rows x 9 fields, 0 mismatches | `productTemplateRel` 410=410; `value` 403=403 | 4 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `c309bc8acc24…` = `c309bc8acc24…` (40) |
| `productAttributeValueProductTemplateAttributeLineRel` | PASS (11 probes) | 0 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 1642 source links = 1642 target links; read back from `productAttributeValueId` (317 endpoints, 1642 links, resolved in odoo_unt13.productAttribute.value.id (wave 2)), `productTemplateAttributeLineId` (410 endpoints, 1642 links, resolved in odoo_src.product_template_attribute_line (PostgreSQL-resident, wave 4)) | none | 2 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 1 unique | `4db800a7b735…` = `4db800a7b735…` (1642) |

Index note: none of this batch's spec indexes declares a partial filter, so the partial-filter check has nothing to compare for the spec's own filters; the live unique indexes carry `{<key>: {$exists: true}}`, which is what `storage_mongodb._create_indexes` (`odoo/orm/storage_mongodb.py:736-742`) adds to every unique index so that omitted NULLs never collide, and the probe expects exactly that filter.

### References (resolved against the real FK parent in `odoo_src`, then located)

A parent that is a merged wave 1-2 collection (or an embedded child array of one) is resolved in `odoo_unt13`; everything else is PostgreSQL-resident (framework tables or units of waves 3+) and is resolved in `odoo_src`. No reference was resolved through an unmerged namespace.

| Unit | Field -> spec `to` | FK parent | Resolved in | Distinct values | Dangling | |
|---|---|---|---|---|---|---|
| `productTag` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productTag` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productTag` | `productProductRel.productProductId->productProduct` | `product_product` | odoo_src.product_product (PostgreSQL-resident, wave 4) | 1 | 0 | PASS |
| `productTag` | `productTemplateRel.productTemplateId->productTemplate` | `product_template` | odoo_src.product_template (PostgreSQL-resident, wave 3) | 159 | 0 | PASS |
| `stockReference` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `stockReference` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `stockReference` | `moveRel.moveId->stockMove` | `stock_move` | odoo_src.stock_move (PostgreSQL-resident, wave 9) | 281 | 0 | PASS |
| `stockReference` | `purchaseRel.purchaseId->purchaseOrder` | `purchase_order` | odoo_src.purchase_order (PostgreSQL-resident, wave 4) | 8 | 0 | PASS |
| `stockReference` | `saleRel.saleId->saleOrder` | `sale_order` | odoo_src.sale_order (PostgreSQL-resident, wave 6) | 113 | 0 | PASS |
| `productAttribute` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productAttribute` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productAttribute` | `productTemplateRel.productTemplateId->productTemplate` | `product_template` | odoo_src.product_template (PostgreSQL-resident, wave 3) | 208 | 0 | PASS |
| `productAttribute` | `value.createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productAttribute` | `value.writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productAttributeValueProductTemplateAttributeLineRel` | `productTemplateAttributeLineId->productTemplateAttributeLine` | `product_template_attribute_line` | odoo_src.product_template_attribute_line (PostgreSQL-resident, wave 4) | 410 | 0 | PASS |
| `productAttributeValueProductTemplateAttributeLineRel` | `productAttributeValueId->productAttribute` | `product_attribute_value` | odoo_unt13.productAttribute.value.id (merged wave 2, w2-b05) | 317 | 0 | PASS |

## Tours

- Batch claim: PR #145 / `result.batch.json`: productAttribute tours (5 HttpCase classes, 13 tests, 11 tours) 13/13 on PostgreSQL storage and 13/13 on MongoDB storage, 0 skipped.
- My re-run on MongoDB storage: scratch copy `odoo_v2b05r` (`createdb -T odoo_src`, admin password set only through `odoo-bin shell -d odoo_v2b05r --db_port=5433 --no-http`), all 25 merged wave 1-2 units loaded under `odoo_unt13.odoo_v2b05r__*` by the shared loader from the copy, then `odoo-bin -d odoo_v2b05r --db_port=5433 -u account,product,stock,uom,sale_stock,sale --test-enable --test-tags /sale:TestProductAttributeValue` with `ODOO_MONGODB_URI` bound to the migration cluster: **0 failed, 0 error(s) of 1 tests**. Copy dropped, scratch prefix 25 -> 0 collections.
- PostgreSQL-storage results were not re-run here (the ticket asks for one tour per batch on MongoDB storage); the PR's PostgreSQL-storage line above is the claim compared against.

## Branch

Committed on `recon/verify-w2-unt14` (new, flat branch; `recon/verify-w2-b01` / `-b02` on origin hold an earlier run's evidence and were left untouched). Files written through the harness's Python file tool (no file-edit tool was available in this session; no shell heredocs). No PR, no merge.

## Findings

None.

Coverage notes (not findings):
- First attempt of the batch tour on scratch copy `odoo_v2b05m` with only `-u sale` errored in setUpClass (0 failed, 1 error(s) of 0 tests): the test's setup creates an opted-in record (`product.pricelist` from the test company, or `product.attribute`) and the storage path's shadow insert hit `NOT NULL` still present on `product_attribute.create_variant` in the copy. `storage_mongodb.auto_init` (odoo/orm/storage_mongodb.py:577-601) drops those NOT NULLs when the module owning an opted-in model is updated, so the copy needs `-u` of the owning modules (`account,product,stock,uom,sale_stock`), as the batch PRs ran; with that the run above passed. Verifier setup, not a batch defect; recorded so the deployment step carries the same module update.
