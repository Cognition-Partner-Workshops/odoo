# Migration notes

## s2.3 dependency register (other writers and readers)

Built fresh on odoo_src at marker v4 (row_counts_sha256 `a100e84ee2fb6282f30b45c003fd1db47561317c739340a10564d9e869e56a4e`, 521 tables, 70 installed modules) from AST scans of the source tree at SOURCE_COMMIT plus catalog reads; in scope = the 223 `in_scope` tables of `.migration/table_buckets.json`. Generators: `.migration/register_db.py` (read-only catalog facts, refuses on a fingerprint mismatch), `.migration/register_probe.py` (rendered `_table_sql` on a throwaway clone), `.migration/register_scan.py` (AST), `.migration/register_notes.py` (this section).

Dispositions: **A** storage path handles it; **B** unit owns it (the unit that migrates the first-moved table it names; every later unit naming it re-checks it); **C** out of estate.

### Coverage

Entry points scanned in every non-test .py file of the 70 installed modules and the core (`odoo/` outside `odoo/addons`): cursor `execute`, `execute_values`, `executemany`, `copy_expert`/`copy_from`/`copy_to`, `mogrify`; `env.execute_query`/`execute_query_dict`; `psycopg2.extras.execute_values`; every `odoo.tools.sql` helper that takes a table (`create_index`, `column_exists`, `drop_view_if_exists`, `add_foreign_key`, `increment_fields_skiplock`, ...); `SQL(...)` fragments built outside a cursor call (search/order/compute overrides); `_auto = False` models (`_table_sql`/`_table_query` rendered from the registry, `init()` views from `pg_rewrite`); `ir_cron` and code server actions; triggers, functions, views and foreign keys from the catalog. Tables come from literal names in the SQL text, `self._table`/`env[m]._table` resolved through the class's model (abstract mixins expand to every stored model inheriting them), and for SQL built from ORM `Query`/`TableSQL` objects the function's `env[...]` models or the class's model. `SELECT ... FOR UPDATE` is a lock, not a write. Sites that name no in-scope table are counted, not listed: 481 fragment, 55 helper, 365 sql; `addons/account/models/account_account.py:1391`: reference columns, resolved at run time; `addons/account/models/account_account.py:1420`: reference columns, resolved at run time; `addons/account/models/account_account.py:1490`: XMLID remap in ir_model_data; no in-scope table; `odoo/addons/base/wizard/base_partner_merge.py:280`: ir_default company-dependent fallback; no in-scope table.

### Raw SQL writes into in-scope tables (26)

| # | disp | kind | site | function | in-scope tables (w = written) | note |
|---|---|---|---|---|---|---|
| 1 | C | upgrade_script | `addons/account/migrations/1.5/pre-migrate.py:2` | `-.migrate` | account_account (w) | upgrade script: runs only on -u from an older module version |
| 2 | B | sql | `addons/account/models/account_account.py:1341` | `account.account._action_unmerge` | 18 tables (18 written) | dynamic table; FK fan-out of account_account: 18 in-scope tables (catalog FKs; Reference/res_id columns not included) |
| 3 | B | sql | `addons/account/models/account_account.py:1362` | `account.account._action_unmerge` | account_cash_rounding (w), product_category (w), product_template (w) | dynamic table; company-dependent Many2one JSONB values to account.account: account.cash.rounding (account_cash_rounding): loss_account_id, profit_account_id; product.category (product_category): property_account_billed_not_received_id, property_account_bills_to_receive_id, property_account_expense_categ_id, property_account_income_categ_id, property_account_invoiced_not_delivered_id, property_account_invoices_to_issue_id, property_price_difference_account_id, property_stock_valuation_account_id; product.template (product_template): property_account_expense_id, property_account_income_id; res.partner (res_partner, out of scope): property_account_payable_id, property_account_receivable_id; no catalog FKs |
| 4 | B | sql | `addons/account/models/account_account.py:1441` | `account.account._action_unmerge` | account_account (w) | dynamic table; company-dependent JSONB field account.account.code_store (account_account) |
| 5 | B | sql | `addons/account/models/account_account.py:1472` | `account.account._action_unmerge` | account_account (w) | dynamic table; company-dependent JSONB field account.account.code_store (account_account) |
| 6 | B | sql | `addons/account/models/account_account_tag.py:125` | `account.account.tag._translate_tax_tags` | account_account_tag (w), account_report, account_report_line |  |
| 7 | B | sql | `addons/account/models/account_full_reconcile.py:30` | `account.full.reconcile.create` | account_move_line (w) |  |
| 8 | B | sql | `addons/account/models/account_full_reconcile.py:39` | `account.full.reconcile.create` | account_partial_reconcile (w) |  |
| 9 | B | sql | `addons/account/models/account_partial_reconcile.py:226` | `account.partial.reconcile._update_matching_number` | account_move_line (w) |  |
| 10 | B | sql | `addons/account/models/sequence_mixin.py:56` | `sequence.mixin.init` | account_move (w) | dynamic table |
| 11 | B | sql | `addons/account/models/sequence_mixin.py:415` | `sequence.mixin._locked_increment` | account_move (w) | dynamic table |
| 12 | B | sql | `addons/account/wizard/account_merge_wizard.py:185` | `account.merge.wizard._action_merge` | account_account (w) |  |
| 13 | B | sql | `addons/account/wizard/account_merge_wizard.py:197` | `account.merge.wizard._action_merge` | account_account (w) |  |
| 14 | B | sql | `addons/account/wizard/account_merge_wizard.py:209` | `account.merge.wizard._action_merge` | account_account (w) |  |
| 15 | A | sql | `addons/analytic/models/analytic_mixin.py:40` | `analytic.mixin.init` | account_move_line (w), account_reconcile_model_line (w), purchase_order_line (w), sale_order_line (w) | generic code; table resolved per model (4 in-scope tables) |
| 16 | A | sql | `addons/mail/models/mail_thread.py:3109` | `mail.thread.set_message_pin` | 12 tables (12 written) | generic code; table resolved per model (12 in-scope tables) |
| 17 | B | sql | `addons/purchase_stock/models/purchase_order_line.py:24` | `purchase.order.line._ondelete_stock_moves` | purchase_order_line (w) | dynamic table |
| 18 | B | sql | `addons/sale_stock/models/sale_order.py:67` | `sale.order._init_column_warehouse_id` | sale_order (w), stock_warehouse |  |
| 19 | B | sql | `addons/stock/__init__.py:92` | `-._save_current_inventory` | product_product (w) |  |
| 20 | B | sql | `addons/stock/models/stock_quant.py:1251` | `stock.quant._merge_quants` | stock_quant (w) |  |
| 21 | A | sql | `odoo/addons/base/wizard/base_partner_merge.py:150` | `base.partner.merge.automatic.wizard._update_foreign_keys_generic` | 39 tables (39 written) | generic core FK fan-out; FK fan-out of account_account: 18 in-scope tables (catalog FKs; Reference/res_id columns not included); FK fan-out of res_partner: 24 in-scope tables (catalog FKs; Reference/res_id columns not included); FK fan-out of res_partner_bank: 5 in-scope tables (catalog FKs; Reference/res_id columns not included) |
| 22 | A | sql | `odoo/addons/base/wizard/base_partner_merge.py:170` | `base.partner.merge.automatic.wizard._update_foreign_keys_generic` | 39 tables (39 written) | generic core FK fan-out; FK fan-out of account_account: 18 in-scope tables (catalog FKs; Reference/res_id columns not included); FK fan-out of res_partner: 24 in-scope tables (catalog FKs; Reference/res_id columns not included); FK fan-out of res_partner_bank: 5 in-scope tables (catalog FKs; Reference/res_id columns not included) |
| 23 | A | sql | `odoo/addons/base/wizard/base_partner_merge.py:180` | `base.partner.merge.automatic.wizard._update_foreign_keys_generic` | 39 tables (39 written) | generic core FK fan-out; FK fan-out of account_account: 18 in-scope tables (catalog FKs; Reference/res_id columns not included); FK fan-out of res_partner: 24 in-scope tables (catalog FKs; Reference/res_id columns not included); FK fan-out of res_partner_bank: 5 in-scope tables (catalog FKs; Reference/res_id columns not included) |
| 24 | A | sql | `odoo/addons/base/wizard/base_partner_merge.py:190` | `base.partner.merge.automatic.wizard._update_foreign_keys_generic` | 39 tables (39 written) | generic core FK fan-out; FK fan-out of account_account: 18 in-scope tables (catalog FKs; Reference/res_id columns not included); FK fan-out of res_partner: 24 in-scope tables (catalog FKs; Reference/res_id columns not included); FK fan-out of res_partner_bank: 5 in-scope tables (catalog FKs; Reference/res_id columns not included) |
| 25 | A | sql | `odoo/addons/base/wizard/base_partner_merge.py:258` | `base.partner.merge.automatic.wizard._update_reference_fields_generic` | account_cash_rounding (w), product_category (w), product_template (w) | generic core merge update; company-dependent Many2one JSONB values to merged models: account.cash.rounding (account_cash_rounding): loss_account_id, profit_account_id; product.category (product_category): property_account_billed_not_received_id, property_account_bills_to_receive_id, property_account_expense_categ_id, property_account_income_categ_id, property_account_invoiced_not_delivered_id, property_account_invoices_to_issue_id, property_price_difference_account_id, property_stock_valuation_account_id; product.template (product_template): property_account_expense_id, property_account_income_id; res.partner (res_partner, out of scope): property_account_payable_id, property_account_receivable_id; no catalog FKs |
| 26 | A | sql | `odoo/addons/base/wizard/base_partner_merge.py:307` | `base.partner.merge.automatic.wizard._update_reference_fields_generic` | account_account (w) | generic core merge update; company-dependent fields on merged records: account.account (account_account): code_store; res.partner (res_partner, out of scope): barcode, credit_limit, ignore_abnormal_invoice_amount, ignore_abnormal_invoice_date, invoice_edi_format_store, invoice_sending_method, property_account_payable_id, property_account_position_id, property_account_receivable_id, property_inbound_payment_method_line_id, property_outbound_payment_method_line_id, property_payment_term_id, property_purchase_currency_id, property_stock_customer, property_stock_supplier, property_supplier_payment_term_id, qr_code_method, receipt_reminder_email, reminder_date_before_receipt, specific_property_product_pricelist, trust |

### Raw SQL reads of in-scope tables (247)

