run_id: ticket-f62b6e27f7664a4db0e43b91dd7eaae5
manifest_sha: ec3ed6d13acd

# Verify report: wave 3, batch w3-b01 (unit stock-config) - **PASS**

Independent verifier; this session migrated none of wave 3 and wrote nothing to `odoo_unt12` (every Atlas connection opened `secondaryPreferred`, no mutating call; the PostgreSQL side read a verifier-owned clone under `default_transaction_read_only`).

## What was re-run
- Batch PR: https://github.com/Cognition-Partner-Workshops/odoo/pull/73, verified at the exact pushed head `4947aabe9306bc4c8837b407fd4a1ac7923aa8db` (the batch-result commit "w3-b01: batch result PASS after the package-type reload", on top of code head `5b2cca27d2a`), base `mongo-run/unt12@f8050a09b32` (confirmed an ancestor of the head; it carries the central fix #74). Verifier branch `recon/verify-w3-b01` is cut from that head; nothing outside `.migration/recon/wave-3/w3-b01/` was changed.
- `.migration/` paths the PR changes outside its own recon directories (`.migration/recon/stock-config/`, `.migration/recon/w3-b01.json`): only `.migration/load/seed_scenario_rows.py` (the w3-b01 seed block) and `.migration/load/scenario_stock_config.py`. `mapping_spec.json`, `recon_tolerances.json`, `allowed_targets.json`, `plugin_sha` and the fixture manifest are byte-identical to `mongo-run/unt12`.
- Mapping `map-draft-2` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc` and tolerances `unt12-3` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea`: committed bytes on the PR head, re-hashed by the verifier, equal to the ticket pins and to the values both rerun `result.json` files record.
- Plugin/harness pinned at `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (detached worktree, unpatched); canonicalization from `skills/mongo-migration/profiles/postgresql.md`.
- Source: `odoo_src` did not exist on this VM; rebuilt from scratch with `.migration/fixtures/build_source.sh` as committed on the head (marker `migration.fixture_source=3`, SOURCE_COMMIT `63446015e3c`, 70 modules, 78 s). Then `createdb -T odoo_src odoo_v48` and every committed seed applied in run-branch order through the pre-opt-in source tree (`odoo-unt12-src/odoo-bin shell`, PostgreSQL storage only): `seed_uom_packaging.py` -> `seed_scenario_rows.py` -> `seed_account_journal.py` (8 s in total; crons 1 and 19-23 deactivated on the clone only). No "already past" line was printed by any sequence pin. The seeds reproduced the live ids: tote package type 3 with routes `[2, 3]`, putaway rule 1 -> package types `[1, 3]`; stock-config block: archived warehouse 3 (location 33, picking types 17-24, routes 6-8, rules 9/10/11/14) resupplied from 1, receipts type 1 favourite of admin with wave locations `[7, 17]`, MTO route 1 on category 5 / template 5 / move 137, putaway rules `[2, 3]`, capacities `[1, 2]`; junction `stock_package_type_stock_putaway_rule_rel` (rule, package type) = `[(1, 1), (1, 3), (3, 1), (3, 2)]`.
- Target: `odoo_unt12` on `MONGODB_ATLAS_URI` (class `migration_cluster`), read-only. Collections graded with `--collections`, one harness run per unit: the batch's 8 (`stockWarehouse`, `stockLocation`, `stockPickingType`, `stockRoute`, `stockRule`, `stockPutawayRule`, `stockStorageCategoryCapacity`, `stockWarehouseOrderpoint`) as unit `stock-config`, plus `uomUom` and `stockPackageType` (wave-1 unit `uom-packaging`, reloaded by UNT12-51, evidence `recon/w3-pkg-reload@76280ac`) as unit `uom-packaging`, as the ticket scopes it.
- Tier 4 ops: the verifier's own files `verify-ops.json` (8 ops, sha256 `77b5a1b3a47a196b4758de6429f09e97187128404352a729a629f0b170906666`) and `verify-ops-uom-packaging.json` (2 ops, sha256 `df00ca18362bff3605465b0f1ec3c3dea363dd796e8c68eec202479e8cd9e365`), not the batch's `.migration/recon/stock-config/ops.json` (5 ops, sha256 `5c6189eee317a4371cf4e22a88b517cac1544f2da4ece4cf7bdc2b7067b631c5`) nor UNT12-51's `.migration/recon/uom-packaging/ops.json` (sha256 `73dae9d33e8078c5cb0ea0038e094e5cd51b7f6e5f704ca8b2b098aa7ee519be`).

## Recon rerun (harness verdict)
- `stock-config/result.json` - verdict **PASS**, mode `live`, target_class `migration_cluster`, merge_eligible `True`, generated `2026-10-21T05:06:30.738846+00:00`, warnings `[]`, 42 s.

| Tier | Name | Checks | Findings | Result |
|---|---|---|---|---|
| 1 | counts_through_mapping | 111 | 0 | PASS |
| 2 | per_field_aggregates | 114 | 0 | PASS |
| 3 | keyed_diffs | 115 | 0 | PASS |
| 4 | app_level_parity | 8 | 0 | PASS |

- Source counts seen by the harness: stockWarehouse 3, stockLocation 38, stockPickingType 24, stockRoute 9, stockRule 15, stockPutawayRule 3, stockStorageCategoryCapacity 2, stockWarehouseOrderpoint 5; embeds graded in Tier 3: stockLocation.stockPickingTypeRel 2, stockPickingType.pickingTypeFavoriteUserRel 1, stockRoute.categ 1, stockRoute.move 1, stockRoute.product 1, stockRoute.warehouse 9, stockWarehouse.stockWhResupplyTable 1. The Tier 1-3 blocks are identical to the worker's `.migration/recon/stock-config/result.json` (111/114/115); Tier 4 differs only in the ops (8 verifier ops vs 5 worker ops).
- `uom-packaging/result.json` - verdict **PASS**, mode `live`, merge_eligible `True`, generated `2026-10-21T05:06:38.697868+00:00`, 8 s: Tier 1 11 checks, Tier 2 20, Tier 3 39 (`stockPackageType` full_diff 3, `uomUom` full_diff 30, embeds `stockPackageType.stockPutawayRuleRel` 4 and `stockPackageType.stockRouteRel` 2), Tier 4 2 - all PASS, 0 findings. Tier 1-3 blocks identical to UNT12-51's run on `recon/w3-pkg-reload`.
- One live run per unit was enough: no mismatch, so no source re-read for drift was needed; the probe script re-read the source counts at its end and they were unchanged.
- A first Tier 4 attempt failed on two of the verifier's own ops (`$project` of nullable booleans left the field missing where PostgreSQL has NULL: `replenish_location`, the five `*_selectable` flags); the rows were otherwise equal, the ops were given `$ifNull` and the whole run was repeated. Data was never at fault; recorded for transparency, the committed `result.json` is the rerun.

### Verifier ops (Tier 4), all 10 PASS
warehouses_with_resupply (per warehouse: code/company/lot_stock/in+out types/steps/active + resupply array size and first supplier), locations_tree_with_wave_picking_types (every location: parent, usage, complete_name, warehouse, storage category, active, replenish flag + wave picking-type link count), picking_types_per_warehouse_and_code ($group: n, n_active, min id, max sequence), routes_with_rule_and_link_counts (per route: flags + rule count via `$lookup` into stockRule + sizes of categ/product/move/warehouse arrays), rules_detail (15 columns per rule), putaway_rules_with_package_type_links (per rule: all scalar columns + the package types linked to it, resolved from `stockPackageType.stockPutawayRuleRel` through `$lookup`, as a count and an ordered id list), storage_capacity_rows, orderpoints_per_warehouse_trigger ($group: n, min/max qty, distinct products/locations); package_types_with_links (per package type: barcode/use/sequence/company + ordered putaway-rule and route id lists from both junction arrays), uom_relative_tree (9 columns per unit).

## Probes past the gate
Script `probe_w3_b01.py` (read-only on both sides), evidence `probe-results.json`. 392 probes: 391 PASS, 0 FAIL, 1 SKIP.

| Probe family | Probes | Result | What it checked |
|---|---|---|---|
| count | 10 | PASS | document count == source row count per collection; none empty (3/38/24/9/15/3/2/5 + 30/3) |
| null_missing | 214 | PASS | per mapped field of the 10 collections: no explicit BSON null on the target, target missing-field count == source NULL count |
| duplicates | 17 | PASS | no duplicate `_id`; no duplicate natural keys (warehouse code+company and name+company, location barcode+company, capacity storageCategory+product / +packageType, orderpoint product+location+company, package type barcode) |
| boundaries | 10 | PASS | min/max `_id` and min/max of a per-collection measure (sequence, parent_path, quantity, product_max_qty, max_weight, factor) equal source |
| boundary_doc | 20 | PASS | first and last row of every collection compared field by field (all mapped scalar fields) against the document |
| full_rows | 7 | PASS | every row and every mapped scalar field of stockWarehouse (3x30), stockRoute (9x15), stockRule (15x23), stockPutawayRule (3x13), stockStorageCategoryCapacity (2x8), stockWarehouseOrderpoint (5x23), stockPackageType (3x15): 0 mismatches, no document without a source row |
| jsonb_fields | 4 | PASS | every JSONB (translated / properties) field of stockWarehouse, stockLocation, stockPickingType, stockRoute, every row, object-equal |
| embed_lengths | 9 | PASS | per parent: array length == source child-row count, no child without a parent document; distributions: stockWarehouse.stockWhResupplyTable {0:2,1:1}, stockLocation.stockPickingTypeRel {0:36,1:2}, stockPickingType.pickingTypeFavoriteUserRel {0:23,1:1}, stockRoute.categ/move/product {0:8,1:1} each, stockRoute.warehouse {0:2,1:6,3:1}, stockPackageType.stockPutawayRuleRel {1:2,2:1}, stockPackageType.stockRouteRel {0:2,2:1} |
| embed_elements | 9 | PASS | the same 9 arrays element by element: multiset of (parent id, child key) on the target == source junction rows, 0 only-source / 0 only-target |
| junction | 2 | PASS | the ticket's probe: `stockPackageType.stockPutawayRuleRel` unwound to (package type, rule) pairs `[(1,1), (1,3), (2,3), (3,1)]` == the PostgreSQL rows of `stock_package_type_stock_putaway_rule_rel` exactly; every embedded rule id {1, 3} resolves in live `stockPutawayRule` (ids {1, 2, 3} == source); likewise `stockRouteRel` pairs `[(3,2), (3,3)]` resolve in `stockRoute` |
| reference | 58 PASS, 1 SKIP | PASS | every outbound reference of the 10 collections (FK target from the census `ref_table`, resolved to a root collection `_id`): 42 into the batch itself (stockWarehouse, stockLocation, stockPickingType, stockRoute, stockRule, stockPutawayRule), 16 into merged wave-1/2 collections (accountAccount, productCategory, productProduct, productRemoval, productSupplierinfo, productTemplate, stockStorageCategory, stockPackageType, uomUom), 0 dangling everywhere. SKIP: stockRoute.move.moveId -> stockMove (later wave, PostgreSQL-resident). Wave 3 has a single batch, so no sibling namespace exists and no `cross_batch_reference` is possible |
| indexes | 10 | PASS | every index declared by the mapping exists on the live collection (26/16/10/11/13/6/3/11 + 4/3) |
| ops_replay | 10 | PASS | the 10 verifier ops replayed independently of the harness (source SQL on the clone vs target pipeline), compared as unordered row sets keyed by column name: 3=3, 38=38, 8=8, 9=9, 15=15, 3=3, 2=2, 4=4, 3=3, 30=30 rows |
| seeded_nonempty | 10 | PASS | the two zero-fixture roots (stockPutawayRule 3, stockStorageCategoryCapacity 2) and the eight zero-fixture arrays the seeds fill are non-empty on the target (1, 2, 1, 1, 1, 1, 4, 2 elements), so none is UNVERIFIED |
| source_stability | 1 | PASS | source counts re-read after all probes, unchanged |

A first probe pass flagged `stockWarehouseOrderpoint.deadlineDate` on all 5 rows: the source column is a PostgreSQL `DATE`, the mapping declares it `bson_type: date` (midnight datetime) and the harness canonicalizes it with `datetime_utc_truncate_ms`; the probe's comparison was stricter than the mapping and was corrected to accept a DATE as a midnight BSON date. Not a data finding.

## Findings
No findings. Nothing in the batch blocks merge; no tolerance, target or model change is requested.

Observations (not findings, for the manager):
- `.migration/recon/w3-b01.json` records `head_sha: 5b2cca27d2a` (the code head), while the pushed head the manager graded and this verifier checked out is `4947aabe930`, the batch-result commit on top of it. The two differ only by that JSON file. Preflight's merge check should compare the verified head against the head it merges, as noted in earlier waves.
- Plugin gap at pin `9a584b4` (unchanged): the harness `result.json` has no `ops_sha256` key, so preflight's `verifier_reused_ops` check cannot be fed from it; the ops sha256 values above are recorded here instead.
- `RECON_REDACT_SALT` is not set in this environment either; the committed artifacts are redacted with unsalted hashes, as in every run of this engagement.
- Not re-run by the verifier: the batch's ORM scenario (`scenario_stock_config.py`, worker 61/61) and the committed Odoo tests (worker: 3 failures / 2 errors of 86 on both the MongoDB clone and the PostgreSQL twin) - both need an opted-in Odoo instance against a prefixed copy of the collections, which this no-write verify did not start. The recon gate, the full-row, element-level embed, junction and reference checks above are the evidence this verdict rests on.

## Verdict
**PASS** - graded from the committed reruns `stock-config/result.json` and `uom-packaging/result.json` (head `4947aabe930`), not asserted.
