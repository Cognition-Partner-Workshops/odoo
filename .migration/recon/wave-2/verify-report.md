run_id: UNT11-41
manifest_sha: 0b73271c13bf

# Wave 2 independent verification: product-catalog (w2-b01)

Verifier session that migrated none of the wave. Run branch `mongo-run/20261014` at `1c9565e`
(PR #34 storage-path fixes at `27d722f`, PR #33 product catalog at `72fca61`, then PR #36 — the
UNT11-43 fix for `_inherits`-delegated fields in SQL, after this verifier's first pass found them
broken, see "D6 readers" below); plugin pinned `0d6bcfd`
(`.migration/plugin_sha`, the harness checkout at the same commit); mapping `map-draft-5`
(`e329b5aec09f4594d2ae8a297ff346e71f0cfe1a82043373c1d995bcdc0b160a`); tolerances `v1` strict
(`59f500708400dbd7ffb23dfbd9264b962cf6307e9a48ec678157cd2dbcdb4b68`); canonicalization
`skills/mongo-migration/profiles/postgresql.md`. Source `odoo_src` rebuilt in this session with
`.migration/fixtures/build_source.sh` (marker 3, pre-opt-in commit `03a3cb5`; 38 templates, 48
variants, 8 categories, 30 uoms as committed); the verifier's own clone `odoo_w2v_src`
(`createdb -T odoo_src`) seeded with the merged `.migration/load/seed_scenario_rows.py` through the
`odoo-base` worktree: 3 tags, 2 base units, 6 `product_uom` rows, 5 / 5 / 6 / 6 rows in the four
relation tables, every `create_date`/`write_date` of the touched tables equal to `FIXED_INSTANT`
(0 rows off). Target `odoo_migration` on the migration cluster, read only by the verifier (no
reload, no writes to any unprefixed collection). Odoo tests ran in a separate database
`odoo_w2v_test2` (first pass: `odoo_w2v_test`) with `mongodb_migration_db = odoo_verify_mig`, so every test collection was
`odoo_w2v_test2__*`.

## Per-batch verdict

| batch | unit | verdict | verifier recon | note |
|---|---|---|---|---|
| w2-b01 | product-catalog | PASS | live from the freshly seeded clone `odoo_w2v_src`, `--collections` the six unit collections, `--ops .migration/recon/product-catalog/ops.json`: PASS, T1 61 / T2 51 / T3 348 / T4 7 checks, 0 warnings, merge_eligible | reproduces the committed `.migration/recon/product-catalog/result.json` check for check (61 / 51 / 348 / 7) |

Wave verdict: **PASS**. The first pass (run branch `72fca61`) found two storage-path defects past the
gate (section "D6 readers" below: `-u product` failed on a database with `account` installed and the
three `_table_query` reports raised); the user chose fix-then-close, UNT11-43 / PR #36 fixed them, and
the D6 probe re-run at `1c9565e` is clean. Circuit breaker: no batch failed; not tripped. `auto_merge` is false for this wave, so the manager grades and merges.

Which collections the live recon graded from the seeded clone rather than `odoo_src`: `productUom`
(6 rows, 0 in `odoo_src`) and the four arrays `productTemplate.uomIds`/`productTagIds`,
`productProduct.extraUomIds`/`additionalProductTagIds` (5 / 6 / 5 / 6 elements, 0 in `odoo_src`);
every other row and array is identical in `odoo_src` and the clone.

## Probes past the gate (`probes.json`, 0 problems)

Read-only, `odoo_w2v_src` vs `odoo_migration`, the six wave 2 collections and the seven wave 1
collections (exception: `productTag`, `productBaseUnit` and `productUom` have 0 rows in `odoo_src`;
their parity is against the seeded clone, which is what the recon reads too):

- counts and `estimated_document_count` equal (38 / 48 / 9 / 24 / 2 / 6; wave 1 30 / 8 / 3 / 2 /
  14 / 101 / 0); min/max `_id` equal to source min/max `id`; the `_id` set equals the `id` set;
  no duplicate `_id`; `updateProductAttributeValue` empty on both sides.