| # | disp | kind | site | function | in-scope tables (w = written) | note |
|---|---|---|---|---|---|---|
| 1 | B | sql | `addons/account/models/account_account.py:191` | `account.account._check_journal_consistency` | account_account, account_journal, account_payment_method, account_payment_method_line |  |
| 2 | B | sql | `addons/account/models/account_account.py:275` | `account.account._check_account_type_sales_purchase_journal` | account_account, account_journal |  |
| 3 | B | sql | `addons/account/models/account_account.py:301` | `account.account._check_account_is_bank_journal_bank_account` | account_account, account_journal |  |
| 4 | B | fragment | `addons/account/models/account_account.py:361` | `account.account._compute_sql_placeholder_code` | account_account_res_company_rel |  |
| 5 | B | fragment | `addons/account/models/account_account.py:377` | `account.account._compute_sql_placeholder_code` | account_account | dynamic table |
| 6 | B | fragment | `addons/account/models/account_account.py:381` | `account.account._compute_sql_placeholder_code` | account_account | dynamic table |
| 7 | B | fragment | `addons/account/models/account_account.py:400` | `account.account._search_placeholder_code` | account_account |  |
| 8 | B | fragment | `addons/account/models/account_account.py:402` | `account.account._search_placeholder_code` | account_account |  |
| 9 | B | fragment | `addons/account/models/account_account.py:424` | `account.account._compute_sql_field_path` | account_account |  |
| 10 | B | fragment | `addons/account/models/account_account.py:440` | `account.account._compute_sql_field_path` | account_account | dynamic table |
| 11 | B | fragment | `addons/account/models/account_account.py:451` | `account.account._compute_sql_account_root` | account_account | dynamic table |
| 12 | B | sql | `addons/account/models/account_account.py:486` | `account.account._search_panel_domain_image` | account_account |  |
| 13 | B | fragment | `addons/account/models/account_account.py:500` | `account.account._compute_sql_used` | account_move_line | dynamic table |
| 14 | B | fragment | `addons/account/models/account_account.py:501` | `account.account._compute_sql_used` | account_move_line | dynamic table |
| 15 | B | fragment | `addons/account/models/account_account.py:612` | `account.account._compute_sql_company_currency_id` | account_account | dynamic table |
| 16 | B | sql | `addons/account/models/account_account.py:623` | `account.account._compute_opening_debit_credit` | account_move_line |  |
| 17 | B | fragment | `addons/account/models/account_account.py:708` | `account.account._compute_sql_internal_group` | account_account | dynamic table |
| 18 | B | fragment | `addons/account/models/account_account.py:798` | `account.account._get_most_frequent_accounts_for_partner` | account_move_line | dynamic table |
| 19 | B | sql | `addons/account/models/account_account.py:800` | `account.account._get_most_frequent_accounts_for_partner` | account_move_line | dynamic table |
| 20 | B | fragment | `addons/account/models/account_account.py:806` | `account.account._order_to_sql` | account_account | dynamic table |
| 21 | B | fragment | `addons/account/models/account_account.py:814` | `account.account._order_to_sql` | account_account | dynamic table |
| 22 | B | fragment | `addons/account/models/account_account.py:822` | `account.account._order_to_sql` | account_account | dynamic table |
| 23 | B | fragment | `addons/account/models/account_account.py:987` | `account.account._search` | account_account |  |
| 24 | B | fragment | `addons/account/models/account_account.py:1287` | `account.account._get_query_company_id` | account_account | dynamic table |
| 25 | B | fragment | `addons/account/models/account_account.py:1288` | `account.account._get_query_company_id` | account_account | dynamic table |
| 26 | B | sql | `addons/account/models/account_account_tag.py:43` | `account.account.tag._compute_report_expression_id` | account_account_tag | dynamic table |
| 27 | B | fragment | `addons/account/models/account_account_tag.py:54` | `account.account.tag._join_report_expression` | account_report_expression | dynamic table |
| 28 | B | fragment | `addons/account/models/account_account_tag.py:67` | `account.account.tag._compute_sql_balance_negate` | account_account_tag | dynamic table |
| 29 | B | sql | `addons/account/models/account_bank_statement.py:331` | `account.bank.statement._get_invalid_statement_ids` | account_bank_statement, account_journal |  |
| 30 | B | sql | `addons/account/models/account_bank_statement_line.py:201` | `account.bank.statement.line._compute_running_balance` | account_bank_statement |  |
| 31 | B | fragment | `addons/account/models/account_bank_statement_line.py:218` | `account.bank.statement.line._compute_running_balance` | account_bank_statement, account_move | dynamic table |
| 32 | B | sql | `addons/account/models/account_bank_statement_line.py:223` | `account.bank.statement.line._compute_running_balance` | account_bank_statement, account_bank_statement_line, account_move |  |
| 33 | B | sql | `addons/account/models/account_journal.py:364` | `account.journal._get_journals_payment_method_information` | account_journal, account_payment_method, account_payment_method_line |  |
| 34 | B | sql | `addons/account/models/account_journal_dashboard.py:47` | `account.journal._compute_last_bank_statement` | account_bank_statement, account_journal |  |
| 35 | B | fragment | `addons/account/models/account_journal_dashboard.py:144` | `account.journal._get_sale_purchase_kpi_amounts` | account_move |  |
| 36 | B | sql | `addons/account/models/account_journal_dashboard.py:148` | `account.journal._get_sale_purchase_kpi_amounts` | account_move |  |
| 37 | B | sql | `addons/account/models/account_journal_dashboard.py:177` | `account.journal._get_cashflow_kpi_amount` | account_move_line | dynamic table |
| 38 | B | fragment | `addons/account/models/account_journal_dashboard.py:286` | `account.journal._get_json_activity_data` | account_journal, account_move |  |
| 39 | B | sql | `addons/account/models/account_journal_dashboard.py:329` | `account.journal._get_json_activity_data` | account_journal, account_move |  |
| 40 | B | fragment | `addons/account/models/account_journal_dashboard.py:349` | `account.journal._query_has_sequence_holes` | account_move |  |
| 41 | B | sql | `addons/account/models/account_journal_dashboard.py:364` | `account.journal._query_has_sequence_holes` | account_move | dynamic table |
| 42 | B | fragment | `addons/account/models/account_journal_dashboard.py:398` | `account.journal._compute_has_entries` | account_journal, account_move |  |
| 43 | B | sql | `addons/account/models/account_journal_dashboard.py:421` | `account.journal._compute_has_entries` | account_journal, account_move |  |
| 44 | B | sql | `addons/account/models/account_journal_dashboard.py:477` | `account.journal._get_bank_cash_graph_data` | account_bank_statement_line, account_move |  |
| 45 | B | sql | `addons/account/models/account_journal_dashboard.py:524` | `account.journal._get_sale_purchase_graph_data` | account_move |  |
| 46 | B | sql | `addons/account/models/account_journal_dashboard.py:646` | `account.journal._fill_bank_cash_dashboard_data` | account_bank_statement_line, account_move |  |
| 47 | B | sql | `addons/account/models/account_journal_dashboard.py:757` | `account.journal._fill_sale_purchase_dashboard_data` | account_move |  |
| 48 | B | fragment | `addons/account/models/account_journal_dashboard.py:761` | `account.journal._fill_sale_purchase_dashboard_data` | account_move |  |
| 49 | B | sql | `addons/account/models/account_journal_dashboard.py:765` | `account.journal._fill_sale_purchase_dashboard_data` | account_move |  |
| 50 | B | fragment | `addons/account/models/account_journal_dashboard.py:777` | `account.journal._fill_sale_purchase_dashboard_data` | account_move |  |
| 51 | B | sql | `addons/account/models/account_journal_dashboard.py:781` | `account.journal._fill_sale_purchase_dashboard_data` | account_move |  |
| 52 | B | sql | `addons/account/models/account_journal_dashboard.py:784` | `account.journal._fill_sale_purchase_dashboard_data` | account_journal, account_move |  |
| 53 | B | fragment | `addons/account/models/account_journal_dashboard.py:905` | `account.journal._get_bills_field_list` | account_move |  |
| 54 | B | fragment | `addons/account/models/account_journal_dashboard.py:906` | `account.journal._get_bills_field_list` | account_move |  |
| 55 | B | fragment | `addons/account/models/account_journal_dashboard.py:907` | `account.journal._get_bills_field_list` | account_move |  |
| 56 | B | fragment | `addons/account/models/account_journal_dashboard.py:908` | `account.journal._get_bills_field_list` | account_move |  |
| 57 | B | fragment | `addons/account/models/account_journal_dashboard.py:909` | `account.journal._get_bills_field_list` | account_move |  |
| 58 | B | fragment | `addons/account/models/account_journal_dashboard.py:910` | `account.journal._get_bills_field_list` | account_move |  |
| 59 | B | fragment | `addons/account/models/account_journal_dashboard.py:911` | `account.journal._get_bills_field_list` | account_move |  |
| 60 | B | fragment | `addons/account/models/account_journal_dashboard.py:923` | `account.journal._get_to_pay_select` | account_journal | dynamic table |
| 61 | B | fragment | `addons/account/models/account_journal_dashboard.py:937` | `account.journal._get_open_sale_purchase_query` | account_move | dynamic table |
| 62 | B | fragment | `addons/account/models/account_journal_dashboard.py:938` | `account.journal._get_open_sale_purchase_query` | account_move | dynamic table |
| 63 | B | fragment | `addons/account/models/account_journal_dashboard.py:939` | `account.journal._get_open_sale_purchase_query` | account_move | dynamic table |
| 64 | B | fragment | `addons/account/models/account_journal_dashboard.py:940` | `account.journal._get_open_sale_purchase_query` | account_move | dynamic table |
| 65 | B | fragment | `addons/account/models/account_journal_dashboard.py:941` | `account.journal._get_open_sale_purchase_query` | account_move | dynamic table |
| 66 | B | fragment | `addons/account/models/account_journal_dashboard.py:942` | `account.journal._get_open_sale_purchase_query` | account_move | dynamic table |
| 67 | B | fragment | `addons/account/models/account_journal_dashboard.py:943` | `account.journal._get_open_sale_purchase_query` | account_move | dynamic table |
| 68 | B | fragment | `addons/account/models/account_journal_dashboard.py:957` | `account.journal._get_to_check_payment_query` | account_move | dynamic table |
| 69 | B | fragment | `addons/account/models/account_journal_dashboard.py:958` | `account.journal._get_to_check_payment_query` | account_move | dynamic table |
| 70 | B | fragment | `addons/account/models/account_journal_dashboard.py:959` | `account.journal._get_to_check_payment_query` | account_move | dynamic table |
| 71 | B | fragment | `addons/account/models/account_journal_dashboard.py:960` | `account.journal._get_to_check_payment_query` | account_move | dynamic table |
| 72 | B | fragment | `addons/account/models/account_journal_dashboard.py:961` | `account.journal._get_to_check_payment_query` | account_move | dynamic table |
| 73 | B | fragment | `addons/account/models/account_journal_dashboard.py:962` | `account.journal._get_to_check_payment_query` | account_move | dynamic table |
| 74 | B | fragment | `addons/account/models/account_journal_dashboard.py:963` | `account.journal._get_to_check_payment_query` | account_move | dynamic table |
| 75 | B | fragment | `addons/account/models/account_journal_dashboard.py:964` | `account.journal._get_to_check_payment_query` | account_move | dynamic table |
| 76 | B | sql | `addons/account/models/account_journal_dashboard.py:1005` | `account.journal._get_journal_dashboard_bank_running_balance` | account_bank_statement, account_bank_statement_line, account_journal, account_move |  |
| 77 | B | sql | `addons/account/models/account_journal_dashboard.py:1048` | `account.journal._get_direct_bank_payments` | account_journal, account_move, account_payment |  |
| 78 | B | sql | `addons/account/models/account_journal_dashboard.py:1076` | `account.journal._get_journal_dashboard_outstanding_payments` | account_move, account_payment |  |
| 79 | B | fragment | `addons/account/models/account_move.py:878` | `account.move._compute_sql_move_sent_values` | account_move | dynamic table |
| 80 | B | fragment | `addons/account/models/account_move.py:895` | `account.move._compute_sql_sanitize_payment_reference` | account_move | dynamic table |
| 81 | B | fragment | `addons/account/models/account_move.py:1293` | `account.move._compute_payment_state` | account_account, account_move, account_move_line, account_partial_reconcile, account_payment |  |
| 82 | B | sql | `addons/account/models/account_move.py:1314` | `account.move._compute_payment_state` | account_partial_reconcile, account_payment | dynamic table |
| 83 | B | fragment | `addons/account/models/account_move.py:1379` | `account.move._compute_sql_status_in_payment` | account_move | dynamic table |
| 84 | B | fragment | `addons/account/models/account_move.py:2192` | `account.move._fetch_duplicate_reference` | account_move |  |
| 85 | B | fragment | `addons/account/models/account_move.py:2206` | `account.move._fetch_duplicate_reference` | account_move | dynamic table |
| 86 | B | fragment | `addons/account/models/account_move.py:2207` | `account.move._fetch_duplicate_reference` | account_move | dynamic table |
| 87 | B | fragment | `addons/account/models/account_move.py:2210` | `account.move._fetch_duplicate_reference` | account_move | dynamic table |
| 88 | B | fragment | `addons/account/models/account_move.py:2211` | `account.move._fetch_duplicate_reference` | account_move | dynamic table |
| 89 | B | fragment | `addons/account/models/account_move.py:2212` | `account.move._fetch_duplicate_reference` | account_move | dynamic table |
| 90 | B | sql | `addons/account/models/account_move.py:2218` | `account.move._fetch_duplicate_reference` | account_move |  |
| 91 | B | fragment | `addons/account/models/account_move.py:2250` | `account.move._get_duplicate_ref_sql_conditions` | account_move | dynamic table |
| 92 | B | fragment | `addons/account/models/account_move.py:2265` | `account.move._get_duplicate_ref_sql_conditions` | account_move | dynamic table |
| 93 | B | sql | `addons/account/models/account_move.py:2388` | `account.move._compute_abnormal_warnings` | account_move |  |
| 94 | B | sql | `addons/account/models/account_move.py:2508` | `account.move._compute_reconciled_payment_ids` | account_account, account_move, account_move_line, account_partial_reconcile, account_payment |  |
| 95 | B | sql | `addons/account/models/account_move.py:2954` | `account.move._get_unbalanced_moves` | account_move, account_move_line |  |
| 96 | B | fragment | `addons/account/models/account_move.py:4314` | `account.move._get_last_sequence_domain` | account_move | dynamic table |
| 97 | B | fragment | `addons/account/models/account_move.py:4315` | `account.move._get_last_sequence_domain` | account_move | dynamic table |
| 98 | B | fragment | `addons/account/models/account_move.py:4336` | `account.move._get_last_sequence_domain` | account_move | dynamic table |
| 99 | B | fragment | `addons/account/models/account_move.py:4359` | `account.move._get_last_sequence_domain` | account_move | dynamic table |
| 100 | B | fragment | `addons/account/models/account_move.py:4363` | `account.move._get_last_sequence_domain` | account_move | dynamic table |
| 101 | B | fragment | `addons/account/models/account_move.py:4365` | `account.move._get_last_sequence_domain` | account_move | dynamic table |
| 102 | B | fragment | `addons/account/models/account_move.py:4368` | `account.move._get_last_sequence_domain` | account_move | dynamic table |
| 103 | B | fragment | `addons/account/models/account_move.py:4370` | `account.move._get_last_sequence_domain` | account_move | dynamic table |
| 104 | B | fragment | `addons/account/models/account_move.py:4374` | `account.move._get_last_sequence_domain` | account_move | dynamic table |
| 105 | B | fragment | `addons/account/models/account_move.py:4376` | `account.move._get_last_sequence_domain` | account_move | dynamic table |
| 106 | B | sql | `addons/account/models/account_move.py:4548` | `account.move._get_frequent_account_and_taxes` | account_move_line, account_move_line_account_tax_rel |  |
| 107 | B | fragment | `addons/account/models/account_move.py:4943` | `account.move._copy_recurring_entries` | account_move | dynamic table |
| 108 | B | fragment | `addons/account/models/account_move.py:4944` | `account.move._copy_recurring_entries` | account_move | dynamic table |
| 109 | B | sql | `addons/account/models/account_move.py:4947` | `account.move._copy_recurring_entries` | account_move |  |
| 110 | B | fragment | `addons/account/models/account_move.py:5540` | `account.move._get_all_reconciled_invoice_partials` | account_move_line, account_partial_reconcile |  |
| 111 | B | fragment | `addons/account/models/account_move.py:5626` | `account.move._get_all_reconciled_invoice_partials` | account_move_line, account_partial_reconcile |  |
| 112 | B | sql | `addons/account/models/account_move.py:5720` | `account.move._get_all_reconciled_invoice_partials` | account_move_line, account_partial_reconcile |  |
| 113 | B | sql | `addons/account/models/account_move.py:6457` | `account.move._update_sequence_made_gap` | account_move |  |
| 114 | B | sql | `addons/account/models/account_move.py:7022` | `account.move._unlink_next_draft_auto_post_moves` | account_move |  |
| 115 | B | fragment | `addons/account/models/account_move.py:7045` | `account.move._check_draftable` | account_partial_reconcile |  |
| 116 | B | sql | `addons/account/models/account_move.py:7053` | `account.move._check_draftable` | account_partial_reconcile |  |
| 117 | B | sql | `addons/account/models/account_move.py:7843` | `account.move._first_date` | account_move | dynamic table |
| 118 | B | fragment | `addons/account/models/account_move.py:8339` | `account.move.get_cash_roundings` | account_cash_rounding | dynamic table |
| 119 | B | sql | `addons/account/models/account_move.py:8345` | `account.move.get_cash_roundings` | account_cash_rounding | dynamic table |
| 120 | B | sql | `addons/account/models/account_move_line.py:729` | `account.move.line._compute_account_id` | account_account, account_account_res_company_rel, account_move_line |  |
| 121 | B | sql | `addons/account/models/account_move_line.py:820` | `account.move.line._search_account_id` | account_account | dynamic table |
| 122 | B | fragment | `addons/account/models/account_move_line.py:945` | `account.move.line._compute_sql_debit_converted` | account_move_line | dynamic table |
| 123 | B | fragment | `addons/account/models/account_move_line.py:948` | `account.move.line._compute_sql_credit_converted` | account_move_line | dynamic table |
| 124 | B | fragment | `addons/account/models/account_move_line.py:951` | `account.move.line._compute_sql_balance_converted` | account_move_line | dynamic table |
| 125 | B | sql | `addons/account/models/account_move_line.py:958` | `account.move.line._compute_consolidation_rate` | account_move_line | dynamic table |
| 126 | B | fragment | `addons/account/models/account_move_line.py:1097` | `account.move.line._join_partial_summary_query` | account_partial_reconcile |  |
| 127 | B | fragment | `addons/account/models/account_move_line.py:1117` | `account.move.line._join_partial_summary_query` | account_move_line | dynamic table |
| 128 | B | fragment | `addons/account/models/account_move_line.py:1126` | `account.move.line._compute_sql_residual_at_date` | account_move_line | dynamic table |
| 129 | B | fragment | `addons/account/models/account_move_line.py:1137` | `account.move.line._compute_sql_residual_currency_at_date` | account_move_line | dynamic table |
| 130 | B | sql | `addons/account/models/account_move_line.py:1148` | `account.move.line._compute_residual_at_date` | account_move_line | dynamic table |
| 131 | B | sql | `addons/account/models/account_move_line.py:1176` | `account.move.line._compute_amount_residual` | account_partial_reconcile |  |
| 132 | B | fragment | `addons/account/models/account_move_line.py:1643` | `account.move.line._compute_sql_payment_date` | account_move_line | dynamic table |
| 133 | B | sql | `addons/account/models/account_move_line.py:1802` | `account.move.line._inverse_analytic_distribution` | account_move_line |  |
| 134 | B | fragment | `addons/account/models/account_move_line.py:2450` | `account.move.line._search_panel_domain_image` | account_account, account_move_line |  |
| 135 | B | fragment | `addons/account/models/account_move_line.py:2457` | `account.move.line._search_panel_domain_image` | account_account | dynamic table |
| 136 | B | sql | `addons/account/models/account_move_line.py:2458` | `account.move.line._search_panel_domain_image` | account_account | dynamic table |
| 137 | B | fragment | `addons/account/models/account_move_line_tax_details.py:38` | `account.move.line._get_query_tax_details` | account_move_line | dynamic table |
| 138 | B | fragment | `addons/account/models/account_move_line_tax_details.py:41` | `account.move.line._get_query_tax_details` | account_move_line | dynamic table |
| 139 | B | fragment | `addons/account/models/account_move_line_tax_details.py:49` | `account.move.line._get_query_tax_details` | account_move, account_move_line, account_move_line_account_tax_rel, account_tax, account_tax_filiation_rel, account_tax_repartition_line |  |
| 140 | B | sql | `addons/account/models/account_payment.py:761` | `account.payment._compute_stat_buttons_from_reconciliation` | account_account, account_move, account_move_line, account_partial_reconcile, account_payment |  |
| 141 | B | sql | `addons/account/models/account_payment.py:804` | `account.payment._compute_stat_buttons_from_reconciliation` | account_account, account_move, account_move_line, account_partial_reconcile, account_payment |  |
| 142 | B | fragment | `addons/account/models/account_payment.py:883` | `account.payment._fetch_duplicate_reference` | account_payment |  |
| 143 | B | fragment | `addons/account/models/account_payment.py:893` | `account.payment._fetch_duplicate_reference` | account_payment | dynamic table |
| 144 | B | fragment | `addons/account/models/account_payment.py:894` | `account.payment._fetch_duplicate_reference` | account_payment | dynamic table |
| 145 | B | fragment | `addons/account/models/account_payment.py:897` | `account.payment._fetch_duplicate_reference` | account_payment | dynamic table |
| 146 | B | fragment | `addons/account/models/account_payment.py:898` | `account.payment._fetch_duplicate_reference` | account_payment | dynamic table |
| 147 | B | fragment | `addons/account/models/account_payment.py:900` | `account.payment._fetch_duplicate_reference` | account_payment |  |
| 148 | B | sql | `addons/account/models/account_payment.py:922` | `account.payment._fetch_duplicate_reference` | account_payment |  |
| 149 | B | fragment | `addons/account/models/account_payment_term.py:60` | `account.payment.term._compute_sql_currency_id` | account_payment_term | dynamic table |
| 150 | B | sql | `addons/account/models/account_reconcile_model.py:219` | `account.reconcile.model.action_reconcile_stat` | account_move_line |  |
| 151 | B | fragment | `addons/account/models/account_report.py:384` | `account.report._compute_sql_active` | account_report | dynamic table |
| 152 | B | fragment | `addons/account/models/account_tax.py:261` | `account.tax.name_search` | account_tax_alternatives |  |
| 153 | B | fragment | `addons/account/models/chart_template.py:444` | `account.chart.template._pre_reload_data` | account_account |  |
| 154 | B | sql | `addons/account/models/company.py:1175` | `res.company._check_hash_integrity` | account_journal, account_move | dynamic table |
| 155 | B | sql | `addons/account/models/company.py:1176` | `res.company._check_hash_integrity` | account_journal, account_move | dynamic table |
| 156 | B | sql | `addons/account/models/company.py:1207` | `res.company._check_hash_integrity` | account_journal, account_move | dynamic table |
| 157 | B | sql | `addons/account/models/kpi_provider.py:39` | `-.get_kpi_summary` | account_bank_statement_line, account_journal, account_move | bare cursor without a registry: no ORM hook can reroute it |
| 158 | B | sql | `addons/account/models/kpi_provider.py:49` | `-.get_kpi_summary` | account_bank_statement_line, account_journal, account_move | bare cursor without a registry: no ORM hook can reroute it |
| 159 | B | fragment | `addons/account/models/partner.py:404` | `res.partner._credit_debit_get` | account_account, account_move_line |  |
| 160 | B | sql | `addons/account/models/partner.py:419` | `res.partner._credit_debit_get` | account_account, account_move_line |  |
| 161 | B | sql | `addons/account/models/partner.py:449` | `res.partner._asset_difference_search` | account_account, account_move, account_move_line |  |
| 162 | B | sql | `addons/account/models/partner.py:479` | `res.partner._invoice_total` | account_move |  |
| 163 | B | sql | `addons/account/models/product.py:246` | `product.template._check_uom_not_in_invoice` | account_move_line, product_product, product_template, uom_uom |  |
| 164 | B | sql | `addons/account/models/res_currency_rate_consolidation_mixin.py:33` | `res.currency.rate.consolidation.mixin._compute_consolidation_rate` | account_move_line, account_report_external_value, purchase_order_line, sale_order_line | dynamic table |
| 165 | B | fragment | `addons/account/models/res_currency_rate_consolidation_mixin.py:57` | `res.currency.rate.consolidation.mixin._compute_sql_consolidation_currency_id` | account_move_line, account_report_external_value, purchase_order_line, sale_order_line | dynamic table |
| 166 | B | helper | `addons/account/models/sequence_mixin.py:55` | `sequence.mixin.init` | account_move | dynamic table |
| 167 | B | sql | `addons/account/models/sequence_mixin.py:66` | `sequence.mixin.init` | account_move | dynamic table |
| 168 | B | fragment | `addons/account/models/sequence_mixin.py:259` | `sequence.mixin._get_last_sequence_domain` | account_move | dynamic table |
| 169 | B | fragment | `addons/account/models/sequence_mixin.py:299` | `sequence.mixin._get_last_sequence` | account_move | dynamic table |
| 170 | B | fragment | `addons/account/models/sequence_mixin.py:303` | `sequence.mixin._get_last_sequence` | account_move | dynamic table |
| 171 | B | fragment | `addons/account/models/sequence_mixin.py:305` | `sequence.mixin._get_last_sequence` | account_move | dynamic table |
| 172 | B | fragment | `addons/account/models/sequence_mixin.py:307` | `sequence.mixin._get_last_sequence` | account_move | dynamic table |
| 173 | B | fragment | `addons/account/models/sequence_mixin.py:308` | `sequence.mixin._get_last_sequence` | account_move | dynamic table |
| 174 | B | sql | `addons/account/models/sequence_mixin.py:311` | `sequence.mixin._get_last_sequence` | account_move | dynamic table |
| 175 | B | sql | `addons/account/wizard/account_merge_wizard.py:144` | `account.merge.wizard._action_merge` | account_account |  |
| 176 | B | sql | `addons/account/wizard/account_merge_wizard.py:170` | `account.merge.wizard._action_merge` | account_account |  |
| 177 | B | sql | `addons/account/wizard/account_merge_wizard.py:268` | `account.merge.wizard.line._compute_account_has_hashed_entries` | account_move_line |  |
| 178 | B | sql | `addons/account/wizard/account_secure_entries_wizard.py:76` | `account.secure.entries.wizard._compute_max_hash_date` | account_move | dynamic table |
| 179 | C | upgrade_script | `addons/analytic/migrations/1.2/pre-migrate.py:6` | `-.migrate` |  | upgrade script: runs only on -u from an older module version |
| 180 | C | upgrade_script | `addons/analytic/migrations/1.2/pre-migrate.py:14` | `-.migrate` |  | upgrade script: runs only on -u from an older module version |
| 181 | C | upgrade_script | `addons/analytic/migrations/1.2/pre-migrate.py:18` | `-.migrate` |  | upgrade script: runs only on -u from an older module version |
| 182 | C | upgrade_script | `addons/analytic/migrations/1.2/pre-migrate.py:30` | `-.migrate` |  | upgrade script: runs only on -u from an older module version |
| 183 | C | upgrade_script | `addons/analytic/migrations/1.2/pre-migrate.py:31` | `-.migrate` |  | upgrade script: runs only on -u from an older module version |
| 184 | A | helper | `addons/analytic/models/analytic_mixin.py:35` | `analytic.mixin.init` | account_move_line, account_reconcile_model_line, purchase_order_line, sale_order_line | generic code; table resolved per model (4 in-scope tables) |
| 185 | A | fragment | `addons/analytic/models/analytic_mixin.py:44` | `analytic.mixin._query_analytic_accounts` | account_move_line, account_reconcile_model_line, purchase_order_line, sale_order_line | generic code; table resolved per model (4 in-scope tables) |
| 186 | B | fragment | `addons/analytic/models/analytic_mixin.py:132` | `analytic.mixin._read_group_groupby` | account_move_line, account_reconcile_model_line, purchase_order_line, sale_order_line | generic code; table resolved per model (4 in-scope tables); B since UNT14-36: unit-owned (storage worker reclassification) |
| 187 | B | fragment | `addons/analytic/models/analytic_mixin.py:143` | `analytic.mixin._read_group_groupby` | account_move_line, account_reconcile_model_line, purchase_order_line, sale_order_line | generic code; table resolved per model (4 in-scope tables); B since UNT14-36: unit-owned (storage worker reclassification) |
| 188 | A | fragment | `addons/analytic/models/analytic_mixin.py:155` | `analytic.mixin._get_count_id` | account_move_line, account_reconcile_model_line, purchase_order_line, sale_order_line | generic code; table resolved per model (4 in-scope tables) |
| 189 | A | fragment | `addons/analytic/models/analytic_mixin.py:157` | `analytic.mixin._get_count_id` | account_move_line, account_reconcile_model_line, purchase_order_line, sale_order_line | generic code; table resolved per model (4 in-scope tables) |
| 190 | A | fragment | `addons/analytic/models/analytic_mixin.py:159` | `analytic.mixin._get_count_id` | account_move_line, account_reconcile_model_line, purchase_order_line, sale_order_line | generic code; table resolved per model (4 in-scope tables) |
| 191 | A | fragment | `addons/mail/models/mail_activity_mixin.py:184` | `mail.activity.mixin._compute_sql_activity_state` | 12 tables (0 written) | generic code; table resolved per model (12 in-scope tables) |
| 192 | A | fragment | `addons/mail/models/mail_activity_mixin.py:204` | `mail.activity.mixin._compute_sql_activity_state` | 12 tables (0 written) | generic code; table resolved per model (12 in-scope tables) |
| 193 | A | fragment | `addons/mail/models/mail_activity_mixin.py:206` | `mail.activity.mixin._compute_sql_activity_state` | 12 tables (0 written) | generic code; table resolved per model (12 in-scope tables) |
| 194 | A | sql | `addons/mail/models/mail_thread.py:264` | `mail.thread._compute_has_message` | 12 tables (0 written) | generic code; table resolved per model (12 in-scope tables) |
| 195 | A | fragment | `addons/mail/models/mail_thread.py:277` | `mail.thread._search_has_message` | 12 tables (0 written) | generic code; table resolved per model (12 in-scope tables) |
| 196 | A | sql | `addons/mail/models/mail_thread.py:283` | `mail.thread._compute_message_needaction` | 12 tables (0 written) | generic code; table resolved per model (12 in-scope tables) |
| 197 | A | sql | `addons/mail/models/mail_thread.py:307` | `mail.thread._compute_message_has_error` | 12 tables (0 written) | generic code; table resolved per model (12 in-scope tables) |
| 198 | A | sql | `addons/mail/models/mail_thread.py:3437` | `mail.thread._notify_cancel_by_type_generic` | 12 tables (0 written) | generic code; table resolved per model (12 in-scope tables) |
| 199 | B | fragment | `addons/product/models/product_product.py:1134` | `product.product._search_display_name` | product_supplierinfo, product_template | dynamic table |
| 200 | B | fragment | `addons/product/models/product_product.py:1138` | `product.product._search_display_name` | product_supplierinfo, product_template | dynamic table |
| 201 | B | fragment | `addons/product/models/product_template.py:413` | `product.template._compute_sql_cost_currency_id` | product_template | dynamic table |
| 202 | B | fragment | `addons/product/models/product_template.py:969` | `product.template._search_display_name` | product_template | dynamic table |
| 203 | B | fragment | `addons/purchase/models/account_invoice.py:154` | `account.move._compute_display_auto_complete` | purchase_order |  |
| 204 | B | fragment | `addons/purchase/models/account_invoice.py:158` | `account.move._compute_display_auto_complete` | purchase_order | dynamic table |
| 205 | B | sql | `addons/purchase/models/account_invoice.py:159` | `account.move._compute_display_auto_complete` | purchase_order | dynamic table |
| 206 | B | fragment | `addons/purchase/models/purchase_bill_line_match.py:98` | `purchase.bill.line.match._select_po_line` | purchase_order, purchase_order_line |  |
| 207 | B | fragment | `addons/purchase/models/purchase_bill_line_match.py:128` | `purchase.bill.line.match._select_am_line` | account_move, account_move_line |  |
| 208 | B | sql | `addons/purchase/models/purchase_order.py:401` | `purchase.order._fetch_duplicate_orders` | purchase_order |  |
| 209 | B | fragment | `addons/purchase/models/purchase_order.py:442` | `purchase.order._search_is_late` | purchase_order | dynamic table |
| 210 | B | fragment | `addons/purchase/models/purchase_order.py:447` | `purchase.order._search_is_late` | purchase_order | dynamic table |
| 211 | B | fragment | `addons/purchase/report/purchase_bill.py:45` | `purchase.bill.union._table_sql` | account_move, purchase_order |  |
| 212 | B | fragment | `addons/purchase/report/purchase_report.py:57` | `purchase.report._table_sql` | purchase_order_line | dynamic table |
| 213 | B | fragment | `addons/purchase_stock/models/stock_move.py:139` | `stock.move._get_origin_company_domains` | stock_move | dynamic table |
| 214 | B | fragment | `addons/purchase_stock/report/purchase_report.py:16` | `purchase.report._select_list` | purchase_order, purchase_order_line, stock_location, stock_move, stock_picking |  |
| 215 | B | sql | `addons/purchase_stock/report/vendor_delay_report.py:23` | `vendor.delay.report.init` | product_category, product_product, product_template, purchase_order_line, stock_move, stock_move_line, uom_uom | view DDL: reads only |
| 216 | B | sql | `addons/sale/models/sale_order.py:836` | `sale.order._search_invoice_ids` | account_move, account_move_line, sale_order, sale_order_line, sale_order_line_invoice_rel |  |
| 217 | B | sql | `addons/sale/models/sale_order.py:1060` | `sale.order._fetch_duplicate_orders` | sale_order |  |
| 218 | B | fragment | `addons/sale/models/sale_order.py:1135` | `sale.order._search_is_unfulfilled` | sale_order | dynamic table |
| 219 | B | sql | `addons/sale/models/utm_campaign.py:55` | `utm.campaign._compute_sale_invoiced_amount` | account_move, account_move_line |  |
| 220 | B | fragment | `addons/sale/report/sale_report.py:127` | `sale.report._table_sql` | sale_order_line | dynamic table |
| 221 | B | fragment | `addons/sale_stock/models/stock.py:59` | `stock.move._compute_sql_order_partner_id` | sale_order_line |  |
| 222 | B | fragment | `addons/sale_stock/models/stock.py:65` | `stock.move._compute_sql_order_partner_id` | sale_order_line |  |
| 223 | B | fragment | `addons/sale_stock/models/stock.py:67` | `stock.move._compute_sql_order_partner_id` | sale_order_line |  |
| 224 | B | fragment | `addons/sale_stock/models/stock.py:157` | `stock.move._get_origin_company_domains` | stock_move | dynamic table |
| 225 | A | sql | `addons/sms/models/mail_thread.py:23` | `mail.thread._compute_message_has_sms_error` | 12 tables (0 written) | generic code; table resolved per model (12 in-scope tables) |
| 226 | B | sql | `addons/stock/__init__.py:46` | `-._create_inventory_adjustment` | product_product |  |
| 227 | B | fragment | `addons/stock/models/product.py:418` | `product.product._get_domain_locations_new` | stock_location |  |
| 228 | B | fragment | `addons/stock/models/stock_picking_type.py:361` | `stock.picking.type._compute_sql_is_favorite` | picking_type_favorite_user_rel |  |
| 229 | B | fragment | `addons/stock/models/stock_quant.py:188` | `stock.quant._compute_sql_last_count_date` | stock_move, stock_move_line, stock_quant |  |
| 230 | B | fragment | `addons/stock/models/stock_quant.py:207` | `stock.quant._compute_sql_last_count_date` | stock_quant | dynamic table |
| 231 | B | fragment | `addons/stock/models/stock_quant.py:210` | `stock.quant._compute_sql_last_count_date` | stock_quant | dynamic table |
| 232 | B | fragment | `addons/stock/models/stock_quant.py:363` | `stock.quant._read_group_select` | stock_quant | dynamic table |
| 233 | B | fragment | `addons/stock/models/stock_quant.py:367` | `stock.quant._read_group_select` | stock_quant | dynamic table |
| 234 | B | fragment | `addons/stock/models/stock_quant.py:666` | `stock.quant._run_least_packages_removal_strategy_astar` | stock_quant | dynamic table |
| 235 | B | fragment | `addons/stock/models/stock_quant.py:667` | `stock.quant._run_least_packages_removal_strategy_astar` | stock_quant | dynamic table |
| 236 | B | fragment | `addons/stock/models/stock_quant.py:668` | `stock.quant._run_least_packages_removal_strategy_astar` | stock_quant | dynamic table |
| 237 | B | sql | `addons/stock/models/stock_quant.py:669` | `stock.quant._run_least_packages_removal_strategy_astar` | stock_quant | dynamic table |
| 238 | B | sql | `addons/stock/models/stock_quant.py:1169` | `stock.quant._unlink_zero_quants` | stock_quant |  |
| 239 | B | fragment | `addons/stock/report/report_stock_quantity.py:51` | `report.stock.quantity.init` | product_product, product_template, stock_location, stock_move, stock_quant, stock_warehouse, uom_uom | view DDL: reads only |
| 240 | B | sql | `addons/stock/report/report_stock_quantity.py:194` | `report.stock.quantity.init` | product_product, product_template, stock_location, stock_move, stock_quant, stock_warehouse, uom_uom | view DDL: reads only |
| 241 | B | fragment | `addons/stock_account/models/product.py:305` | `product.product._get_last_product_value` | product_value |  |
| 242 | B | fragment | `addons/stock_account/models/product.py:306` | `product.product._get_last_product_value` | product_value |  |
| 243 | B | sql | `addons/stock_account/models/product.py:307` | `product.product._get_last_product_value` | product_value |  |
| 244 | B | fragment | `addons/stock_account/models/stock_move.py:131` | `stock.move._compute_sql_order_partner_id` | stock_move | dynamic table |
| 245 | B | sql | `addons/stock_account/report/stock_avco_audit_report.py:91` | `stock.avco.report.init` | product_category, product_product, product_template, product_value, stock_move, stock_picking, uom_uom | view DDL: reads only |
| 246 | A | helper | `odoo/addons/base/wizard/base_partner_merge.py:137` | `base.partner.merge.automatic.wizard._update_foreign_keys_generic` | 39 tables (0 written) | generic core FK fan-out; FK fan-out of account_account: 18 in-scope tables (catalog FKs; Reference/res_id columns not included); FK fan-out of res_partner: 24 in-scope tables (catalog FKs; Reference/res_id columns not included); FK fan-out of res_partner_bank: 5 in-scope tables (catalog FKs; Reference/res_id columns not included) |
| 247 | A | sql | `odoo/addons/base/wizard/base_partner_merge.py:143` | `base.partner.merge.automatic.wizard._update_foreign_keys_generic` | 39 tables (0 written) | generic core FK fan-out; FK fan-out of account_account: 18 in-scope tables (catalog FKs; Reference/res_id columns not included); FK fan-out of res_partner: 24 in-scope tables (catalog FKs; Reference/res_id columns not included); FK fan-out of res_partner_bank: 5 in-scope tables (catalog FKs; Reference/res_id columns not included) |

