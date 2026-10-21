# w3-b01 stock-config: committed scenarios (units.json) on the MongoDB clone vs the PostgreSQL twin

Same test tags on both clones (`~/w3b01/run_tests.sh`): `odoo_w3b01` on the PR tree (collections `odoo_w3b01__*`, live documents mirrored) and
`odoo_w3b01pg` on the pre-opt-in tree (`.migration/fixtures/build_source.sh` SOURCE_COMMIT). Crons 1, 19-23 deactivated on both by the seed.

| module | MongoDB clone (failures/errors/tests) | PostgreSQL twin |
|---|---|---|
| stock | 1/6/23 | 2/2/23 |
| purchase_stock | 0/4/18 | -/-/- |
| all modules (incl. post_install classes) | 3/14/86 | 3/2/86 |

Classes run: TestProcRule (23), TestProcRuleLoad (1), TestPurchaseLeadTime (10), TestReorderingRule (28), TestReturnOrderController (8), TestRoutes (5), TestStockLocationSearch (3), TestStockOrderpointActivity (1), TestStockReplenish (4), TestSupplier (3)

## Failing tests on the MongoDB clone (all pass on the twin unless listed under it)

- TestProcRule.test_orderpoint_warning
- TestProcRule.test_qty_to_order_remainder_decimal
- TestProcRule.test_reordering_rule_1
- TestProcRule.test_reordering_rule_2
- TestProcRule.test_reordering_rule_3
- TestProcRule.test_replenishment_creation
- TestProcRule.test_replenishment_order_to_max
- TestPurchaseLeadTime.test_01_product_level_delay
- TestPurchaseLeadTime.test_reordering_days_to_purchase
- TestPurchaseLeadTime.test_supplier_lead_time
- TestReorderingRule.test_multi_locations_and_reordering_rule
- TestReorderingRule.test_reordering_rule_1
- TestReorderingRule.test_reordering_rule_2
- TestReorderingRule.test_reordering_rule_3
- TestReorderingRule.test_reordering_rule_horizon_days_display
- TestReturnOrderController.test_download_label_logs_chatter_message
- TestRoutes.test_allow_rule_creation_for_route_without_company

## PostgreSQL twin failures (pre-existing: the same TestProcRule failures occur on a fresh `odoo_src` clone seeded with the committed seed only, without the w3-b01 block)

- TestProcRule.test_orderpoint_warning
- TestProcRule.test_reordering_rule_1
- TestProcRule.test_reordering_rule_3
- TestProcRule.test_replenishment_order_to_max
- TestReturnOrderController.test_download_label_logs_chatter_message

## Root causes on the MongoDB clone (shared storage path, not patched here)

- 10x `NotImplementedError: stock.warehouse.orderpoint.product_uom_name is stored in MongoDB and has no SQL expression; cross-store conditions are resolved through the`
- 1x `NotImplementedError: Cannot join account.tax through purchase.order.line.tax_ids: stored in MongoDB`
- 1x `NotImplementedError: stock.route.rule_ids is stored in MongoDB and has no SQL expression; cross-store conditions are resolved through the comodel's own search (`

## Notes

- Storage gap 1 (`read_group` ordered by a non-requested aggregate) no longer reaches the tests: `stock.rule._search_rule_for_warehouses` requests the ordering aggregates. The gap itself is still reproducible (scenario check) and stays reported for the central fix.
- `NotImplementedError: Cannot join account.tax through purchase.order.line.tax_ids` (TestPurchaseLeadTime.test_01_product_level_delay) is `fields_get` → `_description_groupable` on a wave-1 collection (account-chart), same class as storage gap 2, not a stock-config path.
- `TestReorderingRule.test_reordering_rule_horizon_days_display` (`qty_to_order` 0.0 != 3 from `stock.replenishment.info.json_lead_days`) fails only on the MongoDB clone; it reproduces with the original `_get_domain_locations_new` too (single-test run), so it is not caused by this PR's rewrites. Not root-caused in this batch; to re-check after the central storage fixes and the rebase.
- `rlPyCairo` / `_rl_renderPM` import errors are environment noise from the twin-less report rendering (reportlab backend missing in the venv), not storage related.