- per-field null-vs-missing counts equal on every mapped field of the 13 collections (e.g.
  `productTemplate.baseUnitId` 38 / 38, `productProduct.barcode` 45 / 45 null-or-missing).
- no top-level fields outside the spec on any document; every spec index present on the target
  (productTemplate 18, productProduct 11, productTemplateAttributeLine 3,
  productTemplateAttributeValue 5, productDocument 1, productUom 4; each collection carries one
  extra index, the default `_id`).
- embedded arrays vs relation-table rows per parent, element sets equal on every parent:
  `productTemplate.taxesId` 74 → 74 (lengths {2: 37, 0: 1}), `supplierTaxesId` 74 → 74,
  `comboIds` 3 → 3 ({0: 37, 3: 1}), `optionalProductIds` 3 → 3, `productTagIds` 6 → 6
  ({0: 35, 1: 1, 2: 1, 3: 1}), `uomIds` 5 → 5, `accountTagIds` 0 → 0, `routeIds` 0 → 0;
  `productProduct.productVariantCombination` 20 → 20 ({0: 33, 1: 10, 2: 5}), `extraUomIds`
  5 → 5, `additionalProductTagIds` 6 → 6; `productTemplateAttributeLine.valueIds` 24 → 24
  ({1: 1, 2: 3, 3: 3, 4: 2}); `productTemplateAttributeValue.excludedValueIds` 1 → 1.
- full-row spot checks on every mapped scalar field of every wave 2 document (the gate aggregates
  or samples some of them): productTemplate 38 rows × 48 fields, productProduct 48 × 19,
  productTemplateAttributeLine 9 × 9, productTemplateAttributeValue 24 × 13, productDocument
  2 × 8, productUom 6 × 8 — 0 mismatches (Decimal128 compared numerically, timestamps at ms).
- natural keys unique on the target: `productUom.barcode`, `productProduct.barcode`,
  `productTemplateAttributeValue (attributeLineId, productAttributeValueId)`.

## Cross-unit consistency (all clean)

- References into wave 1, 0 dangling: `productTemplate.uomId` → `uomUom` (38 refs),
  `productTemplate.categId` → `productCategory` (38), `productTemplate.baseUnitId` and
  `productProduct.baseUnitId` → `productBaseUnit` (0 refs, all null),
  `productTemplateAttributeLine.attributeId` → `productAttribute` (9),
  `productTemplateAttributeValue.productAttributeValueId` → `productAttributeValue` (24) and
  `.attributeId` → `productAttribute` (24), `productUom.uomId` → `uomUom` (6); embedded
  `productTemplate.productTagIds` → `productTag` (6), `productTemplate.uomIds` → `uomUom` (5),
  `productProduct.extraUomIds` → `uomUom` (5), `productProduct.additionalProductTagIds` →
  `productTag` (6), `productTemplateAttributeLine.valueIds` → `productAttributeValue` (24).
- Wave 1's embedded `productAttribute.productTmplIds.productTemplateId` → `productTemplate._id`
  (9 refs): 0 dangling (now resolvable on the target).
- Within the unit, 0 dangling: `productProduct.productTmplId` → `productTemplate` (48),
  `productTemplateAttributeLine.productTmplId` → `productTemplate` (9),
  `productTemplateAttributeValue.attributeLineId` → `productTemplateAttributeLine` (24) and
  `.productTmplId` → `productTemplate` (24), `productUom.productId` → `productProduct` (6),
  `productProduct.productVariantCombination` → `productTemplateAttributeValue` (20),
  `productTemplateAttributeValue.excludedValueIds` → `productTemplateAttributeValue` (1).
- `_inherits` delegation: every one of the 48 variants points at an existing template, the set of
  38 templates with variants and the variants-per-template histogram equal the source.
- D6 shadow columns, source row vs document: `product_product (product_tmpl_id, weight, volume,
  standard_price)` 48 rows and `product_template (uom_id, categ_id, is_storable, purchase_method)`
  38 rows, 0 mismatches. In the test database (below) the shadow tables are reduced to exactly
  `id` + the shadow columns (`product_product`: `product_tmpl_id, weight, volume, standard_price`;
  `product_template`: `uom_id, categ_id, is_storable` — `purchase_method` is absent because
  `purchase` is not installed there; `uom_uom`: `factor`), and `uom_uom.factor` equals the 30
  `odoo_w2v_test2__uomUom` documents; `product_*` shadow tables and documents are both empty after
  the tests' rollbacks.
