run_id: ticket-8cc5fa2c31ee422d9443c1dfdb650d6e
manifest_sha: b965d1e5f34e
verified_head: 2fc8dc3e280f6476c79ca3782feb0e2369fd785b
verified_orm_rerun: 2fc8dc3e280f6476c79ca3782feb0e2369fd785b merged locally onto mongo-run/unt12 59975936d46a979da3267ba59745c8cf262a2ae5 (PR #67; local merge 8caae0835d5, nothing pushed or rebased); re-run 3 was the same head onto 375581b77efe8bc00939a37cbe434b69b4e303c9 (PR #66)

# Wave 1 / batch w1-b02 (product-taxonomy) — independent verify, re-run 2 (after the rebase onto 83cc4af) + ORM re-runs 3 and 4 (after PR #66 375581b and PR #67 5997593)

**Verdict: PASS** (graded from `.migration/recon/wave-1/w1-b02/result.json`, this verifier's own live recon re-run from PR #61 head `2fc8dc3e280f6476c79ca3782feb0e2369fd785b`; 194/194 beyond-gate probes pass; 45/45 read-only ORM probes and 28/28 unlink-parity probes pass on the head merged locally onto 5997593 — the two storage-path gaps found by re-run 2 (dotted company-dependent search, 43/45) and re-run 3 (company-dependent write materializing fallbacks, unlink 18/28) are closed by PR #66 and PR #67; no open finding against the run branch). Re-run 1 (head `0238c8e9f7f`, PASS) is in this branch's history at `85c9e4f09de`.

## What was verified, from where

- Batch PR: #61, branch `devin/1792505455-w1-b02-product-taxonomy` at head `2fc8dc3e280f6476c79ca3782feb0e2369fd785b`, based on `mongo-run/unt12` `83cc4af173eeef6fe2cecbc48cdc6fe151d451d9` (the PR #63 storage fixes; ancestry confirmed with git). This verifier authored none of it and changed nothing in `odoo_unt12` (snapshot proof below).
- Mapping `.migration/mapping_spec.json` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc` (map-draft-2) and tolerances `.migration/recon_tolerances.json` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea` (unt12-3): the bytes as committed at that head, unchanged by the rebase, matching the ticket's pins (`sha256sum`), and echoed back by the harness in `result.json`.
- Plugin: worktree of `mongo-migration-plugin` at `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (= `.migration/plugin_sha` at the head), unpatched.
- Source: `odoo_src` rebuilt again with `.migration/fixtures/build_source.sh` (pre-opt-in commit `63446015e3c`, marker `migration.fixture_source=3`, 70 modules), then cloned fresh with `createdb -T` as `odoo_v_w1b02r2` and reseeded by running `.migration/load/seed_product_taxonomy.py` through the pre-opt-in `odoo-unt12-src` tree (tags 1–3, base units 1–2, picking-type wave categories `{1: [1, 4], 3: [5]}`, 3+3+3 junction rows). Recon and probes read `odoo_v_w1b02r2` over a read-only connection built in-process from the source RO DSN secret (by name only, as in re-run 1; never persisted).
- Target: `odoo_unt12` via `MONGODB_ATLAS_URI`, read only; no load step, no `odoo-bin -u`, no `ensure_indexes`.

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
  --ops .migration/recon/product-taxonomy/ops.json --out .migration/recon/wave-1/w1-b02
```

Result (run from the head checkout, `generated_at` 2026-10-20T16:31:34Z): `recon PASS ... merge_eligible=True`, exit 0, `warnings: []`, `error: null`.

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 18 | PASS |
| 2 per_field_aggregates | 22 | PASS |
| 3 keyed_diffs | 27 | PASS |
| 4 app_level_parity | 7 | PASS |

Same tier shape as re-run 1 and the worker's run (18/22/27/7). Evidence: `result.json`, `report.md`, `recon.summary.md` in this directory.

## Probes past the gate (`verify-probes.py` → `verify-probes.json`, 194 pass / 0 fail)

Unchanged from re-run 1 and re-executed against the new clone and the live target: per collection presence, counts (7 / 4 / 3 / 2 / 2), `_id` sets, boundaries, null/missing rates, full-precision value equality on every mapped field, no unmapped fields, natural-key uniqueness, spec indexes, translation JSONB keys, `parentPath` consistency; the three embedded junction arrays against seeded child rows; references resolve inside the batch or in the relational source, none toward a sibling wave-1 batch; the 7 `ops.json` operations replayed independently of the harness.

## Read-only ORM probes (`verify-orm-probes.py`, `verify-orm-compare.py` → `verify-orm-compare.json`, 45 pass / 0 fail at 2fc8dc3+5997593; 43/45 at 2fc8dc3 alone, 45/45 at 2fc8dc3+375581b)

Method: the same probe script ran twice through `odoo-bin shell` on the same seeded clone `odoo_v_w1b02r2` — once on the pre-opt-in tree (PostgreSQL storage, `verify-orm-probes.postgresql.json`) and once on the PR head merged locally onto `mongo-run/unt12` 5997593 (`verify-src/w1-b02-r4`, local merge 8caae0835d5) with `mongodb_migration_db = odoo_v_w1b02r2` so `product.category` and `product.tag` are served unprefixed from the live `odoo_unt12` collections (`verify-orm-probes.mongodb.json`; `storage.prefix == ''`, `storage.database == 'odoo_unt12'` asserted). No ORM mutation calls, the cursor is rolled back, and a sha256 of every document of the five batch collections taken before and after is identical (`target_unchanged_by_orm_probe`; re-checked after the final recon run and again after each unlink-parity run).

Exact equality against PostgreSQL:
- Company-dependent fields, per company (3 companies × 7 categories × 17 `property_*` fields incl. `property_cost_method`, `property_valuation`, `property_stock_journal`, every `property_account_*`): Mongo-path ORM reads equal the PostgreSQL-path reads, and the 10 JSONB-backed ones equal the raw `product_category` JSONB per company key (`mongodb_orm_company_dependent_vs_pg_jsonb`). `get_property_definition` equal.
- Company-dependent search by value (`property_x = v`, `property_x != False`) per company: equal for every stored field (68 domains).
- tag↔template: `product.tag.product_template_ids`, `product.template.product_tag_ids` (37 templates), search templates by tag, tags by template, tags without templates — equal, and the Mongo-side pairs equal `product_tag_product_template_rel` rows (`{1: [1, 2], 2: [1]}`).
- tag↔variant: `product.tag.product_product_ids`, `product.tag.product_ids`, `product.product.additional_product_tag_ids`, `all_product_tag_ids` (47 variants), search variants by tag / all-tags, tags by variant — equal, and the Mongo-side pairs equal `product_tag_product_product_rel` rows (`{1: [1, 2, 3]}`).
- picking-type↔category: `stock.picking.type.wave_category_ids` (16 picking types), search picking types by `wave_category_ids` — equal, and equal `product_category_stock_picking_type_rel` rows (`{1: [1, 4], 3: [5]}`).
- Full `read()` of every stored non-binary field, `search_count`, `parent_id` / `child_of` searches on all five models — equal.

- Dotted search through a company-dependent many2one (`property_*_id.active`, `property_account_*_active`), per company: equal (the re-run 2 gap, closed by PR #66).

## Unlink parity (`verify-orm-unlink-probe.py` → `verify-orm-unlink-probe.{postgresql,mongodb}.json`, `verify-orm-compare.py unlink` → `unlink_probes` in `verify-orm-compare.json`, 28 pass / 0 fail at 2fc8dc3+5997593; 18/28 at 2fc8dc3+375581b)

Method: the same script ran twice on throwaway clones of the seed — `odoo_v_w1b02ulpg` on the pre-opt-in tree (PostgreSQL storage) and `odoo_v_w1b02ulmg` on the head+5997593 tree with `mongodb_migration_db = odoo_v_w1b02r2`, so the storage prefix is `odoo_v_w1b02ulmg__`: the live documents were copied into those temporary collections first, every Mongo write went to them only, and all eight were dropped afterwards (`list_collection_names()` shows none left; the sha256 snapshot of the five batch collections is unchanged). Each PostgreSQL change ran under a savepoint and the cursor was rolled back. Scenario: create an `account.account`, point `product.category` company-dependent properties at it (category 1 in company 1, category 7 in company 3, plus the `ondelete='restrict'` `property_stock_valuation_account_id` on category 7), then unlink it four ways. Everything is equal on both paths: direct and dotted searches by the account; restrict → `UserError` "You cannot delete account.account(187,), as it is used by product.category(7,)"; `ir.default` fallback referencing the account → `UserError` "Unable to delete ... used as the default value of product.category.property_account_billed_not_received_id"; plain unlink once the restrict link is removed → the referencing company values become null, the account is gone, searches by it return `[]` in every company and `= False` returns all 7 categories; unlinking an unreferenced account → ok; ORM-visible values per company and the raw stored per-company map (document `{"3": 187}` = JSONB `{"3": 187}`) after every step.

## Findings

1. Closed by PR #66 (verified 45/45 in re-runs 3 and 4): the re-run 2 gap — on the Mongo path, searching `product.category` through a related field over a company-dependent many2one (`[('property_account_income_categ_id.active', '=', True)]`, `property_account_*_active`) returned `[]` where PostgreSQL returns all 7 categories.
2. Closed by PR #67 (verified 28/28 in re-run 4): the re-run 3 gap — at 375581b, writing one company's value of a company-dependent many2one on the Mongo path rewrote the whole per-company map and stored the other companies' `ir.default` fallbacks as values (`{"1": 10, "2": null, "3": 185}` vs JSONB `{"3": 185}`), so category 7 kept 10 after the fallback changed or the account was unlinked and `= False` returned 6 categories instead of 7 (18/28 unlink probes). At 5997593 the stored map equals the JSONB after every step.
3. Verifier bookkeeping: commit 44fea3c on this branch (re-run 3) carried only the three unlink-probe files — its verify-report.md / verify-result.json / verify-orm-compare.json edits were lost to a branch checkout before the commit (gitignored path overwritten), so that commit's report still reads as re-run 2. This commit supersedes it; the re-run 3 numbers above (45/45, 18/28) are from that run's output, re-established here only as history.
4. PR #61 and `.migration/recon/w1-b02.json` self-report 62/62 ORM scenario checks; the scenario was again not run here since it creates a scratch namespace inside `odoo_unt12`. The read-only probes above replace it for the relations and company-dependent reads the manager asked for.
5. Both runs are redacted with unsalted hashes (`redaction_salted: false`) since no `RECON_REDACT_SALT` secret exists; `result.json` warnings stay empty, so the verdict is unaffected.
6. `odoo_unt12` also holds `_connectivity_probe` and other wave-1 batches' collections, and at the end of re-run 4 six `odoo_v_w1b06__*` prefixed collections (another batch's temporary namespace, not this verifier's); none belong to this batch, all left untouched.
7. Plugin gap, unpatched: the installed mongo-recon-harness skill text names a `--source-concurrency` flag the pinned CLI rejects; the flag was omitted and `recon_tolerances.json`'s `source_concurrency` key was accepted as-is.
8. Environment: `requirements.txt` line 36 at the head pins the Mongo driver (4.19.0) but the pre-built odoo venv lacked it (`ModuleNotFoundError: bson` on the first Mongo-path `odoo-bin shell`); pip-installed in the verifier's venv only, no repo change.