### SQL views and `_table_sql` reports

| # | disp | model | how | in-scope tables read | note |
|---|---|---|---|---|---|
| 1 | C | `account.code.mapping` | `_table_sql` | - |  |
| 2 | B | `account.invoice.report` | `_table_sql` | account_move, account_move_line, product_product, product_template, uom_uom | rebuilt from Mongo data by the owning unit |
| 3 | C | `account.root` | `_table_sql` | - |  |
| 4 | C | `auth_totp.device` | `_table_sql` | - |  |
| 5 | B | `purchase.bill.line.match` | `_table_sql` | account_move, account_move_line, purchase_order, purchase_order_line | rebuilt from Mongo data by the owning unit |
| 6 | B | `purchase.bill.union` | `_table_sql` | account_move, purchase_order | rebuilt from Mongo data by the owning unit |
| 7 | B | `purchase.report` | `_table_sql` | product_product, product_template, purchase_order, purchase_order_line, stock_location, stock_move, stock_picking, stock_picking_type, uom_uom | rebuilt from Mongo data by the owning unit |
| 8 | B | `report.stock.quantity` | init() view `report_stock_quantity` + `_table_sql` | product_product, product_template, stock_location, stock_move, stock_quant, stock_warehouse, uom_uom | rebuilt from Mongo data by the owning unit |
| 9 | C | `res.device` | init() view `res_device` + `_table_sql` | - |  |
| 10 | C | `res.session` | init() view `res_session` + `_table_sql` | - |  |
| 11 | C | `res.users.apikeys` | `_table_sql` | - |  |
| 12 | C | `res.users.apikeys.show` | `_table_sql` | - |  |
| 13 | B | `sale.report` | `_table_sql` | product_product, product_template, sale_order, sale_order_line, uom_uom | rebuilt from Mongo data by the owning unit |
| 14 | B | `vendor.delay.report` | init() view `vendor_delay_report` + `_table_sql` | product_category, product_product, product_template, purchase_order_line, stock_move, stock_move_line, uom_uom | rebuilt from Mongo data by the owning unit |
| 15 | B | `-` | view `stock_avco_report` | product_category, product_product, product_template, product_value, stock_move, stock_picking, uom_uom | rebuilt from Mongo data by the owning unit |

