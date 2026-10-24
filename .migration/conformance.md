# UNT14-12 ORM conformance sweep (final)

Odoo's own tests for the six scope addons and every installed bridge, one addon per run, on PostgreSQL storage
(baseline) and MongoDB storage. Base `mongo-run/unt13` at 1a746f30e0f43398e2333fd2d379d9891332db85, plugin
608ef5b035ba2d13a1246d4d731aa525ce04ff6f, signed spec map-draft-5 (mapping_sha256
c0b93dad9526fc8f02df6b8199436d76da9f938a05ccadc98ab3adb7a35202a7; runtime `SPEC_SHA256` matches).
Local evidence, not merge evidence. This replaces the first sweep (base 66e6ff7).

## Bottom line

- PostgreSQL: 3,383 tests, 34 fail or error (15 fail, 19 error).
- MongoDB: 2,902 tests run, 140 fail or error (86 fail, 54 error). Classified: (a) also fails on PostgreSQL 24,
  (b) accepted Studio field 4, (c) unit-owned addon raw SQL 69, (d) environment load 3, (e) storage-path gap 40.
- (e) is 7 families, E1-E7 below. They go back to the storage worker; none was fixed here.
- The first-sweep gaps G1-G5 and G7 no longer occur (0 log hits for their errors). G6 remains as E1.
- The strict layout (PostgreSQL keeps only the declared shadow columns) still cannot load the scope: U1, class (c).

## How it ran

- Every run used a fresh `createdb -T` copy of a template cloned from `odoo_fixture` (never `odoo_src`), then
  `odoo-bin -u <addon> --test-enable --test-tags /<addon> --stop-after-init` on that copy, one process at a time,
  PostgreSQL then MongoDB, so no two test HTTP servers ever ran together.