- Source forward references that now resolve on the target: `product_template.uom_id` (3 distinct),
  `categ_id` (6), `product_template_attribute_line.attribute_id` (5), `product_uom.uom_id` (2),
  the two tag relation tables (3 each): 0 unresolved.
- The unprefixed namespace holds exactly the thirteen wave 1 + wave 2 collections (plus
  `_connectivity_probe`); no shared collection between batches.

## D6 readers on an opted-in clone (probe past the gate; two findings found at `72fca61`, fixed at `1c9565e`)

Clone `odoo_w2v_views` of the seeded source (sale, purchase, stock, account installed, as in
`odoo_src`), run with the run-branch code and `mongodb_migration_db = odoo_verify_mig`, so every
collection the storage path touched was `odoo_w2v_views__*` (pre-populated with a copy of the 13
unprefixed collections so the fail-closed guard is satisfied); the unprefixed collections kept their
counts throughout (`d6-readers-counts.json`). Pre-opt-in baseline from the `odoo-base` worktree
(`03a3cb5`, PostgreSQL storage) on clone `odoo_w2v_base` of the same seeded source.

First pass, run branch `72fca61` (`d6-readers.log` tail, `d6-update-traceback-72fca61.log`):
`-u uom,product` failed to load the registry (`account/security/ir.access.csv`: `Invalid domain
[('company_id', 'in', company_ids)]: product.product is stored in MongoDB: no SQL for field 'uom_id'
(not in _shadow_columns)`) and `sale.report`, `purchase.report`, `account.invoice.report` raised the
same `NotImplementedError` from `Query.__getitem__`, also on a plain clone with no update and no
writes. Cause: `uom_id` is an `_inherits`-delegated `product.template` field, checked against
`product.product`'s own `_shadow_columns` before the join through the shadow `product_tmpl_id` to the
shadow `product_template.uom_id`. Reported as two high findings; fixed by UNT11-43 (PR #36,
`odoo/orm/query.py`: resolve `_inherits`-delegated fields through the parent shadow join).

Re-run at `1c9565e` (`d6-readers.log`), all against the pre-opt-in baseline:

| reader | pre-opt-in (`odoo_w2v_base`, PostgreSQL) | opted-in clone at `1c9565e` |
|---|---|---|
| `-u uom,product` | n/a | exit 0, 51.7 s, 0 ERROR lines (the `72fca61` registry failure is gone) |
| `sale.report` | 51 | 51 |
| `purchase.report` | 32 | 32 |
| `account.invoice.report` | 62 | 62 |
| `purchase.bill.line.match` | 27 | 27 |
| view `report_stock_quantity` | 5268 | 5268 |
| view `stock_avco_report` | 7 | 7 |
| view `vendor_delay_report` | 10 | 10 |

The opted-in clone really ran on the storage path: `registry.mongo_store` prefix `odoo_w2v_views__`,
48 `productProduct` documents read from it, ORM `product.product` search resolving `uom_id` through
`_inherits`, and after the update the moved `product_template` columns (`name`, `type`, `sale_ok`)
have their NOT NULL dropped while the shadow column `uom_id` keeps it, so the three views were
recreated by `stock` / `stock_account` / `purchase_stock` over the reduced tables. `report_stock_quantity`
is date-projected (5263 rows on 2026-10-19, 5268 on 2026-10-20 on both sides). `stock.quant` (57)
and `stock.move` (137) also read. Both findings closed; the views probe is closed.

## Wave 1 collections re-checked (`wave-1-recheck/`)

