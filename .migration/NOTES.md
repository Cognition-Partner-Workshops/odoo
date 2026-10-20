# Run notes — Odoo PostgreSQL → MongoDB Atlas (board UNT12)

## s2.3 Dependency register: readers and writers outside the ORM storage path

Source: `odoo_src` rebuilt by `.migration/fixtures/build_source.sh` (marker 3, 70 installed modules) and the run-branch code at
`2829802be45` (`mongo-run/unt12`). Scope: the 223 tables + 3 views bucketed `in_scope` in `.migration/table_buckets.json`
(owners product, uom, sale, purchase, stock, account and their 9 bridge modules). Everything that reaches one of them other
than through `odoo/orm` (`BaseModel` create/write/unlink/search/read_group, the storage path) is listed below.

Odoo 20 names: `ir_cron` has no `model_id` (join `ir_cron.ir_actions_server_id → ir_act_server.model_id → ir_model`);
`_auto = False` models define `_table_sql` (the Odoo 20 name for what the ticket calls `_table_query`), consumed by
`odoo/orm/query.py:64` and `:107`; there are no `ir_property` / `ir_translation` / `mail_tracking_value` tables.

Dispositions:

| Code | Meaning |
|---|---|
| **R** rewrite | the statement reads or writes columns of a Mongo-backed table; the owning unit rewrites it against the MongoDB backend (aggregation or ORM call) in its batch |
| **S** id shadow | the statement stays on PostgreSQL; it touches only PostgreSQL-resident tables and/or the `id` of a migrated table, which the id shadow (same table name, `id` PK + `<table>_id_seq`, kept on PostgreSQL) still resolves |
| **B** blocked | cannot run against a Mongo-backed table and no shadow or local rewrite suffices; needs a manager decision before the owning wave |
| orm | on the storage path (ORM calls only); nothing to rewrite, listed so wave scheduling can account for it |

### 1. Scheduled logic (`ir_cron`)

