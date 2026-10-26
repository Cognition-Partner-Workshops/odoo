run_id: UNT14-54
manifest_sha: ef5b8af24b0b

# w2-b01 independent verification: accountJournalGroup, productBaseUnit, productDocument, stockScrapReasonTag, productRemoval

**Verdict: PASS** (live recon, `target_class: migration_cluster`, `merge_eligible: true` on all 5 units; probes past the gate PASS; MongoDB-storage tour PASS)

Batch PR [#142](https://github.com/Cognition-Partner-Workshops/odoo/pull/142), merged; batch evidence head `9b90e5561056f14661b2e5d77a719c36ba864158` (`result.batch.json`, base `2f68f21`, manifest `ef5b8af24b0b`). Verified on the merged base `573f2cd0e8ea4a9b5b5f89aa808e1dd226376b98` (tip of `mongo-run/unt13`), which contains that head. I migrated none of these units.
Plugin pin `2c1160efde323c570425953b7e38bcc3496c6053` (`.migration/plugin_sha`), harness run from a detached worktree at that commit.

## Source

- `odoo_src` rebuilt with `.migration/fixtures/build_source.sh` (source commit `63446015e3c1`, `total_wall_seconds=247`).
- `.migration/fixtures/source_fingerprint.py` (via `secret:personal:ODOO_PG_RO_DSN`, one-shot exec): `a100e84ee2fb6282f30b45c003fd1db47561317c739340a10564d9e869e56a4e`, exact match to the ticket and `.migration/source_fingerprint.json`.
- Every recon run records `source_db: odoo_src`, `source_server: hmac-sha256:545efbd0aca82e45` (`RECON_REDACT_SALT` bound from `secret:org:RECON_REDACT_SALT`), matching `.migration/connectivity.json`. `odoo_unt13` was not reloaded or reseeded.

## Recon (my runs, `<unit>/result.json` beside this report)

Each unit: `recon.cli run --mode live --family postgresql --unit <u> --collections <u> --target-db odoo_unt13 --target-class migration_cluster --allowed-targets-file .migration/allowed_targets.json --seed 1`, committed `mapping_spec.json` (map-draft-5, sha `c0b93dad…02a7`) and `recon_tolerances.json` (v1, sha `8c9b9e4c…5416`), canonicalization = the mapping's `canonicalization` block, Tier 4 = my own `verify-ops.json`. All runs: `git_head 573f2cd`, `git_dirty false`, no warnings, Tiers 1-4 passed.

| Unit | Verdict / merge_eligible | Checks T1 / T2 / T3 / T4 | Source rows (embeds) | T1-T3 stats = batch result.json | ops_sha256 mine vs batch | batch git_head |
|---|---|---|---|---|---|---|
| `accountJournalGroup` | PASS / True | 2 / 4 / 2 / 2 | 2 | yes | `cf78532dab5a…` vs `7b2d9726fb5a…` | `12944a6` |
| `productBaseUnit` | PASS / True | 1 / 3 / 2 / 2 | 2 | yes | `2d89955b9e13…` vs `268f8a6a9d1c…` | `12944a6` |
| `productDocument` | PASS / True | 2 / 5 / 2 / 2 | 2 | yes | `5ac3143ccba6…` vs `f70af1137a0c…` | `4cdc6ff` |
| `stockScrapReasonTag` | PASS / True | 2 / 5 / 3 / 2 | 3 | yes | `af21e9ea1eec…` vs `124011c81a73…` | `12944a6` |
| `productRemoval` | PASS / True | 1 / 4 / 4 / 2 | 4 | yes | `3b75e4814e52…` vs `68bd5e0f79a9…` | `12944a6` |

Comparison with the batch evidence (`.migration/recon/<unit>/result.json`): same mapping and tolerance sha256, same source server fingerprint, identical Tier 1 counts, Tier 2 aggregate stats and Tier 3 keyed-diff stats (full diff of every row, 0 duplicate source keys); only `ops_sha256`, `git_head` and timestamps differ, as they must.

### Tier 4 ops (verifier-owned, not the batch's)

- `accountJournalGroup`: `verify_accountJournalGroup_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_accountJournalGroup_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id)
- `productBaseUnit`: `verify_productBaseUnit_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_productBaseUnit_rows_per_create_uid` (record count per creating user (the 'created by' grouping of the list view))
- `productDocument`: `verify_productDocument_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_productDocument_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id)
- `stockScrapReasonTag`: `verify_stockScrapReasonTag_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_stockScrapReasonTag_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id)
- `productRemoval`: `verify_productRemoval_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_productRemoval_rows_per_create_uid` (record count per creating user (the 'created by' grouping of the list view))

## Probes past the gate (`../probe_w2_unt14.py`, read-only; `<unit>/probe.json`)

Per unit: count; every mapped field (missing = source NULL count, no explicit nulls, BSON type = spec `bson_type`); no unmapped keys at the root or inside embedded elements; no duplicate `_id` / junction pair / natural key; every root row compared field by field with `odoo_src`; every embedded array compared element by element with its child table; declared indexes present with the same key order, unique flag and partial filter; raw-BSON sha256 of the collection before recon and after all probes and tours.

| Unit | Probes | Fields | Rows / junction | Embeds (source children = target elements) | Indexes | raw-BSON sha256 before = after (docs) |
|---|---|---|---|---|---|---|
| `accountJournalGroup` | PASS (9 probes) | 6 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 2 rows x 6 fields, 0 mismatches | none | 1 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 1 unique | `6667624a3e94…` = `6667624a3e94…` (2) |
| `productBaseUnit` | PASS (9 probes) | 5 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 2 rows x 5 fields, 0 mismatches | none | 0 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `9bd2c1216763…` = `9bd2c1216763…` (2) |
| `productDocument` | PASS (10 probes) | 8 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 2 rows x 8 fields, 0 mismatches | none | 1 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `b1bb0c15d92c…` = `b1bb0c15d92c…` (2) |
| `stockScrapReasonTag` | PASS (9 probes) | 7 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 3 rows x 7 fields, 0 mismatches | none | 1 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 1 unique | `b659e5698fa7…` = `b659e5698fa7…` (3) |
| `productRemoval` | PASS (9 probes) | 6 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 4 rows x 6 fields, 0 mismatches | none | 0 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `205367f5bca1…` = `205367f5bca1…` (4) |

Index note: none of this batch's spec indexes declares a partial filter, so the partial-filter check has nothing to compare for the spec's own filters; the live unique indexes carry `{<key>: {$exists: true}}`, which is what `storage_mongodb._create_indexes` (`odoo/orm/storage_mongodb.py:736-742`) adds to every unique index so that omitted NULLs never collide, and the probe expects exactly that filter.

### References (resolved against the real FK parent in `odoo_src`, then located)

A parent that is a merged wave 1-2 collection (or an embedded child array of one) is resolved in `odoo_unt13`; everything else is PostgreSQL-resident (framework tables or units of waves 3+) and is resolved in `odoo_src`. No reference was resolved through an unmerged namespace.

| Unit | Field -> spec `to` | FK parent | Resolved in | Distinct values | Dangling | |
|---|---|---|---|---|---|---|
| `accountJournalGroup` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountJournalGroup` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productBaseUnit` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productBaseUnit` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productDocument` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productDocument` | `irAttachmentId->irAttachment` | `ir_attachment` | odoo_src.ir_attachment (PostgreSQL-resident, framework table) | 2 | 0 | PASS |
| `productDocument` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `stockScrapReasonTag` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `stockScrapReasonTag` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productRemoval` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productRemoval` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |

