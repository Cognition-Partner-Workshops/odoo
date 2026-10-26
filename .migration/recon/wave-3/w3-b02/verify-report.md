run_id: UNT14-59
manifest_sha: 79a896029481

# Wave 3 verifier report: w3-b02

Verdict: **PASS**

Independent verifier (ticket UNT14-59, plan step s4.3-wave-verify), who migrated none of these units. Base checked: mongo-run/unt13 at f84dbc723f61eeca98de9030e0a3fb4cb30dc540 (merge of https://github.com/Cognition-Partner-Workshops/odoo/pull/147, f84dbc723f6). Plugin 2c1160efde323c570425953b7e38bcc3496c6053 from a detached worktree; recon harness 0.3.3 in live mode, target class migration_cluster, target odoo_unt13 as it stands (no reload), committed mapping_spec.json and recon_tolerances.json, PostgreSQL profile canonicalization. odoo_src rebuilt with build_source.sh; source_fingerprint.py printed a100e84ee2fb6282f30b45c003fd1db47561317c739340a10564d9e869e56a4e. Branch: recon/verify-w3-unt14.

## Recon re-runs (verifier ops, Tiers 1-4)

| unit | verdict | merge_eligible | source_server | T1 | T2 | T3 | T4 | result |
|---|---|---|---|---|---|---|---|---|
| stockLocation | PASS | True | hmac-sha256:545efbd0aca82e45 | 88 | 65 | 164 | 4 | `.migration/recon/wave-3/w3-b02/verify/stockLocation/result.json` |
| saleOrderLineStockRouteRel | PASS | True | hmac-sha256:545efbd0aca82e45 | 3 | 0 | 1 | 2 | `.migration/recon/wave-3/w3-b02/verify/saleOrderLineStockRouteRel/result.json` |
| productTemplate | PASS | True | hmac-sha256:545efbd0aca82e45 | 12 | 17 | 439 | 1 | `.migration/recon/wave-3/w3-b02/verify/productTemplate/result.json` |
| productOptionalRel | PASS | True | hmac-sha256:545efbd0aca82e45 | 3 | 0 | 3 | 2 | `.migration/recon/wave-3/w3-b02/verify/productOptionalRel/result.json` |
| accountTax | PASS | True | hmac-sha256:545efbd0aca82e45 | 26 | 16 | 2574 | 1 | `.migration/recon/wave-3/w3-b02/verify/accountTax/result.json` |

Every run recorded git_head f84dbc723f61 with git_dirty false; verifier ops are in each unit's `verify/<unit>/ops.json` (sha256 recorded in result.json, distinct from the worker's).

## Comparison with batch evidence

| unit | source counts | T2 aggregates | T3 populations | mapping/tolerance sha |
|---|---|---|---|---|
| stockLocation | same {"stockLocation": 62, "stockPickingType": 40, "stockRoute": 13, "stockWarehouse": 5} | same | same | same |
| saleOrderLineStockRouteRel | same {"saleOrderLineStockRouteRel": 1} | same | same | same |
| productTemplate | same {"productTemplate": 439} | same | same | same |
| productOptionalRel | same {"productOptionalRel": 3} | same | same | same |
| accountTax | same {"accountTax": 65} | same | same | same |