### Scheduled jobs (`ir_cron`)

| id | disp | xmlid | model | active | every | direct (method-level) | class-level-only possible (2-hop; count + up to 6 names) | note |
|---|---|---|---|---|---|---|---|---|
| 1 | A | `base.autovacuum_job` | `ir.autovacuum` | True | 1 days | - | 0: - | vacuums every transient/in-scope model with _gc_* hooks; pause it |
| 2 | A | `base.ir_cron_res_users_deletion` | `res.users.deletion` | True | 1 days | - | 1: stock_warehouse | possible indirect reach (class-level, unproven): review before load |
| 3 | A | `resource.ir_cron_calendar_clean_up` | `resource.calendar` | True | 1 months | - | 22: account_account, account_accrued_orders_wizard, account_bank_statement_line, account_cash_rounding, account_fiscal_position, account_incoterms, ... | possible indirect reach (class-level, unproven): review before load |
| 4 | A | `mail.ir_cron_mail_scheduler_action` | `mail.mail` | True | 1 hours | - | 60: account_account, account_account_tag, account_accrued_orders_wizard, account_bank_statement, account_bank_statement_line, account_cash_rounding, ... | possible indirect reach (class-level, unproven): review before load |
| 5 | A | `mail.ir_cron_module_update_notification` | `publisher_warranty.contract` | True | 1 weeks | - | 2: account_account_tag, stock_warehouse | possible indirect reach (class-level, unproven): review before load |
| 6 | A | `mail.ir_cron_delete_notification` | `mail.notification` | True | 1 months | - | 17: account_account, account_fiscal_position, account_incoterms, account_move, account_move_line, account_payment_method_line, ... | possible indirect reach (class-level, unproven): review before load |
| 7 | A | `mail.ir_cron_mail_gateway_action` | `fetchmail.server` | False | 5 minutes | - | 59: account_account, account_account_tag, account_accrued_orders_wizard, account_bank_statement, account_bank_statement_line, account_cash_rounding, ... | possible indirect reach (class-level, unproven): review before load |
| 8 | A | `mail.ir_cron_post_scheduled_message` | `mail.scheduled.message` | True | 1 days | - | 60: account_account, account_account_tag, account_accrued_orders_wizard, account_bank_statement, account_bank_statement_line, account_cash_rounding, ... | possible indirect reach (class-level, unproven): review before load |
| 9 | A | `mail.ir_cron_send_scheduled_message` | `mail.message.schedule` | True | 1 hours | - | 59: account_account, account_account_tag, account_accrued_orders_wizard, account_bank_statement, account_bank_statement_line, account_cash_rounding, ... | possible indirect reach (class-level, unproven): review before load |
| 10 | C | `mail.ir_cron_web_push_notification` | `mail.push` | True | 1 days | - | 0: - |  |
| 11 | A | `mail.ir_cron_mail_end_polls` | `mail.poll` | True | 1 days | - | 3: account_account, account_move, account_tax | possible indirect reach (class-level, unproven): review before load |
| 12 | A | `mail.ir_cron_discuss_channel_member_unmute` | `discuss.channel.member` | True | 1 days | - | 18: account_account, account_fiscal_position, account_incoterms, account_move, account_move_line, account_payment_method_line, ... | possible indirect reach (class-level, unproven): review before load |
| 13 | A | `mail.ir_cron_discuss_channel_sync_last_interest_dt` | `discuss.channel` | True | 1 days | - | 60: account_account, account_account_tag, account_accrued_orders_wizard, account_bank_statement, account_bank_statement_line, account_cash_rounding, ... | possible indirect reach (class-level, unproven): review before load |
| 14 | A | `auth_signup.ir_cron_auth_signup_send_pending_user_reminder` | `res.users` | True | 1 days | - | 71: account_account, account_account_tag, account_accrued_orders_wizard, account_autopost_bills_wizard, account_bank_statement, account_bank_statement_line, ... | possible indirect reach (class-level, unproven): review before load |
| 15 | A | `sms.ir_cron_sms_scheduler_action` | `sms.sms` | True | 24 hours | - | 17: account_account, account_fiscal_position, account_incoterms, account_move, account_move_line, account_payment_method_line, ... | possible indirect reach (class-level, unproven): review before load |
| 16 | A | `digest.ir_cron_digest_scheduler_action` | `digest.digest` | True | 1 days | - | 47: account_account, account_account_tag, account_accrued_orders_wizard, account_bank_statement, account_bank_statement_line, account_cash_rounding, ... | possible indirect reach (class-level, unproven): review before load |
| 17 | A | `payment.processing_cron` | `payment.data` | True | 1 days | account_journal, account_move, account_move_line, account_payment, sale_order, validate_account_move | 0: - | ORM writes; pause during load windows |
| 18 | A | `payment.post_processing_cron` | `payment.transaction` | False | 1 days | account_autopost_bills_wizard, account_bank_statement, account_bank_statement_line, account_journal, account_move, account_move_line, account_partial_reconcile, account_payment, account_tax, product_product, sale_advance_payment_inv, sale_order, sale_order_line, stock_picking, validate_account_move | 24: account_account, account_cash_rounding, account_fiscal_position, account_incoterms, account_journal_group, account_move_send_batch_wizard, ... | ORM writes; pause during load windows |
| 19 | B | `account.ir_cron_auto_post_draft_entry` | `account.move` | True | 1 days | account_account, account_account_tag, account_bank_statement_line, account_fiscal_position, account_full_reconcile, account_journal, account_move, account_move_line, account_partial_reconcile, account_payment, product_product, sale_order_line, stock_move, uom_uom | 66: account_accrued_orders_wizard, account_autopost_bills_wizard, account_bank_statement, account_cash_rounding, account_fiscal_position_account, account_incoterms, ... | reaches raw SQL |
| 20 | A | `account.ir_cron_account_move_send` | `account.move` | True | 1 days | account_move, product_document | 78: account_account, account_account_tag, account_accrued_orders_wizard, account_autopost_bills_wizard, account_bank_statement, account_bank_statement_line, ... | ORM writes; pause during load windows |
| 21 | B | `account.ir_cron_post_stock_valuation` | `res.company` | True | 1 days | account_account, account_accrued_orders_wizard, account_bank_statement_line, account_fiscal_position, account_full_reconcile, account_journal, account_move, account_move_line, account_partial_reconcile, account_payment, purchase_order_line, sale_order_line, stock_location, stock_move | 68: account_account_tag, account_autopost_bills_wizard, account_bank_statement, account_cash_rounding, account_financial_year_op, account_fiscal_position_account, ... | reaches raw SQL |
| 22 | B | `stock.ir_cron_scheduler_action` | `stock.rule` | True | 1 days | account_move_line, product_category, product_product, product_template, purchase_order_line, stock_location, stock_lot, stock_move, stock_move_line, stock_package, stock_package_type, stock_picking, stock_picking_batch, stock_picking_type, stock_putaway_rule, stock_quant, stock_reference, stock_route, stock_rule, stock_warehouse, stock_warehouse_orderpoint, uom_uom | 37: account_account, account_account_tag, account_accrued_orders_wizard, account_bank_statement_line, account_cash_rounding, account_fiscal_position, ... | reaches raw SQL |
| 23 | A | `purchase.purchase_send_reminder_mail` | `purchase.order` | True | 1 days | purchase_order | 80: account_account, account_account_tag, account_accrued_orders_wizard, account_autopost_bills_wizard, account_bank_statement, account_bank_statement_line, ... | ORM writes; pause during load windows |
| 24 | A | `sale.send_invoice_cron` | `payment.transaction` | False | 1 days | account_move | 38: account_account, account_autopost_bills_wizard, account_bank_statement, account_bank_statement_line, account_cash_rounding, account_fiscal_position, ... | ORM writes; pause during load windows |
| 25 | A | `sale.send_pending_emails_cron` | `sale.order` | False | 1 days | sale_order | 75: account_account, account_account_tag, account_accrued_orders_wizard, account_autopost_bills_wizard, account_bank_statement, account_bank_statement_line, ... | ORM writes; pause during load windows |

