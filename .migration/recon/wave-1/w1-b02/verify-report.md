run_id: ticket-8cc5fa2c31ee422d9443c1dfdb650d6e
manifest_sha: b965d1e5f34e
verified_head: 2fc8dc3e280f6476c79ca3782feb0e2369fd785b

# Wave 1 / batch w1-b02 (product-taxonomy) — independent verify, re-run 2 (after the rebase onto 83cc4af)

**Verdict: PASS** (graded from `.migration/recon/wave-1/w1-b02/result.json`, this verifier's own live recon re-run from PR #61 head `2fc8dc3e280f6476c79ca3782feb0e2369fd785b`; 194/194 beyond-gate probes pass; 43/45 read-only ORM probes pass — the 2 failures are one storage-path search gap, finding 1 below, in `odoo/orm/storage_mongodb.py` on the run branch, not in this batch's data, left to the manager to grade). Re-run 1 (head `0238c8e9f7f`, PASS) is in this branch's history at `85c9e4f09de`.

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

## Read-only ORM probes (`verify-orm-probes.py`, `verify-orm-compare.py` → `verify-orm-compare.json`, 43 pass / 2 fail)

Method: the same probe script ran twice through `odoo-bin shell` on the same seeded clone `odoo_v_w1b02r2` — once on the pre-opt-in tree (PostgreSQL storage, `verify-orm-probes.postgresql.json`) and once on the PR head checkout with `mongodb_migration_db = odoo_v_w1b02r2` so `product.category` and `product.tag` are served unprefixed from the live `odoo_unt12` collections (`verify-orm-probes.mongodb.json`; `storage.prefix == ''`, `storage.database == 'odoo_unt12'` asserted). No ORM mutation calls, the cursor is rolled back, and a sha256 of every document of the five batch collections taken before and after is identical (`target_unchanged_by_orm_probe`; re-checked again after the final recon run).

Exact equality against PostgreSQL:
- Company-dependent fields, per company (3 companies × 7 categories × 17 `property_*` fields incl. `property_cost_method`, `property_valuation`, `property_stock_journal`, every `property_account_*`): Mongo-path ORM reads equal the PostgreSQL-path reads, and the 10 JSONB-backed ones equal the raw `product_category` JSONB per company key (`mongodb_orm_company_dependent_vs_pg_jsonb`). `get_property_definition` equal.
- Company-dependent search by value (`property_x = v`, `property_x != False`) per company: equal for every stored field (68 domains).
- tag↔template: `product.tag.product_template_ids`, `product.template.product_tag_ids` (37 templates), search templates by tag, tags by template, tags without templates — equal, and the Mongo-side pairs equal `product_tag_product_template_rel` rows (`{1: [1, 2], 2: [1]}`).
- tag↔variant: `product.tag.product_product_ids`, `product.tag.product_ids`, `product.product.additional_product_tag_ids`, `all_product_tag_ids` (47 variants), search variants by tag / all-tags, tags by variant — equal, and the Mongo-side pairs equal `product_tag_product_product_rel` rows (`{1: [1, 2, 3]}`).
- picking-type↔category: `stock.picking.type.wave_category_ids` (16 picking types), search picking types by `wave_category_ids` — equal, and equal `product_category_stock_picking_type_rel` rows (`{1: [1, 4], 3: [5]}`).
- Full `read()` of every stored non-binary field, `search_count`, `parent_id` / `child_of` searches on all five models — equal.

## Findings

1. **Storage-path gap (PR #63 / run branch code, not this batch's data):** on the Mongo path, searching `product.category` through a *related field over a company-dependent many2one* returns nothing while PostgreSQL returns all 7 categories: `[('property_account_income_categ_id.active', '=', True)]` → `[]` vs `[1..7]` for all 8 `property_*_id` → `account.account` fields in every company, and therefore the related booleans `property_account_*_active` / `property_stock_valuation_account_active` (`= True` and `!= False`) → `[]`. Dotted paths over plain many2ones (`parent_id.id`, `parent_id.name`) and direct company-dependent searches are correct, so the gap is specific to dotted traversal of company-dependent fields in `odoo/orm/storage_mongodb.py` (`orm_equality.company_dependent_search`, `orm_equality.search_dotted_company_dependent` in `verify-orm-compare.json`). The recon gate does not cover ORM search; the manager grades whether this holds PR #61.
2. PR #61 and `.migration/recon/w1-b02.json` self-report 62/62 ORM scenario checks; the scenario was again not run here since it creates a scratch namespace inside `odoo_unt12`. The read-only probes above replace it for the relations and company-dependent reads the manager asked for.
3. Both runs are redacted with unsalted hashes (`redaction_salted: false`) since no `RECON_REDACT_SALT` secret exists; `result.json` warnings stay empty, so the verdict is unaffected.
4. `odoo_unt12` also holds `_connectivity_probe` and other wave-1 batches' collections; none belong to this batch, all left untouched.
5. Plugin gap, unpatched: the installed mongo-recon-harness skill text names a `--source-concurrency` flag the pinned CLI rejects; the flag was omitted and `recon_tolerances.json`'s `source_concurrency` key was accepted as-is.
6. Environment: `requirements.txt` line 36 at the head pins the Mongo driver (4.19.0) but the pre-built odoo venv lacked it (`ModuleNotFoundError: bson` on the first Mongo-path `odoo-bin shell`); pip-installed in the verifier's venv only, no repo change.