- MongoDB: local `mongo:7` on localhost (never Atlas), database `odoo_unt13`, each copy in its own collection prefix.
  Every model whose table the signed spec maps (76 models, 71 collections, 22,757 documents seeded from the copy's
  own rows through the storage path's encoders) was opted in to `_storage = 'mongodb'` by an uncommitted local hook.
- Because of U1 the MongoDB runs kept every stored column mirrored in PostgreSQL as a shadow column (uncommitted
  local hook), so raw SQL still runs against PostgreSQL rows and failures isolate the ORM-to-MongoDB path.
- A failure counts as (d) only if the same test, re-run alone on a fresh copy, passes. 13 suspects were re-run; 3 passed.
- MongoDB run counts are lower for product, purchase, stock, stock_account and purchase_stock because a
  `setUpClass` error (mostly E1) aborts the whole class before it counts any test.

## Pass/fail per addon

| Addon | PostgreSQL | MongoDB | MongoDB failures by class |
|---|---|---|---|
| uom | FAIL 0 run, 0 fail, 1 err | FAIL 0 run, 0 fail, 1 err | (a) 1 |
| product | FAIL 155 run, 1 fail, 0 err | FAIL 136 run, 1 fail, 3 err | (a) 1, E1 3 |
| account | FAIL 1154 run, 2 fail, 5 err | FAIL 1154 run, 70 fail, 12 err | (a) 7, C1 65, C2 1, C3 1, C4 1, D 1, E2 2, E3 1, E4 1, E6 2 |
| purchase | FAIL 124 run, 1 fail, 0 err | FAIL 123 run, 3 fail, 1 err | (a) 1, E1 1, E6 2 |
| stock | FAIL 703 run, 6 fail, 6 err | FAIL 363 run, 4 fail, 10 err | (a) 4, C5 1, E1 7, E7 2 |
| sale | FAIL 293 run, 1 fail, 0 err | FAIL 293 run, 3 fail, 2 err | (a) 1, E1 2, E6 2 |
| stock_account | pass 240 run, 0 fail, 0 err | FAIL 195 run, 0 fail, 1 err | D 1 |
| purchase_stock | FAIL 231 run, 1 fail, 2 err | FAIL 155 run, 2 fail, 14 err | (a) 1, E1 13, E5 1, E6 1 |
| sale_stock | FAIL 178 run, 1 fail, 0 err | FAIL 178 run, 1 fail, 1 err | (a) 1, D 1 |
| sale_purchase | pass 13 run, 0 fail, 0 err | pass 13 run, 0 fail, 0 err | - |
| sale_purchase_stock | pass 24 run, 0 fail, 0 err | pass 24 run, 0 fail, 0 err | - |
| account_payment | FAIL 31 run, 0 fail, 1 err | FAIL 31 run, 0 fail, 1 err | (a) 1 |
| account_edi_ubl_cii | FAIL 227 run, 2 fail, 1 err | FAIL 227 run, 2 fail, 5 err | (a) 3, B 4 |
| account_qr_code_sepa | FAIL 4 run, 0 fail, 3 err | FAIL 4 run, 0 fail, 3 err | (a) 3 |
| sale_edi_ubl | pass 1 run, 0 fail, 0 err | pass 1 run, 0 fail, 0 err | - |
| purchase_edi_ubl_bis3 | pass 5 run, 0 fail, 0 err | pass 5 run, 0 fail, 0 err | - |
| l10n_us_account | pass 0 run, 0 fail, 0 err | pass 0 run, 0 fail, 0 err | - |
| sale_sms | pass 0 run, 0 fail, 0 err | pass 0 run, 0 fail, 0 err | - |
| stock_sms | pass 0 run, 0 fail, 0 err | pass 0 run, 0 fail, 0 err | - |

Totals: PostgreSQL 3,383 run, 15 fail, 19 error. MongoDB 2,902 run, 86 fail, 54 error.
The 10 PostgreSQL failures not in (a) are not MongoDB failures (their classes passed or did not run on MongoDB).

## (e) Storage-path gaps (40, for the storage worker)

| Gap | Count | Where it breaks | Example test | Minimal repro |
|---|---|---|---|---|
| E1 | 26 | NOT NULL left on a shadow column whose field comes from a later module: `product_template.invoice_policy` (sale) and `sale_order.picking_policy` (sale_stock). `models.py:2543` hands MongoDB models to `storage_mongodb.auto_init` (`storage_mongodb.py:532`) and returns before `_check_removed_columns` (`models.py:2585`), which on PostgreSQL drops NOT NULL on columns with no loaded field. Seen here because every column is mirrored; it applies to any required shadow column a later module adds. | `product: setUpClass (TestProductPricelist)` | `odoo-bin -u product --test-tags /product:TestProductPricelist` on the MongoDB copy: `NotNullViolation ... "invoice_policy"`; passes on the PostgreSQL copy |
| E6 | 7 | `storage_mongodb.py:1540` `_groupby_expr`: `cannot group by 'product_tag_ids' on MongoDB storage yet` (many2many group-by). Raised by the product catalog search panel (`web/models/models.py:1708` `_search_panel_domain_image`), so every catalog tour stops at its first kanban step. All 7 also fail alone. | `sale: TestSaleOrderProductCatalog.test_add_section_from_product_catalog_on_sale_order_tour` | `env['product.template']._read_group([], ['product_tag_ids'], ['__count'])`: PostgreSQL returns `[(product.tag(1,), 47), ...]`, MongoDB raises `NotImplementedError` |
| E2 | 2 | Partner merge: `odoo/addons/base/wizard/base_partner_merge.py:150-190` rewrites foreign keys with raw SQL (register rows 21-24, disposition A, so the storage path owns it). The MongoDB `account.payment` documents keep the old partner / bank id and the unlink raises `ForeignKeyViolation: res.partner(887,) is still referenced by account.payment.partner_id` at `storage_mongodb.py:222` `unlink_dependents`. | `account: TestMergePartner.test_merge_partners_with_bank_accounts_linked_to_payments` | `--test-tags /account:TestMergePartner` on the MongoDB copy |
| E7 | 2 | `product.template` default order `is_favorite desc, name` is not honoured: a new favourite product is not on the first kanban page. Both tours also fail alone. | `stock: TestStockReportTour.test_forecast_replenishment` | create `{'name': 'Lovely Product', 'is_storable': True, 'is_favorite': True}`, then `search([('type', '=', 'consu')], limit=80)`: PostgreSQL has it first; MongoDB does not have it in the 80 (of 276) |
| E3 | 1 | `storage_mongodb.py:1413` `read_group`: `TypeError: unhashable type: 'dict'` building the group key when grouping `account.move.line` by the JSON `analytic_distribution` (`account/models/account_analytic_account.py:21` `_compute_invoice_count`). | `account: TestAccountAnalyticAccount.test_cross_analytics_computing` | `--test-tags /account:TestAccountAnalyticAccount.test_cross_analytics_computing` on the MongoDB copy (needs posted lines with a distribution; fixture rows have none) |
| E4 | 1 | Query-shape only: reading `reconciled_lines_ids` returns the right lines (the inner `assertEqual` passes), but sends three `SELECT id FROM ... WHERE id IN %s` shadow lookups instead of the four PostgreSQL reads the test pins, so `assertQueries` fails. The storage worker decides whether this needs a change or a storage-aware expectation. | `account: TestAccountMoveReconcile.test_perf_reconciled_lines_ids` | `--test-tags /account:TestAccountMoveReconcile.test_perf_reconciled_lines_ids` |
| E5 | 1 | Deleting a selection value (`force_delete`) resets the column with raw SQL in base `odoo/addons/base/models/ir_model.py:2005` (`_process_ondelete`). Only PostgreSQL changes; MongoDB keeps `'stock_moves'`. Framework code with no dependency-register entry, so not unit-owned. | `purchase_stock: TestUninstallPurchaseStock.test_qty_received_method` | `--test-tags /purchase_stock:TestUninstallPurchaseStock.test_qty_received_method` |

Tests per family:
- E1: product: `setUpClass (TestPricelistAutoCreation)`; product: `setUpClass (TestProductCombo)`; product: `setUpClass (TestProductPricelist)`; purchase: `setUpClass (TestPurchaseWithoutStock)`; stock: `setUpClass (TestStockMove)`; stock: `setUpClass (TestSinglePicking)`; stock: `setUpClass (TestOldRules)`; stock: `setUpClass (TestProcRule)`; stock: `setUpClass (TestReports)`; stock: `setUpClass (TestStockFlow)`; stock: `setUpClass (TestWarehouse)`; sale: `TestSaleFlow.test_qty_delivered`; sale: `TestSaleFlow.test_so_is_delivered_when_consumable_lines_are_delivered`; purchase_stock: `setUpClass (TestCreatePicking)`; purchase_stock: `setUpClass (TestMoveCancelPropagation)`; purchase_stock: `setUpClass (TestPurchaseOldRules)`; purchase_stock: `TestOnchangeProductId.test_onchange_product_id`; purchase_stock: `TestProductTemplate.test_name_search`; purchase_stock: `TestProductTemplate.test_product_purchase_method_with_purchase_as_default_purchase_method`; purchase_stock: `TestProductTemplate.test_product_purchase_method_with_receive_as_default_purchase_method`; purchase_stock: `setUpClass (TestDeleteOrder)`; purchase_stock: `setUpClass (TestPurchaseLeadTime)`; purchase_stock: `setUpClass (TestPurchaseStockReports)`; purchase_stock: `setUpClass (TestReplenishWizard)`; purchase_stock: `TestRoutes.test_po_final_location`; purchase_stock: `setUpClass (TestSupplier)`
- E6: account: `TestUi.test_add_section_from_product_catalog_on_invoice_tour`; account: `TestUi.test_use_product_catalog_on_invoice`; purchase: `TestPurchaseOrderProductCatalog.test_add_section_from_product_catalog_on_purchase_order_tour`; purchase: `TestPurchaseProductCatalog.test_catalog_vendor_uom`; sale: `TestSaleOrderProductCatalog.test_add_section_from_product_catalog_on_sale_order_tour`; sale: `TestSaleOrderProductCatalog.test_sale_order_product_catalog_branch_company_tour`; purchase_stock: `TestPurchaseOrderSuggest.test_purchase_order_suggest_search_panel_ux`
- E2: account: `TestMergePartner.test_merge_partners_with_bank_accounts_linked_to_payments`; account: `TestMergePartner.test_merge_partners_with_duplicate_bank_accounts_linked_to_payments`
- E7: stock: `TestStockReportTour.test_context_from_warehouse_filter`; stock: `TestStockReportTour.test_forecast_replenishment`
- E3: account: `TestAccountAnalyticAccount.test_cross_analytics_computing`
- E4: account: `TestAccountMoveReconcile.test_perf_reconciled_lines_ids`
- E5: purchase_stock: `TestUninstallPurchaseStock.test_qty_received_method`

## (d) Environment load (3, each passed when re-run alone)

All three first failed with the MongoDB driver's `_OperationCancelled: operation cancelled` inside a storage write
(`storage_mongodb.py:982` `insert`, `:889` `_update_children`) during the full run. Re-run alone on a fresh copy with
`odoo-bin -u <addon> --test-enable --test-tags /<addon>:<test> --stop-after-init`:

| Test | Re-run alone |
|---|---|
| `account: TestAccountEarlyPaymentDiscount.test_mixed_epd_with_tax_refund` | `0 failed, 0 error(s) of 1 tests` |
| `sale_stock: TestSaleExpectedDate.test_invoice_delivery_date` | `0 failed, 0 error(s) of 1 tests` |
| `stock_account: setUpClass (TestLotValuation)` | `0 failed, 0 error(s) of 45 tests` |

The other 10 re-runs still failed alone and are classified elsewhere: the 9 tours (E6, E7) and
`sale_stock: TestReturnOrderController.test_download_label_logs_chatter_message` (a).

## (c) Unit-owned addon raw SQL (69, for the unit tickets)

Each is addon raw SQL with disposition B (unit owns it) in the dependency register of `.migration/NOTES.md`.
The SQL changes PostgreSQL rows only, and the MongoDB-backed ORM then reads the old values.

| Id | Count | Unit | Raw SQL (file:line) | Register entry | What fails |
|---|---|---|---|---|---|
| C1 | 65 | account | `addons/account/models/account_full_reconcile.py:30`, `:39`; `addons/account/models/account_partial_reconcile.py:226` | sql rows 7 (`account.full.reconcile.create`, account_move_line w), 8 (same, account_partial_reconcile w), 9 (`account.partial.reconcile._update_matching_number`, account_move_line w) | `full_reconcile_id` and `matching_number` read back `False`. Repro: reconcile two receivable lines, then read them: PostgreSQL ORM `('43', 43)`; MongoDB ORM `(False, False)` while its PostgreSQL row holds `('P79', 43)` |
| C2 | 1 | account | `addons/account/models/account_move.py:4548` | sql row 106 (`account.move._get_frequent_account_and_taxes`) | `UndefinedTable: missing FROM-clause entry for table "account_move_line__account_id"`. The addon SQL names the alias that PostgreSQL `_search` creates when it joins `account_id` for the domain; MongoDB `_search` (`storage_mongodb.py:1302`) answers with an id-list query that has no joins, by design. Kept in (c) because the register marks this SQL unit-owned: the account unit has to stop relying on that internal alias. The storage worker may disagree; flagged for routing |
| C3 | 1 | account | `addons/account/models/account_account.py:1341`, `:1362`, `:1441`, `:1472` | sql rows 2-5 (`account.account._action_unmerge`) | `tax_ids` / `tag_ids` of the unmerged accounts differ from PostgreSQL |
| C4 | 1 | account | `addons/account/wizard/account_merge_wizard.py:185`, `:197`, `:209` | sql rows 12-14 (`account.merge.wizard._action_merge`) | merged account keeps both accounts' links (`tax_ids` `[207, 216]` vs `[207]`) |
| C5 | 1 | stock | `addons/stock/models/stock_quant.py:1251` | sql row 20 (`stock.quant._merge_quants`) | duplicate quants not merged: `0.0 != 1` |

U1 (stock, not a test failure): with the strict layout, `-u` of the scope stops loading the registry (prep exit 255):
the SQL view at `addons/stock/report/report_stock_quantity.py:194` (sql row 240, view row 8 `report.stock.quantity`,
both B) reads `stock_location.parent_path`, which is not a shadow column.

Tests per family:
- C1: account: `TestAccountMoveOutInvoiceOnchanges.test_date_reversal_exchange_move` x2; account: `TestAccountMovePaymentsWidget.test_payments_with_exchange_difference_invoice_with_caba`; account: `TestAccountMovePaymentsWidget.test_payments_with_exchange_difference_payment_with_caba`; account: `TestAccountMoveReconcile.test_caba_dest_acc_reconciliation_partial_pmt`; account: `TestAccountMoveReconcile.test_caba_mix_reconciliation`; account: `TestAccountMoveReconcile.test_caba_undo_reconciliation`; account: `TestAccountMoveReconcile.test_full_reconcile_bunch_lines` x4; account: `TestAccountMoveReconcile.test_full_reconcile_foreign_currency_rounding_difference_credit_larger`; account: `TestAccountMoveReconcile.test_full_reconcile_foreign_currency_rounding_difference_debit_larger`; account: `TestAccountMoveReconcile.test_full_reconcile_unlink_clears_matching_number`; account: `TestAccountMoveReconcile.test_matching_loop`; account: `TestAccountMoveReconcile.test_matching_number_full_reconcile`; account: `TestAccountMoveReconcile.test_matching_number_partial_multi_reconcile`; account: `TestAccountMoveReconcile.test_matching_number_partial_multi_separate_reconcile`; account: `TestAccountMoveReconcile.test_matching_number_partial_single_reconcile`; account: `TestAccountMoveReconcile.test_matching_number_unreconcile_multi`; account: `TestAccountMoveReconcile.test_modify_all_reconciled_lines`; account: `TestAccountMoveReconcile.test_partial_reconcile_amounts_of_several_matching_lines`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_exchange_difference_transfer_account_check_entries_1`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_exchange_difference_transfer_account_check_entries_2`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_exchange_difference_transfer_account_check_entries_3`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_revert`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_tax_grid_multi_taxes`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_workflow_multi_currency`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_workflow_single_currency`; account: `TestAccountMoveReconcile.test_reconcile_draft_cash_basis_surprise_use_case`; account: `TestAccountMoveReconcile.test_reconcile_draft_cash_basis_use_case`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_credit_foreign_currency_credit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_credit_foreign_currency_credit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_credit_foreign_currency_debit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_credit_foreign_currency_debit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_debit_foreign_currency_credit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_debit_foreign_currency_credit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_debit_foreign_currency_debit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_debit_foreign_currency_debit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_same_foreign_currency_credit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_same_foreign_currency_credit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_same_foreign_currency_debit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_same_foreign_currency_debit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_foreign_currency_rounding_issue` x4; account: `TestAccountMoveReconcile.test_reconcile_import`; account: `TestAccountMoveReconcile.test_reconcile_import_same_matching_different_account`; account: `TestAccountMoveReconcile.test_reconcile_lines_corner_case_1_zero_balance_same_foreign_currency`; account: `TestAccountMoveReconcile.test_reconcile_lines_corner_case_2_zero_amount_currency_same_foreign_currency`; account: `TestAccountMoveReconcile.test_reconcile_lines_corner_case_3_zero_balance_one_foreign_currency`; account: `TestAccountMoveReconcile.test_reconcile_lines_multiple_in_foreign_currency` x8; account: `TestAccountMoveReconcile.test_reconcile_partial_reconciliations`; account: `TestAccountMoveReconcile.test_reconcile_special_mexican_workflow_1`; account: `TestAccountMoveReconcile.test_reconcile_special_mexican_workflow_2`; account: `TestAccountMoveReconcile.test_reverse_with_multiple_lines`; account: `TestTransferWizard.test_change_period_reconcile_pair_by_pair_customer_invoices`
- C2: account: `TestAccountMoveOutInvoiceOnchanges.test_quick_edit_total_amount`
- C3: account: `TestAccountAccount.test_unmerge`
- C4: account: `TestAccountMergeWizard.test_merge`
- C5: stock: `TestInventory.test_inventory_7`

## (b) Accepted by the user (4)

`StorageError: account.move: column 'x_studio_peppol_tax_point_date' is not in the signed mapping of 'account_move'`
(`storage_mongodb.py:115` `_layout`): account_edi_ubl_cii: `TestAccountEdiUblCii.test_credit_note_optional_fields`; account_edi_ubl_cii: `TestAccountEdiUblCii.test_invoice_optional_fields`; account_edi_ubl_cii: `TestUblImportBis3InvoiceBEOptionalFields.test_import_credit_note_with_optional_fields`; account_edi_ubl_cii: `TestUblImportBis3InvoiceBEOptionalFields.test_import_invoice_optional_fields`

## (a) Also fail on PostgreSQL (24)

Environment, same on both storages: no PDF engine or `rlPyCairo` renderer, cloned databases without a filestore copy,
and tests that run before later modules load (`uom` `setUpClass`: `res_partner.autopost_bills` NOT NULL; fiscal lock dates).
uom: `setUpClass (TestUom)`; product: `TestImportFiles.test_import_create_product_demo_xls [product.pricelist]`; account: `TestAccountAccount.test_compute_account_type_on_code_change`; account: `TestAuditTrailAttachment.test_audit_trail_attachment`; account: `TestAuditTrailAttachment.test_audit_trail_write_attachment`; account: `setUpClass (TestAccountDigest)`; account: `TestAccountEarlyPaymentDiscount.test_invoice_report_without_invoice_date`; account: `setUpClass (TestKpiProvider)`; account: `TestSequenceMixin.test_journal_sequence_format`; purchase: `TestImportFiles.test_import_requests_for_quotation_template_xlsx`; stock: `TestBatchPicking02.test_batch_validation_without_backorder`; stock: `TestBatchPicking02.test_same_package_several_pickings`; stock: `TestStockPickingTour.test_inventory_adjustment_apply_all`; stock: `TestStockQuant.test_relocate`; sale: `TestImportFiles.test_import_quotation_template_xlsx`; purchase_stock: `TestReorderingRule.test_2steps_and_partner_on_orderpoint`; sale_stock: `TestReturnOrderController.test_download_label_logs_chatter_message`; account_payment: `TestAccountPayment.test_generate_and_send_invoice_with_qr_code`; account_edi_ubl_cii: `CiiExportFacturXFR.test_invoice_deferred_dates`; account_edi_ubl_cii: `TestUblImportBis3InvoiceBE.test_generate_pdf_when_xml_does_not_provide_one`; account_edi_ubl_cii: `TestUblImportBis3InvoiceBEAutoGeneratePDF.test_import_invoice_auto_generate_pdf`; account_qr_code_sepa: `TestSEPAQRCode.test_out_invoice_create_refund_qr_code`; account_qr_code_sepa: `TestSEPAQRCode.test_sepa_qr_code_detection`; account_qr_code_sepa: `TestSEPAQRCode.test_sepa_qr_code_generation`

## Plugin findings

- P2 `hooks/mongo_guard.py:95` (`DB_NAME`, plugin 608ef5b): the `use\s+` alternative has no word boundary, so plain
  words such as "because the" read as `use the`, a MongoDB database named `the`. With the driver package name
  (`MONGO_TOOL`, line 74) and a write verb in the same text, a local notes-file write was refused as "'the' is not in
  the committed allowed_targets.json databases"; without "because" the same text was refused as "MongoDB write does
  not name its database". Repro: `python3 -c "import sys; open('notes.md','w').write(sys.stdin.read())"` fed a
  heredoc that names the driver package, says "updates" and "because the". No MongoDB write was involved.
- P1 from the first sweep (`-d` of `odoo-bin` read as a MongoDB database, same line 95) is unchanged at 608ef5b.