### Database-side writers: foreign keys, triggers, functions

Triggers in the catalog: 0; user functions in `public`: 0; code server actions using the cursor: 0. Foreign keys: 468 inside the in-scope set, 415 from in-scope tables to PostgreSQL tables, 50 from PostgreSQL tables into in-scope tables (all **A**: the storage path drops the constraint with the column move and must enforce `ondelete` itself; a PostgreSQL-side cascade into a Mongo-backed table no longer fires).

In-scope -> PostgreSQL by `ondelete`: cascade 20, set null 352, restrict 43.

| PostgreSQL table (bucket) | column | -> in-scope table | ondelete |
|---|---|---|---|
| account_analytic_applicability (shared_postgresql) | product_categ_id | product_category | set null |
| account_analytic_distribution_model (shared_postgresql) | product_categ_id | product_category | cascade |
| account_analytic_distribution_model (shared_postgresql) | product_id | product_product | cascade |
| account_analytic_line (shared_postgresql) | general_account_id | account_account | restrict |
| account_analytic_line (shared_postgresql) | journal_id | account_journal | set null |
| account_analytic_line (shared_postgresql) | move_line_id | account_move_line | cascade |
| account_analytic_line (shared_postgresql) | order_id | sale_order | set null |
| account_analytic_line (shared_postgresql) | product_id | product_product | set null |
| account_analytic_line (shared_postgresql) | product_uom_id | uom_uom | set null |
| account_analytic_line (shared_postgresql) | reinvoice_move_id | account_move | set null |
| account_analytic_line (shared_postgresql) | so_line | sale_order_line | set null |
| account_invoice_transaction_rel (shared_postgresql) | invoice_id | account_move | cascade |
| barcode_rule (shared_postgresql) | associated_uom_id | uom_uom | set null |
| payment_provider_product_pricelist_rel (shared_postgresql) | product_pricelist_id | product_pricelist | cascade |
| payment_refund_wizard (shared_postgresql) | payment_id | account_payment | set null |
| payment_transaction (shared_postgresql) | payment_id | account_payment | set null |
| res_company (orm_framework) | account_cash_basis_base_account_id | account_account | set null |
| res_company (orm_framework) | account_default_pos_receivable_account_id | account_account | set null |
| res_company (orm_framework) | account_discount_expense_allocation_id | account_account | set null |
| res_company (orm_framework) | account_discount_income_allocation_id | account_account | set null |
| res_company (orm_framework) | account_journal_early_pay_discount_gain_account_id | account_account | set null |
| res_company (orm_framework) | account_journal_early_pay_discount_loss_account_id | account_account | set null |
| res_company (orm_framework) | account_journal_suspense_account_id | account_account | set null |
| res_company (orm_framework) | account_opening_move_id | account_move | set null |
| res_company (orm_framework) | account_production_wip_account_id | account_account | set null |
| res_company (orm_framework) | account_production_wip_overhead_account_id | account_account | set null |
| res_company (orm_framework) | account_purchase_receipt_fiscal_position_id | account_fiscal_position | set null |
| res_company (orm_framework) | account_purchase_tax_id | account_tax | set null |
| res_company (orm_framework) | account_sale_tax_id | account_tax | set null |
| res_company (orm_framework) | automatic_entry_default_journal_id | account_journal | set null |
| res_company (orm_framework) | currency_exchange_journal_id | account_journal | set null |
| res_company (orm_framework) | default_cash_difference_expense_account_id | account_account | set null |
| res_company (orm_framework) | default_cash_difference_income_account_id | account_account | set null |
| res_company (orm_framework) | domestic_fiscal_position_id | account_fiscal_position | set null |
| res_company (orm_framework) | downpayment_account_id | account_account | set null |
| res_company (orm_framework) | expense_accrual_account_id | account_account | set null |
| res_company (orm_framework) | expense_currency_exchange_account_id | account_account | set null |
| res_company (orm_framework) | income_currency_exchange_account_id | account_account | set null |
| res_company (orm_framework) | incoterm_id | account_incoterms | set null |
| res_company (orm_framework) | internal_transit_location_id | stock_location | restrict |
| res_company (orm_framework) | price_difference_account_id | account_account | set null |
| res_company (orm_framework) | revenue_accrual_account_id | account_account | set null |
| res_company (orm_framework) | sale_discount_product_id | product_product | set null |
| res_company (orm_framework) | tax_cash_basis_journal_id | account_journal | set null |
| res_company (orm_framework) | transfer_account_id | account_account | set null |
| res_country_group_pricelist_rel (orm_framework) | pricelist_id | product_pricelist | cascade |
| res_partner (orm_framework) | incoterm_id | account_incoterms | set null |
| res_partner (orm_framework) | purchase_incoterm_id | account_incoterms | set null |
| res_partner_stock_lot_rel (orm_framework) | stock_lot_id | stock_lot | cascade |
| stock_picking_sms_rel (shared_postgresql) | stock_picking_id | stock_picking | cascade |

### Totals

| kind | op | A | B | C |
|---|---|---|---|---|
| cron | possible | 14 | 0 | 0 |
| cron | read | 0 | 0 | 1 |
| cron | write | 7 | 3 | 0 |
| foreign_key | write | 933 | 0 | 0 |
| fragment | read | 8 | 146 | 0 |
| helper | read | 2 | 1 | 0 |
| report | read | 0 | 8 | 7 |
| sql | read | 6 | 79 | 0 |
| sql | write | 8 | 17 | 0 |
| upgrade_script | read | 0 | 0 | 5 |
| upgrade_script | write | 0 | 0 | 1 |

### Writes outside odoo_unt13

None during this ticket: `odoo_src` was only read (role `odoo_ro`, read-only session) and the
`_table_sql` render ran on a throwaway clone `odoo_reg_probe`. Later units will need writes to
the application's PostgreSQL (never `odoo_src`, never Atlas), each needing a plan decision:
- the 8 **B** reports/views above: their PostgreSQL view or `_table_sql` stops seeing rows once
  its tables move, so the owning unit re-points or rebuilds them;
- the 10 crons that reach in-scope tables (including `base.autovacuum_job`): pausing direct
  writers during load and parallel-run windows is an `ir_cron.active` write;
- plus 14 with only possible indirect reach, to review before load;
- the 50 PostgreSQL -> in-scope foreign keys: dropping each constraint when its target table
  moves is DDL on the PostgreSQL side.

### Plugin findings

None new from this ticket.

## s3.4 accepted-empty (user decision d-accepted-empty: accept-all-7)

`.migration/recon_tolerances.json` `accepted_empty` lists these 7 keys from the signed-off `mapping_spec.json` (map-draft-4). The pinned harness reads bare strings, so each reason is recorded here. It is the build's reason from `.migration/fixtures/expected_empty.txt`. All 7 tables hold 0 rows in `.migration/source_fingerprint.json`.

| accepted_empty key | kind | source table | reason |
|---|---|---|---|
| `accountMove.adjustingEntriesAccountMove` | embed | `adjusting_entries__account_move` | links written only by the accrual/deferral adjusting-entry wizard (Enterprise deferrals), not reachable from Community flows |
| `accountPayment.accountBankStatementLineRel` | embed | `account_payment_account_bank_statement_line_rel` | payments auto-created by the bank reconciliation widget, which is Odoo Enterprise only |
| `purchaseOrderLine.accrualMoveRel` | embed | `purchase_order_line_accrual_move_rel` | accrued-expense entries from the account.accrued.orders.wizard reversal flow; needs period-end accrual run |
| `saleOrder.transactionRel` | embed | `sale_order_transaction_rel` | online payment transactions linked to sale orders; needs a configured payment provider |
| `saleOrderLineAccrualMoveRel` | root | `sale_order_line_accrual_move_rel` | accrued-revenue entries from the account.accrued.orders.wizard reversal flow; needs period-end accrual run |
| `stockMove.accountAnalyticLineStockMoveRel` | embed | `account_analytic_line_stock_move_rel` | analytic lines from stock valuation of moves with an analytic distribution; only written by the mrp/project stock-analytic flows, which are not installed |
| `stockMoveLine.consumeRel` | embed | `stock_move_line_consume_rel` | component-consumption traceability, written only by manufacturing (mrp is not installed) |

## s3.5 units and waves

Generated by `.migration/derive_units.py` from the signed spec map-draft-5 (sha256 `c0b93dad9526fc8f02df6b8199436d76da9f938a05ccadc98ab3adb7a35202a7`) and the row counts in `.migration/source_fingerprint.json` (row_counts_sha256 `a100e84ee2fb6282f30b45c003fd1db47561317c739340a10564d9e869e56a4e`); machine copy `.migration/units.json`. Plugin 2c1160efde323c570425953b7e38bcc3496c6053.

71 collections -> 64 units in 10 waves (19 batches of at most 5 units), 39536 rows.

**Canary**: `accountLockException` (1 row), wave 1 alone; it lands the run's one shared loader (`.migration/load/load_unit.py`), which every later batch imports.

### Rules

- A reference orders waves when its column is NOT NULL, has filled rows in the live profile (unsampled fk_integrity child_rows - null_fk > 0; an unmeasured stat orders, fail closed), or code on the write path sets it (cited in WRITE_PATH_SETTERS).
- A reference held by a pure link table (two NOT NULL foreign-key columns) is a junction reference: a plain id, it orders nothing.
- A never-filled reference whose target is not already in an earlier wave is a forward reference and must be cited in NO_WRITE_PATH_SETTER; an uncited one stops the derivation.
- Collections that reference each other in a cycle form one unit (strongly connected component); a unit's depth is its longest ordering path to a unit with no dependencies.
- Wave 1 is the canary alone: the smallest depth-0 non-junction unit by rows with at least one row; it lands the run's one shared loader. Wave 2 holds the other depth-0 non-junction units, wave d+2 depth d. Within a wave, non-junction units go smallest first (rows, then id); in that order, each unit and its junctions (sorted by rows, then id) form an indivisible group, and batches greedily pack whole groups up to 5 units.
- A root junction unit (its root table is a pure link table) is placed with the earlier of its endpoint units in migration order (the first one to opt into MongoDB; the many2many owner and comodel are cited in JUNCTION_OWNERS): it joins that unit's batch right after it and takes its wave and depth, because storage_mongodb.relation_layout (odoo/orm/storage_mongodb.py:284) routes a relation to MongoDB once the model or the comodel is on MongoDB. A junction unit is never the canary, and a group larger than 5 units stops the derivation.

Never-filled references that still order because installed code sets them:

- `account_move.tax_cash_basis_rec_id`: `addons/account/models/account_partial_reconcile.py:555`
- `product_value.lot_id`: `addons/stock_account/models/stock_lot.py:100`
- `product_value.move_id`: `addons/stock_account/models/stock_move.py:230`
- `purchase_order_line.sale_line_id`: `addons/sale_purchase/models/sale_order_line.py:207`
- `sale_order_line.combo_item_id`: `addons/sale/models/sale_order.py:1403`
- `stock_move.account_move_id`: `addons/stock_account/models/stock_move.py:283`
- `stock_warehouse_orderpoint.supplier_id`: `addons/purchase_stock/models/product.py:322`

### Waves

| wave | depth | batch | units (non-junction smallest first; junctions after anchor) | rows |
|---|---|---|---|---|
| 1 | 0 | w1-b01 | `accountLockException` | 1 |
| 2 | 0 | w2-b01 | `accountJournalGroup`, `productBaseUnit`, `productDocument`, `stockScrapReasonTag`, `productRemoval` | 13 |
| 2 | 0 | w2-b02 | `returnReason`, `stockStorageCategory`, `accountCashRounding`, `stockPackageType`, `productPricelist` | 34 |
| 2 | 0 | w2-b03 | `accountIncoterms`, `accountReport`, `productCategory`, `accountTaxGroup`, `accountPaymentTerm` | 107 |
| 2 | 0 | w2-b04 | `uomUom`, `productTemplateUomUomRel`, `accountFullReconcile`, `accountAccountTag`, `accountAccount` | 603 |
| 2 | 0 | w2-b05 | `productTag`, `stockReference`, `productAttribute`, `productAttributeValueProductTemplateAttributeLineRel` | 3506 |
| 3 | 1 | w3-b01 | `accountReportLine`, `accountReconcileModel`, `accountReconcileModelLineAccountTaxRel`, `accountJournal`, `accountFiscalPosition` | 106 |
| 3 | 1 | w3-b02 | `stockLocation`, `saleOrderLineStockRouteRel`, `productTemplate`, `productOptionalRel`, `accountTax` | 3181 |
| 4 | 2 | w4-b01 | `stockPickingBatch`, `stockPackage`, `accountBankStatement`, `accountReportExpression`, `accountPaymentMethod` | 29 |
| 4 | 2 | w4-b02 | `purchaseOrder` | 27 |
| 4 | 2 | w4-b03 | `productTemplateAttributeLine`, `productTemplateAttributeExcludedValueIdsRel`, `productTemplateAttributeValueSaleOrderLineRel`, `productTemplateAttributeValuePurchaseOrderLineRel`, `templateAttributeValueStockMoveRel` | 2058 |
| 4 | 2 | w4-b04 | `productProduct` | 5064 |
| 5 | 3 | w5-b01 | `stockPutawayRule`, `stockPackageHistory`, `stockStorageCategoryCapacity`, `productCombo`, `productPricelistItem` | 270 |
| 5 | 3 | w5-b02 | `stockLot` | 254 |
| 6 | 4 | w6-b01 | `stockQuant`, `saleOrder`, `saleOrderLineAccrualMoveRel`, `saleOrderLineInvoiceRel` | 1223 |
| 7 | 5 | w7-b01 | `productAttributeCustomValue`, `purchaseOrderLine`, `stockPicking` | 342 |
| 8 | 6 | w8-b01 | `accountMoveLine` | 21602 |
| 9 | 7 | w9-b01 | `stockMove` | 751 |
| 10 | 8 | w10-b01 | `productValue`, `stockMoveLine` | 365 |

### Root junction units