## Tours

- Batch claim: PR #142: units list `tours: []`, so the owning addons' HttpCase classes were run: `/account:TestUi` (6), `/stock:TestStockPickingTour` (4), `/stock:TestStockReportTour` (3), `/product:TestPricelistReportController` (2); PostgreSQL storage (base 2f68f21) 14 pass / 1 fail (`test_inventory_adjustment_apply_all`, identical on the unchanged base tree), MongoDB storage 14 pass / the same 1 fail; `result.batch.json`: tours 14/15 on both storages.
- My re-run on MongoDB storage: scratch copy `odoo_v2b01m` (`createdb -T odoo_src`, admin password set only through `odoo-bin shell -d odoo_v2b01m --db_port=5433 --no-http`), all 25 merged wave 1-2 units loaded under `odoo_unt13.odoo_v2b01m__*` by the shared loader from the copy, then `odoo-bin -d odoo_v2b01m --db_port=5433 -u product --test-enable --test-tags /product:TestPricelistReportController` with `ODOO_MONGODB_URI` bound to the migration cluster: **0 failed, 0 error(s) of 2 tests**. Copy dropped, scratch prefix 25 -> 0 collections.
- PostgreSQL-storage results were not re-run here (the ticket asks for one tour per batch on MongoDB storage); the PR's PostgreSQL-storage line above is the claim compared against.

## Branch

Committed on `recon/verify-w2-unt14` (new, flat branch; `recon/verify-w2-b01` / `-b02` on origin hold an earlier run's evidence and were left untouched). Files written through the harness's Python file tool (no file-edit tool was available in this session; no shell heredocs). No PR, no merge.

## Findings

None.

Coverage notes (not findings):
- `/product:TestPricelistReportController` has no `start_tour` steps (HttpCase export tests, 0 `tour succeeded` lines), so `/stock:TestStockReportTour` was also run on MongoDB storage on scratch copy `odoo_v2b01u`: 0 failed, 0 error(s) of 3 tests, 3 tours succeeded, scratch prefix 25 -> 0 collections.
- First attempt of `/stock:TestStockReportTour` on scratch copy `odoo_v2b01t` with only `-u stock` errored in setUpClass (0 failed, 1 error(s) of 3 tests): the test's setup creates an opted-in record (`product.pricelist` from the test company, or `product.attribute`) and the storage path's shadow insert hit `NOT NULL` still present on `product_attribute.create_variant` in the copy. `storage_mongodb.auto_init` (odoo/orm/storage_mongodb.py:577-601) drops those NOT NULLs when the module owning an opted-in model is updated, so the copy needs `-u` of the owning modules (`account,product,stock,uom,sale_stock`), as the batch PRs ran; with that the run above passed. Verifier setup, not a batch defect; recorded so the deployment step carries the same module update.
