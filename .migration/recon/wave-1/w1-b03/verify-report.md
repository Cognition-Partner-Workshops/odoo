run_id: ticket-43d6a24ad805454a85b7f6f8a58fd524
manifest_sha: b965d1e5f34e

# Verify report: wave 1, batch w1-b03 (uom-packaging), re-verify after the rebase onto 68bcca0

Verified head: `9fba21dcbe4b1b371b79c8fda481138f56d3d371` (PR #62 branch `devin/1792505452-w1-b03-uom-packaging`, frozen; code head `128305b39a5`; rebased onto `mongo-run/unt12` `68bcca0d81f`, after PRs #61, #60, #64 and #59 merged). Supersedes the verifies of heads `2b13474f3ab`, `1e206c1fd02` and `c2aa63efc58` (branch commits `6d95f63daf4`, `8fb23a07830`, `edf5fd9b39d`); every artifact under `.migration/recon/wave-1/w1-b03/` was regenerated from this head.

Verdict: **PASS**

Verifier worked no batch ticket of wave 1 and wrote nothing to the live collections `odoo_unt12.uomUom` / `odoo_unt12.stockPackageType` (nor any other live collection): the harness, the probe script, the ORM probes and the report-parity probes only read them. The only target writes were the verifier's TEMPORARY prefixed namespace `odoo_unt12.odoo_v_w1b03__*` (loaded from the verifier's clone, read by the ORM probes, dropped afterwards; `list_collection_names` shows no `odoo_v_w1b03__*` left). Odoo was never run with the collections unprefixed: no `mongodb_migration_db` is set, so the storage path derives `prefix = 'odoo_v_w1b03__'` from the clone name, and both ORM probe scripts assert it.

