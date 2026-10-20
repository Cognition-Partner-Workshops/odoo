run_id: ticket-0b5f81f6294a43d394fc0cb0732d4025
manifest_sha: b965d1e5f34e

# Verify report: batch w1-b06 (wave 1, unit account-chart) — re-verification at frozen head def85b9

Verdict: **PASS**

Independent verifier; this session migrated none of the batch and wrote nothing to the batch collections. Supersedes the earlier verifies of PR #64 at 5d3ca17 (8acd45d) and e5c213e (d375169); this branch was rewritten from the new head.

## What was re-run
- Worker PR: https://github.com/Cognition-Partner-Workshops/odoo/pull/64, branch `devin/1792506997-w1-b06-account-chart` as pushed, frozen head **`def85b9f061e27296ba65c1216e2ad2514d052dc`** (result-JSON commit; code head `201cc38`), merge-base with `mongo-run/unt12` = `a25acb9` (unified loader PR #68). This branch `recon/verify-w1-b06` is cut from `def85b9`.
- Mapping `.migration/mapping_spec.json` = map-draft-2, sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc` (matches ticket pin).
- Tolerances `.migration/recon_tolerances.json` = unt12-3, sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea` (matches ticket pin).
- Plugin: worktree at pinned `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c`, unpatched; `recon selftest` PASS.
- Source: `odoo_src` dropped and rebuilt from scratch by this verifier with `.migration/fixtures/build_source.sh` from the def85b9 tree (deterministic, marker `migration.fixture_source=3`, source commit `63446015e3c`, 70 modules). Row counts: account_account 184, account_account_tag 8, account_tax 57, account_tax_group 26, account_tax_repartition_line 228, account_fiscal_position 4.
- Fresh verifier clone: `createdb -p 5433 -T odoo_src odoo_v_w1b06` (old clone dropped first), reseeded with the def85b9 `.migration/load/seed_scenario_rows.py` through the pre-opt-in tree `odoo-unt12-src` (PostgreSQL only): 184 / 10 / 58 / 26 / 232 / 4 plus the seven zero-fixture embedded arrays (1-2 elements each).
- Target: `odoo_unt12` on `MONGODB_ATLAS_URI` (target_class migration_cluster). Batch collections read only; the only writes were to the temporary verifier prefix below.

## Source-DSN check on the committed worker result
`.migration/recon/account-chart/result.json` at def85b9 (generated 2026-10-20T18:29:38Z, `w1-b06.json` head_sha 201cc38, base a25acb9) records Tier-1 source_counts 184 / 8 / 57 / 26 / 228 / 4 = the `odoo_src` counts (a seeded clone reads 10 / 58 / 232). The target holds exactly those documents and none of the seeded-only array elements. Confirmed graded against `odoo_src`.

## Recon re-run (live, source = odoo_src, branch as pushed, scoped with --collections)
```
PYTHONPATH=<plugin>/skills/mongo-recon-harness/harness python -m recon.cli run \
  --unit account-chart --family postgresql --mapping .migration/mapping_spec.json \
  --collections accountAccount,accountAccountTag,accountTax,accountTaxGroup,accountTaxRepartitionLine,accountFiscalPosition \
  --tolerances .migration/recon_tolerances.json --canonicalization .migration/rehearsal/canon.postgresql.json \
  --mode live --source-dsn-secret ODOO_PG_RO_DSN --target-uri-secret MONGODB_ATLAS_URI \
  --target-db odoo_unt12 --target-class migration_cluster --allowed-targets-file .migration/allowed_targets.json \
  --ops .migration/recon/account-chart/ops.json --out .migration/recon/wave-1/w1-b06
```
Result: `.migration/recon/wave-1/w1-b06/result.json` — verdict PASS, merge_eligible true, warnings [], generated_at 2026-10-20T18:40:11.974819+00:00 (run after the scenario and the prefix clean-up, so it also shows the batch collections unchanged; an identical PASS was obtained before the scenario at 18:38:31Z).
Tiers: 1 counts_through_mapping 62 PASS; 2 per_field_aggregates 52 PASS; 3 keyed_diffs 981 PASS; 4 app_level_parity 6 PASS. Identical to the worker's committed result.json except `generated_at`. No mismatch, so no drift re-run was needed.

## Probes past the gate (`verify-probes.py` -> `verify-probes.json`, source = odoo_src): 459 probes, 459 pass, 0 fail
Same checks as the previous verify: row counts, key sets, min/max `_id` boundary docs, non-empty; per mapped field null-vs-missing rate, full value equality by id, min/max boundary values; no unmapped target fields; natural key `account_account_tag_name_uniq` unique; all declared indexes present; 15 embedded arrays (length distribution = child-row counts, element keys unique, element values equal, no orphan parents); all outbound and embedded child references resolve (in-batch targets also as `_id` in the target; later-wave and framework tables in PostgreSQL); no reference to a wave-1 sibling collection; parentPath / codeStore / distribution spot checks; all 6 Tier-4 `ops.json` operations replayed row-for-row.

## ORM scenario (`.migration/load/scenario_account_chart.py` at def85b9, 79 checks) on the seeded verifier clone — temporary prefix only
The clone's documents were loaded with `verify-load-prefixed.py` (the def85b9 unified `load_unit.py` functions, unchanged; the wrapper only adapts to `unit_collections` now returning a tuple) into the verifier-private prefixed namespace `odoo_unt12.odoo_v_w1b06__<collection>` — the storage path's own test-isolation prefix (no `mongodb_migration_db` in the conf, so Odoo never ran with the collections unprefixed). The piped copy of the scenario replaces `assert st.prefix == ''` with an assert that the prefix is `odoo_v_w1b06__`; nothing else changed. Run: `odoo-bin shell -c <conf: db_port 5433, addons_path of the def85b9 tree> -d odoo_v_w1b06 --no-http < scenario`.
- def85b9: **79/79** checks passed, relations reading empty: none, storage-path unsupported: none, "rollback leaves the loaded collections byte-identical" PASS (`scenario-def85b9.log`).
- The six prefixed collections were dropped afterwards (none left); the batch collections were then re-reconciled: PASS, unchanged.

## Findings
None blocking.

Non-blocking notes for the manager (not parity findings):
- The live load mirrors plain `odoo_src`, so the seven embedded arrays with 0 fixture rows (units.json recon_unverified) are exercised only by the ORM scenario on the seeded clone, not by the live recon.
- `RECON_REDACT_SALT` is not set in this environment, so the live report is redacted with unsalted hashes (harness warning).
- Plugin gap: `wave-verify` SKILL text advertises `--source-concurrency`; the pinned CLI does not accept it (not used).
- A verifier can only run the scenario in a prefix by editing its `prefix == ''` assert; a namespace option on the scenario and loader would make the verifier path first-class.
