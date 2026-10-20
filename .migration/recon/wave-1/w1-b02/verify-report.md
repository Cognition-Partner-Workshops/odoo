run_id: ticket-8cc5fa2c31ee422d9443c1dfdb650d6e
manifest_sha: b965d1e5f34e
verified_head: 30117cc5b355d65e9793aca1054b88e3554dfbc4
verified_base: mongo-run/unt12 a25acb9ede8 (unified loader PR #68; ancestry confirmed with git merge-base --is-ancestor)

# Wave 1 / batch w1-b02 (product-taxonomy) — independent verify, re-run 5 (PR #61 rebased onto a25acb9 and frozen at 30117cc)

**Verdict: PASS** (graded from `.migration/recon/wave-1/w1-b02/result.json`, this verifier's own live recon re-run from PR #61 head `30117cc5b355d65e9793aca1054b88e3554dfbc4`, 18/22/27/7 checks PASS, `warnings: []`; 194/194 beyond-gate probes; 45/45 read-only ORM probes and 28/28 unlink-parity probes, all exact equality against PostgreSQL, run on that same head with no local merge this time). Nothing written to the five batch collections (sha256 snapshot identical before and after); nothing merged.

## What was verified, from where

- Batch PR: #61 at head `30117cc5b355d65e9793aca1054b88e3554dfbc4` (fetched via `pull/61/head`), based on `mongo-run/unt12` `a25acb9ede8` (PR #68, unified loader + `seed_scenario_rows.py`). This verifier authored none of it, did not rebase or push it, and changed nothing in `odoo_unt12`.
- Mapping `.migration/mapping_spec.json` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc` (map-draft-2) and tolerances `.migration/recon_tolerances.json` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea` (unt12-3): bytes as committed at that head, equal to the ticket pins; `result.json` records the same two hashes.
- Plugin: worktree of `mongo-migration-plugin` at `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (= `.migration/plugin_sha` at the head), unpatched.
- Source: `odoo_src` (pre-opt-in commit `63446015e3c`, marker `migration.fixture_source=3`) passed through `.migration/fixtures/build_source.sh` again (exit 0; deterministic), then cloned fresh with `createdb -T odoo_src odoo_v_w1b02r5c` and reseeded independently by running the head's `.migration/load/seed_scenario_rows.py` through the pre-opt-in `odoo-unt12-src` tree (PostgreSQL-only writes: 3 tags, 2 base units, junction rows `{1:[1,2],2:[1]}`, `{1:[1,2,3]}`, `{1:[1,4],3:[5]}`). The clone name differs from every `mongodb_migration_db` value used; no `-u`/`-i` was run on any database.
- Target: `odoo_unt12` via `MONGODB_ATLAS_URI`, read only on the live collections; no load step, no `odoo-bin -u`/`-i`, no `ensure_indexes`.

## Recon re-run (merge authority)

```
PYTHONPATH=<plugin@9a584b4>/skills/mongo-recon-harness/harness python -m recon.cli run \
  --unit product-taxonomy --family postgresql --mapping .migration/mapping_spec.json \
  --collections productCategory,productRemoval,productTag,productDocument,productBaseUnit \
  --tolerances .migration/recon_tolerances.json \
  --canonicalization <plugin@9a584b4>/skills/mongo-migration/profiles/postgresql.md \
  --mode live --source-dsn-secret VERIFY_SRC_DSN --target-uri-secret MONGODB_ATLAS_URI \
  --target-db odoo_unt12 --target-class migration_cluster \
  --allowed-targets-file .migration/allowed_targets.json \
  --ops .migration/recon/product-taxonomy/ops.json --out <dir copied to .migration/recon/wave-1/w1-b02>
```

`VERIFY_SRC_DSN` is the read-only `odoo_ro` credential with `database` set to the verifier clone, built in-session and never printed. Result (`generated_at` 2026-10-20T18:42:10Z): `recon PASS ... merge_eligible=True`, exit 0, `warnings: []`, `error: null`.

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 18 | PASS |
| 2 per_field_aggregates | 22 | PASS |
| 3 keyed_diffs | 27 | PASS |
| 4 app_level_parity | 7 | PASS |

Source counts 7 / 4 / 3 / 2 / 2 (productCategory / productRemoval / productTag / productDocument / productBaseUnit). Same tier shape as re-runs 1–2 and the worker's run at this head (`.migration/recon/w1-b02.json`: 18/22/27/7). Evidence: `result.json`, `report.md`, `recon.summary.md` in this directory.

## Probes past the gate (`verify-probes.py` → `verify-probes.json`, 194 pass / 0 fail)

Same probe set as re-runs 1–2, re-executed against the new clone and the live target: per collection presence, counts, `_id` sets, boundaries, null/missing rates, full-precision value equality on every mapped field, no unmapped fields, natural-key uniqueness, spec indexes, translation JSONB keys, `parentPath` consistency, the three embedded junction arrays (length vs source child rows, element keys, no duplicates, no arrays on parents without rows, child references resolved on PostgreSQL), outbound references, and the 7-op tier-4 replay.

## Read-only ORM probes (`verify-orm-probes.py`, `verify-orm-compare.py` → `verify-orm-compare.json`, 45 pass / 0 fail)

Method unchanged: the same probe script ran twice through `odoo-bin shell` on the seeded clone `odoo_v_w1b02r5c` — once on the pre-opt-in tree (PostgreSQL storage, `verify-orm-probes.postgresql.json`) and once on the PR head `30117cc` itself (no local merge needed any more: PR #66/#67 are ancestors) with `mongodb_migration_db = odoo_v_w1b02r5c`, so `product.category` and `product.tag` are served unprefixed from the live `odoo_unt12` collections (`verify-orm-probes.mongodb.json`). No ORM mutation calls, cursor rolled back, and the sha256 of every document of the five batch collections is identical before and after (`verify-orm-compare.json: target_unchanged`). The two probe outputs are byte-identical to re-run 4's (the seeded clone is deterministic).

Exact equality against PostgreSQL for: company-dependent fields per company (3 companies × 7 categories × 17 `property_*` fields, raw JSONB per company key), company-dependent search by value per company (68 domains), dotted search through company-dependent many2ones (the re-run 2 gap, still closed), tag↔template, tag↔variant and picking-type↔category from both sides (relations also equal to the junction rows), full `read()` of every stored non-binary field, `search_count`, `parent_id`/`child_of` on all five models.

## Unlink parity (`verify-orm-unlink-probe.py` → `verify-orm-compare.json: unlink_probes`, 28 pass / 0 fail)

Throwaway clones `odoo_v_w1b02r5culpg` (pre-opt-in tree, PostgreSQL) and `odoo_v_w1b02r5culmg` (head tree, prefixed namespace `odoo_v_w1b02r5culmg__*` filled by a read-only precopy of the live collections). Unlinking an `account.account` referenced through `product.category` company-dependent properties behaves identically on both paths: restrict `UserError` with the same message, `ir.default` fallback protection, set-null on plain unlink, unreferenced delete, equal searches before/after, and the raw stored company-dependent map equals the PostgreSQL JSONB after every step (the re-run 3 gap, still closed). All eight `odoo_v_w1b02r5culmg__*` collections were dropped afterwards; `odoo_unt12` holds no verifier-prefixed collection.

## Findings (none hold the batch)

1. Environment, not plugin: the saved `ODOO_PG_RO_DSN` secret is now a `postgresql://` URL, while `build_source.sh` (lines 20–44) and the pinned harness (`parse_postgresql_secret`) require the JSON form `{"user","password","host","port","database"}`; the first pipeline attempt failed on both until the URL was converted to that JSON in-session (value never printed). Earlier re-runs saw the JSON form, so the secret was re-saved between re-run 4 and now; whoever owns it should restore the JSON form or the worker/verifier scripts will keep failing.
2. The worker's `.migration/recon/w1-b02.json` at this head self-reports `70/70` ORM scenario checks and evidence commit `acc537aff39`; not re-run here (the scenario writes a scratch namespace inside `odoo_unt12`); the read-only ORM and unlink probes above cover the manager-requested behaviour instead.
3. `odoo_unt12` held other sessions' temporary prefixed collections during this run (`odoo_v_w1b06__*` six collections during attempt 1, `odoo_v_w1b03__stockPackageType`, `odoo_v_w1b03__uomUom` during attempt 2, none at the end of attempt 3); not this verifier's, left untouched.
4. Both runs are redacted with unsalted hashes since no `RECON_REDACT_SALT` secret exists; `result.json` warnings stay empty, verdict unaffected.
5. Plugin gap, unpatched (carried): the installed mongo-recon-harness skill text names a `--source-concurrency` flag the pinned CLI rejects; flag omitted, `recon_tolerances.json` `source_concurrency` key accepted as-is.

## History

Re-run 1 (85c9e4f) PASS at the original head; re-run 2 (5a661b2) PASS at 2fc8dc3 on 83cc4af with 43/45 ORM probes (dotted company-dependent search gap → PR #66); re-run 3 (44fea3c) 45/45 ORM, 18/28 unlink on 2fc8dc3+375581b (company-dependent write fallback gap → PR #67); re-run 4 (971478f) 45/45, 28/28 on 2fc8dc3+5997593; re-run 5 (this commit) everything repeated from scratch on 30117cc.
