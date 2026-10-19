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

Wave verdict: **PASS** on the recon gate (the batch's PASS reproduces from an independent clone).
Two storage-path findings past the gate (section "D6 readers" below: `-u product` fails on a database
with `account` installed, and the three `_table_query` reports raise) need their own fix ticket; they
are not data-parity defects and do not change the recon verdict. Circuit breaker: no batch failed;
not tripped. `auto_merge` is false for this wave, so the manager grades and merges.

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

## D6 readers on an opted-in clone (probe past the gate: two storage-path findings)

Clone `odoo_w2v_views` of the seeded source (sale, purchase, stock, account installed, as in
`odoo_src`), run with the run-branch code at `72fca61` and `mongodb_migration_db = odoo_verify_mig`,
so every collection the storage path touched was `odoo_w2v_views__*` (pre-populated with a copy of
the 13 unprefixed collections so the fail-closed guard is satisfied); the unprefixed collections kept
their counts throughout (`d6-readers-counts.json`).

1. **`-u uom,product` fails to load the registry** on that clone: `Module loading account failed:
   file account/security/ir.access.csv could not be processed: Invalid domain [('company_id', 'in',
   company_ids)]: product.product is stored in MongoDB: no SQL for field 'uom_id' (not in
   _shadow_columns)` (`d6-update-traceback.log`). The update rolled back, so the shadow reduction
   never happened on this clone.
2. **The three `_table_query` reports the contract lists as D6 readers raise** the same
   `NotImplementedError` from `Query.__getitem__` (`odoo/orm/query.py:431`, reached from
   `Many2one.property_to_sql`, `odoo/orm/fields_relational.py:499`, from `sale_report.py:197`
   `table.product_id.uom_id`): `sale.report`, `purchase.report`, `account.invoice.report`
   `search_count([])` all fail. Reproduced on a second, plain clone `odoo_w2v_plain` with
   `mongodb_migration_db = odoo_w2v_plain` (unprefixed reads, no update, no writes): `d6-readers.log`.
   `purchase.bill.line.match` (27 rows), `stock.quant` (57), `stock.move` (137) and the ORM
   `product.product` search reading `uom_id` through `_inherits` work.

Reading: `uom_id` is a `product.template` field reached from `product.product` through `_inherits`;
`product_template.uom_id` and `product_product.product_tmpl_id` are both shadow columns, so the SQL
path could join through them, but `Query.__getitem__` checks the delegated field against
`product.product`'s own `_shadow_columns` and raises before the `_inherits` join. The product + uom
test database does not install sale/purchase/account, which is why the suites show 160/161. This is
not a data-parity defect (the recon PASS stands), but the migrated build breaks three reports and
`-u product` on any database that has `account` installed. The verifier fixes no code; this needs
its own storage-path ticket, as UNT11-42 was.

3. The 3 PostgreSQL views `report_stock_quantity` (5263 rows), `stock_avco_report` (7) and
   `vendor_delay_report` (10) exist and return rows on the clone, but because the update rolled back
   they read the full PostgreSQL tables, not the shadow tables; not evidence that the views work on
   the reduced tables. That probe stays open until finding 1 is fixed.

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
- `.migration/recon/wave-2/d6-readers.log`, `d6-update-traceback.log`, `d6-readers-counts.json`: D6 reader probe on the opted-in clone (two findings)
- `.migration/recon/wave-2/verify-result.json`
