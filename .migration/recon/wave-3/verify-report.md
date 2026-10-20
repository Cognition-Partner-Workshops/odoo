run_id: UNT11-49
manifest_sha: 3548af4a78e1

# Wave 3 independent verification: product-pricing (w3-b01), product-supplierinfo (w3-b02), product-combo (w3-b03), product-variant-extras (w3-b04)

Verifier session that migrated none of the wave. Run branch `mongo-run/20261014` at `1c12182` (merge of
supplier-info PR #43; holds pricing PR #44, combos PR #45, variant extras PR #47 and the shared fixes PR #48
digits-Float BSON, PR #51 stock install hook, PR #57 order-independent seed script). Harness: plugin
`0d6bcfd` (`.migration/plugin_sha`, a worktree at that commit); `mongo_guard` hook from plugin main `79b3b29`
(guard fix #111), every write below ran from `/home/ubuntu/repos/odoo` with `origin/HEAD` -> `mongo-run/20261014`.
Mapping `map-draft-5` (`e329b5aec09f4594d2ae8a297ff346e71f0cfe1a82043373c1d995bcdc0b160a`); tolerances `v1`
strict (`59f500708400dbd7ffb23dfbd9264b962cf6307e9a48ec678157cd2dbcdb4b68`); canonicalization
`skills/mongo-migration/profiles/postgresql.md`. Source `odoo_src` rebuilt in this session with
`.migration/fixtures/build_source.sh` (marker 3, pre-opt-in commit `03a3cb5`, 68 s); the verifier's own clone
`odoo_w3v_src` (`createdb -T odoo_src`) seeded with the merged `.migration/load/seed_scenario_rows.py` through
the `odoo-base` shell: `3 tags, 2 base units, 6 product uoms, 4 combos, 6 custom values, 5 label layouts,
4 pricelists, 7 pricelist items, 32 sellers` (the expected 4 / 7 / 32). Target `odoo_migration` on the migration
cluster was only read (no reload, no write to any unprefixed collection): a count + sha256 digest of all 21
unprefixed collections (353 documents) was taken before the first scratch write and again after the last
(`estate/unprefixed-digest.before.json`, `estate/unprefixed-digest.after.json`, identical). Scratch namespaces
`odoo_w3v_estate__*`, `odoo_w3v_fresh__*`, `odoo_w3v_test__*` (conf `mongodb_migration_db = odoo_verify_mig`,
so no scratch database is the migration database) were dropped at the end, as were the PostgreSQL clones.

## Verdict

**Wave 3: PASS.** All four batches PASS on the verifier's own live strict recon, merge_eligible, with check
counts identical to the committed worker results; probes past the gate found 0 problems; the full-estate
update, the seven D6 readers, the fresh `stock,purchase_stock` install and the product/uom test suite behave as
in wave 2. No new finding needs a ticket. `auto_merge` is `false`: the manager relays the user's merge call.

## Per-batch verdict

| batch | unit | verdict | verifier's live recon (`w3-bNN/<unit>/result.json`) | vs committed worker result |
|---|---|---|---|---|
| w3-b01 | product-pricing | PASS | `--collections productPricelist,productPricelistItem --ops .migration/recon/product-pricing/ops.json`: PASS, T1 18 / T2 26 / T3 12 / T4 7, 0 warnings, merge_eligible; source 4 / 7 | identical check counts to `.migration/recon/product-pricing/result.json` (PR #44) |
| w3-b02 | product-supplierinfo | PASS | `--collections productSupplierinfo --ops .migration/recon/product-supplierinfo/ops.json`: PASS, T1 7 / T2 13 / T3 32 / T4 5, 0 warnings, merge_eligible; source 32 | identical to `.migration/recon/product-supplierinfo/result.json` (PR #43) |
| w3-b03 | product-combo | PASS | `--collections productCombo,productComboItem --ops .migration/recon/product-combo/ops.json`: PASS, T1 5 / T2 11 / T3 14 / T4 3, 0 warnings, merge_eligible; source 4 / 10 | identical to `.migration/recon/product-combo/result.json` (PR #45) |
| w3-b04 | product-variant-extras | PASS | `--collections productAttributeCustomValue,productLabelLayout --ops .migration/recon/product-variant-extras/ops.json`: PASS, T1 10 / T2 12 / T3 28 / T4 9, 0 warnings, merge_eligible; source 6 / 5 | identical to `.migration/recon/product-variant-extras/result.json` (PR #47) |

All eight runs: `--mode live --target-class migration_cluster --target-db odoo_migration`, source DSN a
session-local JSON secret pointing at `odoo_w3v_src` (same read-only role as `ODOO_PG_RO_DSN`), target
`MONGODB_ATLAS_URI`, `--allowed-targets-file .migration/allowed_targets.json`, same mapping and tolerance
sha256 as the worker results. Like the worker results, the live output is redacted with unsalted hashes
(`RECON_REDACT_SALT` is not set engagement-wide; `redaction_salted: false`); informational, not a wave-3 defect.

## Probes past the gate (`probes.json`, read-only, 0 problems)

`probes.py` reads the seven real wave-3 collections plus `productTemplate` and records counts only. It derives a
`problems` list (count != the verifier's recon Tier 1 source count, non-distinct or non-int `_id`, non-int or dangling
reference, non-Decimal128 decimal, non-datetime date) and exits 1 when that list is non-empty; `verify-result.json`
`probes.problems` is copied from it. This run: `problems: []`, exit 0.

- Counts equal the seeded source (`productPricelist` 4, `productPricelistItem` 7, `productSupplierinfo` 32,
  `productCombo` 4, `productComboItem` 10, `productAttributeCustomValue` 6, `productLabelLayout` 5); every
  `_id` is an int and distinct (`distinct_ids == count`).
- Every declared decimal field is `Decimal128` wherever present, no float leaked (PR #48 holds for all of them):
  `productPricelistItem.minQuantity/fixedPrice/priceDiscount/priceRound/priceSurcharge/priceMinMargin/priceMaxMargin`,
  `productSupplierinfo.minQty/price/discount`, `productComboItem.extraPrice`.
- `createDate`/`writeDate`/`dateStart`/`dateEnd`: datetime or absent, 0 bad values.
- Indexes exist per collection (e.g. `productPricelistItem` `pricelistId_1`, `basePricelistId_1`, `categId_1`, the
  compound `base_1_basePricelistId_1_pricelistId_1_appliedOn_1_minQuantity_1_categId_1__id_1`;
  `productSupplierinfo` `productTmplId_1_partnerId_1_sequence_1_minQty_1_price_1__id_1`, `partnerId_1`,
  `productId_1`; `productComboItem` `comboId_1`, `productId_1`; `productLabelLayout`
  `productIds.productProductId_1`, `productTmplIds.productTemplateId_1`, `moveIds.stockMoveId_1`).

## Cross-unit consistency (all clean, `probes.json` -> `refs`)

0 dangling references, 0 nulls, 0 non-int ids in every checked reference:

| reference | values | into |
|---|---|---|
| `productPricelistItem.pricelistId` 7, `basePricelistId` 1, `productLabelLayout.pricelistId` 1 | 9 | `productPricelist` (same wave) |
| `productPricelistItem.categId` 2 | 2 | `productCategory` (wave 1) |
| `productPricelistItem.productTmplId` 3, `productSupplierinfo.productTmplId` 32 | 35 | `productTemplate` (wave 2) |
| `productPricelistItem.productId` 1, `productSupplierinfo.productId` 3, `productComboItem.productId` 10 | 14 | `productProduct` (wave 2) |
| `productPricelistItem.uomId` 1, `productSupplierinfo.uomId` 32 | 33 | `uomUom` (wave 1) |
| `productComboItem.comboId` 10 | 10 | `productCombo` (same wave) |
| `productAttributeCustomValue.customProductTemplateAttributeValueId` 6 | 6 | `productTemplateAttributeValue` (wave 2) |
| `productLabelLayout.productIds[].productProductId` (3 docs) | 6 | `productProduct` (wave 2) |
| `productLabelLayout.productTmplIds[].productTemplateId` (1 doc) | 3 | `productTemplate` (wave 2) |
| `productLabelLayout.productUomIds[].productUomId` (2 docs) | 2 | `productUom` (wave 2) |
| `productTemplate.comboIds[].productComboId` (1 doc) | 3 | `productCombo` (wave 2 -> wave 3) |

`productLabelLayout.moveIds[].stockMoveId` (6 values, 2 docs) and `packagingId` (1) point at tables that are not
opted in (`stock_move`, `product_packaging`) and are only shape-checked (int, non-null).

## Full-estate probe past the gate (`estate/`)

Pre-opt-in baseline: `odoo_w3v_base` = `createdb -T odoo_w3v_src` read through the `odoo-base` shell
(PostgreSQL storage, `estate/estate-readers.baseline.txt`). Migrated side: `odoo_w3v_estate` =
`createdb -T odoo_w3v_src` (sale, purchase, stock, account installed), the 21 unprefixed collections pre-copied
into `odoo_w3v_estate__*` (`estate/precopy.py`, counts equal on both sides, `estate/estate-precopy.log`), then
`odoo-bin -d odoo_w3v_estate -c <conf> --no-http -u product,uom,sale,purchase,stock --stop-after-init` at
`1c12182`: exit 0 in ~1 min, 0 ERROR / 0 Traceback lines (`estate/estate-update.log`); afterwards every opted-in
model's ORM count equals its document count (`estate/estate-readers.mongo.txt`, e.g. product.combo 4 / 4,
product.combo.item 10 / 10, product.template 38 / 38, product.product 48 / 48) and the four combos read back
through the ORM with their item counts and base prices (1.98 / 147.0 / 33.0 / 14.0).

Seven D6 readers, `search_count([])` through the ORM on both sides (`estate/estate-readers.py`):

| reader | pre-opt-in (`odoo_w3v_base`) | migrated (`odoo_w3v_estate`, run branch) |
|---|---|---|
| sale.report | 51 | 51 |
| purchase.report | 32 | 32 |
| account.invoice.report | 62 | 62 |
| purchase.bill.line.match | 27 | 27 |
| report.stock.quantity | 5263 | 5263 |
| stock.avco.report | 7 | 7 |
| vendor.delay.report | 10 | 10 |

7 / 7 equal (wave 2 saw 5268 for the date-window stock view on 2026-10-19; both sides read 5263 today).

Fresh install: `createdb odoo_w3v_fresh` + `odoo-bin -d odoo_w3v_fresh -c <conf> --no-http -i stock,purchase_stock
--stop-after-init` at `1c12182`: 59 modules, `Modules loaded.`, exit 0, 0 ERROR / 0 Traceback
(`estate/fresh-install.log`); `estate/fresh-check.txt`: stock, purchase_stock, product, uom, account installed,
namespace `odoo_w3v_fresh__*`, uom.uom 30 / 30 / 30, product.category 3 / 3 / 3, product.attribute 5 / 5 / 5
(ORM / documents / PostgreSQL shadow), the product, pricing, supplierinfo, combo, label-layout, stock and purchase
models 0 on every side (no demo data in that database; same shape as the wave-2 fresh test database).

## Odoo tests against the migrated build (`odoo-tests.log`, `odoo-tests.json`)

Build: run branch `1c12182`, `createdb odoo_w3v_test` + `odoo-bin -d odoo_w3v_test -c <conf> --no-http -i product,uom
--test-enable --test-tags /product,/uom --stop-after-init`, conf `mongodb_migration_db = odoo_verify_mig`, so the
fresh test database is not the migration database and every in-scope model wrote `odoo_w3v_test__*` collections
(20 of them; `odoo_w3v_test__uomUom` 30, `odoo_w3v_test__productAttribute` 5, `odoo_w3v_test__productCategory` 3,
the other 17 empty after the tests' rollbacks; `odoo-tests.json`). Result (15:30 -> 15:55 UTC, 25 min):
`1 failed, 0 error(s) of 161 tests`, exit 1. The one failure is the accepted Atlas timing test
`TestProductAttributeValueConfig.test_get_closest_possible_combinations` (as in waves 1 and 2); no other FAIL or
ERROR line in `odoo-tests.log`. The 21 unprefixed collections have identical counts before and after the run
(`unprefixed_unchanged: true` in `odoo-tests.json`) and an identical content digest (`estate/`).

## Wave 1 and wave 2 collections re-checked (`wave-1-recheck/`, `wave-2-recheck/`)

Same harness, same seeded clone, read-only on the target:

| unit | verdict | checks |
|---|---|---|
| uom | PASS, merge_eligible | T1 3 / T2 8 / T3 30 (no ops file for uom, as in the wave-1 and wave-2 verifications); `uomUom` 30 |
| product-taxonomy | PASS, merge_eligible | T1 10 / T2 13 / T3 13 / T4 4; `productCategory` 8, `productTag` 3, `productBaseUnit` 2 |
| product-attributes | PASS; `merge_eligible=false` only for the wave-1-accepted warning `UNVERIFIED collection updateProductAttributeValue: 0 source rows` | T1 8 / T2 16 / T3 124 / T4 2; `productAttribute` 14, `productAttributeValue` 101 |
| product-catalog | PASS, merge_eligible | T1 61 / T2 51 / T3 348 / T4 7; `productTemplate` 38, `productProduct` 48, `productTemplateAttributeLine` 9, `productTemplateAttributeValue` 24, `productDocument` 2, `productUom` 6 |

Same check counts as the wave-2 verifier's runs (`.migration/recon/wave-2/`).

## Preflight

`python3 skills/wave-preflight/preflight.py --wave .migration/waves/wave-3.json --root . --grade
.migration/recon/w3-b01.json --grade .migration/recon/w3-b02.json --grade .migration/recon/w3-b03.json --grade
.migration/recon/w3-b04.json` (plugin `0d6bcfd`): exit 0, every batch `status PASS`, `merge_eligible true`,
`undeclared_write_targets []`, `wave 3 OK: 4 batches, manifest_sha 3548af4a78e1` (all four committed batch
results carry their `pr_url`, so no scratch copy was needed). `--verify .migration/recon/wave-3/verify-result.json
--run-id UNT11-49`: run after this branch (`recon/wave-3`) was pushed, exit 0, `verify_problems: []`, `wave 3 OK: 4 batches, manifest_sha 3548af4a78e1`.

## Findings

No new finding; nothing needs a ticket. Informational notes, with evidence:

1. `RECON_REDACT_SALT` is not set for any session of this run, so every committed live result (workers and
   verifiers, waves 1-3) is redacted with unsalted hashes (`redaction_salted: false`). Engagement-wide setting,
   not a wave-3 defect.
2. `.migration/recon/w3-b03.json` (product-combo) carries no `fixture_results`; the grade does not require one
   and the live recon is the merge authority.
3. The run-branch conf parser logs `unknown option 'mongodb_migration_db' in the config file ... stored as-is`;
   the option is read by `odoo/orm/storage_mongodb.py` and worked (every scratch collection was prefixed).

## Evidence

- `verify-result.json` (this verdict), `verify-report.md`
- `w3-b01/product-pricing/`, `w3-b02/product-supplierinfo/`, `w3-b03/product-combo/`,
  `w3-b04/product-variant-extras/`: `result.json`, `report.md`, `recon.summary.md`, `recon.stdout.log`
- `wave-1-recheck/{uom,product-taxonomy,product-attributes}/`, `wave-2-recheck/product-catalog/`
- `probes.json`, `probes.py`
- `estate/`: `unprefixed-digest.before.json`, `unprefixed-digest.after.json`, `digest_unprefixed.py`, `precopy.py`,
  `estate-precopy.log`, `estate-update.log`, `estate-readers.py`, `estate-readers.baseline.txt`,
  `estate-readers.mongo.txt`, `fresh-install.log`, `fresh-check.py`, `fresh-check.txt`
- `odoo-tests.log`, `odoo-tests.json`