Worker evidence: `.migration/recon/wave-3/w3-b02/result.batch.json` (status PASS, recon_git_head 64b5e9ae6f3e, PR https://github.com/Cognition-Partner-Workshops/odoo/pull/147).

## Probes past the gate

- Documents scanned: {"stockLocation": 62, "stockPickingType": 40, "stockRoute": 13, "stockWarehouse": 5, "saleOrderLineStockRouteRel": 1, "productTemplate": 439, "productOptionalRel": 3, "accountTax": 65}
- Unmapped keys: 0; BSON type errors: 0; explicit null values: 0
- Spec indexes present: {"stockLocation": "18/18", "stockPickingType": "11/11", "stockRoute": "23/23", "stockWarehouse": "24/24", "saleOrderLineStockRouteRel": "2/2", "productTemplate": "11/11", "productOptionalRel": "2/2", "accountTax": "18/18"}; missing: 0
- Unique indexes carrying the storage path's `$exists` partial filter (by design, not listed in the spec): [{"collection": "stockWarehouse", "keys": [["code", 1], ["companyId", 1]]}, {"collection": "stockWarehouse", "keys": [["name", 1], ["companyId", 1]]}, {"collection": "saleOrderLineStockRouteRel", "keys": [["stockRouteId", 1], ["saleOrderLineId", 1]]}, {"collection": "productOptionalRel", "keys": [["destId", 1], ["srcId", 1]]}]
- References checked: 65, dangling: 0; resolved against: mongo:accountAccount._id, mongo:accountTax._id, mongo:accountTaxGroup._id, mongo:productBaseUnit._id, mongo:productCategory._id, mongo:productRemoval._id, mongo:productTemplate._id, mongo:stockLocation._id, mongo:stockPickingType._id, mongo:stockRoute._id, mongo:stockRoute.stockRule.id, mongo:stockStorageCategory._id, mongo:stockWarehouse._id, pg:ir_sequence.id, pg:l10n_us_res_county.id, pg:res_city.id, pg:res_company.id, pg:res_country.id, pg:res_country_state.id, pg:res_partner.id, pg:res_users.id, pg:sale_order_line.id
- Junction read-back saleOrderLineStockRouteRel: {"links_mongo": 1, "links_pg": 1, "dup_pairs": 0, "missing_in_mongo": 0, "extra_in_mongo": 0, "endpoint_a_fanout_matches": true, "endpoint_b_fanout_matches": true, "distinct_a": 1, "distinct_b": 1}
- Junction read-back productOptionalRel: {"links_mongo": 3, "links_pg": 3, "dup_pairs": 0, "missing_in_mongo": 0, "extra_in_mongo": 0, "endpoint_a_fanout_matches": true, "endpoint_b_fanout_matches": true, "distinct_a": 3, "distinct_b": 2}
- Detail: `.migration/recon/wave-3/w3-b02/verify/probe.json`

## Tour replay on MongoDB storage

- Scratch copy `odoo_w3v_b02` from odoo_src; 35 merged units loaded into prefix `odoo_w3v_b02__` with load_unit.py, then `-u product,stock,account,purchase_stock,sale_stock` (no errors), admin password set through odoo-bin shell as instructed.
- purchase_stock:TestPurchaseOrderSuggest (addons/purchase_stock/tests/test_purchase_order_suggest.py): 9 tests, 0 failed, 0 error(s), 1 tour(s) succeeded. test_purchase_order_suggest_search_panel_ux tour succeeded in 72 s (15:36:02 to 15:37:14) under its user-approved 120 s whole-tour limit; the other eight tests ran with normal limits; worker PR evidence reports 35/35 on both storages.
- Log excerpt: `.migration/recon/wave-3/w3-b02/verify/tour-mongodb.log`. Scratch PostgreSQL copy and `odoo_w3v_b02__*` collections dropped afterwards.

## Findings

- All 5 units re-ran live against odoo_unt13 as it stands with verifier-authored Tier 4 ops and returned PASS with merge_eligible true and source_server hmac-sha256:545efbd0aca82e45.
- Verifier Tier 1 source counts, Tier 2 aggregates and Tier 3 graded populations equal the worker's committed result.json for every unit, against the same mapping and tolerance sha256.
- Probe over 628 documents found no unmapped keys, no BSON type errors and no explicit nulls, and every spec index is present (0 missing).
- The unique indexes carry a partialFilterExpression requiring every key to exist, which the spec does not list; odoo/orm/storage_mongodb.py adds it by design so missing keys never collide like PostgreSQL NULLs, and the harness index check accepts it, so this is informational.
- All 65 declared references resolve with 0 dangling ids, into merged wave 1-3 collections in odoo_unt13 or PostgreSQL-resident tables only.
- Root junction links read back identically from both endpoints: every (a, b) pair in MongoDB matches odoo_src with no duplicates and the per-endpoint fan-out counts agree.
- MongoDB-storage tour replay on scratch copy odoo_w3v_b02 (purchase_stock:TestPurchaseOrderSuggest (addons/purchase_stock/tests/test_purchase_order_suggest.py)): 9 tests, 0 failed, 0 error(s), 1 tour(s) succeeded; test_purchase_order_suggest_search_panel_ux tour succeeded in 72 s (15:36:02 to 15:37:14) under its user-approved 120 s whole-tour limit; the other eight tests ran with normal limits; worker PR evidence reports 35/35 on both storages.
- The ticket's scratch recipe (createdb -T odoo_src, then -u product,stock,account,purchase_stock,sale_stock) fails on the first -u with MissingError account.report(1) until the 35 merged wave 1-3 units are loaded into the <scratch>__ prefix with .migration/load/load_unit.py --prefix; after that load the same -u completed with no errors, so this is a recipe gap, not a data defect.
- Scratch state was removed afterwards: both PostgreSQL copies dropped and 76 odoo_w3v_b0*__ collections dropped from odoo_unt13, leaving its migrated collections untouched; recon and probes were read-only on both endpoints.
