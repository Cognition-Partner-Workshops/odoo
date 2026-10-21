# w3-b01 stock-config: committed scenarios (units.json) on the MongoDB clone vs the PostgreSQL twin

Same test tags on both clones (`~/w3b01/run_tests.sh`): `odoo_w3b01` on the PR tree (collections `odoo_w3b01__*`, live documents mirrored) and
`odoo_w3b01pg` on the pre-opt-in tree (`.migration/fixtures/build_source.sh` SOURCE_COMMIT). Crons 1, 19-23 deactivated on both by the seed.

| module | MongoDB clone (failures/errors/tests) | PostgreSQL twin |
|---|---|---|
| stock | 0/20/23 | 2/2/23 |
| purchase_stock | 0/13/18 | -/-/- |
| all modules (incl. post_install classes) | 0/67/86 | 3/2/86 |

Classes run: TestProcRule (23), TestProcRuleLoad (1), TestPurchaseLeadTime (10), TestReorderingRule (28), TestReturnOrderController (8), TestRoutes (5), TestStockLocationSearch (3), TestStockOrderpointActivity (1), TestStockReplenish (4), TestSupplier (3)

## Failing tests on the MongoDB clone (all pass on the twin unless listed under it)

- TestProcRule.test_compute_qty_to_order
- TestProcRule.test_compute_qty_to_order_after_receipt_line_deletion
- TestProcRule.test_endless_loop_rules_from_location
- TestProcRule.test_get_rule_respects_sequence_order
- TestProcRule.test_get_rules_from_location_preserves_route
- TestProcRule.test_orderpoint_deadline_date
- TestProcRule.test_orderpoint_location_archive
- TestProcRule.test_orderpoint_replenishment_view_1
- TestProcRule.test_orderpoint_replenishment_view_2
- TestProcRule.test_orderpoint_replenishment_view_3
- TestProcRule.test_orderpoint_replenishment_view_internal_transfer
- TestProcRule.test_orderpoint_warning
- TestProcRule.test_orderpoint_wizard_warehouse_option_lead_time
- TestProcRule.test_proc_rule
- TestProcRule.test_qty_to_order_remainder_decimal
- TestProcRule.test_reordering_rule_1
- TestProcRule.test_reordering_rule_2
- TestProcRule.test_reordering_rule_3
- TestProcRule.test_replenishment_creation
- TestProcRule.test_replenishment_order_to_max
- TestPurchaseLeadTime.test_00_product_company_level_delays
- TestPurchaseLeadTime.test_01_product_level_delay
- TestPurchaseLeadTime.test_02_product_level_delay
- TestPurchaseLeadTime.test_03_group_week
- TestPurchaseLeadTime.test_lead_time_with_no_supplier
- TestPurchaseLeadTime.test_merge_po_line
- TestPurchaseLeadTime.test_merge_po_line_3
- TestPurchaseLeadTime.test_merge_po_line_4
- TestPurchaseLeadTime.test_reordering_days_to_purchase
- TestPurchaseLeadTime.test_supplier_lead_time
- TestReorderingRule.test_2steps_and_partner_on_orderpoint
- TestReorderingRule.test_backorder_mto_buy
- TestReorderingRule.test_change_of_scheduled_date
- TestReorderingRule.test_forbid_snoozing_auto_trigger_orderpoint
- TestReorderingRule.test_intercompany_reordering_rules
- TestReorderingRule.test_multi_lingual_orderpoints
- TestReorderingRule.test_multi_locations_and_reordering_rule
- TestReorderingRule.test_orderpoint_warning_purchase_stock
- TestReorderingRule.test_procure_multi_lingual
- TestReorderingRule.test_procure_not_default_partner
- TestReorderingRule.test_reordering_rule_1
- TestReorderingRule.test_reordering_rule_2
- TestReorderingRule.test_reordering_rule_3
- TestReorderingRule.test_reordering_rule_horizon_days
- TestReorderingRule.test_reordering_rule_horizon_days_display
- TestReorderingRule.test_reordering_rule_multicurrency
- TestReorderingRule.test_reordering_rule_triggered_two_times
- TestReorderingRule.test_replenish_expired_seller
- TestReorderingRule.test_replenish_from_last_po_line
- TestReorderingRule.test_replenish_report_1
- TestReorderingRule.test_replenish_report_2
- TestReorderingRule.test_set_supplier_in_orderpoint
- TestReorderingRule.test_supplierinfo_last_purchase_date
- TestReorderingRule.test_tax_po_line_reordering_rule_with_branch_company
- TestReorderingRule.test_update_po_line_without_purchase_access_right
- TestReturnOrderController.test_download_label_invalid_token_redirects
- TestReturnOrderController.test_download_label_logs_chatter_message
- TestReturnOrderController.test_download_return_label_missing_params
- TestReturnOrderController.test_fully_returned_line_is_not_returnable
- TestReturnOrderController.test_multiple_pickings_are_returnable_separately
- TestReturnOrderController.test_partial_return_remaining_delivered_qty
- TestReturnOrderController.test_return_data_invalid_token_returns_error
- TestReturnOrderController.test_return_data_returnable_line_structure
- TestRoutes.test_allow_rule_creation_for_route_without_company
- TestStockOrderpointActivity.test_orderpoint_activity_portal_context_leak
- TestSupplier.test_effective_vendor
- TestSupplier.test_missing_seller_does_not_crash_po_confirmation

## PostgreSQL twin failures (pre-existing: the same TestProcRule failures occur on a fresh `odoo_src` clone seeded with the committed seed only, without the w3-b01 block)

- TestProcRule.test_orderpoint_warning
- TestProcRule.test_reordering_rule_1
- TestProcRule.test_reordering_rule_3
- TestProcRule.test_replenishment_order_to_max
- TestReturnOrderController.test_download_label_logs_chatter_message

## Root causes on the MongoDB clone (shared storage path, not patched here)

- 59x `ValueError: Order term 'route_sequence:min' is not a valid aggregate nor valid groupby`
- 9x `NotImplementedError: stock.warehouse.orderpoint.product_uom_name is stored in MongoDB and has no SQL expression; cross-store conditions are resolved through the`
- 1x `NotImplementedError: stock.route.rule_ids is stored in MongoDB and has no SQL expression; cross-store conditions are resolved through the comodel's own search (`