| unit | relation | owner field (declared at) | endpoints | placed with | wave | batch |
|---|---|---|---|---|---|---|
| `productTemplateUomUomRel` | `product_template_uom_uom_rel` | `product.template.uom_ids` (`addons/product/models/product_template.py:160`) | `uomUom`, `productTemplate` | `uomUom` | 2 | `w2-b04` |
| `productAttributeValueProductTemplateAttributeLineRel` | `product_attribute_value_product_template_attribute_line_rel` | `product.template.attribute.line.value_ids` (`addons/product/models/product_template_attribute_line.py:32`) | `productAttribute`, `productTemplateAttributeLine` | `productAttribute` | 2 | `w2-b05` |
| `accountReconcileModelLineAccountTaxRel` | `account_reconcile_model_line_account_tax_rel` | `account.reconcile.model.line.tax_ids` (`addons/account/models/account_reconcile_model.py:51`) | `accountReconcileModel`, `accountTax` | `accountReconcileModel` | 3 | `w3-b01` |
| `saleOrderLineStockRouteRel` | `sale_order_line_stock_route_rel` | `sale.order.line.route_ids` (`addons/sale_stock/models/sale_order_line.py:16`) | `stockLocation`, `saleOrder` | `stockLocation` | 3 | `w3-b02` |
| `productOptionalRel` | `product_optional_rel` | `product.template.optional_product_ids` (`addons/sale/models/product_template.py:55`) | `productTemplate` | `productTemplate` | 3 | `w3-b02` |
| `productTemplateAttributeExcludedValueIdsRel` | `product_template_attribute_excluded_value_ids_rel` | `product.template.attribute.value.excluded_value_ids` (`addons/product/models/product_template_attribute_value.py:50`) | `productTemplateAttributeLine` | `productTemplateAttributeLine` | 4 | `w4-b03` |
| `productTemplateAttributeValueSaleOrderLineRel` | `product_template_attribute_value_sale_order_line_rel` | `sale.order.line.product_no_variant_attribute_value_ids` (`addons/sale/models/sale_order_line.py:138`) | `productTemplateAttributeLine`, `saleOrder` | `productTemplateAttributeLine` | 4 | `w4-b03` |
| `productTemplateAttributeValuePurchaseOrderLineRel` | `product_template_attribute_value_purchase_order_line_rel` | `purchase.order.line.product_no_variant_attribute_value_ids` (`addons/purchase/models/purchase_order_line.py:141`) | `productTemplateAttributeLine`, `purchaseOrderLine` | `productTemplateAttributeLine` | 4 | `w4-b03` |
| `templateAttributeValueStockMoveRel` | `template_attribute_value_stock_move_rel` | `stock.move.never_product_template_attribute_value_ids` (`addons/stock/models/stock_move.py:47`) | `productTemplateAttributeLine`, `stockMove` | `productTemplateAttributeLine` | 4 | `w4-b03` |
| `saleOrderLineAccrualMoveRel` | `sale_order_line_accrual_move_rel` | `sale.order.line.accrual_move_ids` (`addons/sale/models/sale_order_line.py:368`) | `saleOrder`, `accountMoveLine` | `saleOrder` | 6 | `w6-b01` |
| `saleOrderLineInvoiceRel` | `sale_order_line_invoice_rel` | `sale.order.line.invoice_lines` (`addons/sale/models/sale_order_line.py:329`) | `saleOrder`, `accountMoveLine` | `saleOrder` | 6 | `w6-b01` |

### Units

Order is the global migration order. Tables: root table first, embedded tables after it. Tours: test files under the scope addons and bridges that call `start_tour` and name one of the unit's models in `env[...]`.

| order | unit | wave | batch | rows | collections and embedded tables | depends on | browser tours |
|---|---|---|---|---|---|---|---|
| 1 | `accountLockException` | 1 | w1-b01 | 1 | `accountLockException` (account_lock_exception 1) | - | - |
| 2 | `accountJournalGroup` | 2 | w2-b01 | 2 | `accountJournalGroup` (account_journal_group 2) | - | - |
| 3 | `productBaseUnit` | 2 | w2-b01 | 2 | `productBaseUnit` (product_base_unit 2) | - | - |
| 4 | `productDocument` | 2 | w2-b01 | 2 | `productDocument` (product_document 2) | - | - |
| 5 | `stockScrapReasonTag` | 2 | w2-b01 | 3 | `stockScrapReasonTag` (stock_scrap_reason_tag 3) | - | - |
| 6 | `productRemoval` | 2 | w2-b01 | 4 | `productRemoval` (product_removal 4) | - | - |
| 7 | `returnReason` | 2 | w2-b02 | 5 | `returnReason` (return_reason 5) | - | - |
| 8 | `stockStorageCategory` | 2 | w2-b02 | 6 | `stockStorageCategory` (stock_storage_category 6) | - | - |
| 9 | `accountCashRounding` | 2 | w2-b02 | 7 | `accountCashRounding` (account_cash_rounding 2, account_cash_rounding_res_currency_rel 1, account_cash_rounding_res_partner_category_rel 2, account_cash_rounding_account_payment_method_line_rel 2) | - | - |
| 10 | `stockPackageType` | 2 | w2-b02 | 7 | `stockPackageType` (stock_package_type 3, stock_package_type_stock_putaway_rule_rel 2, stock_package_type_stock_route_rel 2) | - | `addons/stock/tests/test_batch_picking.py` |
| 11 | `productPricelist` | 2 | w2-b02 | 9 | `productPricelist` (product_pricelist 9) | - | - |
| 12 | `accountIncoterms` | 2 | w2-b03 | 11 | `accountIncoterms` (account_incoterms 11) | - | - |
| 13 | `accountReport` | 2 | w2-b03 | 17 | `accountReport` (account_report 7, account_report_column 8, account_report_section_rel 2) | - | - |
| 14 | `productCategory` | 2 | w2-b03 | 24 | `productCategory` (product_category 20, product_category_stock_picking_type_rel 4) | - | `addons/purchase_stock/tests/test_purchase_order_suggest.py` |
| 15 | `accountTaxGroup` | 2 | w2-b03 | 27 | `accountTaxGroup` (account_tax_group 27) | - | `addons/sale/tests/test_sale_order.py` |
| 16 | `accountPaymentTerm` | 2 | w2-b03 | 28 | `accountPaymentTerm` (account_payment_term 13, account_payment_term_line 15) | - | - |
| 17 | `uomUom` | 2 | w2-b04 | 30 | `uomUom` (uom_uom 30) | - | - |
| 18 | `productTemplateUomUomRel` | 2 | w2-b04 | 2 | `productTemplateUomUomRel` (product_template_uom_uom_rel 2) | - | - |
| 19 | `accountFullReconcile` | 2 | w2-b04 | 42 | `accountFullReconcile` (account_full_reconcile 42) | - | - |
| 20 | `accountAccountTag` | 2 | w2-b04 | 68 | `accountAccountTag` (account_account_tag 15, account_account_tag_account_move_line_rel 51, account_account_tag_account_tax_repartition_line_rel 1, account_account_tag_product_template_rel 1) | - | - |
| 21 | `accountAccount` | 2 | w2-b04 | 461 | `accountAccount` (account_account 213, account_account_res_company_rel 213, account_account_account_tag 34, account_account_tax_default_rel 1) | - | `addons/account/tests/test_tour.py` |
| 22 | `productTag` | 2 | w2-b05 | 487 | `productTag` (product_tag 10, product_tag_product_product_rel 1, product_tag_product_template_rel 476) | - | - |
| 23 | `stockReference` | 2 | w2-b05 | 524 | `stockReference` (stock_reference 121, stock_reference_move_rel 281, stock_reference_purchase_rel 8, stock_reference_sale_rel 114) | - | - |
| 24 | `productAttribute` | 2 | w2-b05 | 853 | `productAttribute` (product_attribute 40, product_attribute_product_template_rel 410, product_attribute_value 403) | - | `addons/purchase/tests/test_purchase_product_catalog.py`, `addons/sale/tests/test_product_attribute_value.py`, `addons/sale/tests/test_sale_combo_configurator.py`, `addons/sale/tests/test_sale_order.py`, `addons/stock/tests/test_report_tours.py` |
| 25 | `productAttributeValueProductTemplateAttributeLineRel` | 2 | w2-b05 | 1642 | `productAttributeValueProductTemplateAttributeLineRel` (product_attribute_value_product_template_attribute_line_rel 1642) | - | - |
| 26 | `accountReportLine` | 3 | w3-b01 | 2 | `accountReportLine` (account_report_line 2) | `accountReport` | - |
| 27 | `accountReconcileModel` | 3 | w3-b01 | 20 | `accountReconcileModel` (account_reconcile_model 9, account_reconcile_model_res_partner_rel 1, account_reconcile_model_line 10) | `accountAccount` | - |
| 28 | `accountReconcileModelLineAccountTaxRel` | 3 | w3-b01 | 1 | `accountReconcileModelLineAccountTaxRel` (account_reconcile_model_line_account_tax_rel 1) | - | - |
| 29 | `accountJournal` | 3 | w3-b01 | 26 | `accountJournal` (account_journal 25, account_journal_account_reconcile_model_rel 1) | `accountJournalGroup`, `accountAccount` | `addons/account/tests/test_tour.py` |
| 30 | `accountFiscalPosition` | 3 | w3-b01 | 57 | `accountFiscalPosition` (account_fiscal_position 4, account_fiscal_position_account 1, account_fiscal_position_res_country_state_rel 2, account_fiscal_position_account_tax_rel 50) | `accountAccount` | `addons/sale/tests/test_sale_order.py` |
| 31 | `stockLocation` | 3 | w3-b02 | 164 | `stockLocation` (stock_location 62, stock_location_stock_picking_type_rel 2); `stockPickingType` (stock_picking_type 40, picking_type_favorite_user_rel 1); `stockRoute` (stock_route 13, stock_route_categ 1, stock_route_move 2, stock_route_product 1, stock_route_warehouse 15, stock_rule 21); `stockWarehouse` (stock_warehouse 5, stock_wh_resupply_table 1) | `stockStorageCategory` | `addons/purchase_stock/tests/test_purchase_order_suggest.py`, `addons/purchase_stock/tests/test_stock_orderpoint.py`, `addons/stock/tests/test_batch_picking.py`, `addons/stock/tests/test_report_tours.py`, `addons/stock/tests/test_stock_flow.py` |
| 32 | `saleOrderLineStockRouteRel` | 3 | w3-b02 | 1 | `saleOrderLineStockRouteRel` (sale_order_line_stock_route_rel 1) | - | - |
| 33 | `productTemplate` | 3 | w3-b02 | 439 | `productTemplate` (product_template 439) | `productBaseUnit`, `productCategory` | `addons/purchase/tests/test_purchase_order_product_catalog.py`, `addons/purchase/tests/test_purchase_product_catalog.py`, `addons/sale/tests/test_product_attribute_value.py`, `addons/sale/tests/test_sale_combo_configurator.py`, `addons/sale/tests/test_sale_order.py`, `addons/sale/tests/test_sale_order_product_catalog.py`, `addons/stock/tests/test_report_tours.py` |
| 34 | `productOptionalRel` | 3 | w3-b02 | 3 | `productOptionalRel` (product_optional_rel 3) | - | - |
| 35 | `accountTax` | 3 | w3-b02 | 2574 | `accountTax` (account_tax 65, account_tax_alternatives 2, account_tax_filiation_rel 5, account_tax_purchase_order_line_rel 35, account_tax_repartition_line 260, account_tax_sale_order_line_rel 455, product_supplier_taxes_rel 876, product_taxes_rel 876) | `accountTaxGroup`, `accountAccount` | `addons/account/tests/test_tour.py`, `addons/sale/tests/test_sale_order.py` |
| 36 | `stockPickingBatch` | 4 | w4-b01 | 2 | `stockPickingBatch` (stock_picking_batch 2) | `stockLocation` | `addons/stock/tests/test_batch_picking.py` |
| 37 | `stockPackage` | 4 | w4-b01 | 3 | `stockPackage` (stock_package 3) | `stockPackageType`, `stockLocation` | `addons/stock/tests/test_batch_picking.py`, `addons/stock/tests/test_stock_flow.py` |
| 38 | `accountBankStatement` | 4 | w4-b01 | 4 | `accountBankStatement` (account_bank_statement 2, account_bank_statement_ir_attachment_rel 2) | `accountJournal` | - |
| 39 | `accountReportExpression` | 4 | w4-b01 | 4 | `accountReportExpression` (account_report_expression 3, account_report_external_value 1) | `accountReportLine` | - |
| 40 | `accountPaymentMethod` | 4 | w4-b01 | 16 | `accountPaymentMethod` (account_payment_method 2, account_payment_method_line 14) | `accountJournal` | - |
| 41 | `purchaseOrder` | 4 | w4-b02 | 27 | `purchaseOrder` (purchase_order 20, purchase_order_stock_picking_rel 7) | `accountPaymentTerm`, `accountFiscalPosition`, `stockLocation` | `addons/purchase/tests/test_purchase_flow.py`, `addons/purchase/tests/test_purchase_product_catalog.py`, `addons/purchase_stock/tests/test_purchase_order_suggest.py` |
| 42 | `productTemplateAttributeLine` | 4 | w4-b03 | 2052 | `productTemplateAttributeLine` (product_template_attribute_line 410, product_template_attribute_value 1642) | `productAttribute`, `productTemplate` | - |
| 43 | `productTemplateAttributeExcludedValueIdsRel` | 4 | w4-b03 | 1 | `productTemplateAttributeExcludedValueIdsRel` (product_template_attribute_excluded_value_ids_rel 1) | - | - |
| 44 | `productTemplateAttributeValueSaleOrderLineRel` | 4 | w4-b03 | 1 | `productTemplateAttributeValueSaleOrderLineRel` (product_template_attribute_value_sale_order_line_rel 1) | - | - |
| 45 | `productTemplateAttributeValuePurchaseOrderLineRel` | 4 | w4-b03 | 2 | `productTemplateAttributeValuePurchaseOrderLineRel` (product_template_attribute_value_purchase_order_line_rel 2) | - | - |
| 46 | `templateAttributeValueStockMoveRel` | 4 | w4-b03 | 2 | `templateAttributeValueStockMoveRel` (template_attribute_value_stock_move_rel 2) | - | - |
| 47 | `productProduct` | 4 | w4-b04 | 5064 | `productProduct` (product_product 1393, customer_product_reference 1, product_product_uom_uom_rel 1, product_uom 1, product_variant_combination 3109, stock_warehouse_orderpoint 30); `productSupplierinfo` (product_supplierinfo 529) | `productBaseUnit`, `uomUom`, `stockLocation`, `productTemplate` | `addons/account/tests/test_tour.py`, `addons/purchase/tests/test_purchase_product_catalog.py`, `addons/purchase_stock/tests/test_purchase_order_suggest.py`, `addons/purchase_stock/tests/test_stock_orderpoint.py`, `addons/sale/tests/test_controllers.py`, `addons/sale/tests/test_sale_order.py`, `addons/sale_stock/tests/test_packaging_tours.py`, `addons/stock/tests/test_batch_picking.py`, `addons/stock/tests/test_picking_tours.py`, `addons/stock/tests/test_report_tours.py`, `addons/stock/tests/test_stock_flow.py` |
| 48 | `stockPutawayRule` | 5 | w5-b01 | 1 | `stockPutawayRule` (stock_putaway_rule 1) | `stockLocation`, `productProduct` | - |
| 49 | `stockPackageHistory` | 5 | w5-b01 | 2 | `stockPackageHistory` (stock_package_history 1, stock_package_history_stock_picking_rel 1) | `stockLocation`, `stockPackage` | - |
| 50 | `stockStorageCategoryCapacity` | 5 | w5-b01 | 2 | `stockStorageCategoryCapacity` (stock_storage_category_capacity 2) | `stockStorageCategory`, `stockPackageType`, `productProduct` | - |
| 51 | `productCombo` | 5 | w5-b01 | 14 | `productCombo` (product_combo 3, product_combo_item 8, product_combo_product_template_rel 3) | `productProduct` | `addons/sale/tests/test_sale_combo_configurator.py` |
| 52 | `productPricelistItem` | 5 | w5-b01 | 251 | `productPricelistItem` (product_pricelist_item 251) | `productPricelist`, `productCategory`, `productTemplate`, `productProduct` | - |
| 53 | `stockLot` | 5 | w5-b02 | 254 | `stockLot` (stock_lot 254) | `stockLocation`, `productProduct` | `addons/stock/tests/test_picking_tours.py`, `addons/stock/tests/test_stock_flow.py` |
| 54 | `stockQuant` | 6 | w6-b01 | 247 | `stockQuant` (stock_quant 247) | `stockLocation`, `stockPackage`, `productProduct`, `stockLot` | `addons/purchase_stock/tests/test_purchase_order_suggest.py`, `addons/stock/tests/test_batch_picking.py`, `addons/stock/tests/test_picking_tours.py`, `addons/stock/tests/test_stock_flow.py` |
| 55 | `saleOrder` | 6 | w6-b01 | 592 | `saleOrder` (sale_order 129, sale_order_tag_rel 8, sale_order_transaction_rel 0, sale_order_line 455) | `productPricelist`, `accountPaymentTerm`, `uomUom`, `accountFiscalPosition`, `stockLocation`, `productProduct`, `productCombo` | `addons/sale/tests/test_controllers.py`, `addons/sale/tests/test_sale_combo_configurator.py`, `addons/sale/tests/test_sale_order.py`, `addons/sale/tests/test_sale_order_ui.py` |
| 56 | `saleOrderLineAccrualMoveRel` | 6 | w6-b01 | 0 | `saleOrderLineAccrualMoveRel` (sale_order_line_accrual_move_rel 0) | - | - |
| 57 | `saleOrderLineInvoiceRel` | 6 | w6-b01 | 384 | `saleOrderLineInvoiceRel` (sale_order_line_invoice_rel 384) | - | - |
| 58 | `productAttributeCustomValue` | 7 | w7-b01 | 1 | `productAttributeCustomValue` (product_attribute_custom_value 1) | `productTemplateAttributeLine`, `saleOrder` | - |
| 59 | `purchaseOrderLine` | 7 | w7-b01 | 35 | `purchaseOrderLine` (purchase_order_line 35, purchase_order_line_accrual_move_rel 0) | `uomUom`, `stockLocation`, `purchaseOrder`, `productProduct`, `saleOrder` | - |
| 60 | `stockPicking` | 7 | w7-b01 | 306 | `stockPicking` (stock_picking 306) | `stockLocation`, `stockPickingBatch`, `saleOrder` | `addons/purchase_stock/tests/test_purchase_order_suggest.py`, `addons/stock/tests/test_batch_picking.py`, `addons/stock/tests/test_picking_tours.py`, `addons/stock/tests/test_stock_flow.py` |
| 61 | `accountMoveLine` | 8 | w8-b01 | 21602 | `accountMove` (account_move 2389, account_bank_statement_line 768, account_move__account_payment 77, account_move_purchase_order_rel 2, adjusting_entries__account_move 0); `accountMoveLine` (account_move_line 11505, account_move_line_account_tax_rel 6106); `accountPartialReconcile` (account_partial_reconcile 78); `accountPayment` (account_payment 677, account_payment_account_bank_statement_line_rel 0) | `accountCashRounding`, `accountTaxGroup`, `accountPaymentTerm`, `uomUom`, `accountFullReconcile`, `accountAccount`, `accountJournal`, `accountFiscalPosition`, `accountTax`, `accountBankStatement`, `accountPaymentMethod`, `productProduct`, `purchaseOrderLine` | `addons/account/tests/test_tour.py` |
| 62 | `stockMove` | 9 | w9-b01 | 751 | `stockMove` (stock_move 748, account_analytic_line_stock_move_rel 0, stock_move_created_purchase_line_rel 1, stock_move_move_rel 1, stock_move_stock_scrap_reason_tag_rel 1) | `uomUom`, `stockLocation`, `productProduct`, `saleOrder`, `purchaseOrderLine`, `stockPicking`, `accountMoveLine` | `addons/purchase_stock/tests/test_purchase_order_suggest.py`, `addons/stock/tests/test_batch_picking.py`, `addons/stock/tests/test_stock_flow.py` |
| 63 | `productValue` | 10 | w10-b01 | 34 | `productValue` (product_value 34) | `productProduct`, `stockLot`, `stockMove` | - |
| 64 | `stockMoveLine` | 10 | w10-b01 | 331 | `stockMoveLine` (stock_move_line 331, stock_move_line_consume_rel 0) | `uomUom`, `stockLocation`, `stockPackage`, `productProduct`, `stockPackageHistory`, `stockLot`, `stockPicking`, `stockMove` | - |

