# w3-b01 stock-config: committed scenarios (units.json) on the MongoDB clone vs the PostgreSQL twin

Same test tags on both clones (`~/w3b01/run_tests.sh`): `odoo_w3b01` on the PR tree (collections `odoo_w3b01__*`, live documents mirrored) and
`odoo_w3b01pg` on the pre-opt-in tree (`.migration/fixtures/build_source.sh` SOURCE_COMMIT). Crons 1, 19-23 deactivated on both by the seed.

| module | MongoDB clone (failures/errors/tests) | PostgreSQL twin |
|---|---|---|
| stock | 2/2/23 | 2/2/23 |
| all modules (incl. post_install classes) | 3/2/86 | 3/2/86 |

Classes run: TestProcRule (23), TestProcRuleLoad (1), TestPurchaseLeadTime (10), TestReorderingRule (28), TestReturnOrderController (8), TestRoutes (5), TestStockLocationSearch (3), TestStockOrderpointActivity (1), TestStockReplenish (4), TestSupplier (3)

## Failing tests on the MongoDB clone (those also listed under the twin fail the same way on both)

- TestProcRule.test_orderpoint_warning
- TestProcRule.test_reordering_rule_1
- TestProcRule.test_reordering_rule_3
- TestProcRule.test_replenishment_order_to_max
- TestReturnOrderController.test_download_label_logs_chatter_message

## PostgreSQL twin failures (pre-existing: the same TestProcRule failures occur on a fresh `odoo_src` clone seeded with the committed seed only, without the w3-b01 block)

- TestProcRule.test_orderpoint_warning
- TestProcRule.test_reordering_rule_1
- TestProcRule.test_reordering_rule_3
- TestProcRule.test_replenishment_order_to_max
- TestReturnOrderController.test_download_label_logs_chatter_message

## Root causes on the MongoDB clone (shared storage path, not patched here)


## Notes

- Branch rebased onto `mongo-run/unt12` f8050a0 (PR #74, central fix for `fields_get` on MongoDB models, `read_group` ordered by a non-requested aggregate, and the per-field flush behind `test_reordering_rule_horizon_days_display`). `stock.rule._search_rule_for_warehouses` keeps requesting its ordering aggregates (harmless on both storages).
- The PostgreSQL twin's failures are pre-existing (same four `TestProcRule` failures on a fresh `odoo_src` clone seeded with the committed seed only; `TestReturnOrderController.test_download_label_logs_chatter_message` is the HttpCase under `--no-http`) and fail the same way on the MongoDB clone.
- `rlPyCairo` / `_rl_renderPM` import errors in the logs are reportlab backend noise in the venv, not storage related.