25 cron jobs in `odoo_src` (`ir_cron ⋈ ir_act_server ⋈ ir_model`; every one is `state = 'code'`, body `model.<method>()`).
9 reach an in-scope table, 16 touch framework tables only (mail, bus, digest plumbing, payment, auth, resource,
autovacuum's own `_gc_*` on base models, SMS).

| id | xmlid | model | method (file) | active | in-scope tables reached | disp. |
|---|---|---|---|---|---|---|
| 19 | account.ir_cron_auto_post_draft_entry | account.move | `_autopost_draft_entries` (addons/account/models/account_move.py:7181) | yes, daily | writes account_move, account_move_line via `_post()`; `_post` calls `sequence.mixin._locked_increment` (raw SQL, §3a row 2) | orm (+R through row 2) |
| 20 | account.ir_cron_account_move_send | account.move | `_cron_account_move_send` (account_move.py:7217) | yes, daily | reads account_move, writes `is_move_sent`; `account.move.send._send_mail` (raw SQL on ir_attachment, §3a row 21) | orm (+S through row 21) |
| 21 | account.ir_cron_post_stock_valuation | res.company | `_cron_post_stock_valuation` (addons/account/models/company.py:1454) | yes, daily | `action_close_stock_valuation` writes account_move / account_move_line, reads product_product and stock valuation | orm |
| 22 | stock.ir_cron_scheduler_action | stock.rule | `run_scheduler` (addons/stock/models/stock_rule.py:722) | yes, daily | writes stock_move, stock_picking, purchase_order (buy rule), stock_warehouse_orderpoint; `stock_rule.py:710` calls `stock.quant._quant_tasks()` → `_merge_quants` / `_unlink_zero_quants` (raw SQL, §3a rows 26–27) | orm (+R through rows 26–27) |
| 23 | purchase.purchase_send_reminder_mail | purchase.order | `_send_reminder_mail` (addons/purchase/models/purchase_order.py:1122) | yes, daily | reads purchase_order; writes mail_message (PostgreSQL) | orm |
| 24 | sale.send_invoice_cron | payment.transaction | `_cron_send_invoice` (addons/sale/models/payment_transaction.py:186) | no | reads account_move (`is_move_sent`, `state`), sends invoices | orm |
| 25 | sale.send_pending_emails_cron | sale.order | `_cron_send_pending_emails` (addons/sale/models/sale_order.py:1741) | no | reads/writes sale_order (`pending_email_template_id`) | orm |
| 16 | digest.ir_cron_digest_scheduler_action | digest.digest | `_cron_send_digest_email` → `_compute_kpi_account_total_revenue_value` (addons/account/models/digest.py:13) | yes, daily | `_read_group` on account_move_line (balance by company) | orm |
| 1 | base.autovacuum_job | ir.autovacuum | `_run_vacuum_cleaner` → every `@api.autovacuum`; the only in-scope one is `stock.warehouse.orderpoint._unlink_processed_orderpoints` (addons/stock/models/stock_orderpoint.py:695) | yes, daily | unlinks stock_warehouse_orderpoint rows | orm |

Jobs 19–23 and job 1 (autovacuum, which unlinks in-scope stock_warehouse_orderpoint rows) are active writers on the
source fixture. Wave 0 must deactivate all six on every migration target database before a load or recon and re-enable
them per unit; the recon harness would otherwise count rows a cron wrote between
load and compare. `base_automation` is not installed, so there are no automated actions. The 66 other `ir_act_server`
rows on in-scope models (`usage = 'ir_actions_server'`, `state = 'code'`) are view buttons calling ORM methods (orm).

### 2. `_auto = False` models and PostgreSQL views

Every `_auto = False` class in an installed module was listed (16); 8 have no table of their own (`account.root` and
`account.code.mapping` with `_table_sql = SQL('(0)')`, the abstract mixins `auth_totp.device` / `spreadsheet.mixin`, and the
framework `res.device` / `res.session` / `res.users.apikeys` / `res.users.apikeys.show`). The 5 that read in-scope tables
through `_table_sql` and the 3 that build a PostgreSQL view in `init()`:

| model | kind | source tables | disp. |
|---|---|---|---|
| sale.report (addons/sale/report/sale_report.py:11) | `_table_sql` property: `sale.order.line._search()` subselect grouped | sale_order_line, sale_order, product_product, product_template, uom_uom (+ res_partner, res_currency rate on PostgreSQL) | R |
| purchase.report (addons/purchase/report/purchase_report.py:12) | `_table_sql` property over `purchase.order.line._search()` | purchase_order_line, purchase_order, product_product, product_template, uom_uom, product_category | R |
| account.invoice.report (addons/account/report/account_invoice_report.py:8) | `_table_sql` property over `account.move.line._search()` | account_move_line, account_move, product_product, product_template, uom_uom, account_account | R |
| purchase.bill.union (addons/purchase/report/purchase_bill.py:7) | `_table_sql` property, raw `UNION` SQL | account_move, purchase_order | R |
| purchase.bill.line.match (addons/purchase/models/purchase_bill_line_match.py:9) | `_table_sql` property, raw `UNION` SQL (`_select_po_line`, `_select_am_line`) | purchase_order_line, purchase_order, account_move_line, account_move | R |
| report.stock.quantity (addons/stock/report/report_stock_quantity.py:7) | PostgreSQL view, `init()` at report_stock_quantity.py:194 | stock_move, stock_quant, stock_location, stock_warehouse, product_product, product_template, uom_uom | R |
| stock.avco.report (addons/stock_account/report/stock_avco_audit_report.py:5) | PostgreSQL view, `init()` at :91 | stock_move, stock_picking, product_value, product_product, product_template, product_category, uom_uom (+ ir_default, ir_model_fields) | R |
| vendor.delay.report (addons/purchase_stock/report/vendor_delay_report.py:8) | PostgreSQL view, `init()` at :23 | purchase_order_line, stock_move, stock_move_line, product_product, product_template, product_category, uom_uom | R |

`pg_views` in `odoo_src` holds exactly these 3 plus the framework views `res_device` and `res_session` (out of scope).
No materialised views, no triggers (`pg_trigger` non-internal = 0), no rules, and the only functions in `public` are
`pg_trgm`'s. The 3 `init()` views are on the module-load path: `init()` runs on every `-i`/`-u`, and the view DDL over
`stock_move` against an id-only shadow fails at load, so their rewrite (or a storage-path rule that skips view DDL for
Mongo-backed sources) belongs to wave 0, not to a late wave. The 5 `_table_sql` models fail at the first `search` /
`read_group` instead and go with the unit that owns their driving table (sale.order.line, purchase.order.line,
account.move.line). R here assumes the s3.1 contract keeps id-only shadows; a decision to keep full shadow columns for
report source tables would turn these 8 rows into S.

### 3. Raw SQL in scope and bridge modules

Two APIs bypass `BaseModel`: the cursor (`cr.execute`, `cr.execute_values`, §3a) and `env.execute_query` /
`env.execute_query_dict` (§3b). Framework code they reach with dynamic table names is in §3c.

Coverage: the same 15 modules were also searched for the other ways SQL can reach the cursor — `cr.copy_expert` /
`cr.copy_from` / `cr.mogrify` (0 uses), `cr.fetch*` / `dictfetch*` (every use sits in a method already counted), and the
`odoo.tools.sql` helpers (`drop_view_if_exists` only in the 3 view `init()`s of §2, `index_exists` only in §3a row 1;
`create_index`, `create_column`, `table_exists`, `column_exists` unused; `SQL` objects only feed the two APIs above).
ORM-level DDL (`models.Index`, `models.UniqueIndex`, `models.Constraint`, field `index=`) goes through `_auto_init` and
is the storage path's job, not a register item. Anything reached from framework code with a table name computed at run
time is found by following callers (§3c), not by scanning, so §3c is complete only for the callers in §3a/§3b.

#### 3a. `cr.execute` / `cr.execute_values`

Scanned every `.py` outside `tests/` in the 15 scope + bridge modules for `cr.execute(` / `cr.execute_values(`
(AST walk; tables taken from the string constants of the enclosing method and matched against the 526 source tables).
62 call sites: 58 `execute` + 4 `execute_values`. 1 is not SQL (`stock.warehouse._check_multiwarehouse_group`,
stock_warehouse.py:321 calls `res.config.settings.execute()`), 3 are the view `init()`s of §2, leaving 58 sites in the 32
rows below. Statement verbs come from the SQL text.

| # | model / function (file:line) | sites | verb | in-scope tables | when | disp. |
|---|---|---|---|---|---|---|
| 1 | sequence.mixin `init` (addons/account/models/sequence_mixin.py:56) | 1 | CREATE INDEX | account_move (`_sequence_index` = journal_id, sequence_prefix, sequence_number) | module load | R — skip the DDL for a Mongo-backed model and create the equivalent compound index |
| 2 | sequence.mixin `_locked_increment` (sequence_mixin.py:415) | 1 | UPDATE | account_move.`name` by id; retries on `UniqueViolation` from `account_move._unique_name` (account_move.py:825) | every `_post` (hot) | R — numbering must get its uniqueness from a unique index on the collection and the same retry loop |
| 3 | account.full.reconcile `create` (addons/account/models/account_full_reconcile.py:30, :39) | 2 | UPDATE (execute_values) | account_move_line.full_reconcile_id, account_partial_reconcile.full_reconcile_id | every full reconciliation (hot) | R |
| 4 | account.partial.reconcile `_update_matching_number` (addons/account/models/account_partial_reconcile.py:226) | 1 | UPDATE (execute_values) | account_move_line.matching_number | every reconciliation (hot) | R |
| 5 | account.move.line `_compute_account_id` (addons/account/models/account_move_line.py:729) | 1 | SELECT | account_move_line, account_account, account_account_res_company_rel | line default (warm) | R |
| 6 | account.move.line `_compute_amount_residual` (account_move_line.py:1176) | 1 | SELECT | account_partial_reconcile (+ res_currency) | every line write (hot) | R |
| 7 | account.move `_compute_abnormal_warnings` (addons/account/models/account_move.py:2388) | 1 | SELECT | account_move aggregates per partner | invoice form (warm) | R |
| 8 | account.payment `_compute_stat_buttons_from_reconciliation` (addons/account/models/account_payment.py:761) | 1 | SELECT | account_payment, account_move, account_move_line, account_partial_reconcile, account_account | payment form (warm) | R |
| 9 | account.bank.statement.line `_compute_running_balance` (addons/account/models/account_bank_statement_line.py:201, :223) | 2 | SELECT (window) | account_bank_statement_line, account_bank_statement, account_move | statement line read (warm) | R |
| 10 | account.bank.statement `_get_invalid_statement_ids` (addons/account/models/account_bank_statement.py:331) | 1 | SELECT | account_bank_statement, account_journal | statement validation (warm) | R |
| 11 | account.journal `_get_journals_payment_method_information` (addons/account/models/account_journal.py:364) | 1 | SELECT | account_journal, account_payment_method, account_payment_method_line | journal form (cold) | R |
| 12 | account.journal dashboard, 12 methods (addons/account/models/account_journal_dashboard.py:47, 148, 329, 364, 421, 477, 524, 646, 765, 781, 784, 1005, 1048, 1076): `_compute_last_bank_statement`, `_get_sale_purchase_kpi_amounts`, `_get_json_activity_data`, `_query_has_sequence_holes`, `_compute_has_entries`, `_get_bank_cash_graph_data`, `_get_sale_purchase_graph_data`, `_fill_bank_cash_dashboard_data`, `_fill_sale_purchase_dashboard_data`, `_get_journal_dashboard_bank_running_balance`, `_get_direct_bank_payments`, `_get_journal_dashboard_outstanding_payments` | 14 | SELECT | account_move, account_journal, account_bank_statement, account_bank_statement_line, account_payment (+ mail_activity) | every accounting dashboard render (warm) | R — aggregation pipelines per KPI |
| 13 | account.account `_check_journal_consistency`, `_check_account_type_sales_purchase_journal`, `_check_account_is_bank_journal_bank_account` (addons/account/models/account_account.py:191, :275, :301) | 3 | SELECT | account_account, account_journal, account_payment_method_line | `@api.constrains` on account edits (cold) | R |
| 14 | account.account `_compute_opening_debit_credit` (account_account.py:623) | 1 | SELECT | account_move_line | account form (cold) | R |
| 15 | account.account `_action_unmerge` (account_account.py:1341, 1362, 1391, 1420, 1441, 1472) | 6 | UPDATE | dynamic (:1341–:1420): every table holding a many2one / many2many / reference / many2one_reference to account.account, in-scope (account_move_line, account_journal, account_payment_method_line, product_category, …) and PostgreSQL-resident (res_company); then account_account's own company-dependent JSON columns (:1441, :1472) | unmerge action (cold) | R — Mongo-backed targets and the account row itself; PostgreSQL-resident targets keep their statement |
| 15b | account.account `_action_unmerge` (account_account.py:1490) | 1 | UPDATE | ir_model_data (xmlids of account_account ids) | unmerge action (cold) | S |
| 16 | account.merge.wizard `_action_merge` (addons/account/wizard/account_merge_wizard.py:185, :197, :209) | 3 | UPDATE / DELETE | account_account (`name`, `code_store`, row delete) | merge wizard (cold) | R |
| 17 | account.account.tag `_translate_tax_tags` (addons/account/models/account_account_tag.py:125) | 1 | UPDATE | account_account_tag, account_report_line, account_report | chart template load / language install (cold) | R |
| 18 | account.reconcile.model `action_reconcile_stat` (addons/account/models/account_reconcile_model.py:219) | 1 | SELECT | account_move_line | stat button (cold) | R |
| 19 | product.template `_check_uom_not_in_invoice` (addons/account/models/product.py:246) | 1 | SELECT | account_move_line ⋈ product_product ⋈ product_template ⋈ uom_uom | `@api.constrains('uom_id')` (cold) | R — cross-collection; two-step (ids from one store, filter in the other) |
| 20 | sale.order `_search_invoice_ids` (addons/sale/models/sale_order.py:836) | 1 | SELECT | sale_order_line_invoice_rel, sale_order_line, sale_order, account_move_line, account_move | search on `invoice_ids` (warm) | R |
| 21 | account.move.send `_send_mail` (addons/account/models/account_move_send.py:578) | 1 | UPDATE | ir_attachment.res_id only | invoice sending (warm) | S |
| 22 | chart_template.py module function `preserve_existing_tags_on_taxes` (addons/account/models/chart_template.py:50), `_get_untranslated_translatable_template_model_records` (:1490) | 2 | UPDATE / SELECT | ir_model_data only | chart template upgrade (cold) | S |
| 23 | `get_kpi_summary` (addons/account/models/kpi_provider.py:39, :49) | 2 | SELECT | account_move, account_journal, account_bank_statement_line (+ ir_model_fields, res_users, res_partner) | KPI summary endpoint; runs **without a registry** (multi-database server) | B — no ORM to route through; drop the KPI, serve it from a direct MongoDB read in the HTTP layer, or keep account_move/account_journal columns on a wide shadow: manager decision |
| 24 | res.partner `_clear_removed_edi_formats` (addons/account/models/partner.py:1240) | 1 | UPDATE | none (res_partner, res_company) — uninstall hook of account_edi_ubl_cii | uninstall only | S |
| 25 | `migrate` (addons/account/migrations/1.5/pre-migrate.py:2) | 1 | UPDATE | account_account | module upgrade from account < 1.5 only; never reached in this run (fresh install at 20.0) | B — not reached; flagged for any future upgrade path |
| 26 | stock.quant `_merge_quants` (addons/stock/models/stock_quant.py:1251) | 1 | UPDATE + DELETE (one CTE) | stock_quant (merge duplicates per product/location/lot/package/owner) | `_quant_tasks` after every move done / picking validation and from the scheduler cron (hot) | R |
| 27 | stock.quant `_unlink_zero_quants` (stock_quant.py:1169) | 1 | SELECT | stock_quant ids → ORM `unlink` | `_quant_tasks`, `stock_move.py:2396` (hot) | R |
| 28 | stock `_create_inventory_adjustment` (addons/stock/__init__.py:46, `post_init_hook`) | 1 | SELECT | product_product.qty_available (the pre-stock stored JSON column) | `-i stock` on a database that already has products | B — install-time raw read of a non-id column; a Mongo-backed product_product cannot serve it (observed in an earlier run on this repo: a fresh `-i stock` dies here on a shadow table). Options: rewrite to `search_read` of the pre-stock field, or always install stock before product opts in: manager decision |
| 29 | stock `_save_current_inventory` (addons/stock/__init__.py:92, `uninstall_hook`) | 1 | UPDATE (execute_values) | product_product.qty_available | uninstall of stock only | B — not reached unless stock is uninstalled; same column as row 28 |
| 30 | purchase.order.line `_ondelete_stock_moves` (addons/purchase_stock/models/purchase_order_line.py:24) | 1 | UPDATE | purchase_order_line (`qty_received_manual`, `qty_received_method`) | selection `ondelete`, uninstall of purchase_stock only | R — trivial ORM `write`; not reached in this run |
| 31 | sale.order `_init_column_warehouse_id` (addons/sale_stock/models/sale_order.py:67) | 1 | UPDATE | sale_order.warehouse_id FROM stock_warehouse | column init when sale_stock installs over existing sale orders (fresh `-i` path) | R — ORM write in the init; on the fresh-install verification path |

Totals 3a: 32 rows, 58 sites; R 24 rows (48 sites), S 4 rows (5 sites), B 4 rows (5 sites). Hot-path writers that must
land in the owning unit's first batch: rows 2, 3, 4 (account.move / account.move.line / account.partial.reconcile) and
row 26 (stock.quant). Everything else is a reader or a cold write.

#### 3b. `env.execute_query` / `env.execute_query_dict`

`Environment.execute_query` (odoo/orm/environments.py:548, `:564`) runs an `SQL` object — usually `Query.select()` built
from `_search()` — on the cursor without going through `BaseModel` read/write, so it is a second raw-SQL API. Same scan
over the 15 scope + bridge modules: 45 call sites in 42 methods. Installed modules outside scope that use it
(base_import_module, mail, privacy_lookup) touch framework tables only.

| # | model / function (file:line) | sites | verb | in-scope tables | when | disp. |
|---|---|---|---|---|---|---|
| 1 | sequence.mixin `init` (addons/account/models/sequence_mixin.py:66) | 1 | SELECT (index_exists probe before the CREATE INDEX of §3a row 1) | account_move | module load | R (with §3a row 1) |
| 2 | sequence.mixin `_get_last_sequence` (sequence_mixin.py:311) | 1 | SELECT | account_move (`sequence_prefix`, `sequence_number`, `name`, ordered, limit 1) | every `_post` (hot) | R |
| 3 | account.move `_update_sequence_made_gap` (addons/account/models/account_move.py:6457) | 1 | SELECT / UPDATE | account_move (`sequence_number`, `made_sequence_gap`) | post / draft reset (warm) | R |
| 4 | account.move `_compute_payment_state` (account_move.py:1314) | 1 | SELECT | account_move_line, account_partial_reconcile, account_payment, account_move, account_account | every invoice write (hot) | R |
| 5 | account.move `_compute_reconciled_payment_ids` (account_move.py:2508) | 1 | SELECT | account_move_line, account_partial_reconcile, account_payment, account_move, account_account | reconciliation (hot) | R |
| 6 | account.move `_get_unbalanced_moves` (account_move.py:2954) | 1 | SELECT | account_move_line, account_move (debit/credit/balance sums) | every entry create / write (hot) | R |
| 7 | account.move `_fetch_duplicate_reference` (account_move.py:2218) | 1 | SELECT | account_move | invoice form (warm) | R |
| 8 | account.move `_get_frequent_account_and_taxes` (account_move.py:4548) | 1 | SELECT | account_move_line, account_move_line_account_tax_rel | invoice line default (warm) | R |
| 9 | account.move `_copy_recurring_entries` (account_move.py:4947) | 1 | SELECT | account_move | recurring post (warm) | R |
| 10 | account.move `_get_all_reconciled_invoice_partials` (account_move.py:5720) | 1 | SELECT | account_move_line, account_partial_reconcile | invoice payment widget (warm) | R |
| 11 | account.move `_unlink_next_draft_auto_post_moves` (account_move.py:7022) | 1 | SELECT | account_move | recurring unlink (cold) | R |
| 12 | account.move `_check_draftable` (account_move.py:7053) | 1 | SELECT | account_partial_reconcile | reset to draft (warm) | R |
| 13 | account.move `_first_date` (account_move.py:7843) | 1 | SELECT | account_move | tooling (cold) | R |
| 14 | account.move `get_cash_roundings` (account_move.py:8345) | 1 | SELECT | account_cash_rounding | invoice form (warm) | R |
| 15 | account.move.line `_search_account_id` (addons/account/models/account_move_line.py:820) | 1 | SELECT | account_account (Query / SQL operand) | search on `account_id` (warm) | R |
| 16 | account.move.line `_compute_consolidation_rate` (account_move_line.py:958) | 1 | SELECT | account_move_line (rate columns) | multi-currency companies, every read (warm) | R |
| 17 | account.move.line `_compute_residual_at_date` (account_move_line.py:1148) | 1 | SELECT | account_move_line, account_partial_reconcile | aged reports (warm) | R |
| 18 | account.move.line `_inverse_analytic_distribution` (account_move_line.py:1802) | 1 | SELECT | account_move_line | analytic write (warm) | R |
| 19 | account.move.line `_search_panel_domain_image` (account_move_line.py:2458) | 1 | SELECT | account_move_line, account_account | search panel (warm) | R |
| 20 | account.account `_search_panel_domain_image` (addons/account/models/account_account.py:486) | 1 | SELECT | account_account | search panel (warm) | R |
| 21 | account.account `_get_most_frequent_accounts_for_partner` (account_account.py:800) | 1 | SELECT | account_move_line grouped by account | invoice line default (warm) | R |
| 22 | account.account.tag `_compute_report_expression_id` (addons/account/models/account_account_tag.py:43) | 1 | SELECT | account_account_tag (+ account_report_expression) | tag read (cold) | R |
| 23 | account.journal `_get_cashflow_kpi_amount` (addons/account/models/account_journal_dashboard.py:177) | 1 | SELECT | account_move_line, account_bank_statement_line | dashboard (warm) | R |
| 24 | account.journal `_fill_sale_purchase_dashboard_data` (account_journal_dashboard.py:757) | 1 | SELECT | account_move, account_journal | dashboard (warm) | R (with §3a row 12) |
| 25 | account.payment `_compute_stat_buttons_from_reconciliation` (addons/account/models/account_payment.py:804) | 1 | SELECT | account_payment, account_move, account_move_line, account_partial_reconcile, account_account | payment form (warm) | R (with §3a row 8) |
| 26 | account.payment `_fetch_duplicate_reference` (account_payment.py:922) | 1 | SELECT | account_payment | payment form (warm) | R |
| 27 | res.company `_check_hash_integrity` (addons/account/models/company.py:1175, :1176, :1207) | 3 | DECLARE CURSOR / FETCH over account_move | inalterability check (cold) | R — server-side cursor over a Mongo-backed table has no equivalent; batch by `_id` ranges |
| 28 | res.partner `_credit_debit_get` (addons/account/models/partner.py:419) | 1 | SELECT | account_move_line, account_account | partner form / credit limit (warm) | R |
| 29 | res.partner `_asset_difference_search` (partner.py:449) | 1 | SELECT | account_move_line, account_move, account_account | partner search (cold) | R |
| 30 | res.partner `_invoice_total` (partner.py:479) | 1 | SELECT | account_move (+ res_currency_rate) | partner form (warm) | R |
| 31 | res.currency `_get_raw_rates` (addons/account/models/res_currency.py:51) | 1 | SELECT | none (res_currency_rate, res_company) | currency rates | S — PostgreSQL-only tables |
| 32 | res.currency.rate.consolidation.mixin `_compute_consolidation_rate` (addons/account/models/res_currency_rate_consolidation_mixin.py:33) | 1 | SELECT | inheritors' tables: sale_order_line, purchase_order_line, account_move_line, account_report_external_value | every read in multi-currency companies (warm) | R |
| 33 | res.partner.bank `_compute_duplicate_bank_partner_ids` (addons/account/models/res_partner_bank.py:72) | 1 | SELECT | none (res_partner_bank) | bank account form | S — PostgreSQL-only table |
| 34 | account.merge.wizard `_action_merge` (addons/account/wizard/account_merge_wizard.py:144, :170) | 2 | SELECT | account_account (`code_store`, `name`) | merge wizard (cold) | R (with §3a row 16) |
| 35 | account.merge.wizard.line `_compute_account_has_hashed_entries` (account_merge_wizard.py:268) | 1 | SELECT | account_move_line | merge wizard (cold) | R |
| 36 | account.secure.entries.wizard `_compute_max_hash_date` (addons/account/wizard/account_secure_entries_wizard.py:76) | 1 | SELECT | account_move | secure entries wizard (cold) | R |
| 37 | account.move (purchase) `_compute_display_auto_complete` (addons/purchase/models/account_invoice.py:159) | 1 | SELECT | purchase_order (+ res_partner) | vendor bill form (warm) | R |
| 38 | purchase.order `_fetch_duplicate_orders` (addons/purchase/models/purchase_order.py:401) | 1 | SELECT | purchase_order | PO form (warm) | R |
| 39 | sale.order `_fetch_duplicate_orders` (addons/sale/models/sale_order.py:1060) | 1 | SELECT | sale_order | SO form (warm) | R |
| 40 | utm.campaign `_compute_sale_invoiced_amount` (addons/sale/models/utm_campaign.py:55) | 1 | SELECT | account_move_line, account_move (+ res_currency_rate) | campaign form (cold) | R |
| 41 | stock.quant `_run_least_packages_removal_strategy_astar` (addons/stock/models/stock_quant.py:669) | 1 | SELECT | stock_quant grouped by package | reservation with least-packages strategy (warm) | R |
| 42 | product.product `_get_last_product_value` (addons/stock_account/models/product.py:307) | 1 | SELECT | product_value (`DISTINCT ON product_id`) | valuation reads (warm) | R |

Totals 3b: 42 rows, 45 sites; R 40 rows (43 sites), S 2 rows (2 sites), B 0.

#### 3c. Framework code reached with a dynamic table name

Found by following §3a/§3b callers, not by table-name matching (the scans above match literal table names, so these
would otherwise be invisible):

| caller | framework code | statements | in-scope tables | disp. |
|---|---|---|---|---|
| account.merge.wizard `_action_merge` (§3a row 16) | `base.partner.merge.automatic.wizard._update_foreign_keys_generic` (odoo/addons/base/wizard/base_partner_merge.py:119) and `_update_reference_fields_generic` (:198) | **discovery**: `_get_fk_on` (:80–:101) lists the referencing columns from `pg_constraint`, `_update_reference_fields_generic` from `ir_model_fields`; then UPDATE / DELETE on each discovered table | account_move_line, account_journal, account_payment_method_line, account_tax_repartition_line, product_category, … plus PostgreSQL-resident res_company | R, and the discovery step is part of the rewrite: a Mongo-backed table has no `account_id` column or FK on PostgreSQL, so `pg_constraint` no longer lists it and the merge would silently leave its documents pointing at the deleted account. The account merge unit must enumerate Mongo-backed references from ORM field metadata (`ir_model_fields` where relation = 'account.account', same source `_action_unmerge` already uses) and update them before the source accounts are removed. PostgreSQL-resident targets keep the `pg_constraint` path (S) |
| module load of account.reconcile.model.line, account.move.line, sale.order.line, purchase.order.line | `analytic.mixin.init` (addons/analytic/models/analytic_mixin.py:33) | `CREATE INDEX IF NOT EXISTS ... USING gin(... analytic_distribution ...)` guarded only by `table_exists` | account_reconcile_model_line, account_move_line, sale_order_line, purchase_order_line | R — an id-only shadow passes `table_exists` but has no `analytic_distribution`, so the load fails; wave 0 skips the DDL for Mongo-backed inheritors (same rule as §3a row 1) |

Out-of-scope installed modules (the other 55 of the 70) were scanned the same way for raw SQL or `_table_sql` naming an
in-scope table: 0 hits by literal table name; the two dynamic-table reaches are in §3c. Modules in the tree but **not installed** do carry such SQL (account_check_printing, account_edi,
account_update_tax_tags, product_margin, sale_service, point_of_sale, event_sale, website, website_sale and 14 `l10n_*` modules, mostly
migration scripts); widening the module set re-opens this register.

### 4. Install / uninstall hooks (`__manifest__.py` of the 15 scope + bridge modules)

| module | hook | body | disp. |
|---|---|---|---|
| sale | post_init `_post_init_hook` | `_synchronize_crons` (cron active flags), `_setup_downpayment_account`, `_setup_accrual_accounts` via `account.chart.template._load_pre_defined_data` → res_company fields, account_account creates | orm |
| purchase | post_init `_post_init_hook` | `_setup_accrual_accounts` (same path) | orm |
| account | post_init `_account_post_init` | `_set_fiscal_country` (res_company compute), `_create_batch_payment_sequence` (ir_sequence) | orm |
| stock | pre_init `pre_init_hook` | `ir.model.data` unlink of stale `stock.*` xmlids | orm (framework) |
| stock | post_init `post_init_hook` | `_assign_default_mail_template_picking_id` (orm); `_create_inventory_adjustment` → §3a row 28 | **B** (row 28) |
| stock | uninstall `uninstall_hook` | picking type sequences unlink (orm); `_save_current_inventory` → §3a row 29 | **B** (row 29, uninstall only) |
| account_edi_ubl_cii | uninstall `uninstall_hook` | `res.partner._clear_removed_edi_formats` → §3a row 24 | S |
| purchase_stock | pre_init `_split_partial_purchase_order_lines` | purchase.order.line copy/write (orm) | orm |
| purchase_stock | post_init `_post_init_hook` | `_create_buy_rules` (stock.warehouse write), `_create_pickings_for_open_purchase_orders` (orm) | orm |
| sale_stock | pre_init `_split_partial_sale_order_lines` | sale.order.line copy/write (orm) | orm |
| sale_stock | post_init `_create_pickings_for_open_sale_orders` | orm; plus `_init_column_warehouse_id` → §3a row 31 at column creation | orm (+R row 31) |
| stock_account | post_init `_post_init_hook` | `_configure_journals` (ir.model.data xmlids), `_create_product_value` (product.value create), `_configure_stock_account_company_data` | orm |

uom, product, account_qr_code_sepa, purchase_edi_ubl_bis3, sale_edi_ubl, sale_purchase, sale_purchase_stock declare no
hooks. 12 hooks: 9 orm, 1 S, 2 B (both the stock install/uninstall pair).

### 5. PostgreSQL-side readers of migrated ids (no code)

| kind | count in `odoo_src` | disp. |
|---|---|---|
| FK edges out-of-scope → in-scope | 50 edges from 13 tables; rows present only in res_company (account defaults; `internal_transit_location_id` → stock_location, 3) and barcode_rule.associated_uom_id → uom_uom (17); account_analytic_line (8 edges), payment_transaction, payment_refund_wizard, stock_picking_sms_rel, res_partner_stock_lot_rel, account_invoice_transaction_rel, res_country_group_pricelist_rel, payment_provider_product_pricelist_rel, account_analytic_distribution_model, account_analytic_applicability hold 0 rows | S — the id shadow keeps the FK target; the FK stays |
| FK edges in-scope → out-of-scope | 415 edges to 28 PostgreSQL-resident tables (res_users 255, res_company 57, res_partner 32, res_currency 23, res_partner_bank 6, …) | orm — stored as PostgreSQL ids in the documents; referential checks move to the application |
| FK edges in-scope → in-scope | 468 | handled by the model (embed / reference) |
| polymorphic `(model, res_id)` rows pointing at in-scope models | mail_message 469, ir_model_data 927, ir_attachment 216, mail_followers 37, mail_activity 20, ir_filters 2 | S — framework tables stay on PostgreSQL and keep the ids; `ir_model_data` must keep resolving xmlids of migrated rows (chart template, demo data, §3a rows 15b and 22) |

### 6. What this shapes

- Wave 0 (storage path) must carry: skip-or-rewrite of view `init()` DDL and of the `sequence.mixin.init` and
  `analytic.mixin.init` index DDL for Mongo-backed models (§2, §3a row 1, §3c); the cron deactivation rule (§1); a decision on the stock install hook (§3a row 28) because the
  fresh-install verification path (`-i stock` on a Mongo-backed product_product) fails without it.
- Unit derivation: account.move + account.move.line + account.partial/full.reconcile form one unit (§3a rows 2–8, 12, 20, §3b rows 1–21 and 27: posting, numbering, payment state and the
  reconcile writes are one transaction; `_check_hash_integrity` needs a cursor-free batching rewrite); stock.quant goes with stock.move (§3a rows 26–27, §3b row 41, `_quant_tasks`); the 5
  `_table_sql` reports and 3 views attach to the unit owning their driving table and are verified by `read_group`
  scenarios, not row counts.
- Blocked items needing a manager decision: §3a rows 23 (kpi_provider, no registry) and 28 (stock post_init_hook).
  Rows 25 and 29 are blocked but unreachable in this run (upgrade / uninstall paths); recorded, no action.
- Plugin gap (pinned `9a584b4`, not patched): the census keeps a `dependencies` section for Oracle only
  (`skills/schema-modeling/catalog_census.py:70`); for PostgreSQL there is no cron / view / raw-SQL inventory, and the
  access scan emits no patterns for `_auto = False` models and treats only `cr.execute(` (the 4 `execute_values` writes and the 45
  `env.execute_query` sites above are invisible to it). This register was built from `odoo_src` catalog queries and AST scans run outside the repo.

Commands (read-only; secret bound by name in one-shot execs): the PostgreSQL client over `ODOO_PG_RO_DSN` for
`ir_cron ⋈ ir_act_server ⋈ ir_model`, `pg_views`, `pg_matviews`, `pg_trigger`, `pg_rules`, `pg_proc`, `pg_constraint`
(contype = 'f') and the polymorphic counts; `ast`-based scans of `addons/<module>/**/*.py` for `cr.execute*`, `env.execute_query*`,
`_auto = False`, `_table_sql`, `init`, and of `__manifest__.py` hooks.

## s3.1 Design decisions: map-draft-2, the plugin gap, and the tolerance bump

- Every open item of the map-draft-1 proposal (580 questions in 10 kinds) is answered in `.migration/answers.txt` (11 lines) and
  `.migration/design_decisions.json` (17 hand-written decisions). The sign-off pack is `.migration/model_review_pack.md`
  (rendered by `.migration/review_pack.py` from the artifacts).
- Plugin gap at the pinned `9a584b4` (reported, not patched): `model_proposal.py:1734` builds `decision.references` from the raw
  table foreign keys after `--exclude-table` removed the excluded tables, so the proposal carries 299 reference rows whose `to`
  names a collection that does not exist (`resUsers`, `resCompany`, `resPartner`, `resCurrency`, ...). `model_patch.py:1743`
  (`_check_references`) then refuses every `--answers`/`--decisions` run with `dangling references after decisions`
  (`.migration/rehearsal/patch_attempt.map-draft-1.txt`), and `check_spec` (`model_patch.py:1961`) skips only
  `modeling.excluded` (the `exclude` op), never `modeling.excluded_tables`, so 1460 census FK edges into excluded tables stay
  `no rationale row` failures that no decision can clear (`exclude` needs an existing, unreferenced collection).
- Plan decision `d-plugin-gap = accept-scratch-draft2`: `.migration/mapping_spec.json` (map-draft-2, mapping_sha256
  `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc`) is the proposal with those 299 dangling reference rows
  filtered out of a copy, then patched by the pinned, unpatched `model_patch.py`. `.migration/rehearsal/scratch_draft2.sh` is
  the reproducible recipe (input: map-draft-1 from `origin/mongo-run/unt12`; it prints the rebuilt sha256 next to the committed
  one). The filtered rows pointed only at excluded tables, which stay in PostgreSQL; their FK columns remain integer id fields on
  the documents. Gate `g-model-evidence` is read as: `--check` leaves only the 1460 excluded-table lines and 0 open items
  (`.migration/rehearsal/check.map-draft-2.txt`).
- Plan decision `d-float-aggregates = rel-tol-float8`: `.migration/recon_tolerances.json` is `unt12-3` with
  `aggregate_rel_tol: 1e-12`, everything else unchanged. Reason: Tier 2 `SUM()` of float8 columns differs in the last place
  between PostgreSQL and MongoDB (summation order) while Tier 3 matches every row. The pinned harness applies the relative
  tolerance to every numeric aggregate (`_agg_close`, `recon/tiers.py`), not to float8 only.
- Model findings from the local rehearsal: the proposal gave `accountMove` 67 indexes against MongoDB's 64-per-collection cap
  (12 unexercised source-index entries removed by `index` decisions); `account_partial_reconcile` keeps its own collection
  with a `debitMoveId` index (hot reads filter on both debit and credit); the stock `post_init_hook` (row 28 above) needs stock
  installed before `product_product` opts in, on every database — an id-only shadow fails its SELECT.