| unit | source | verdict | checks |
|---|---|---|---|
| uom | `odoo_src` | PASS, merge_eligible | T1 3 / T2 8 / T3 30 |
| product-taxonomy | seeded clone `odoo_w2v_src` (`productTag`, `productBaseUnit` have 0 rows in `odoo_src`) | PASS, merge_eligible | T1 10 / T2 13 / T3 13 / T4 4 (`--ops .migration/recon/product-taxonomy/ops.json`) |
| product-attributes | `odoo_src` | PASS; warning `UNVERIFIED collection updateProductAttributeValue: 0 source rows` (accepted by the user in wave 1), `merge_eligible=false` for that reason only | T1 8 / T2 16 / T3 124 / T4 2 (`--ops .migration/recon/product-attributes/ops.json`) |

Same check counts as the wave 1 verifier's runs (`.migration/recon/wave-1/`).

## Odoo tests against the migrated build

Build: run branch `1c9565e`, `odoo-bin -d odoo_w2v_test2 --db_port=5433 -c <conf> --no-http
-i product,uom --test-enable --test-tags /product,/uom --stop-after-init` with the conf holding
`mongodb_migration_db = odoo_verify_mig`, so the fresh test database `odoo_w2v_test2` is not the
migration database and every in-scope model wrote `odoo_w2v_test2__*` collections
(`odoo_w2v_test2__uomUom` 30, `odoo_w2v_test2__productAttribute` 5, `odoo_w2v_test2__productCategory`
3, the ten others 0 after the tests' rollbacks; `odoo-tests.json`). The fourteen unprefixed
collections have identical counts before and after the run (`unprefixed_unchanged: true`). In the
test database the shadow tables are exactly `id` + the shadow columns (`product_product`:
`product_tmpl_id, weight, volume, standard_price`; `product_template`: `uom_id, categ_id, is_storable`
— `purchase_method` is absent because `purchase` is not installed there; `uom_uom`: `factor`), and
`uom_uom.factor` equals the 30 `odoo_w2v_test2__uomUom` documents.

Result: `1 failed, 0 error(s) of 161 tests when loading database 'odoo_w2v_test2'`, exit code 1
(`odoo-tests.log`). The one failure is `TestProductAttributeValueConfig.
test_get_closest_possible_combinations`: `AssertionError: 0.8114664554595947 not less than 0.5`, the Atlas round-trip timing
test the manager accepted as known (d-w2-timing-test = accept-known; expected 160/161). No other test
failed or errored (uom 15.64s incl. 3.50s test; product 52.82s incl. 37.29s at-install test;
the whole run took 28 min against Atlas). The first pass at `72fca61` on `odoo_w2v_test` gave the same
160/161 with the same single failure.

## Preflight

`python3 skills/wave-preflight/preflight.py --wave .migration/waves/wave-2.json --root . --grade <w2-b01 batch result>
--verify .migration/recon/wave-2/verify-result.json --run-id UNT11-41` (plugin `0d6bcfd`, after this branch was
pushed). The committed `.migration/recon/w2-b01.json` has `pr_url: ""`, so graded verbatim the batch is downgraded to
FAIL/missing_pr and the verifier result is rejected as `unexpected verdicts for w2-b01`. With the batch's PR URL
filled in (https://github.com/Cognition-Partner-Workshops/odoo/pull/33, a scratch copy outside the repo) it exits 0:
batch PASS, merge_eligible, `verify_problems: []`, `wave 2 OK: 1 batches, manifest_sha 0b73271c13bf`. The verifier
did not edit the worker's batch file; the manager's graded copy carries the PR URL.

## Evidence

- `.migration/recon/wave-2/w2-b01/product-catalog/result.json` (+ `report.md`, `recon.summary.md`): live, PASS, the batch verdict's evidence
- `.migration/recon/wave-2/wave-1-recheck/uom/result.json`, `product-taxonomy/result.json`, `product-attributes/result.json`: wave 1 re-checks
- `.migration/recon/wave-2/probes.json`: probes past the gate and cross-unit checks
- `.migration/recon/wave-2/odoo-tests.json`, `odoo-tests.log`: test namespace, unchanged unprefixed counts, shadow parity, test result
- `.migration/recon/wave-2/d6-readers.log`, `d6-update-traceback-72fca61.log`, `d6-readers-counts.json`: D6 reader probe on the opted-in clone (two findings at `72fca61`, closed at `1c9565e`)
- `.migration/recon/wave-2/verify-result.json`
