# UNT14-12 ORM conformance sweep (re-run after UNT14-36)

Odoo's own tests for the six scope addons and every installed bridge, one addon per run, on PostgreSQL storage
(baseline) and MongoDB storage. Base `mongo-run/unt13` at 90cf74d9f9e6d3148a28a333a7062e602dac50f4, plugin
608ef5b035ba2d13a1246d4d731aa525ce04ff6f, signed spec map-draft-5 (mapping_sha256
c0b93dad9526fc8f02df6b8199436d76da9f938a05ccadc98ab3adb7a35202a7; runtime `SPEC_SHA256` matches).
Local evidence, not merge evidence. This replaces the previous sweep (base 1a746f30).

## Bottom line

- PostgreSQL: 3,383 tests, 36 fail or error (17 fail, 19 error).
- MongoDB: 3,377 tests run, 118 fail or error (86 fail, 32 error). Classified: (a) also fails on PostgreSQL 36,
  (b) accepted Studio field 4, (c) unit-owned addon raw SQL 71, (d) environment load 5, (e) storage-path gap 1,
  pending decision d-perf-query-count 1.
- (e): E8 only, MongoDB keeps datetimes to the millisecond. It goes back to the storage worker; not fixed here.
- The previous gaps E1, E2, E6 and E7 no longer occur. E3, E5 and C2 are now (c) as the storage worker reclassified them.
  E4 is listed on its own as pending decision d-perf-query-count.
- The strict layout (PostgreSQL keeps only the declared shadow columns) still cannot load the scope: U1, class (c).

## How it ran

- Every run used a fresh `createdb -T` copy of a template cloned from `odoo_fixture` (never `odoo_src`), then
  `odoo-bin -u <addon> --test-enable --test-tags /<addon> --stop-after-init` on that copy, one process at a time,
  PostgreSQL then MongoDB, so no two test HTTP servers ever ran together. `websocket-client` 1.9.2 is in the Odoo
  venv, so browser tours ran (no tour was skipped).
