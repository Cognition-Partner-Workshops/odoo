run_id: UNT11-15
manifest_sha: ea9f6b868dc7

# Wave 1 independent verification: product + uom

Verifier session that migrated none of the wave. Run branch `mongo-run/20261014` at `a7faf9a`;
plugin pinned `0d6bcfd` (`.migration/plugin_sha`); mapping `map-draft-5`
(`e329b5aec09f4594d2ae8a297ff346e71f0cfe1a82043373c1d995bcdc0b160a`); tolerances `v1` strict
(`59f500708400dbd7ffb23dfbd9264b962cf6307e9a48ec678157cd2dbcdb4b68`); canonicalization
`skills/mongo-migration/profiles/postgresql.md`. Source `odoo_src` rebuilt in this session with
`.migration/fixtures/build_source.sh` (marker 3, pre-opt-in commit `03a3cb5`); target
`odoo_migration` on the migration cluster, read only by the verifier (no reload, no writes to any
unprefixed collection). Odoo tests ran in a separate database `odoo_v1t` with
`mongodb_migration_db = odoo_verify_mig`, so every test collection was `odoo_v1t__*`.

## Per-batch verdicts

| batch | unit | verdict | verifier recon | note |
|---|---|---|---|---|
| w1-b01 | uom | PASS | live from `odoo_src`: PASS, T1 3 / T2 8 / T3 30 checks, 0 findings, merge_eligible | fixture-mode rerun (post-#29 source) PASS |
| w1-b02 | product-taxonomy | FAIL | live from `odoo_src`: FAIL T1 (`product_tag` 0 rows vs 3 docs, `product_base_unit` 0 rows vs 2 docs); live from a fresh seeded clone: T1 10/10, T2 13/13, T4 4/4 PASS, T3 FAIL 10 of 13 | drift explained below: scenario-seed timestamps, not migration code |
| w1-b03 | product-attributes | PASS | live from `odoo_src`: PASS, T1 8 / T2 16 / T3 124 / T4 2 checks, 0 findings; warning `UNVERIFIED updateProductAttributeValue: 0 source rows` (accepted by the user, not a FAIL) | `merge_eligible=false` on the verifier re-run only because of that warning; the worker's committed result carries the same warning |

Wave verdict: **FAIL** (w1-b02 not independently reproducible). Circuit breaker: one failure, one
class (scenario-seed drift); not tripped.

## w1-b02 product-taxonomy: what the verifier saw

1. From the read-only source `odoo_src` the target does not reconcile: `productTag` has 3 documents
   and `productBaseUnit` 2 while the source tables have 0 rows
   (`w1-b02/product-taxonomy-odoo_src/result.json`). Those documents came from the worker's seeded
   clone `odoo_w1b02_fix` (PR #22 says so; the manager-accepted 0-row scenario-row pattern).
2. Reproducing that pattern independently (`odoo_w1v_fix` = clone of `odoo_fixture` +
   `.migration/load/seed_scenario_rows.py` run with the pre-opt-in code) gives Tier 1, 2 and 4
   PASS and Tier 3 FAIL on exactly 10 checks: `createDate` and `writeDate` of all 5 scenario
   documents (3 `productTag`, 2 `productBaseUnit`)
   (`w1-b02/product-taxonomy-scenario/result.json`). Every other field of those documents
   (name, sequence, color, visibleToCustomers, create/write uid) matches.
3. Cause: `seed_scenario_rows.py` lets the ORM stamp `create_date`/`write_date` with `now()`, so
   each clone produces different timestamps and the worker's PASS can only be reproduced inside
   the worker's own session. The 8 `productCategory` rows (the only collection with live rows)
   match `odoo_src` in full in both runs.
4. Not fixed here (verifier never fixes code). Manager's options: pin the seed timestamps the way
   `build_source.sh` pins `FIXED_INSTANT` and reload `productTag`/`productBaseUnit`, then
   re-verify; or grade the batch DRIFT-EXPLAINED on the evidence above.

## Fixture-mode reruns requested by the manager (post-#29 source)

- uom: PASS from `odoo_fixture` (`w1-b01/uom-fixture/result.json`); `uom_uom` is untouched by the
  fixture outlier, so it is the same 30 rows. Fixture PASS is not merge evidence; the live run is.
- product-attributes: not rerun. The fixture adds 3 attributes / 13 values (17 / 114) that the
  target, loaded from `odoo_src` (14 / 101), does not hold; a fixture-mode run would require the
  verifier to reload the target from `odoo_fixture`, which this ticket forbids. The live rerun
  from `odoo_src` is the merge evidence; the committed fixture result predating #29 remains the
  worker's.
- Rebuilding `odoo_src` and `odoo_fixture` reproduced the committed row counts exactly
  (33 tables, 661 fixture rows, outlier 60 variants). The regenerated `odoo_fixture.json` differed
  only in `produced_at` and `source_database_uuid` (uuid1 per install); not committed.

## Probes past the gate (`probes.json`, 0 problems)

Read-only, `odoo_src` vs `odoo_migration`, all seven collections of the wave:
counts and `estimated_document_count` equal; min/max `_id` equal to source min/max `id`;
no duplicate `_id`; per-field null-vs-missing rates equal on every mapped field; no top-level
fields outside the spec; embedded arrays `productAttribute.productTmplIds` (9 child rows → 9
embedded, lengths {0:9, 1:1, 2:4}) and `productCategory.routeIds` (0 → 0) match child-row counts
per parent; every spec index present on the target; `updateProductAttributeValue` empty on both
sides. Spot checks on fields the harness covers by aggregate only: all 30 `uomUom`
(`relativeFactor`, `factor`, `uneceCode`, `sequence`, `relativeUomId`) and all 101
`productAttributeValue` (`attributeId`, `color`, `htmlColor`, `defaultExtraPrice`, `sequence`)
rows equal the source.

## Cross-unit consistency (all clean)

- `productAttributeValue.attributeId` → `productAttribute._id`: 0 dangling.
- `productCategory.parentId` → `productCategory._id` and `uomUom.relativeUomId` → `uomUom._id`:
  0 dangling; `parentPath` consistent with the parent chain on every document.
- Forward references from the not-yet-migrated product tables resolve on the target:
  `product_template.uom_id` (3 distinct), `product_template.categ_id` (6),
  `product_template_attribute_line.attribute_id` (5), attribute-value/line rel (16),
  `product_tag_product_template_rel` (0): 0 unresolved. Embedded `productTmplIds` all exist in
  source `product_template`.
- Natural keys unique on the target: `uomUom.name`, `productTag.name`,
  `productAttributeValue (attributeId, name)`.
- Shared collections: none across batches; each batch writes only its manifest targets, and the
  unprefixed namespace holds exactly the seven wave collections (plus `_connectivity_probe`).

## Odoo tests against the migrated build

Build: run branch `a7faf9a` (storage path opted in), `./odoo-bin -d odoo_v1u --db_port=5433 -c <conf> --no-http
-i product,uom --test-enable --test-tags /product,/uom --stop-after-init` with the conf holding
`mongodb_migration_db = odoo_verify_mig`, so the test database `odoo_v1u` is not the migration
database and every in-scope model wrote `odoo_v1u__*` collections (`odoo_v1u__uomUom` 30,
`odoo_v1u__productAttribute` 5, `odoo_v1u__productCategory` 3, others 0); the unprefixed
wave collections kept their counts (30 / 8 / 3 / 2 / 14 / 101 / 0) throughout.

Result: `0 failed, 0 error(s) of 161 tests when loading database 'odoo_v1u'`, exit code 0
(uom 2.84s test, product 9.75s test). An earlier identical run on `odoo_v1t` also ended with no
test error at warn level.

Aside (not a migration finding): re-running on the already-installed `odoo_v1t` with
`-u product,uom` gives `TestUom.setUpClass` a PostgreSQL error (`res_users.notification_type`
NOT NULL on `new_test_user`), because on update `uom` is loaded and tested before `mail`,
whose column that is; `res_users` is not in scope and this is vanilla-Odoo update ordering, so the
fresh-install run above is the evidence.

## Evidence

- `.migration/recon/wave-1/w1-b01/uom/result.json` (live, PASS)
- `.migration/recon/wave-1/w1-b01/uom-fixture/result.json` (fixture, PASS)
- `.migration/recon/wave-1/w1-b02/product-taxonomy-odoo_src/result.json` (live, FAIL T1)
- `.migration/recon/wave-1/w1-b02/product-taxonomy-scenario/result.json` (live from seeded clone, FAIL T3 timestamps)
- `.migration/recon/wave-1/w1-b03/product-attributes/result.json` (live, PASS, accepted warning)
- `.migration/recon/wave-1/probes.json`
- `.migration/recon/wave-1/verify-result.json`
