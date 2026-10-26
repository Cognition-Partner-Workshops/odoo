run_id: UNT14-54
manifest_sha: ef5b8af24b0b

# w2-b02 independent verification: returnReason, stockStorageCategory, accountCashRounding, stockPackageType, productPricelist

**Verdict: PASS** (live recon, `target_class: migration_cluster`, `merge_eligible: true` on all 5 units; probes past the gate PASS; MongoDB-storage tour PASS)

Batch PR [#141](https://github.com/Cognition-Partner-Workshops/odoo/pull/141), merged; batch evidence head `47d4f88fa279bf2b523d949bf27421ad11b44b19` (`result.batch.json`, base `2f68f21`, manifest `ef5b8af24b0b`). Verified on the merged base `573f2cd0e8ea4a9b5b5f89aa808e1dd226376b98` (tip of `mongo-run/unt13`), which contains that head. I migrated none of these units.
Plugin pin `2c1160efde323c570425953b7e38bcc3496c6053` (`.migration/plugin_sha`), harness run from a detached worktree at that commit.

## Source

- `odoo_src` rebuilt with `.migration/fixtures/build_source.sh` (source commit `63446015e3c1`, `total_wall_seconds=247`).
- `.migration/fixtures/source_fingerprint.py` (via `secret:personal:ODOO_PG_RO_DSN`, one-shot exec): `a100e84ee2fb6282f30b45c003fd1db47561317c739340a10564d9e869e56a4e`, exact match to the ticket and `.migration/source_fingerprint.json`.
- Every recon run records `source_db: odoo_src`, `source_server: hmac-sha256:545efbd0aca82e45` (`RECON_REDACT_SALT` bound from `secret:org:RECON_REDACT_SALT`), matching `.migration/connectivity.json`. `odoo_unt13` was not reloaded or reseeded.

## Recon (my runs, `<unit>/result.json` beside this report)

Each unit: `recon.cli run --mode live --family postgresql --unit <u> --collections <u> --target-db odoo_unt13 --target-class migration_cluster --allowed-targets-file .migration/allowed_targets.json --seed 1`, committed `mapping_spec.json` (map-draft-5, sha `c0b93dad…02a7`) and `recon_tolerances.json` (v1, sha `8c9b9e4c…5416`), canonicalization = the mapping's `canonicalization` block, Tier 4 = my own `verify-ops.json`. All runs: `git_head 573f2cd`, `git_dirty false`, no warnings, Tiers 1-4 passed.

| Unit | Verdict / merge_eligible | Checks T1 / T2 / T3 / T4 | Source rows (embeds) | T1-T3 stats = batch result.json | ops_sha256 mine vs batch | batch git_head |
|---|---|---|---|---|---|---|
| `returnReason` | PASS / True | 1 / 4 / 5 / 2 | 5 | yes | `35cfd1b785bd…` vs `717af885a5a7…` | `cd323f1` |
| `stockStorageCategory` | PASS / True | 2 / 6 / 6 / 2 | 6 | yes | `2c46c29a4809…` vs `6dc0598094ca…` | `cd323f1` |
| `accountCashRounding` | PASS / True | 9 / 7 / 7 / 3 | 2 (+resCurrencyRel 1, resPartnerCategoryRel 2, accountPaymentMethodLineRel 2) | yes | `79986d18a0e5…` vs `92cc3a5c56c3…` | `cd323f1` |
| `stockPackageType` | PASS / True | 6 / 12 / 7 / 3 | 3 (+stockPutawayRuleRel 2, stockRouteRel 2) | yes | `985ead020ca2…` vs `54a7a62b9aa5…` | `cd323f1` |
| `productPricelist` | PASS / True | 4 / 6 / 9 / 2 | 9 | yes | `d1f62218ff42…` vs `4230b7ba77ba…` | `cd323f1` |

Comparison with the batch evidence (`.migration/recon/<unit>/result.json`): same mapping and tolerance sha256, same source server fingerprint, identical Tier 1 counts, Tier 2 aggregate stats and Tier 3 keyed-diff stats (full diff of every row, 0 duplicate source keys); only `ops_sha256`, `git_head` and timestamps differ, as they must.

### Tier 4 ops (verifier-owned, not the batch's)

- `returnReason`: `verify_returnReason_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_returnReason_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id)
- `stockStorageCategory`: `verify_stockStorageCategory_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_stockStorageCategory_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id)
- `accountCashRounding`: `verify_accountCashRounding_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_accountCashRounding_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id); `verify_accountCashRounding_embed_fanout_by_parent` (per-parent count of each embedded array (account_cash_rounding_res_currency_rel, account_cash_rounding_res_par)
- `stockPackageType`: `verify_stockPackageType_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_stockPackageType_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id); `verify_stockPackageType_embed_fanout_by_parent` (per-parent count of each embedded array (stock_package_type_stock_putaway_rule_rel, stock_package_type_stock_r)
- `productPricelist`: `verify_productPricelist_audit_columns_by_id` (create/write uid and date per row (mail/chatter and the record's metadata read), keyed by id); `verify_productPricelist_scalar_listing` (every int/string/bool column of every row as a list view reads it, keyed by id)

## Probes past the gate (`../probe_w2_unt14.py`, read-only; `<unit>/probe.json`)

Per unit: count; every mapped field (missing = source NULL count, no explicit nulls, BSON type = spec `bson_type`); no unmapped keys at the root or inside embedded elements; no duplicate `_id` / junction pair / natural key; every root row compared field by field with `odoo_src`; every embedded array compared element by element with its child table; declared indexes present with the same key order, unique flag and partial filter; raw-BSON sha256 of the collection before recon and after all probes and tours.

| Unit | Probes | Fields | Rows / junction | Embeds (source children = target elements) | Indexes | raw-BSON sha256 before = after (docs) |
|---|---|---|---|---|---|---|
| `returnReason` | PASS (9 probes) | 6 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 5 rows x 6 fields, 0 mismatches | none | 0 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `1370a0920f1a…` = `1370a0920f1a…` (5) |
| `stockStorageCategory` | PASS (10 probes) | 8 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 6 rows x 8 fields, 0 mismatches | none | 1 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `faff8bc5a6c0…` = `faff8bc5a6c0…` (6) |
| `accountCashRounding` | PASS (16 probes) | 13 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 2 rows x 13 fields, 0 mismatches | `resCurrencyRel` 1=1; `resPartnerCategoryRel` 2=2; `accountPaymentMethodLineRel` 2=2 | 5 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `454fc20b2d38…` = `454fc20b2d38…` (2) |
| `stockPackageType` | PASS (15 probes) | 15 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 3 rows x 15 fields, 0 mismatches | `stockPutawayRuleRel` 2=2; `stockRouteRel` 2=2 | 3 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `6c0fe9e74ed1…` = `6c0fe9e74ed1…` (3) |
| `productPricelist` | PASS (11 probes) | 9 fields: 0 explicit nulls, 0 type errors, missing = source NULLs | 9 rows x 9 fields, 0 mismatches | none | 3 declared, 0 missing, 0 option mismatches, 0 extra, 0 with a spec partial filter, 0 unique | `3d425809f028…` = `3d425809f028…` (9) |

Index note: none of this batch's spec indexes declares a partial filter, so the partial-filter check has nothing to compare for the spec's own filters; the live unique indexes carry `{<key>: {$exists: true}}`, which is what `storage_mongodb._create_indexes` (`odoo/orm/storage_mongodb.py:736-742`) adds to every unique index so that omitted NULLs never collide, and the probe expects exactly that filter.

### References (resolved against the real FK parent in `odoo_src`, then located)

A parent that is a merged wave 1-2 collection (or an embedded child array of one) is resolved in `odoo_unt13`; everything else is PostgreSQL-resident (framework tables or units of waves 3+) and is resolved in `odoo_src`. No reference was resolved through an unmerged namespace.

| Unit | Field -> spec `to` | FK parent | Resolved in | Distinct values | Dangling | |
|---|---|---|---|---|---|---|
| `returnReason` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `returnReason` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `stockStorageCategory` | `companyId->resCompany` | `res_company` | odoo_src.res_company (PostgreSQL-resident, framework table) | 0 | 0 | PASS |
| `stockStorageCategory` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `stockStorageCategory` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountCashRounding` | `companyId->resCompany` | `res_company` | odoo_src.res_company (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountCashRounding` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountCashRounding` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountCashRounding` | `resCurrencyRel.resCurrencyId->resCurrency` | `res_currency` | odoo_src.res_currency (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `accountCashRounding` | `resPartnerCategoryRel.resPartnerCategoryId->resPartnerCategory` | `res_partner_category` | odoo_src.res_partner_category (PostgreSQL-resident, framework table) | 2 | 0 | PASS |
| `accountCashRounding` | `accountPaymentMethodLineRel.accountPaymentMethodLineId->accountPaymentMethod` | `account_payment_method_line` | odoo_src.account_payment_method_line (PostgreSQL-resident, wave 4) | 2 | 0 | PASS |
| `stockPackageType` | `companyId->resCompany` | `res_company` | odoo_src.res_company (PostgreSQL-resident, framework table) | 0 | 0 | PASS |
| `stockPackageType` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `stockPackageType` | `sequenceId->irSequence` | `ir_sequence` | odoo_src.ir_sequence (PostgreSQL-resident, framework table) | 2 | 0 | PASS |
| `stockPackageType` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `stockPackageType` | `stockPutawayRuleRel.stockPutawayRuleId->stockPutawayRule` | `stock_putaway_rule` | odoo_src.stock_putaway_rule (PostgreSQL-resident, wave 5) | 1 | 0 | PASS |
| `stockPackageType` | `stockRouteRel.stockRouteId->stockRoute` | `stock_route` | odoo_src.stock_route (PostgreSQL-resident, wave 3) | 2 | 0 | PASS |
| `productPricelist` | `companyId->resCompany` | `res_company` | odoo_src.res_company (PostgreSQL-resident, framework table) | 3 | 0 | PASS |
| `productPricelist` | `createUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productPricelist` | `currencyId->resCurrency` | `res_currency` | odoo_src.res_currency (PostgreSQL-resident, framework table) | 1 | 0 | PASS |
| `productPricelist` | `writeUid->resUsers` | `res_users` | odoo_src.res_users (PostgreSQL-resident, framework table) | 1 | 0 | PASS |

## Tours

- Batch claim: PR #141 / `result.batch.json`: `stock:TestBatchPickingSynchronization` 1 test, 0 failed, 0 error, tour succeeded on the PostgreSQL copy (base 2f68f21) and on the MongoDB copy.
- My re-run on MongoDB storage: scratch copy `odoo_v2b02m` (`createdb -T odoo_src`, admin password set only through `odoo-bin shell -d odoo_v2b02m --db_port=5433 --no-http`), all 25 merged wave 1-2 units loaded under `odoo_unt13.odoo_v2b02m__*` by the shared loader from the copy, then `odoo-bin -d odoo_v2b02m --db_port=5433 -u stock --test-enable --test-tags /stock:TestBatchPickingSynchronization` with `ODOO_MONGODB_URI` bound to the migration cluster: **0 failed, 0 error(s) of 1 tests**. Copy dropped, scratch prefix 25 -> 0 collections.
- PostgreSQL-storage results were not re-run here (the ticket asks for one tour per batch on MongoDB storage); the PR's PostgreSQL-storage line above is the claim compared against.

## Branch

Committed on `recon/verify-w2-unt14` (new, flat branch; `recon/verify-w2-b01` / `-b02` on origin hold an earlier run's evidence and were left untouched). Files written through the harness's Python file tool (no file-edit tool was available in this session; no shell heredocs). No PR, no merge.

## Findings

None.

Coverage notes (not findings):
- none