- MongoDB: local `mongo:7` on localhost (never Atlas), database `odoo_unt13`, each copy in its own collection prefix.
  Every model whose table the signed spec maps (76 models, 71 collections, 22,757 documents seeded from the copy's
  own rows through the storage path's encoders) was opted in to `_storage = 'mongodb'` by an uncommitted local hook.
- Because of U1 the MongoDB runs kept every stored column mirrored in PostgreSQL as a shadow column (uncommitted
  local hook), so raw SQL still runs against PostgreSQL rows and failures isolate the ORM-to-MongoDB path.
- A failure counts as (d) only if the same test, re-run alone on a fresh copy, passes. 6 suspects were re-run; 5 passed.
- MongoDB run counts are 6 lower than PostgreSQL (sale 3, stock_account 2, sale_stock 1) because the (d)
  `setUpClass` errors abort a class before it counts its tests.

## Pass/fail per addon

| Addon | PostgreSQL | MongoDB | MongoDB failures by class |
|---|---|---|---|
| uom | FAIL 0 run, 0 fail, 1 err | FAIL 0 run, 0 fail, 1 err | (a) 1 |
| product | FAIL 155 run, 1 fail, 0 err | FAIL 155 run, 1 fail, 0 err | (a) 1 |
| account | FAIL 1154 run, 2 fail, 5 err | FAIL 1154 run, 68 fail, 9 err | (a) 7, C1 65, C2 1, C3 1, C4 1, C6 1, P 1 |
| purchase | FAIL 124 run, 1 fail, 0 err | FAIL 124 run, 1 fail, 0 err | (a) 1 |
| stock | FAIL 703 run, 8 fail, 6 err | FAIL 703 run, 10 fail, 6 err | (a) 14, C5 1, E8 1 |
| sale | FAIL 293 run, 1 fail, 0 err | FAIL 290 run, 1 fail, 1 err | (a) 1, D 1 |
| stock_account | pass 240 run, 0 fail, 0 err | FAIL 238 run, 0 fail, 2 err | D 2 |
| purchase_stock | FAIL 231 run, 1 fail, 2 err | FAIL 231 run, 2 fail, 2 err | (a) 3, C7 1 |
| sale_stock | FAIL 178 run, 1 fail, 0 err | FAIL 177 run, 1 fail, 1 err | (a) 1, D 1 |
| sale_purchase | pass 13 run, 0 fail, 0 err | pass 13 run, 0 fail, 0 err | - |
| sale_purchase_stock | pass 24 run, 0 fail, 0 err | pass 24 run, 0 fail, 0 err | - |
| account_payment | FAIL 31 run, 0 fail, 1 err | FAIL 31 run, 0 fail, 1 err | (a) 1 |
| account_edi_ubl_cii | FAIL 227 run, 2 fail, 1 err | FAIL 227 run, 2 fail, 6 err | (a) 3, B 4, D 1 |
| account_qr_code_sepa | FAIL 4 run, 0 fail, 3 err | FAIL 4 run, 0 fail, 3 err | (a) 3 |
| sale_edi_ubl | pass 1 run, 0 fail, 0 err | pass 1 run, 0 fail, 0 err | - |
| purchase_edi_ubl_bis3 | pass 5 run, 0 fail, 0 err | pass 5 run, 0 fail, 0 err | - |
| l10n_us_account | pass 0 run, 0 fail, 0 err | pass 0 run, 0 fail, 0 err | - |
| sale_sms | pass 0 run, 0 fail, 0 err | pass 0 run, 0 fail, 0 err | - |
| stock_sms | pass 0 run, 0 fail, 0 err | pass 0 run, 0 fail, 0 err | - |

Totals: PostgreSQL 3,383 run, 17 fail, 19 error. MongoDB 3,377 run, 86 fail, 32 error.
All 36 PostgreSQL failures also fail on MongoDB and are the 36 in (a).

## (e) Storage-path gaps (1, for the storage worker)

| Gap | Count | Where it breaks | Example test | Minimal repro |
|---|---|---|---|---|
| E8 | 1 | Datetime fields lose their microseconds on MongoDB: BSON dates keep milliseconds, PostgreSQL `timestamp` keeps microseconds. The test compares `forecast_expected_date` with a `datetime.now()` value: `22:06:08.074000 != 22:06:08.074311`. Fails alone too. | `stock: TestReports.test_report_forecast_10_report_line_corresponding_to_picking_highlighted` | set `stock.move.date_deadline = datetime(2026, 10, 27, 22, 6, 8, 74311)`, flush, invalidate, read: PostgreSQL `...08.074311` (equal), MongoDB `...08.074000` (not equal) |

## Pending decision d-perf-query-count (1, not a storage gap)

`account: TestAccountMoveReconcile.test_perf_reconciled_lines_ids`: reading `reconciled_lines_ids` returns the right
lines (the inner `assertEqual` passes) but sends three `SELECT id FROM ... WHERE id IN %s` shadow lookups instead of
the four PostgreSQL reads the test pins, so `assertQueries` fails. Waiting on the user's decision.

## (d) Environment load (5, each passed when re-run alone)

Four first failed with the MongoDB driver's `_OperationCancelled: operation cancelled` inside a storage write during
the full run (for example `storage_mongodb.py:487` `add_links`); the fifth raised `The entry is not balanced.` from
`account.move._check_balanced`. Re-run alone on a fresh copy with
`odoo-bin -u <addon> --test-enable --test-tags /<addon>:<test> --stop-after-init`:

| Test | Re-run alone |
|---|---|
| `sale: setUpClass (TestAccruedSaleOrders)` | `0 failed, 0 error(s) of 3 tests` |
| `sale_stock: setUpClass (TestAngloSaxonAccounting)` | `0 failed, 0 error(s) of 1 tests` |
| `stock_account: TestStockValuation.test_at_date_average_2` | `0 failed, 0 error(s) of 1 tests` |
| `stock_account: setUpClass (TestAngloSaxonAccounting)` | `0 failed, 0 error(s) of 2 tests` |
| `account_edi_ubl_cii: TestCiiImportFacturXFRCashRounding.test_import_cash_rounding_add_invoice_line` | `0 failed, 0 error(s) of 1 tests` |

The sixth re-run (E8) still failed alone.

## (c) Unit-owned addon raw SQL (71, for the unit tickets)

Each is addon raw SQL listed in the dependency register of `.migration/NOTES.md` (every row already exists; none added).
The SQL reads or changes PostgreSQL rows only, so the MongoDB-backed ORM sees other values.

| Id | Count | Unit | Raw SQL (file:line) | Register entry | What fails |
|---|---|---|---|---|---|
| C1 | 65 | account | `addons/account/models/account_full_reconcile.py:30`, `:39`; `addons/account/models/account_partial_reconcile.py:226` | sql rows 7 (`account.full.reconcile.create`, account_move_line w), 8 (same, account_partial_reconcile w), 9 (`account.partial.reconcile._update_matching_number`, account_move_line w), all B | `full_reconcile_id` and `matching_number` read back `False`. Repro: reconcile two receivable lines, then read them: PostgreSQL ORM `('43', 43)`; MongoDB ORM `(False, False)` while its PostgreSQL row holds `('P79', 43)` |
| C2 | 1 | account | `addons/account/models/account_move.py:4546-4570` | sql row 106 (`account.move._get_frequent_account_and_taxes`, line 4548), B | `UndefinedTable: missing FROM-clause entry for table "account_move_line__account_id"`: the SQL names the alias PostgreSQL `_search` creates for the `account_id` join; MongoDB `_search` returns an id-list query with no joins. Reclassified to (c) by the storage worker |
| C3 | 1 | account | `addons/account/models/account_account.py:1341`, `:1362`, `:1441`, `:1472` | sql rows 2-5 (`account.account._action_unmerge`), B | `tax_ids` / `tag_ids` of the unmerged accounts differ from PostgreSQL |
| C4 | 1 | account | `addons/account/wizard/account_merge_wizard.py:185`, `:197`, `:209` | sql rows 12-14 (`account.merge.wizard._action_merge`), B | merged account keeps both accounts' links (`tax_ids` `[207, 216]` vs `[207]`) |
| C5 | 1 | stock | `addons/stock/models/stock_quant.py:1251` | sql row 20 (`stock.quant._merge_quants`), B | duplicate quants not merged: `0.0 != 1` |
| C6 | 1 | analytic (account) | `addons/analytic/models/analytic_mixin.py:126-145` (`_read_group_groupby` builds a SQL subquery over `query.from_clause`) | fragment rows 186 (`:132`) and 187 (`:143`), `analytic.mixin._read_group_groupby`. The register marks them A; the storage worker reclassified this as unit-owned, and the disposition is left for the register owner | grouping move lines by `analytic_distribution`: `TypeError: unhashable type: 'dict'` at `storage_mongodb.py:1438` `read_group` |
| C7 | 1 | purchase_stock | `addons/purchase_stock/models/purchase_order_line.py:15-25` (`_ondelete_stock_moves`) | sql row 17 (line 24), B | deleting the `stock_moves` selection value resets `qty_received_method` in PostgreSQL only; MongoDB keeps `'stock_moves'` |

U1 (stock, not a test failure): with the strict layout, `-u` of the scope stops loading the registry (prep exit 255):
the SQL view at `addons/stock/report/report_stock_quantity.py:194` (sql row 240, view row 8 `report.stock.quantity`,
both B) reads `stock_location.parent_path`, which is not a shadow column.

Tests per family:
- C1: account: `TestAccountMoveOutInvoiceOnchanges.test_date_reversal_exchange_move` x2; account: `TestAccountMovePaymentsWidget.test_payments_with_exchange_difference_invoice_with_caba`; account: `TestAccountMovePaymentsWidget.test_payments_with_exchange_difference_payment_with_caba`; account: `TestAccountMoveReconcile.test_caba_dest_acc_reconciliation_partial_pmt`; account: `TestAccountMoveReconcile.test_caba_mix_reconciliation`; account: `TestAccountMoveReconcile.test_caba_undo_reconciliation`; account: `TestAccountMoveReconcile.test_full_reconcile_bunch_lines` x4; account: `TestAccountMoveReconcile.test_full_reconcile_foreign_currency_rounding_difference_credit_larger`; account: `TestAccountMoveReconcile.test_full_reconcile_foreign_currency_rounding_difference_debit_larger`; account: `TestAccountMoveReconcile.test_full_reconcile_unlink_clears_matching_number`; account: `TestAccountMoveReconcile.test_matching_loop`; account: `TestAccountMoveReconcile.test_matching_number_full_reconcile`; account: `TestAccountMoveReconcile.test_matching_number_partial_multi_reconcile`; account: `TestAccountMoveReconcile.test_matching_number_partial_multi_separate_reconcile`; account: `TestAccountMoveReconcile.test_matching_number_partial_single_reconcile`; account: `TestAccountMoveReconcile.test_matching_number_unreconcile_multi`; account: `TestAccountMoveReconcile.test_modify_all_reconciled_lines`; account: `TestAccountMoveReconcile.test_partial_reconcile_amounts_of_several_matching_lines`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_exchange_difference_transfer_account_check_entries_1`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_exchange_difference_transfer_account_check_entries_2`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_exchange_difference_transfer_account_check_entries_3`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_revert`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_tax_grid_multi_taxes`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_workflow_multi_currency`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_workflow_single_currency`; account: `TestAccountMoveReconcile.test_reconcile_draft_cash_basis_surprise_use_case`; account: `TestAccountMoveReconcile.test_reconcile_draft_cash_basis_use_case`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_credit_foreign_currency_credit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_credit_foreign_currency_credit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_credit_foreign_currency_debit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_credit_foreign_currency_debit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_debit_foreign_currency_credit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_debit_foreign_currency_credit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_debit_foreign_currency_debit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_debit_foreign_currency_debit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_same_foreign_currency_credit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_same_foreign_currency_credit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_same_foreign_currency_debit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_same_foreign_currency_debit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_foreign_currency_rounding_issue` x4; account: `TestAccountMoveReconcile.test_reconcile_import`; account: `TestAccountMoveReconcile.test_reconcile_import_same_matching_different_account`; account: `TestAccountMoveReconcile.test_reconcile_lines_corner_case_1_zero_balance_same_foreign_currency`; account: `TestAccountMoveReconcile.test_reconcile_lines_corner_case_2_zero_amount_currency_same_foreign_currency`; account: `TestAccountMoveReconcile.test_reconcile_lines_corner_case_3_zero_balance_one_foreign_currency`; account: `TestAccountMoveReconcile.test_reconcile_lines_multiple_in_foreign_currency` x8; account: `TestAccountMoveReconcile.test_reconcile_partial_reconciliations`; account: `TestAccountMoveReconcile.test_reconcile_special_mexican_workflow_1`; account: `TestAccountMoveReconcile.test_reconcile_special_mexican_workflow_2`; account: `TestAccountMoveReconcile.test_reverse_with_multiple_lines`; account: `TestTransferWizard.test_change_period_reconcile_pair_by_pair_customer_invoices`
- C2: account: `TestAccountMoveOutInvoiceOnchanges.test_quick_edit_total_amount`
- C3: account: `TestAccountAccount.test_unmerge`
- C4: account: `TestAccountMergeWizard.test_merge`
- C5: stock: `TestInventory.test_inventory_7`
- C6: account: `TestAccountAnalyticAccount.test_cross_analytics_computing`
- C7: purchase_stock: `TestUninstallPurchaseStock.test_qty_received_method`

## (b) Accepted by the user (4)

`StorageError: account.move: column 'x_studio_peppol_tax_point_date' is not in the signed mapping of 'account_move'`
(`storage_mongodb.py:115` `_layout`): account_edi_ubl_cii: `TestAccountEdiUblCii.test_credit_note_optional_fields`; account_edi_ubl_cii: `TestAccountEdiUblCii.test_invoice_optional_fields`; account_edi_ubl_cii: `TestUblImportBis3InvoiceBEOptionalFields.test_import_credit_note_with_optional_fields`; account_edi_ubl_cii: `TestUblImportBis3InvoiceBEOptionalFields.test_import_invoice_optional_fields`

## (a) Also fail on PostgreSQL (36)

Environment, same on both storages: no PDF engine or `rlPyCairo` renderer, cloned databases without a filestore copy,
and tests that run before later modules load (`uom` `setUpClass`: `res_partner.autopost_bills` NOT NULL; fiscal lock dates).
uom: `setUpClass (TestUom)`; product: `TestImportFiles.test_import_create_product_demo_xls [product.pricelist]`; account: `TestAccountAccount.test_compute_account_type_on_code_change`; account: `TestAuditTrailAttachment.test_audit_trail_attachment`; account: `TestAuditTrailAttachment.test_audit_trail_write_attachment`; account: `setUpClass (TestAccountDigest)`; account: `TestAccountEarlyPaymentDiscount.test_invoice_report_without_invoice_date`; account: `setUpClass (TestKpiProvider)`; account: `TestSequenceMixin.test_journal_sequence_format`; purchase: `TestImportFiles.test_import_requests_for_quotation_template_xlsx`; stock: `TestProcRule.test_orderpoint_warning`; stock: `TestProcRule.test_reordering_rule_1`; stock: `TestProcRule.test_reordering_rule_3`; stock: `TestProcRule.test_replenishment_order_to_max`; stock: `TestReports.test_report_forecast_11_non_reserved_order`; stock: `TestReports.test_report_quantity_1`; stock: `TestReports.test_report_quantity_2`; stock: `TestReports.test_report_quantity_3`; stock: `TestWarehouse.test_modified_global_route`; stock: `TestBatchPicking02.test_batch_validation_without_backorder`; stock: `TestBatchPicking02.test_same_package_several_pickings`; stock: `TestInventory.test_cyclic_inventory`; stock: `TestStockPickingTour.test_inventory_adjustment_apply_all`; stock: `TestStockQuant.test_relocate`; sale: `TestImportFiles.test_import_quotation_template_xlsx`; purchase_stock: `TestPurchaseStockReports.test_vendor_delay_report_with_multi_location`; purchase_stock: `TestReplenishWizard.test_product_replenish_wizard_multiple_buy_routes`; purchase_stock: `TestReorderingRule.test_2steps_and_partner_on_orderpoint`; sale_stock: `TestReturnOrderController.test_download_label_logs_chatter_message`; account_payment: `TestAccountPayment.test_generate_and_send_invoice_with_qr_code`; account_edi_ubl_cii: `CiiExportFacturXFR.test_invoice_deferred_dates`; account_edi_ubl_cii: `TestUblImportBis3InvoiceBE.test_generate_pdf_when_xml_does_not_provide_one`; account_edi_ubl_cii: `TestUblImportBis3InvoiceBEAutoGeneratePDF.test_import_invoice_auto_generate_pdf`; account_qr_code_sepa: `TestSEPAQRCode.test_out_invoice_create_refund_qr_code`; account_qr_code_sepa: `TestSEPAQRCode.test_sepa_qr_code_detection`; account_qr_code_sepa: `TestSEPAQRCode.test_sepa_qr_code_generation`

## Plugin findings

- P2 (logged) and P1 from the earlier sweeps are unchanged at 608ef5b (`hooks/mongo_guard.py:95`). No new plugin findings.
