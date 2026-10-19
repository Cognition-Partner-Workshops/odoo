run_id: UNT11-41
manifest_sha: 0b73271c13bf

# Wave 2 independent verification: product-catalog (w2-b01)

Verifier session that migrated none of the wave. Run branch `mongo-run/20261014` at `72fca61`
(PR #34 storage-path fixes at `27d722f`, then PR #33 product catalog); plugin pinned `0d6bcfd`
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
`odoo_w2v_test` with `mongodb_migration_db = odoo_verify_mig`, so every test collection was
`odoo_w2v_test__*`.

## Per-batch verdict

| batch | unit | verdict | verifier recon | note |
|---|---|---|---|---|
| w2-b01 | product-catalog | PASS | live from the freshly seeded clone `odoo_w2v_src`, `--collections` the six unit collections, `--ops .migration/recon/product-catalog/ops.json`: PASS, T1 61 / T2 51 / T3 348 / T4 7 checks, 0 warnings, merge_eligible | reproduces the committed `.migration/recon/product-catalog/result.json` check for check (61 / 51 / 348 / 7) |

Wave verdict: **PASS**. Circuit breaker: no batch failed; not tripped. `auto_merge` is false for
this wave, so the manager grades and merges.

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
  `odoo_w2v_test__uomUom` documents; `product_*` shadow tables and documents are both empty after
  the tests' rollbacks.
- Source forward references that now resolve on the target: `product_template.uom_id` (3 distinct),
  `categ_id` (6), `product_template_attribute_line.attribute_id` (5), `product_uom.uom_id` (2),
  the two tag relation tables (3 each): 0 unresolved.
- The unprefixed namespace holds exactly the thirteen wave 1 + wave 2 collections (plus
  `_connectivity_probe`); no shared collection between batches.

Not re-run by the verifier: the 3 PostgreSQL views that read the shadow columns
(`report_stock_quantity`, `stock_avco_report`, `vendor_delay_report`) do not exist in the
product + uom test database (`stock`, `stock_account`, `purchase_stock` are not installed there),
and exercising them on an opted-in clone of the seeded source needs `-u product` through the
storage path against the unprefixed collections, which writes documents.

## Wave 1 collections re-checked (`wave-1-recheck/`)

| unit | source | verdict | checks |
|---|---|---|---|
| uom | `odoo_src` | PASS, merge_eligible | T1 3 / T2 8 / T3 30 |
| product-taxonomy | seeded clone `odoo_w2v_src` (`productTag`, `productBaseUnit` have 0 rows in `odoo_src`) | PASS, merge_eligible | T1 10 / T2 13 / T3 13 / T4 4 (`--ops .migration/recon/product-taxonomy/ops.json`) |
| product-attributes | `odoo_src` | PASS; warning `UNVERIFIED collection updateProductAttributeValue: 0 source rows` (accepted by the user in wave 1), `merge_eligible=false` for that reason only | T1 8 / T2 16 / T3 124 / T4 2 (`--ops .migration/recon/product-attributes/ops.json`) |

Same check counts as the wave 1 verifier's runs (`.migration/recon/wave-1/`).

## Odoo tests against the migrated build

Build: run branch `72fca61`, `odoo-bin -d odoo_w2v_test --db_port=5433 -c <conf> --no-http
-i product,uom --test-enable --test-tags /product,/uom --stop-after-init` with the conf holding
`mongodb_migration_db = odoo_verify_mig`, so the fresh test database `odoo_w2v_test` is not the
migration database and every in-scope model wrote `odoo_w2v_test__*` collections
(`odoo_w2v_test__uomUom` 30, `odoo_w2v_test__productAttribute` 5, `odoo_w2v_test__productCategory`
3, the ten others 0 after the tests' rollbacks; `odoo-tests.json`). The fourteen unprefixed
collections have identical counts before and after the run (`unprefixed_unchanged: true`).

Result: `1 failed, 0 error(s) of 161 tests when loading database 'odoo_w2v_test'`, exit code 1
(`odoo-tests.log`). The one failure is `TestProductAttributeValueConfig.
test_get_closest_possible_combinations`: `AssertionError: 0.709648609161377 not less than 0.5`, the
Atlas round-trip timing test the manager accepted as known (d-w2-timing-test = accept-known;
expected 160/161). No other test failed or errored (uom 13.7 s incl. 3.0 s test; product 49.8 s incl.
36.2 s at-install test; the post-install run took the remaining 24 min against Atlas).

## Evidence

- `.migration/recon/wave-2/w2-b01/product-catalog/result.json` (+ `report.md`, `recon.summary.md`): live, PASS, the batch verdict's evidence
- `.migration/recon/wave-2/wave-1-recheck/uom/result.json`, `product-taxonomy/result.json`, `product-attributes/result.json`: wave 1 re-checks
- `.migration/recon/wave-2/probes.json`: probes past the gate and cross-unit checks
- `.migration/recon/wave-2/odoo-tests.json`, `odoo-tests.log`: test namespace, unchanged unprefixed counts, shadow parity, test result
- `.migration/recon/wave-2/verify-result.json`