### Acceptance per unit

Raw-SQL failures (from `.migration/conformance.md`, per-unit list of 71) sit on the unit that completes every register row the test needs; a register row is owned by the first unit in migration order among the tables it names, and later units naming it re-check it. Reports and cron rows follow the same owner rule. Every unit pauses `base.autovacuum_job` during its load window.

- `accountLockException`: autovacuum pause only
- `accountJournalGroup`: autovacuum pause only
- `productBaseUnit`: autovacuum pause only
- `productDocument`: pause crons `account.ir_cron_account_move_send` (A)
- `stockScrapReasonTag`: autovacuum pause only
- `productRemoval`: autovacuum pause only
- `returnReason`: autovacuum pause only
- `stockStorageCategory`: autovacuum pause only
- `accountCashRounding`: owns register rows write sql 3 (`addons/account/models/account_account.py:1362`); junction refs into later or same-wave units `account_cash_rounding_account_payment_method_line_rel.account_payment_method_line_id` -> `accountPaymentMethod`
- `stockPackageType`: pause crons `stock.ir_cron_scheduler_action` (B); junction refs into later or same-wave units `stock_package_type_stock_putaway_rule_rel.stock_putaway_rule_id` -> `stockPutawayRule`, `stock_package_type_stock_route_rel.stock_route_id` -> `stockLocation`
- `productPricelist`: autovacuum pause only
- `accountIncoterms`: autovacuum pause only
- `accountReport`: autovacuum pause only
- `productCategory`: re-checks register rows write sql 3 (owner `accountCashRounding`); SQL-view reports 14 `vendor.delay.report` (owner), 15 `-` (owner); pause crons `stock.ir_cron_scheduler_action` (B); forward refs (never filled, listed as never_filled_refs) `fk_integrity:product_category->product_removal(removal_strategy_id)` -> `productRemoval`: profile shows 0 filled rows; user setting only: set from the form (stock/views/product_views.xml:23), read at stock/models/stock_quant.py:653; junction refs into later or same-wave units `product_category_stock_picking_type_rel.stock_picking_type_id` -> `stockLocation`
- `accountTaxGroup`: autovacuum pause only
- `accountPaymentTerm`: autovacuum pause only
- `uomUom`: SQL-view reports 2 `account.invoice.report` (owner), 7 `purchase.report` (owner), 8 `report.stock.quantity` (owner), 13 `sale.report` (owner), 14 `vendor.delay.report` (recheck of `productCategory`), 15 `-` (recheck of `productCategory`); pause crons `account.ir_cron_auto_post_draft_entry` (B), `stock.ir_cron_scheduler_action` (B); forward refs (never filled, listed as never_filled_refs) `fk_integrity:uom_uom->stock_package_type(package_type_id)` -> `stockPackageType`: profile shows 0 filled rows; user setting only: field at stock/models/product.py:1346, no code assigns it
- `productTemplateUomUomRel`: junction refs into later or same-wave units `product_template_uom_uom_rel.product_template_id` -> `productTemplate`, `product_template_uom_uom_rel.uom_uom_id` -> `uomUom`
- `accountFullReconcile`: pause crons `account.ir_cron_auto_post_draft_entry` (B), `account.ir_cron_post_stock_valuation` (B)
- `accountAccountTag`: pause crons `account.ir_cron_auto_post_draft_entry` (B); junction refs into later or same-wave units `account_account_tag_account_move_line_rel.account_move_line_id` -> `accountMoveLine`, `account_account_tag_account_tax_repartition_line_rel.account_tax_repartition_line_id` -> `accountTax`, `account_account_tag_product_template_rel.product_template_id` -> `productTemplate`
- `accountAccount`: raw-SQL failures 2 (C3 1, C4 1): account: `TestAccountAccount.test_unmerge`; account: `TestAccountMergeWizard.test_merge`; owns register rows write sql 2 (`addons/account/models/account_account.py:1341`), write sql 4 (`addons/account/models/account_account.py:1441`), write sql 5 (`addons/account/models/account_account.py:1472`), write sql 12 (`addons/account/wizard/account_merge_wizard.py:185`), write sql 13 (`addons/account/wizard/account_merge_wizard.py:197`), write sql 14 (`addons/account/wizard/account_merge_wizard.py:209`); mirrored link tables `account_account_res_company_rel` (`account.account.company_ids`); pause crons `account.ir_cron_auto_post_draft_entry` (B), `account.ir_cron_post_stock_valuation` (B); junction refs into later or same-wave units `account_account_account_tag.account_account_tag_id` -> `accountAccountTag`, `account_account_tax_default_rel.tax_id` -> `accountTax`
- `productTag`: junction refs into later or same-wave units `product_tag_product_product_rel.product_product_id` -> `productProduct`, `product_tag_product_template_rel.product_template_id` -> `productTemplate`
- `stockReference`: pause crons `stock.ir_cron_scheduler_action` (B); junction refs into later or same-wave units `stock_reference_move_rel.move_id` -> `stockMove`, `stock_reference_purchase_rel.purchase_id` -> `purchaseOrder`, `stock_reference_sale_rel.sale_id` -> `saleOrder`
- `productAttribute`: junction refs into later or same-wave units `product_attribute_product_template_rel.product_template_id` -> `productTemplate`
- `productAttributeValueProductTemplateAttributeLineRel`: junction refs into later or same-wave units `product_attribute_value_product_template_attribute_line_rel.product_attribute_value_id` -> `productAttribute`, `product_attribute_value_product_template_attribute_line_rel.product_template_attribute_line_id` -> `productTemplateAttributeLine`
- `accountReportLine`: autovacuum pause only
- `accountReconcileModel`: raw-SQL failures 1 (C6 1): account: `TestAccountAnalyticAccount.test_cross_analytics_computing`; owns register rows read fragment 186 (`addons/analytic/models/analytic_mixin.py:132`), read fragment 187 (`addons/analytic/models/analytic_mixin.py:143`); re-checks register rows write sql 2 (owner `accountAccount`)
- `accountReconcileModelLineAccountTaxRel`: junction refs into later or same-wave units `account_reconcile_model_line_account_tax_rel.account_reconcile_model_line_id` -> `accountReconcileModel`, `account_reconcile_model_line_account_tax_rel.account_tax_id` -> `accountTax`
- `accountJournal`: re-checks register rows write sql 2 (owner `accountAccount`); pause crons `payment.processing_cron` (A), `payment.post_processing_cron` (A, inactive), `account.ir_cron_auto_post_draft_entry` (B), `account.ir_cron_post_stock_valuation` (B); junction refs into later or same-wave units `account_journal_account_reconcile_model_rel.account_reconcile_model_id` -> `accountReconcileModel`
- `accountFiscalPosition`: re-checks register rows write sql 2 (owner `accountAccount`); pause crons `account.ir_cron_auto_post_draft_entry` (B), `account.ir_cron_post_stock_valuation` (B); junction refs into later or same-wave units `account_fiscal_position_account_tax_rel.account_tax_id` -> `accountTax`
- `stockLocation`: re-checks register rows write sql 2 (owner `accountAccount`); SQL-view reports 7 `purchase.report` (recheck of `uomUom`), 8 `report.stock.quantity` (recheck of `uomUom`); mirrored link tables `stock_route_product` (`stock.route.product_ids`), `stock_route_warehouse` (`stock.route.warehouse_ids`), `picking_type_favorite_user_rel` (`stock.picking.type.favorite_user_ids`); pause crons `account.ir_cron_post_stock_valuation` (B), `stock.ir_cron_scheduler_action` (B); U1: the scope must load with only the declared shadow columns: the SQL view at addons/stock/report/report_stock_quantity.py:194 (register sql read 240, report 8) reads stock_location.parent_path, which is not a shadow column (.migration/conformance.md, U1); junction refs into later or same-wave units `stock_route_move.move_id` -> `stockMove`, `stock_route_product.product_id` -> `productTemplate`
- `saleOrderLineStockRouteRel`: junction refs into later or same-wave units `sale_order_line_stock_route_rel.sale_order_line_id` -> `saleOrder`, `sale_order_line_stock_route_rel.stock_route_id` -> `stockLocation`
- `productTemplate`: re-checks register rows write sql 3 (owner `accountCashRounding`); SQL-view reports 2 `account.invoice.report` (recheck of `uomUom`), 7 `purchase.report` (recheck of `uomUom`), 8 `report.stock.quantity` (recheck of `uomUom`), 13 `sale.report` (recheck of `uomUom`), 14 `vendor.delay.report` (recheck of `productCategory`), 15 `-` (recheck of `productCategory`); pause crons `stock.ir_cron_scheduler_action` (B)
- `productOptionalRel`: junction refs into later or same-wave units `product_optional_rel.dest_id` -> `productTemplate`, `product_optional_rel.src_id` -> `productTemplate`
- `accountTax`: re-checks register rows write sql 2 (owner `accountAccount`); mirrored link tables `account_tax_filiation_rel` (`account.tax.children_tax_ids`), `account_tax_alternatives` (`account.tax.replacing_tax_ids`); pause crons `payment.post_processing_cron` (A, inactive); junction refs into later or same-wave units `account_tax_purchase_order_line_rel.purchase_order_line_id` -> `purchaseOrderLine`, `account_tax_sale_order_line_rel.sale_order_line_id` -> `saleOrder`, `product_supplier_taxes_rel.prod_id` -> `productTemplate`, `product_taxes_rel.prod_id` -> `productTemplate`
- `stockPickingBatch`: pause crons `stock.ir_cron_scheduler_action` (B)
- `stockPackage`: pause crons `stock.ir_cron_scheduler_action` (B)
- `accountBankStatement`: pause crons `payment.post_processing_cron` (A, inactive)
- `accountReportExpression`: autovacuum pause only
- `accountPaymentMethod`: re-checks register rows write sql 2 (owner `accountAccount`)
- `purchaseOrder`: SQL-view reports 5 `purchase.bill.line.match` (owner), 6 `purchase.bill.union` (owner), 7 `purchase.report` (recheck of `uomUom`); pause crons `purchase.purchase_send_reminder_mail` (A); junction refs into later or same-wave units `purchase_order_stock_picking_rel.stock_picking_id` -> `stockPicking`
- `productTemplateAttributeLine`: autovacuum pause only
- `productTemplateAttributeExcludedValueIdsRel`: junction refs into later or same-wave units `product_template_attribute_excluded_value_ids_rel.excluded_product_template_attribute_value_id` -> `productTemplateAttributeLine`, `product_template_attribute_excluded_value_ids_rel.product_template_attribute_value_id` -> `productTemplateAttributeLine`
- `productTemplateAttributeValueSaleOrderLineRel`: junction refs into later or same-wave units `product_template_attribute_value_sale_order_line_rel.product_template_attribute_value_id` -> `productTemplateAttributeLine`, `product_template_attribute_value_sale_order_line_rel.sale_order_line_id` -> `saleOrder`
- `productTemplateAttributeValuePurchaseOrderLineRel`: junction refs into later or same-wave units `product_template_attribute_value_purchase_order_line_rel.product_template_attribute_value_id` -> `productTemplateAttributeLine`, `product_template_attribute_value_purchase_order_line_rel.purchase_order_line_id` -> `purchaseOrderLine`
- `templateAttributeValueStockMoveRel`: junction refs into later or same-wave units `template_attribute_value_stock_move_rel.template_attribute_value_id` -> `productTemplateAttributeLine`, `template_attribute_value_stock_move_rel.move_id` -> `stockMove`
- `productProduct`: SQL-view reports 2 `account.invoice.report` (recheck of `uomUom`), 7 `purchase.report` (recheck of `uomUom`), 8 `report.stock.quantity` (recheck of `uomUom`), 13 `sale.report` (recheck of `uomUom`), 14 `vendor.delay.report` (recheck of `productCategory`), 15 `-` (recheck of `productCategory`); pause crons `payment.post_processing_cron` (A, inactive), `account.ir_cron_auto_post_draft_entry` (B), `stock.ir_cron_scheduler_action` (B); junction refs into later or same-wave units `product_variant_combination.product_template_attribute_value_id` -> `productTemplateAttributeLine`
- `stockPutawayRule`: pause crons `stock.ir_cron_scheduler_action` (B)
- `stockPackageHistory`: junction refs into later or same-wave units `stock_package_history_stock_picking_rel.stock_picking_id` -> `stockPicking`
- `stockStorageCategoryCapacity`: autovacuum pause only
- `productCombo`: autovacuum pause only
- `productPricelistItem`: autovacuum pause only
- `stockLot`: pause crons `stock.ir_cron_scheduler_action` (B)
- `stockQuant`: raw-SQL failures 1 (C5 1): stock: `TestInventory.test_inventory_7`; owns register rows write sql 20 (`addons/stock/models/stock_quant.py:1251`); SQL-view reports 8 `report.stock.quantity` (recheck of `uomUom`); pause crons `stock.ir_cron_scheduler_action` (B)
- `saleOrder`: re-checks register rows read fragment 186 (owner `accountReconcileModel`), read fragment 187 (owner `accountReconcileModel`); SQL-view reports 13 `sale.report` (recheck of `uomUom`); pause crons `payment.processing_cron` (A), `payment.post_processing_cron` (A, inactive), `account.ir_cron_auto_post_draft_entry` (B), `account.ir_cron_post_stock_valuation` (B), `sale.send_pending_emails_cron` (A, inactive)
- `saleOrderLineAccrualMoveRel`: junction refs into later or same-wave units `sale_order_line_accrual_move_rel.move_id` -> `accountMoveLine`, `sale_order_line_accrual_move_rel.order_line_id` -> `saleOrder`
- `saleOrderLineInvoiceRel`: mirrored link tables `sale_order_line_invoice_rel` (`sale.order.line.invoice_lines`); junction refs into later or same-wave units `sale_order_line_invoice_rel.invoice_line_id` -> `accountMoveLine`, `sale_order_line_invoice_rel.order_line_id` -> `saleOrder`
- `productAttributeCustomValue`: autovacuum pause only
- `purchaseOrderLine`: raw-SQL failures 1 (C7 1): purchase_stock: `TestUninstallPurchaseStock.test_qty_received_method`; owns register rows write sql 17 (`addons/purchase_stock/models/purchase_order_line.py:24`); re-checks register rows read fragment 186 (owner `accountReconcileModel`), read fragment 187 (owner `accountReconcileModel`); SQL-view reports 5 `purchase.bill.line.match` (recheck of `purchaseOrder`), 7 `purchase.report` (recheck of `uomUom`), 14 `vendor.delay.report` (recheck of `productCategory`); pause crons `account.ir_cron_post_stock_valuation` (B), `stock.ir_cron_scheduler_action` (B); junction refs into later or same-wave units `purchase_order_line_accrual_move_rel.move_id` -> `accountMoveLine`
- `stockPicking`: SQL-view reports 7 `purchase.report` (recheck of `uomUom`), 15 `-` (recheck of `productCategory`); pause crons `payment.post_processing_cron` (A, inactive), `stock.ir_cron_scheduler_action` (B)
- `accountMoveLine`: raw-SQL failures 66 (C1 65, C2 1): account: `TestAccountMoveOutInvoiceOnchanges.test_date_reversal_exchange_move (format_incrementor='month', expected_date='2017-01-31')`; account: `TestAccountMoveOutInvoiceOnchanges.test_date_reversal_exchange_move (format_incrementor='year', expected_date='2017-12-31')`; account: `TestAccountMovePaymentsWidget.test_payments_with_exchange_difference_invoice_with_caba`; account: `TestAccountMovePaymentsWidget.test_payments_with_exchange_difference_payment_with_caba`; account: `TestAccountMoveReconcile.test_caba_dest_acc_reconciliation_partial_pmt`; account: `TestAccountMoveReconcile.test_caba_mix_reconciliation`; account: `TestAccountMoveReconcile.test_caba_undo_reconciliation`; account: `TestAccountMoveReconcile.test_full_reconcile_bunch_lines (sub_test_name='All batches', login='simple_accountman')`; account: `TestAccountMoveReconcile.test_full_reconcile_bunch_lines (sub_test_name='Batch in company currency', login='simple_accountman')`; account: `TestAccountMoveReconcile.test_full_reconcile_bunch_lines (sub_test_name='Batch in foreign currency', login='simple_accountman')`; account: `TestAccountMoveReconcile.test_full_reconcile_bunch_lines (sub_test_name='Batch with multiple currencies', login='simple_accountman')`; account: `TestAccountMoveReconcile.test_full_reconcile_foreign_currency_rounding_difference_credit_larger`; account: `TestAccountMoveReconcile.test_full_reconcile_foreign_currency_rounding_difference_debit_larger`; account: `TestAccountMoveReconcile.test_full_reconcile_unlink_clears_matching_number`; account: `TestAccountMoveReconcile.test_matching_loop`; account: `TestAccountMoveReconcile.test_matching_number_full_reconcile`; account: `TestAccountMoveReconcile.test_matching_number_partial_multi_reconcile`; account: `TestAccountMoveReconcile.test_matching_number_partial_multi_separate_reconcile`; account: `TestAccountMoveReconcile.test_matching_number_partial_single_reconcile`; account: `TestAccountMoveReconcile.test_matching_number_unreconcile_multi`; account: `TestAccountMoveReconcile.test_modify_all_reconciled_lines`; account: `TestAccountMoveReconcile.test_partial_reconcile_amounts_of_several_matching_lines`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_exchange_difference_transfer_account_check_entries_1`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_exchange_difference_transfer_account_check_entries_2`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_exchange_difference_transfer_account_check_entries_3`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_revert`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_tax_grid_multi_taxes`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_workflow_multi_currency`; account: `TestAccountMoveReconcile.test_reconcile_cash_basis_workflow_single_currency`; account: `TestAccountMoveReconcile.test_reconcile_draft_cash_basis_surprise_use_case`; account: `TestAccountMoveReconcile.test_reconcile_draft_cash_basis_use_case`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_credit_foreign_currency_credit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_credit_foreign_currency_credit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_credit_foreign_currency_debit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_credit_foreign_currency_debit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_debit_foreign_currency_credit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_debit_foreign_currency_credit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_debit_foreign_currency_debit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_one_debit_foreign_currency_debit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_same_foreign_currency_credit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_same_foreign_currency_credit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_same_foreign_currency_debit_expense_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_exchange_difference_on_partial_same_foreign_currency_debit_income_full_payment`; account: `TestAccountMoveReconcile.test_reconcile_foreign_currency_rounding_issue (sub_test_name='sign: -1, reco_account: Accounts Receivable (copy)')`; account: `TestAccountMoveReconcile.test_reconcile_foreign_currency_rounding_issue (sub_test_name='sign: -1, reco_account: Product Sales (copy)')`; account: `TestAccountMoveReconcile.test_reconcile_foreign_currency_rounding_issue (sub_test_name='sign: 1, reco_account: Accounts Receivable (copy)')`; account: `TestAccountMoveReconcile.test_reconcile_foreign_currency_rounding_issue (sub_test_name='sign: 1, reco_account: Product Sales (copy)')`; account: `TestAccountMoveReconcile.test_reconcile_import_same_matching_different_account`; account: `TestAccountMoveReconcile.test_reconcile_import`; account: `TestAccountMoveReconcile.test_reconcile_lines_corner_case_1_zero_balance_same_foreign_currency`; account: `TestAccountMoveReconcile.test_reconcile_lines_corner_case_2_zero_amount_currency_same_foreign_currency`; account: `TestAccountMoveReconcile.test_reconcile_lines_corner_case_3_zero_balance_one_foreign_currency`; account: `TestAccountMoveReconcile.test_reconcile_lines_multiple_in_foreign_currency (rate1=0.3333333333333333, rate2=0.3333333333333333, rate3=0.3333333333333333)`; account: `TestAccountMoveReconcile.test_reconcile_lines_multiple_in_foreign_currency (rate1=0.3333333333333333, rate2=0.3333333333333333, rate3=0.5)`; account: `TestAccountMoveReconcile.test_reconcile_lines_multiple_in_foreign_currency (rate1=0.3333333333333333, rate2=0.5, rate3=0.3333333333333333)`; account: `TestAccountMoveReconcile.test_reconcile_lines_multiple_in_foreign_currency (rate1=0.3333333333333333, rate2=0.5, rate3=0.5)`; account: `TestAccountMoveReconcile.test_reconcile_lines_multiple_in_foreign_currency (rate1=0.5, rate2=0.3333333333333333, rate3=0.3333333333333333)`; account: `TestAccountMoveReconcile.test_reconcile_lines_multiple_in_foreign_currency (rate1=0.5, rate2=0.3333333333333333, rate3=0.5)`; account: `TestAccountMoveReconcile.test_reconcile_lines_multiple_in_foreign_currency (rate1=0.5, rate2=0.5, rate3=0.3333333333333333)`; account: `TestAccountMoveReconcile.test_reconcile_lines_multiple_in_foreign_currency (rate1=0.5, rate2=0.5, rate3=0.5)`; account: `TestAccountMoveReconcile.test_reconcile_partial_reconciliations`; account: `TestAccountMoveReconcile.test_reconcile_special_mexican_workflow_1`; account: `TestAccountMoveReconcile.test_reconcile_special_mexican_workflow_2`; account: `TestAccountMoveReconcile.test_reverse_with_multiple_lines`; account: `TestTransferWizard.test_change_period_reconcile_pair_by_pair_customer_invoices`; account: `TestAccountMoveOutInvoiceOnchanges.test_quick_edit_total_amount`; owns register rows write sql 7 (`addons/account/models/account_full_reconcile.py:30`), write sql 8 (`addons/account/models/account_full_reconcile.py:39`), write sql 9 (`addons/account/models/account_partial_reconcile.py:226`), read sql 106 (`addons/account/models/account_move.py:4548`); re-checks register rows write sql 2 (owner `accountAccount`), read fragment 186 (owner `accountReconcileModel`), read fragment 187 (owner `accountReconcileModel`); SQL-view reports 2 `account.invoice.report` (recheck of `uomUom`), 5 `purchase.bill.line.match` (recheck of `purchaseOrder`), 6 `purchase.bill.union` (recheck of `purchaseOrder`); mirrored link tables `account_move_line_account_tax_rel` (`account.move.line.tax_ids`); pause crons `payment.processing_cron` (A), `payment.post_processing_cron` (A, inactive), `account.ir_cron_auto_post_draft_entry` (B), `account.ir_cron_account_move_send` (A), `account.ir_cron_post_stock_valuation` (B), `stock.ir_cron_scheduler_action` (B), `sale.send_invoice_cron` (A, inactive); forward refs (never filled, listed as never_filled_refs) `fk_integrity:account_move_line->stock_move(stock_move_id)` -> `stockMove`: profile shows 0 filled rows; only repair (repair/models/stock_move.py:169) and l10n_in_boe set it; neither is installed (no repair_order / l10n_in_* table in census.json)
- `stockMove`: SQL-view reports 7 `purchase.report` (recheck of `uomUom`), 8 `report.stock.quantity` (recheck of `uomUom`), 14 `vendor.delay.report` (recheck of `productCategory`), 15 `-` (recheck of `productCategory`); pause crons `account.ir_cron_auto_post_draft_entry` (B), `account.ir_cron_post_stock_valuation` (B), `stock.ir_cron_scheduler_action` (B)
- `productValue`: SQL-view reports 15 `-` (recheck of `productCategory`)
- `stockMoveLine`: SQL-view reports 14 `vendor.delay.report` (recheck of `productCategory`); pause crons `stock.ir_cron_scheduler_action` (B)

### Scheduled jobs with only possible indirect reach (review before any load)

`base.ir_cron_res_users_deletion`, `resource.ir_cron_calendar_clean_up`, `mail.ir_cron_mail_scheduler_action`, `mail.ir_cron_module_update_notification`, `mail.ir_cron_delete_notification`, `mail.ir_cron_mail_gateway_action`, `mail.ir_cron_post_scheduled_message`, `mail.ir_cron_send_scheduled_message`, `mail.ir_cron_mail_end_polls`, `mail.ir_cron_discuss_channel_member_unmute`, `mail.ir_cron_discuss_channel_sync_last_interest_dt`, `auth_signup.ir_cron_auth_signup_send_pending_user_reminder`, `sms.ir_cron_sms_scheduler_action`, `digest.ir_cron_digest_scheduler_action`, `payment.post_processing_cron`, `account.ir_cron_auto_post_draft_entry`, `account.ir_cron_account_move_send`, `account.ir_cron_post_stock_valuation`, `stock.ir_cron_scheduler_action`, `purchase.purchase_send_reminder_mail`, `sale.send_invoice_cron`, `sale.send_pending_emails_cron`

### Plugin findings

- No unit or wave derivation tool at the pin: skills/migration-planning/SKILL.md:90 states the s3.3 rule in prose and no script under skills/ computes units or waves, so this run carries the derivation in .migration/derive_units.py.
- skills/wave-preflight/preflight.py:380 refuses every never_filled_refs entry when connectivity.json source.server is null (a local-socket PostgreSQL source), even though data_profile.json source is the same {database: odoo_src, server: null}. Repro: preflight.py --wave <wave 2 spec built from units.json> --root . -> "profile source (database, server) is not the probed source". The profile (as_of 2026-10-22) is also past the 24h limit at preflight.py:101, so waves 2 and 8 need a fresh live profile and this fix before they preflight.
- skills/migration-planning/SKILL.md:90 orders waves on "code on the write path sets it", but no plugin artifact records ORM field writes (access_patterns.json write patterns are raw SQL only), so the setters are cited by hand in WRITE_PATH_SETTERS.
- skills/migration-planning/SKILL.md:90 has no rule for reference cycles; this derivation merges each cycle into one unit.

