run_id: ticket-6e7dd72da7154e028400b438e867eafa
manifest_sha: b965d1e5f34e

# Verify report: wave 1, batch w1-b01 (stock-reference)

Verdict: **PASS**

Verifier worked no batch ticket of wave 1 and wrote nothing to the target: every target access below is a read.

## What was re-run
- Batch PR: https://github.com/Cognition-Partner-Workshops/odoo/pull/56, branch `devin/1792502915-w1-b01-stock-reference` at `ba7c23cc7ef` (checked out as `recon/verify-w1-b01`, no code changes).
- Contracts as committed on that head: `.migration/mapping_spec.json` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc` (map-draft-2), `.migration/recon_tolerances.json` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea` (unt12-3); both equal the ticket's pins.
- Plugin: pinned worktree at `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c`, unpatched (`recon selftest` PASS, 9 rules).
- Source: `odoo_src` rebuilt with `.migration/fixtures/build_source.sh` (source commit `63446015e3c154f552633f54951843dcbb51e9a9`, marker `migration.fixture_source=3`, 70 modules), then cloned with `createdb -T odoo_src odoo_v_w1b01` and seeded through the pre-opt-in tree with `.migration/load/seed_scenario_rows.py` (crons 1,19-23 off; scrap tags ids 1-3 at `2026-10-20 00:00:00`). Clone populations: stock_storage_category 6, stock_scrap_reason_tag 3, return_reason 5. DSN derived from `ODOO_PG_RO_DSN` (database swapped) inside a one-shot shell; no credential in any artifact.
- Target: `odoo_unt12` on `MONGODB_ATLAS_URI`, class `migration_cluster`, collections `returnReason`, `stockScrapReasonTag`, `stockStorageCategory` only.

## Recon re-run (harness verdict)
Command (from the Odoo root): `recon run --unit stock-reference --family postgresql --mapping .migration/mapping_spec.json --collections returnReason,stockScrapReasonTag,stockStorageCategory --tolerances .migration/recon_tolerances.json --canonicalization <plugin>/skills/mongo-migration/profiles/postgresql.md --mode live --source-dsn-secret VERIFY_SRC_DSN --target-uri-secret MONGODB_ATLAS_URI --target-db odoo_unt12 --target-class migration_cluster --allowed-targets-file .migration/allowed_targets.json --ops .migration/recon/stock-reference/ops.json --out .migration/recon/wave-1/w1-b01`

- Result: `.migration/recon/wave-1/w1-b01/result.json` -> verdict **PASS**, merge_eligible True, mode live, target_class migration_cluster, warnings [], error None.
- Tiers: T1 counts_through_mapping 5 checks PASS / T2 per_field_aggregates 15 checks PASS / T3 keyed_diffs 14 checks PASS / T4 app_level_parity 3 checks PASS. Tier 1 source counts {"returnReason": 5, "stockScrapReasonTag": 3, "stockStorageCategory": 6}; Tier 3 full_diff on all three collections, 0 duplicate source keys.
- Against the worker's `.migration/recon/stock-reference/result.json`: every key is byte-identical except `generated_at` and `snapshot`.

## Probes past the gate (`.migration/recon/wave-1/w1-b01/verify-probes.py` -> `verify-probes.json`)
81 probes, 81 pass, 0 fail:
- boundary_max_id: 3/3 pass
- boundary_min_id: 3/3 pass
- boundary_values: 3/3 pass
- declared_collections_present: 1/1 pass
- embeds_declared_none: 3/3 pass
- index[('companyId', 1)]: 1/1 pass
- index[('name', 1)]: 1/1 pass
- key_set: 3/3 pass
- natural_key_unique[stock_scrap_reason_tag_name_uniq]: 1/1 pass
- no_same_wave_sibling_reference: 3/3 pass
- no_unmapped_target_fields: 3/3 pass
- not_empty: 3/3 pass
- null_missing_rate: 21/21 pass
- other_collections_in_target_db: 1/1 pass
- outbound_reference: 4/4 pass
- row_count: 3/3 pass
- tier4_replay: 3/3 pass
- value_equality: 21/21 pass

- Null/missing: per spec field, PG `IS NULL` count equals target missing-or-null count (e.g. stockStorageCategory.companyId, maxWeight; tags/reasons never null).
- Duplicates: `stockScrapReasonTag.name` unique index present and no duplicate groups; key sets equal, no duplicate `_id`.
- Boundaries: min/max `_id` per collection present; min/max of `maxWeight` (Decimal128 vs numeric at full precision) and `sequence` equal on both sides.
- Empty collections: none; all three populated and equal to the clone.
- Embedded arrays: the spec declares no embeds for these collections; no unmapped target fields found.
- Outbound references: `companyId -> res_company` and `writeUid -> res_users` resolve in PostgreSQL (tables of no wave-1 batch, still relational); the spec declares no references from these collections to any wave-1 sibling collection, so no sibling namespace was probed.
- App-level parity: the three `ops.json` operations were replayed independently (source_sql on the clone vs target_pipeline on Atlas, sorted, full precision) and match row for row.

## Findings
- PR #56's description says 31/31 ORM scenario checks while the committed .migration/recon/w1-b01.json says 30/30 and scenario_stock_reference.py holds 27 static check() sites; a self-reported count, not gate evidence, and not re-run here because the scenario needs a prefixed scratch namespace written into odoo_unt12, which this verify was told not to do.
- Both the worker's run and this re-run are redacted with unsalted hashes because no RECON_REDACT_SALT secret exists (harness stderr warning; result.json warnings stay empty, so the verdict is unaffected).
- odoo_unt12 also holds a `_connectivity_probe` collection that belongs to no wave-1 write target; not this batch's, left untouched for the manager.
- Plugin gap, unpatched: the installed mongo-recon-harness skill text (plugin 0.7.0) names a `--source-concurrency` flag that the pinned CLI at 9a584b4cdb311ddd64fb07cbd1cf35fc9485062c rejects; the flag was omitted and recon_tolerances.json's source_concurrency key was accepted as-is.