## What was re-run
- Batch PR: https://github.com/Cognition-Partner-Workshops/odoo/pull/62 at `9fba21dcbe4b1b371b79c8fda481138f56d3d371`, checked out as `recon/verify-w1-b03` (contains `origin/mongo-run/unt12` = `68bcca0d81fbbc45b3f4a181652364272d57b8d0`); the only additions are the evidence files under `.migration/recon/wave-1/w1-b03/`.
- Contracts as committed on that head: `.migration/mapping_spec.json` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc` (map-draft-2), `.migration/recon_tolerances.json` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea` (unt12-3); both equal the ticket's pins and `result.json` records the same two digests; neither was touched.
- Plugin: pinned worktree at `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (= `.migration/plugin_sha`), unpatched.
- Source: the previous clone was dropped and `odoo_src` rebuilt fresh with `.migration/fixtures/build_source.sh` (source commit `63446015e3c154f552633f54951843dcbb51e9a9`, marker `migration.fixture_source=3`; uom_uom 30, stock_package_type 2, product_category 7), then cloned with `createdb -T odoo_src odoo_v_w1b03` and seeded through the pre-opt-in tree (`odoo-unt12-src` at the source commit) with the batch's committed `.migration/load/seed_uom_packaging.py`: crons 1,19-23 off; package type `TOTE-SEED` id 3 at `2026-10-20 00:00:00`; `stock_package_type_stock_route_rel` = [(3,2),(3,3)]; `stock_package_type_stock_putaway_rule_rel` = [(1,1),(3,1)]. Clone populations: uom_uom 30, stock_package_type 3. DSN derived from `ODOO_PG_RO_DSN` (database swapped) inside one-shot shells; no credential in any artifact.
- Temporary prefix (`verify-prefixed-load.py --units uom-packaging,product-taxonomy,stock-reference,product-attributes,account-settings,account-chart`): the head's own unified loader `.migration/load/load_unit.py` unchanged, with only the Database handle wrapped so every collection name gets `odoo_v_w1b03__`; every unit whose collections are live in `odoo_unt12` (every merged opted-in model) was loaded from the clone, 25 root collections. Dropped with `--cleanup` after the probes.
- Target: `odoo_unt12` on `MONGODB_ATLAS_URI`, class `migration_cluster`; recon and probes scoped to `uomUom`, `stockPackageType` only.

## Recon re-run (harness verdict)
Command (from the Odoo root, pinned harness on `PYTHONPATH`): `recon run --unit uom-packaging --family postgresql --mapping .migration/mapping_spec.json --collections uomUom,stockPackageType --tolerances .migration/recon_tolerances.json --canonicalization <plugin>/skills/mongo-migration/profiles/postgresql.md --mode live --source-dsn-secret VERIFY_SRC_DSN --target-uri-secret MONGODB_ATLAS_URI --target-db odoo_unt12 --target-class migration_cluster --allowed-targets-file .migration/allowed_targets.json --ops .migration/recon/uom-packaging/ops.json --out .migration/recon/wave-1/w1-b03`

- Result: `.migration/recon/wave-1/w1-b03/result.json` -> verdict **PASS**, merge_eligible True, mode live, target_class migration_cluster, warnings [], error None, generated_at 2026-10-20T19:26:32.099879+00:00.
- Tiers: T1 counts_through_mapping 11 checks PASS / T2 per_field_aggregates 20 checks PASS / T3 keyed_diffs 37 checks PASS / T4 app_level_parity 4 checks PASS. Tier 1 stats {"stockPackageType": 3, "uomUom": 30}; tier 3 embeds graded stockRouteRel 2, stockPutawayRuleRel 2.
- Against the worker's `.migration/recon/uom-packaging/result.json` on the same head: every key is byte-identical except `generated_at`.

## Probes past the gate (`verify-probes.py` -> `verify-probes.json`, recon venv)
149 probes, 149 pass, 0 fail, same families as the previous verifies: row_count, key_set, min/max `_id`, null_missing_rate (28), value_equality (28), bson_type_observed (28), no_unmapped_root/element_fields, array_length_vs_child_rows, childless_parents_have_no_array, element_key_set, natural_key_unique (`unece_code`, `barcode`), 7 declared indexes present + no_undeclared_indexes, boundary_values (8), decimal_exact (NUMERIC vs Decimal128 at full precision), jsonb_object_equality (translated `name`), parentPath_consistent_with_relativeUomId, outbound_reference (10), no_same_wave_sibling_reference, tier4_replay of the four `ops.json` operations (source_sql on the clone vs target_pipeline on Atlas, sorted, full precision).

## Read-only ORM probes through the temporary prefix (`verify-orm-probes.py` -> `verify-orm-probes.json`)
Run through the verified head's own tree with its default prefix: `odoo-bin shell -d odoo_v_w1b03 --db_host=/var/run/postgresql --db_port=5433 --no-http < verify-orm-probes.py`. `uom.uom` / `stock.package.type` (`_storage = 'mongodb'`) read the prefixed verifier-loaded documents, `product.template` / `product.product` and the clone's legacy tables stay on PostgreSQL. Every relation is read through the ORM and compared for exact (sorted pair-set) equality with the clone's PostgreSQL rows; the two embeds also against the prefixed documents the ORM reads and, read-only, against the live batch documents; the prefixed documents are compared whole against the live ones. 29 probes, 29 pass, 0 fail:
- ORM reads the prefixed namespace only: ['odoo_v_w1b03__uomUom', 'odoo_v_w1b03__stockPackageType']
- uom.uom count: 30
- stock.package.type count: 3
- uom.uom scalar fields equal PostgreSQL rows: []
- stock.package.type scalar fields equal PostgreSQL rows: 3 rows
- product.template.uom_ids (ORM) == product_template_uom_uom_rel: orm=0 pg=0 pairs
- product.product.extra_uom_ids (ORM) == product_product_uom_uom_rel: orm=0 pg=0 pairs
- product.template search on uom_ids over every uom: orm=0 pg=0 pairs
- product.product search on extra_uom_ids over every uom: orm=0 pg=0 pairs
- uom.uom.product_ids reverse side (if declared): orm=0 pg=0 pairs
- uom_ids / extra_uom_ids relation tables are still PostgreSQL tables (row counts): product_template_uom_uom_rel=0 product_product_uom_uom_rel=0 (0 estate rows: equality is of empty sets on both sides; no link was made because this verify writes nothing)
- no productTemplate / productProduct documents are consulted for these relations: productTemplate present=False
- stockRouteRel documents == stock_package_type_stock_route_rel [prefixed, what the ORM reads]: orm=2 pg=2 pairs
- stockPutawayRuleRel documents == stock_package_type_stock_putaway_rule_rel [prefixed, what the ORM reads]: orm=2 pg=2 pairs
- stockRouteRel documents == stock_package_type_stock_route_rel [live batch collection, read-only]: orm=2 pg=2 pairs
- stockPutawayRuleRel documents == stock_package_type_stock_putaway_rule_rel [live batch collection, read-only]: orm=2 pg=2 pairs
- uomUom: prefixed documents (verifier load from the clone) == live batch documents: 30 vs 30 docs
- stockPackageType: prefixed documents (verifier load from the clone) == live batch documents: 3 vs 3 docs
- stock.package.type.route_ids (owner side, ORM): orm=2 pg=2 pairs
- stock.package.type search on route_ids over every route: orm=2 pg=2 pairs
- stock.route has no package_type_ids field; other side covered by the search through the array: ['package_type_selectable']
- stock.putaway.rule.package_type_ids (other side, ORM): orm=2 pg=2 pairs
- stock.putaway.rule search on package_type_ids over every package type: orm=2 pg=2 pairs
- stock.package.type has no putaway_rule_ids field; owner side covered by the putaway-rule search: ['route_ids']
- uom.uom.package_type_id -> stock.package.type (cross-store m2o, ORM) == live documents: orm=0 pg=0 pairs
- uom.uom.relative_uom_id / related_uom_ids both sides: orm=23 pg=23 pairs
- uom.uom.related_uom_ids == PostgreSQL: orm=23 pg=23 pairs
- live and prefixed collections untouched (sha256 of every document before == after): {'uomUom': '30 docs 7c699d1724d5', 'stockPackageType': '3 docs 158cce7ed884', 'odoo_v_w1b03__uomUom': '30 docs 7c699d1724d5', 'odoo_v_w1b03__stockPackageType': '3 docs 158cce7ed884'}
- transaction rolled back, no PostgreSQL write in the probe: cr.rollback()

## Report row parity against PostgreSQL (`verify-report-parity.py` -> `verify-report-parity-baseline.json`, `verify-report-parity.json`)
Same script, two passes on the same seeded clone. Baseline: through the pre-opt-in source tree, where `stock.avco.report` and `vendor.delay.report` are plain PostgreSQL views; every row (all stored and computed non-relational fields, many2one as id, dates ISO, floats rounded to 6 places), `search_count` and a `vendor.delay.report` `_read_group` by `category_id` dumped to the baseline JSON. Compare: through the verified head with `product.category` and `uom.uom` opted in (`_storage = 'mongodb'`, read from the prefixed load; asserted), the same reads through the ORM, compared one for one. 14 probes, 14 pass, 0 fail:
- ORM prefix is the clone's own, never unprefixed: odoo_v_w1b03__
- product.category opted in and read from the prefixed collection: storage=mongodb coll=odoo_v_w1b03__productCategory docs=7
- uom.uom opted in and read from the prefixed collection: storage=mongodb coll=odoo_v_w1b03__uomUom docs=30
- product.category documents in the prefix equal PostgreSQL product_category rows (id set): 7 docs
- every opted-in root model has its prefixed collection loaded from the clone (document count == PostgreSQL row count): 25 root models equal; embedded child models (arrays of a root): ['account.fiscal.position.account', 'account.payment.term.line', 'account.report.column', 'account.report.line', 'product.attribute.value']
- stock.avco.report: ORM rows on the PR head == legacy PostgreSQL view rows (every field, ordered by id): orm=6 pg=6 first_diff=[]
- stock.avco.report: search_count == PostgreSQL view count: orm=6 pg=6
- stock.avco.report: cost-method / category filter leaves no row the legacy view lacks and drops none it has: ids orm=6 pg=6
- vendor.delay.report: ORM rows on the PR head == legacy PostgreSQL view rows (every field, ordered by id): orm=9 pg=9 first_diff=[]
- vendor.delay.report: search_count == PostgreSQL view count: orm=9 pg=9
- vendor.delay.report: cost-method / category filter leaves no row the legacy view lacks and drops none it has: ids orm=9 pg=9
- vendor.delay.report read_group by category_id (MongoDB product.category) == legacy view aggregation: orm=[[5, 9, 715.0, 25.0]] pg=[[5, 9, 715.0, 25.0]]
- prefixed collections untouched by the report reads (sha256 before == after): {'uomUom': '7c699d1724d5', 'stockPackageType': '158cce7ed884', 'productCategory': 'b1ee18ce3af5'}
- transaction rolled back, no PostgreSQL write in the probe: env.cr.rollback()

Notes on what these prove:
- `stock.avco.report`: the head applies the cost-method filter in `_search` through MongoDB `product.category` (the legacy view did it in SQL over `product_category`); the 6 rows, every field and the id set equal the legacy view.
- `vendor.delay.report`: the 9 rows, every field (incl. `product_id`, `category_id`, `qty_total`, `qty_on_time`, `on_time_rate`), the count and the grouping by `category_id` (sum of `qty_total` / `qty_on_time`) equal the legacy view.
- `product.template.uom_ids` / `product.product.extra_uom_ids` read from PostgreSQL and equal it exactly (record side and search side); both relation tables hold zero rows in the estate, so the equality is of empty sets; no link was made because that would be an ORM write. The write-then-read case stays the worker's scenario evidence (66/66 on its prefixed clone).
- `stockRouteRel` / `stockPutawayRuleRel` match from both sides: prefixed and live documents == junction rows, owner side `stock.package.type.route_ids` and its array search, other side `stock.putaway.rule.package_type_ids` and its search.
- No write to any live collection: sha256 over every document of live `uomUom` (30) and `stockPackageType` (3) and of the prefixed collections is identical before and after each pass; every cursor was rolled back. The shell does not run `auto_init`, so `ensure_indexes` was not invoked either.

## Findings
- Verifier-harness lesson, recorded because it looks like a code bug until the namespace is complete: with only the batch's and product.category's collections in the prefix, `vendor.delay.report.search_read` returned `product_id = False` for 5 of 9 rows on the head while the legacy view had the ids. Cause: `product.product.display_name` of variant products reads `product.attribute` (opted in, collection `productAttribute`), which was absent from the prefix; `convert_to_read` swallows the resulting `MissingError` into `False`. With every merged opted-in unit loaded into the prefix the rows are equal (14/14). The compare pass now asserts that every opted-in root model's prefixed collection equals its PostgreSQL row count (25 root models; `account.fiscal.position.account`, `account.payment.term.line`, `account.report.column`, `account.report.line`, `product.attribute.value` are embedded arrays of a root). Nothing in the live namespace is affected; the finding is that a partially loaded namespace silently degrades many2one reads to `False` instead of raising.
- `product.template.uom_ids` / `product.product.extra_uom_ids` equality is proven on the estate's zero rows only (see above); the ORM-link-then-read case is outside a read-only verify.
- Both package-type junction tables are empty in the unseeded `odoo_src`, so the embed mappings are only exercised through the seeded tote; with the seed, array lengths, element keys, element fields and both ORM sides match row for row.
- Plan gap, unpatched: `.migration/load/load_unit.py` has no prefix / namespace option (it always writes `--target-db.<collection>`), so a verifier cannot load into a temporary prefix with the committed tool alone; this verify wrapped its Database handle from outside (`verify-prefixed-load.py`).
- Both the worker's run and this re-run are redacted with unsalted hashes because no `RECON_REDACT_SALT` secret exists (harness stderr warning; `result.json` warnings stay empty, so the verdict is unaffected).
- Plugin gap, unpatched: the installed mongo-recon-harness skill text (plugin 0.7.0) names a `--source-concurrency` flag that the pinned CLI at `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` rejects; the flag was omitted and `recon_tolerances.json`'s `source_concurrency` key was accepted as-is.
