run_id: ticket-8cc5fa2c31ee422d9443c1dfdb650d6e
manifest_sha: b965d1e5f34e

# Wave 1 / batch w1-b02 (product-taxonomy) — independent verify

**Verdict: PASS** (graded from `.migration/recon/wave-1/w1-b02/result.json`, this verifier's own live recon re-run; 194/194 beyond-gate probes also pass).

## What was verified, from where

- Batch PR: #61, branch `devin/1792505455-w1-b02-product-taxonomy` at `0238c8e9f7f`, based on `mongo-run/unt12`. This verifier wrote none of it and wrote nothing to `odoo_unt12`.
- Mapping `.migration/mapping_spec.json` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc` (map-draft-2) and tolerances `.migration/recon_tolerances.json` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea` (unt12-3): the bytes as committed on the PR branch, matching the ticket's pins (`sha256sum`), and echoed back by the harness in `result.json`.
- Plugin: worktree of `mongo-migration-plugin` at `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (= `.migration/plugin_sha`), unpatched; `recon selftest` passed (9 canonicalization rules).
- Source: `odoo_src` rebuilt with `.migration/fixtures/build_source.sh` (pre-opt-in commit `63446015e3c`, marker `migration.fixture_source=3`, 70 modules), then cloned `createdb -T odoo_src odoo_v_w1b02` and reseeded by running `.migration/load/seed_product_taxonomy.py` through the pre-opt-in `odoo-unt12-src` tree (tags 1–3, base units 1–2, picking-type wave categories `{1: [1, 4], 3: [5]}`, 3+3+3 junction rows, timestamps pinned to `2026-10-20 00:00:00`). Recon and probes read `odoo_v_w1b02` over a read-only connection built in-process from `ODOO_PG_RO_DSN` (secret by name; never written out).
- Target: `odoo_unt12` via `MONGODB_ATLAS_URI`, read only (`secondaryPreferred` reads; no load step run).

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

Result: `recon PASS ... merge_eligible=True`, exit 0, `warnings: []`, `error: null`.

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 18 | PASS |
| 2 per_field_aggregates | 22 | PASS |
| 3 keyed_diffs | 27 | PASS |
| 4 app_level_parity | 7 | PASS |

Same tier shape as the worker's live run (18/22/27/7). Evidence: `result.json`, `report.md`, `recon.summary.md` in this directory.

## Probes past the gate (`verify-probes.py` → `verify-probes.json`, 194 pass / 0 fail)

Per collection (all five): declared collection present and non-empty; row count source = target (7 / 4 / 3 / 2 / 2); `_id` key set equal, no duplicate `_id`; min and max id present; every mapped field's null/missing count equal and full-precision value equality on every row (Decimal as text, datetimes to ms, JSONB as sorted JSON); no unmapped target fields; natural-key uniqueness for the keys the spec declares (`productTag.name`); every spec index present with the required `unique` flag; translation JSONB (`name`, `method`) has the same language keys on both sides; boundary values for `sequence`, `irAttachmentId`, `parentPath`; `productCategory.parentPath` consistent with `parentId` on the target alone.

Embedded junction arrays (`productCategory.stockPickingTypeRel`, `productTag.productProductRel`, `productTag.productTemplateRel`): source child rows actually seeded (3 each); per-parent array length = child-row count; element key sets equal; no duplicate elements; no array on a parent without child rows; elements carry only the key field; child references (`stockPickingType`, `productProduct`, `productTemplate` — later-wave tables) resolve in the source tables.

References: `parentId`→`productCategory` and `removalStrategyId`→`productRemoval` resolve inside this batch's own target collections; `companyId`, `createUid`/`writeUid`, `irAttachmentId` resolve in the relational source (still relational, later waves). No reference from this batch points at any other wave-1 batch's collection (`no_same_wave_sibling_reference` on all five).

Tier-4 replay: all 7 operations in `ops.json` (`category_tree`, `category_wave_picking_types`, `removal_strategies`, `tags_with_templates`, `tag_variants`, `documents_by_attachment`, `base_units`) re-executed independently of the harness, sorted source SQL rows = sorted target aggregation rows.

## Findings (none change the verdict)

1. PR #61 and `.migration/recon/w1-b02.json` say 62/62 ORM scenario checks and "1 storage-path gap (company-dependent writes)"; `scenario_product_taxonomy.py` holds 53 static `check()` sites. Self-reported, not gate evidence, and not re-run here because the scenario writes a scratch namespace into `odoo_unt12`, which this verify was told not to do.
2. Both the worker's run and this re-run are redacted with unsalted hashes (`redaction_salted: false`) because no `RECON_REDACT_SALT` secret exists; the harness warns on stderr and `result.json` warnings stay empty, so the verdict is unaffected.
3. `odoo_unt12` also holds `_connectivity_probe` and 15 collections from other wave-1 batches, including `productAttributeValueProductTemplateAttributeLineRel` (a junction table stored as its own collection); none belong to this batch, all left untouched, listed in `verify-probes.json` for the manager.
4. Plugin gap, unpatched: the installed mongo-recon-harness skill text names a `--source-concurrency` flag the pinned CLI rejects; the flag was omitted and `recon_tolerances.json`'s `source_concurrency` key was accepted as-is (same as w1-b01).
