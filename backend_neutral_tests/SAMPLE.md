# Backend-neutral ORM test suite: representative code sample

Pinned to `Cognition-Partner-Workshops/odoo` branch `20.0`, commit `63446015e3c`. Machine-readable twin: [`sample.yaml`](sample.yaml); validate both with `python3 backend_neutral_tests/check_sample.py` (checks every file path, symbol and line below exists; `--render` regenerates this file from the YAML).

## Purpose

Odoo's ~2,700 test files assume PostgreSQL. This manifest names the models and code paths a **backend-neutral** suite will cover: tests that assert only on records, field values, ordering and raised exception classes, never on SQL text, query counts, cursors or savepoints, so they pass on PostgreSQL today and can run unchanged against another backend. It is a sample, not an inventory: the goal is to hit every *kind* of backend-sensitive behaviour from more than one addon.

## Addon spread

- Core: `odoo/orm`, `odoo/addons/base`
- Addons (confirmed from the starting hypothesis): `account`, `stock`, `sale`, `mail`, `website`, `hr_holidays`, `point_of_sale`, `project`
- Supporting: `product` (dependency of stock/sale/point_of_sale; only `product.category` hierarchy is used)

The hypothesis was kept because the static scan confirms it: `account` is the heaviest raw-SQL and constraint user outside core; `mail` and `website` hold the most lock/upsert and text-search SQL; `stock`, `project`, `hr_holidays`, `sale`, `point_of_sale` each own a different style of SQL-view report and heavy `read_group`/`child_of` use. Addons that scored high but were not added (`payment`, `mass_mailing`, `l10n_*_edi`) are listed under *Deliberately left out* with the reason.

## Selection criteria (use these to extend the sample)

- **C1** The target contains the category's pattern per the static scan (grep patterns listed in SAMPLE.md), not just a mention in a comment.
- **C2** The behaviour is reachable through a public ORM entry point (create/write/unlink/search/search_fetch/_read_group/flush) so an assertion can be written on records, values or a raised exception class only.
- **C3** Each category has targets in core plus at least two addons from the spread, so a backend bug is caught from more than one data shape.
- **C4** Prefer models whose fixtures are cheap (no chart of accounts, no POS session) unless the category is concentrated in that addon (account for raw SQL, point_of_sale for its own report).
- **C5** Prefer targets that an existing test already exercises, so the neutral test can reuse its data setup and the two can be diffed later.
- **C6** Prefer stable, named symbols (class attribute, method) over anonymous inline SQL so the manifest survives refactors; the checker verifies the symbol still exists.

To add a target: pick a symbol that satisfies C1 and C2, add it to `sample.yaml` with `file`, `symbols`, `line`, `existing_tests` and a one-line `neutral_assertion`, then run the checker with `--render`. Scan patterns per category are recorded in each category's `scan` key.

## Targets by category

### DB-enforced integrity (SQL constraints, unique indexes, FK ondelete)

Scan pattern: `models.Constraint( | models.UniqueIndex( | ondelete=`; scan counts: `{'constraint_files_non_test': 249, 'ondelete_files_non_test': 531, 'ondelete_restrict_sites': 170, 'ondelete_cascade_sites': 455, 'ondelete_set_null_sites': 93}`

#### `integrity.res_users` - res.users / res.partner (`base`)

- Code: `odoo/addons/base/models/res_users.py:267` - `_login_key`, `partner_id`; `odoo/addons/base/models/res_partner.py:418` - `_check_name`
- Pattern: UNIQUE(login); CHECK on partner type/name; Many2one partner_id ondelete='restrict'
- Why: The simplest core unique constraint, a CHECK constraint, and a 'restrict' FK on the two models every other test touches.
- Existing tests: `addons/website/tests/test_website_reset_password.py`
- Neutral assertion: create two users with the same login -> integrity-violation exception; create contact without name -> integrity violation; unlink a partner that has a user -> integrity violation, partner still exists.

#### `integrity.account_move` - account.move / account.move.line (`account`)

- Code: `addons/account/models/account_move.py:825` - `_unique_name`, `_check_document_tax_mode_set`; `addons/account/models/account_move_line.py:549` - `_check_credit_debit`, `_check_accountable_required_fields`, `move_id`
- Pattern: partial UniqueIndex "(name, journal_id) WHERE state='posted' AND name != '/'"; CHECK credit*debit=0; move_id ondelete='cascade'
- Why: Partial (conditional) unique index is the hardest integrity shape to emulate on a non-SQL backend; account is the largest constraint user outside core.
- Existing tests: `addons/account/tests/test_sequence_mixin.py::test_journal_sequence`
- Neutral assertion: two posted moves with same name+journal -> integrity violation, but two drafts named '/' are fine; a line with debit and credit both > 0 -> integrity violation; unlinking a move leaves zero lines for it.

#### `integrity.hr_leave` - hr.leave (`hr_holidays`)

- Code: `addons/hr_holidays/models/hr_leave.py:307` - `_date_check2`, `_date_check3`, `_duration_check`, `employee_id`
- Pattern: three CHECK constraints on date order / non-negative duration; employee_id ondelete='restrict'
- Why: Plain CHECK constraints that an application layer could also enforce; the neutral test must fail identically whichever layer enforces them.
- Existing tests: `addons/hr_holidays/tests/test_holidays_flow.py::test_sql_constraint_dates`
- Neutral assertion: create/write with request_date_from > request_date_to -> integrity violation and no record persisted; unlink employee with leaves -> integrity violation.

#### `integrity.mail_followers` - mail.followers / discuss.channel.member (`mail`)

- Code: `addons/mail/models/mail_followers.py:39` - `_mail_followers_res_partner_res_model_id_uniq`, `partner_id`; `addons/mail/models/discuss/discuss_channel_member.py:251` - `_partner_unique`, `_guest_unique`, `_partner_or_guest_exists`
- Pattern: composite unique (res_model,res_id,partner_id); partner_id ondelete='cascade'; partial UniqueIndex WHERE partner_id IS NOT NULL; XOR CHECK partner/guest
- Why: Composite uniqueness on a polymorphic (model,res_id) key plus cascade on partner delete is how every chatter-enabled model behaves; channel member adds the partial-unique + XOR shape.
- Existing tests: `addons/test_mail/tests/test_mail_followers.py::test_followers_multiple_subscription_force`
- Neutral assertion: subscribing the same partner twice to one record keeps exactly one follower (ORM path) and direct double create raises integrity violation; unlinking the partner removes its follower rows; a member with neither partner nor guest -> integrity violation.

#### `integrity.stock_location` - stock.location / stock.quant (`stock`)

- Code: `addons/stock/models/stock_location.py:94` - `_barcode_company_uniq`, `_inventory_freq_nonneg`; `addons/stock/models/stock_quant.py:47` - `product_id`, `location_id`; `addons/stock/models/stock_orderpoint.py:127` - `_product_location_check`
- Pattern: unique(barcode,company_id) with NULL barcodes allowed; CHECK >= 0; quant product_id/location_id ondelete='restrict'; orderpoint unique(product_id,location_id,company_id)
- Why: Unique constraint where NULLs must not collide (SQL NULL semantics vs document-store null) and 'restrict' FKs protecting stock quantities.
- Existing tests: `addons/stock/tests/test_stock_location_search.py::test_10_location_search_by_barcode`
- Neutral assertion: two locations with same barcode in one company -> integrity violation; two locations with barcode False are fine; unlink a product that has quants -> integrity violation.

#### `integrity.sale_order_line` - sale.order / sale.order.line (`sale`)

- Code: `addons/sale/models/sale_order_line.py:24` - `_accountable_required_fields`, `_non_accountable_null_fields`, `order_id`; `addons/sale/models/sale_order.py:51` - `_date_order_conditional_required`, `campaign_id`
- Pattern: CHECK constraints keyed on display_type; order_id ondelete='cascade'; campaign_id ondelete='set null'
- Why: Covers all three ondelete modes on one document (cascade lines, set-null UTM fields, restrict partner) plus state-dependent CHECK.
- Existing tests: `addons/sale/tests/test_sale_order.py`
- Neutral assertion: section line with a product -> integrity violation; unlink order -> its lines are gone; unlink utm.campaign -> order.campaign_id is False and order survives.

### Concurrency and locking (FOR UPDATE / NOWAIT / SKIP LOCKED, serialization retry)

Scan pattern: `FOR UPDATE | NOWAIT | SKIP LOCKED | FOR NO KEY UPDATE | lock_for_update | OperationalError | SerializationFailure`; scan counts: `{'lock_files_non_test': 44, 'retry_files_non_test': 19}`

#### `concurrency.ir_sequence` - ir.sequence (`base`)

- Code: `odoo/addons/base/models/ir_sequence.py:57` - `_update_nogap`, `_select_nextval`, `_predict_nextval`
- Pattern: "SELECT ... FOR UPDATE NOWAIT" on no-gap sequences; PG sequences (nextval) for standard ones
- Why: The canonical "two transactions want the next number" problem; standard vs no_gap implementations have different backend expectations.
- Existing tests: `odoo/addons/base/tests/test_ir_sequence.py::TestIrSequenceNoGap`
- Neutral assertion: N concurrent cursors each drawing from one no_gap sequence produce N distinct, contiguous numbers once all commit; a second cursor drawing while the first holds the row raises a lock/concurrency exception class (not a hang).

#### `concurrency.ir_cron` - ir.cron (`base`)

- Code: `odoo/addons/base/models/ir_cron.py:311` - `_acquire_one_job`, `_get_all_ready_jobs`, `_process_job`
- Pattern: "FOR NO KEY UPDATE SKIP LOCKED" job acquisition; TransactionRollbackError handling
- Why: Work-queue semantics (exactly one worker gets a job) are the behaviour a backend must preserve regardless of how locking is spelled.
- Existing tests: `odoo/addons/base/tests/test_ir_cron.py::test_cron_process_jobs_locked`, `odoo/addons/base/tests/test_ir_cron.py::test_acquire_processed_job`
- Neutral assertion: with the job row held by cursor A, _acquire_one_job on cursor B returns None; after A commits, B acquires it; a job is never run twice.

#### `concurrency.lock_for_update` - BaseModel (`core`)

- Code: `odoo/orm/models.py:5056` - `lock_for_update`, `try_lock_for_update`
- Pattern: generic row locks (FOR [NO KEY] UPDATE SKIP LOCKED) used by payment, account_edi, base_automation, point_of_sale
- Why: The ORM-level locking API every addon is being migrated to; a backend only has to implement these two methods correctly.
- Existing tests: `odoo/addons/test_base/tests/test_orm/test_models.py`, `addons/payment/tests/test_payment_transaction.py`
- Neutral assertion: try_lock_for_update on cursor B returns the subset not locked by cursor A (empty when all are locked); lock_for_update on locked rows raises a concurrency exception class; records remain unchanged.

#### `concurrency.discuss_channel` - discuss.channel / mail.guest (`mail`)

- Code: `addons/mail/models/discuss/discuss_channel.py:770` - `_sync_last_interest_dt`, `_update_last_interest_dt`; `addons/mail/models/discuss/mail_guest.py:129` - `_update_timezone`
- Pattern: try_lock_for_update(allow_referencing=True) + psycopg2.OperationalError swallowed; raw "FOR NO KEY UPDATE SKIP LOCKED"
- Why: "Best-effort update" pattern - a lost lock must degrade silently, not raise - which is the opposite expectation from ir_sequence.
- Existing tests: `addons/mail/tests/discuss/test_discuss_channel_last_interest.py`
- Neutral assertion: concurrent _sync_last_interest_dt on a channel locked elsewhere does not raise and leaves last_interest_dt either old or new (never corrupt); later call converges to the newest value.

#### `concurrency.website_visitor` - website.visitor (`website`)

- Code: `addons/website/models/website_visitor.py:361` - `_update_visitor_last_visit`, `_update_visitor_timezone`, `_upsert_visitor`
- Pattern: "UPDATE ... WHERE id IN (SELECT ... FOR NO KEY UPDATE SKIP LOCKED)"; INSERT ... ON CONFLICT upsert
- Why: High-frequency, contention-tolerant update plus an upsert keyed on a unique access_token.
- Existing tests: `addons/website/tests/test_website_visitor.py::test_visitor_creation_on_tracked_page`
- Neutral assertion: two upserts with the same token yield one visitor; last_visit update under a concurrent lock is skipped without error and applied on the next call.

#### `concurrency.stock_orderpoint_retry` - stock.warehouse.orderpoint (`stock`)

- Code: `addons/stock/models/stock_orderpoint.py:728` - `_procure_orderpoint_confirm`; `addons/account/models/partner.py:891` - `_increase_rank`
- Pattern: savepoint + except psycopg2.OperationalError -> retry/skip loop; separate registry cursor + OperationalError swallow
- Why: Application-level serialization retry; the neutral test only cares that the end state is correct after the retry, whichever error class triggered it.
- Existing tests: `addons/stock/tests/test_stock_order_point.py`, `addons/website_sale_loyalty/tests/test_concurrent_promo_code.py`
- Neutral assertion: running the procurement twice concurrently creates exactly one replenishment per orderpoint; partner rank increments by the number of successful calls and never raises to the caller.

### Raw SQL bypassing the ORM (cr.execute / SQL())

Scan pattern: `cr.execute( | SQL(`; scan counts: `{'call_sites_non_test': 2026, 'top': {'odoo/orm': 297, 'account': 265, 'odoo/addons/base': 200, 'odoo/tools': 129, 'mass_mailing': 63, 'mail': 59, 'website': 53}}`

#### `raw_sql.orm_core` - BaseModel / Many2many (`core`)

- Code: `odoo/orm/models.py:1996` - `_read_group`, `_write_multi`, `_create`, `exists`, `_parent_store_compute`; `odoo/orm/fields_relational.py:1428` - `read`, `write_batch`, `relation_delete`
- Pattern: hand-built SELECT/UPDATE/INSERT; INSERT ... ON CONFLICT DO NOTHING for m2m relation tables
- Why: The ORM's own SQL is the minimum any backend must replace; m2m relation writes have set semantics (no duplicates, idempotent link/unlink).
- Existing tests: `odoo/addons/test_base/tests/test_orm/test_read_group_private.py`, `odoo/addons/test_base/tests/test_orm/test_many2many.py`, `odoo/addons/test_base/tests/test_orm/test_create.py`
- Neutral assertion: create/write/exists round-trips through the public API; linking the same m2m pair twice yields one link; unlink of a non-linked pair is a no-op.

#### `raw_sql.account_move` - account.move / account.account / res.partner (`account`)

- Code: `addons/account/models/account_move.py:2182` - `_fetch_duplicate_reference`, `_get_last_sequence_domain`; `addons/account/models/account_account.py:974` - `_search`, `_compute_sql_placeholder_code`; `addons/account/models/partner.py:391` - `_credit_debit_get`, `_invoice_total`
- Pattern: multi-join SELECT with GROUP BY / regexp_replace / LATERAL to detect duplicate bills, compute partner credit/debit, order accounts by code
- Why: account is the heaviest raw-SQL addon (265 sites); these three methods feed stored/computed fields whose values are directly observable.
- Existing tests: `addons/account/tests/test_account_move_in_invoice.py`, `addons/account/tests/test_account_account.py`
- Neutral assertion: two vendor bills with same ref+partner -> duplicated_ref_ids populated; partner.credit/debit equal the sum of its posted receivable/payable lines; account search ordered by code matches Python sort.

#### `raw_sql.mail_followers` - mail.followers / mail.message / mail.thread (`mail`)

- Code: `addons/mail/models/mail_followers.py:91` - `_get_recipient_data`, `_get_subscription_data`; `addons/mail/models/mail_message.py:568` - `_filter_accessible_from_query`; `addons/mail/models/mail_thread.py:252` - `_search_message_is_follower`, `_search_message_partner_ids`
- Pattern: 4 LATERAL subqueries building recipient lists; access filtering via subquery; custom _search_* on non-stored fields
- Why: Notification routing and message access are security-relevant behaviours implemented in raw SQL; mistakes are silent.
- Existing tests: `addons/test_mail/tests/test_mail_followers.py`, `addons/test_mail/tests/test_mail_thread_internals.py`
- Neutral assertion: message_post on a record notifies exactly the followers subscribed to that subtype (compare notification partner set); search on message_is_follower / message_partner_ids matches a Python-side filter.

#### `raw_sql.website` - website / website.visitor (`website`)

- Code: `addons/website/models/website.py:2122` - `_is_snippet_used`, `get_similarity_subquery`; `addons/website/models/website_visitor.py:220` - `_upsert_visitor`, `_get_additional_track_query_parts`
- Pattern: full-text / similarity search (pg_trgm style) over html fields; INSERT ... ON CONFLICT upsert for visitor tracking
- Why: Text-search SQL is the most backend-specific SQL in the repo; the neutral test asserts result sets, not ranking internals.
- Existing tests: `addons/website/tests/test_website_visitor.py`, `addons/website/tests/test_fuzzy.py`
- Neutral assertion: a page containing a snippet is reported as used after save and not after removal; visitor upsert is idempotent per token.

#### `raw_sql.stock_quant` - stock.quant (`stock`)

- Code: `addons/stock/models/stock_quant.py:1210` - `_merge_quants`, `_unlink_zero_quants`, `_run_least_packages_removal_strategy_astar`
- Pattern: UPDATE/DELETE with GROUP BY to merge duplicate quants and drop zero quants
- Why: Inventory correctness depends on these clean-up queries; observable through quant counts and quantities.
- Existing tests: `addons/stock/tests/test_quant.py`
- Neutral assertion: after two moves into the same location/lot, exactly one quant exists with the summed quantity; quants at 0 are removed after _unlink_zero_quants.

#### `raw_sql.sale_project` - sale.order / project.task (`sale`)

- Code: `addons/sale/models/sale_order.py:1042` - `_fetch_duplicate_orders`, `_search_invoice_ids`; `addons/project/models/project_task.py:737` - `_search_portal_user_names`; `addons/point_of_sale/models/pos_order.py:1131` - `search_order_ids`
- Pattern: raw SELECT behind non-stored searchable fields and duplicate detection; POS order search with raw SQL
- Why: Spreads the category over sale/project/point_of_sale with small, independently testable queries.
- Existing tests: `addons/sale/tests/test_sale_order.py`, `addons/project/tests/test_project_sharing.py`, `addons/point_of_sale/tests/test_point_of_sale_flow.py`
- Neutral assertion: search([('invoice_ids','in',..)]) returns the same set as filtering in Python; duplicate orders are flagged symmetric and never include self.

### SQL-view reporting models (_auto = False) and recursive CTE / window / LATERAL

Scan pattern: `_auto = False | WITH RECURSIVE | OVER ( | LATERAL`; scan counts: `{'auto_false_files_non_test': 43, 'cte_window_lateral_files_non_test': 49}`

#### `sql_views.account_invoice_report` - account.invoice.report (`account`)

- Code: `addons/account/report/account_invoice_report.py:8` - `AccountInvoiceReport`, `_table_sql`, `_read_group_select`
- Pattern: _auto = False with _table_sql() subquery and a custom _read_group_select for price averages
- Why: The newer "_table_sql" style of SQL view with an aggregate override; tested at result level already.
- Existing tests: `addons/account/tests/test_account_invoice_report.py::test_invoice_report_multiple_types`
- Neutral assertion: _read_group on the report for one invoice equals the invoice's untaxed total / quantity; grouping by month puts the invoice in its invoice_date month.

#### `sql_views.sale_report` - sale.report (`sale`)

- Code: `addons/sale/report/sale_report.py:11` - `SaleReport`, `_table_sql`, `_select_dict`
- Pattern: _auto = False, _table_sql built from a dict of SELECT expressions; extended by many addons
- Why: Most-extended report in the repo; its sum/avg semantics are the contract downstream addons rely on.
- Existing tests: `addons/sale/tests/test_sale_report.py::test_sale_report_with_downpayment`
- Neutral assertion: price_subtotal grouped by order equals order.amount_untaxed; a productless line contributes a row with product False.

#### `sql_views.report_pos_order` - report.pos.order (`point_of_sale`)

- Code: `addons/point_of_sale/report/pos_order_report.py:7` - `ReportPosOrder`, `_select`, `_from`, `_group_by`, `init`
- Pattern: legacy init()/drop_view_if_exists style; date_trunc arithmetic (delay_validation)
- Why: The older SQL-view style (init creates the view) and date arithmetic in SQL.
- Existing tests: `addons/point_of_sale/tests/test_report_session.py`
- Neutral assertion: one paid order -> one report row per line with matching qty/price_total; delay_validation is 0 for same-day orders.

#### `sql_views.project_reports` - report.project.task.user / project.task.burndown.chart.report / project.task.stage.report (`project`)

- Code: `addons/project/report/project_task_burndown_chart_report.py:10` - `ProjectTaskBurndownChartReport`, `_read_group`; `addons/project/report/project_report.py:9` - `ReportProjectTaskUser`, `_select`, `_group_by`; `addons/project/report/project_time_by_stage_report.py:5` - `ReportProjectTaskStage`, `_from`
- Pattern: window functions (SUM OVER, LAG OVER), UNION, CROSS JOIN LATERAL jsonb_each, a _read_group override on an AbstractModel view
- Why: Window functions and LATERAL over JSON are the SQL features least likely to map 1:1; the burndown report is fully behaviour-tested already.
- Existing tests: `addons/project/tests/test_burndown_chart.py::test_burndown_chart`, `addons/project/tests/test_project_report.py::test_avg_rating_measure`
- Neutral assertion: burndown counts per stage per day equal a Python replay of the task's stage history; task analysis avg rating equals the mean of its ratings.

#### `sql_views.hr_leave_reports` - hr.leave.employee.type.report / hr.leave.report (`hr_holidays`)

- Code: `addons/hr_holidays/report/hr_leave_employee_type_report.py:7` - `HrLeaveEmployeeTypeReport`, `init`; `addons/hr_holidays/report/hr_leave_report.py:5` - `HrLeaveReport`, `init`
- Pattern: window functions (MAX/SUM/ROW_NUMBER OVER PARTITION) plus UNION ALL of leaves and allocations
- Why: Overlapping-allocation arithmetic done in window functions; tested on balances today.
- Existing tests: `addons/hr_holidays/tests/test_hr_leave_report.py::test_overlapping_allocations_leaves_balance`
- Neutral assertion: for an employee with two overlapping allocations and one leave, the report balance equals allocated - taken computed in Python.

#### `sql_views.stock_quantity_report` - report.stock.quantity (`stock`)

- Code: `addons/stock/report/report_stock_quantity.py:7` - `ReportStockQuantity`, `init`
- Pattern: UNION ALL of quants and forecasted moves over a generated date series
- Why: Date-series generation inside the view; forecast rows are derived, not stored.
- Existing tests: `addons/stock/tests/test_report_stock_quantity.py::test_report_stock_quantity`
- Neutral assertion: for a product with 10 on hand and an outgoing move of 3 tomorrow, rows show 10 today and 7 tomorrow for state 'forecast'.

#### `sql_views.recursive_cte` - BaseModel / project.task / product.product / ir.ui.view (`core`)

- Code: `odoo/orm/models.py:2423` - `_parent_store_compute`, `_has_cycle`; `addons/project/models/project_task.py:1839` - `_get_subtask_ids_per_task_id`; `addons/stock/models/product.py:404` - `_get_domain_locations_new`; `odoo/addons/base/models/ir_ui_view.py:734` - `_get_inheriting_views`
- Pattern: WITH RECURSIVE for parent_path rebuild, cycle detection, subtask trees, location descendants, view inheritance
- Why: Recursive CTEs have no direct equivalent in a document store ($graphLookup differs); all four have observable results (paths, booleans, id sets).
- Existing tests: `odoo/addons/test_base/tests/test_orm/test_parent_store.py`, `odoo/addons/base/tests/test_res_partner.py`, `addons/project/tests/test_project_subtasks.py`
- Neutral assertion: after re-parenting, every record's parent_path lists its ancestors in order; _has_cycle is True iff a Python DFS finds a cycle; subtask ids per task equal a Python tree walk.

#### `sql_views.lateral_rates` - res.currency (`base`)

- Code: `odoo/addons/base/models/res_currency.py:171` - `_get_rates`, `_current_rate_sql`; `addons/mail/models/discuss/discuss_channel.py:1957` - `_get_last_messages`, `_get_last_needaction_messages`
- Pattern: LEFT JOIN LATERAL "latest row per key" queries
- Why: The "latest rate / last message per parent" idiom appears in 20+ files; its result is a plain value per record.
- Existing tests: `odoo/addons/base/tests/test_res_currency.py`, `addons/mail/tests/discuss/test_discuss_channel.py`
- Neutral assertion: _get_rates returns the rate dated on or before the asked date (not the newest); channel last message equals max(id) of its messages.

### Aggregation (_read_group) and hierarchy (child_of / parent_of / parent_path)

Scan pattern: `_read_group( | read_group( | 'child_of' | 'parent_of' | parent_path`; scan counts: `{'read_group_files_non_test': 312, 'hierarchy_files_non_test': 190, 'parent_store_models': 15}`

#### `aggregation.read_group_core` - BaseModel (`core`)

- Code: `odoo/orm/models.py:1996` - `_read_group`, `_read_group_orderby`, `_read_group_having`
- Pattern: groupby on char/m2o/date parts/m2m, aggregates (sum/avg/count/array_agg/count_distinct), having, limit/offset
- Why: Everything else in this category is a caller of this method; the private test file already asserts on returned tuples.
- Existing tests: `odoo/addons/test_base/tests/test_orm/test_read_group_private.py::test_simple_private_read_group`, `odoo/addons/test_base/tests/test_orm/test_read_group_private.py::test_groupby_date`
- Neutral assertion: for a fixed dataset, _read_group output tuples equal a Python itertools.groupby replay for every groupby/aggregate combination in the private tests.

#### `aggregation.stock_product_quantities` - product.product / stock.location (`stock`)

- Code: `addons/stock/models/product.py:156` - `_compute_quantities_dict`, `_search_field_by_quants`; `addons/stock/models/stock_location.py:180` - `_compute_child_internal_location_ids`, `_child_of`, `unlink`; `addons/stock/models/stock_quant.py:803` - `_gather`, `_get_gather_domain`
- Pattern: _read_group over quants/moves with ('location_id','child_of',...) domains; parent_path string comparisons
- Why: Combines aggregation and hierarchy in the hottest business path (qty_available); stock is the top read_group user (14 files).
- Existing tests: `addons/stock/tests/test_quant.py`, `addons/stock/tests/test_auto_waving.py`
- Neutral assertion: qty_available of a product equals the sum of its quants in the warehouse view location's subtree only; searching qty_available > 0 returns exactly those products; unlinking a parent location removes its children.

#### `aggregation.account_account_hierarchy` - account.account / res.partner (`account`)

- Code: `addons/account/models/account_account.py:588` - `_compute_current_balance`, `_compute_parent_ids`, `_search`; `addons/account/models/partner.py:1208` - `_compute_account_move_count`, `_increase_rank`
- Pattern: _read_group with ('company_id','child_of',root) domains; parent_path-based parent_ids; partner ('id','child_of',self.ids)
- Why: Hierarchy over companies (multi-company branches) and accounts; balance aggregation is the accounting invariant.
- Existing tests: `addons/account/tests/test_account_account.py`, `addons/account/tests/test_account_move_out_invoice.py`
- Neutral assertion: current_balance of an account equals sum(balance) of posted lines across the company and its branches; partner invoice counts include child contacts' moves.

#### `aggregation.project_task_subtasks` - project.task / project.project (`project`)

- Code: `addons/project/models/project_task.py:659` - `_compute_subtask_count`, `_read_group`, `_read_grouping_sets`; `addons/project/models/project_project.py:38` - `__compute_task_count`, `_compute_milestone_count`
- Pattern: _read_group with __count on parent_id; _read_group override injecting personal-stage grouping
- Why: A model-level _read_group override is the main extension point a backend must respect; subtask counts are a plain integer to assert.
- Existing tests: `addons/project/tests/test_project_subtasks.py::test_subtask_project`, `addons/project/tests/test_project_flow.py`
- Neutral assertion: subtask_count equals len(child_ids) after create/write/unlink of children; project task_count excludes closed tasks consistently with a Python filter; grouping tasks by personal stage returns every stage even when empty (group_expand).

#### `aggregation.hr_leave_mail_pos` - hr.leave.allocation / discuss.channel / pos.session (`hr_holidays`)

- Code: `addons/hr_holidays/models/hr_leave_allocation.py:352` - `_check_negative_allocation`; `addons/mail/models/discuss/discuss_channel.py:480` - `_compute_member_count`, `_compute_message_count`; `addons/point_of_sale/models/pos_session.py:361` - `_compute_order_count`, `_compute_total_payments_amount`
- Pattern: _read_group with sum/count used inside constraints and computes
- Why: Spreads the category over three addons with trivially checkable counts and sums.
- Existing tests: `addons/hr_holidays/tests/test_allocations.py`, `addons/mail/tests/discuss/test_discuss_channel.py`, `addons/point_of_sale/tests/test_point_of_sale_flow.py`
- Neutral assertion: member_count/message_count equal len() of the relation; total_payments_amount equals sum of payment amounts; an allocation below taken leaves raises ValidationError.

#### `hierarchy.parent_store_models` - res.partner / res.company / product.category / hr.department / website.menu (`base`)

- Code: `odoo/addons/base/models/res_partner.py:231` - `_parent_store`, `_search_display_name`, `_compute_same_vat_partner_id`; `odoo/addons/base/models/res_company.py:66` - `_parent_store`, `_all_branches_selected`; `addons/product/models/product_category.py:13` - `_parent_store`, `_compute_product_count`; `addons/website/models/website_menu.py:20` - `_parent_store`, `parent_id`
- Pattern: _parent_store = True models with child_of/parent_of domains in searches and computes
- Why: 15 models declare _parent_store; these four cover partner, company, catalog and website trees with existing child_of call sites.
- Existing tests: `odoo/addons/test_base/tests/test_orm/test_parent_store.py`, `odoo/addons/test_base/tests/test_orm/test_fields.py::TestParentStore`, `odoo/addons/base/tests/test_res_partner.py`
- Neutral assertion: search([('id','child_of',root)]) equals a Python descent over parent_id/child_ids; parent_of is its inverse; moving a subtree updates both; creating a cycle raises UserError.

### Core ORM semantics already tested in odoo/addons/test_base/tests/test_orm

Scan pattern: `assertQueryCount | assertQueries | cr.execute | SQL( | psycopg2 | registry | _as_query | flush_all/invalidate_all (allowed)`

Classification by static scan of each file; counts are test methods. 'as-is' = zero backend-specific lines; 'edit' = neutral after removing or skipping the listed assertions; 'split' = reuse only the listed classes; 'exclude' = measures PostgreSQL itself.

#### `core.reuse_as_is` - various test_orm.* models (`test_base`)

- Code: `odoo/addons/test_base/tests/test_orm/test_access.py:11` - `TestAccess`; `odoo/addons/test_base/tests/test_orm/test_acl.py` - `test_field_visibility_restriction`; `odoo/addons/test_base/tests/test_orm/test_copy.py` - `TestCopyTranslations`; `odoo/addons/test_base/tests/test_orm/test_create.py` - `TestCreate`; `odoo/addons/test_base/tests/test_orm/test_prefetch.py` - `TestPrefecth`; `odoo/addons/test_base/tests/test_orm/test_views.py` - `TestDefaultView`, `TestViewGroups`; `odoo/addons/test_base/tests/test_orm/test_check_access.py` - `test_check_access`; `odoo/addons/test_base/tests/test_orm/test_config_settings.py` - `TestConfigSettings`; `odoo/addons/test_base/tests/test_orm/test_json_field.py` - `JsonFieldTest`; `odoo/addons/test_base/tests/test_orm/test_ir_qweb_fields.py` - `TestExport`; `odoo/addons/test_base/tests/test_orm/test_action_bindings.py` - `TestActionBindings`; `odoo/addons/test_base/tests/test_orm/test_autovacuum.py` - `TestAutovacuum`
- Pattern: no SQL text, no query counts, no cursor/savepoint use
- Why: 13 files / ~80 tests are already backend-neutral and can be collected unchanged.
- Existing tests: `odoo/addons/test_base/tests/test_orm/test_access.py`, `odoo/addons/test_base/tests/test_orm/test_acl.py`, `odoo/addons/test_base/tests/test_orm/test_copy.py`, `odoo/addons/test_base/tests/test_orm/test_create.py`, `odoo/addons/test_base/tests/test_orm/test_prefetch.py`, `odoo/addons/test_base/tests/test_orm/test_views.py`
- Neutral assertion: run as-is; they assert on record values, access errors (AccessError) and view structure only.

#### `core.reuse_with_edits` - test_orm.* models (`test_base`)

- Code: `odoo/addons/test_base/tests/test_orm/test_domain.py:15` - `TestDomain`, `TestDomainComplement`, `TestDomainOptimize`; `odoo/addons/test_base/tests/test_orm/test_parent_store.py` - `TestParentStore`; `odoo/addons/test_base/tests/test_orm/test_many2many.py` - `test_not_in_relation_as_query`; `odoo/addons/test_base/tests/test_orm/test_one2many.py` - `assertQueryCount`; `odoo/addons/test_base/tests/test_orm/test_inherits.py` - `assertQueries`; `odoo/addons/test_base/tests/test_orm/test_ir_rules.py` - `assertQueryCount`; `odoo/addons/test_base/tests/test_orm/test_company_checks.py` - `assertQueryCount`; `odoo/addons/test_base/tests/test_orm/test_search_order.py` - `assertQueries`; `odoo/addons/test_base/tests/test_orm/test_sort.py` - `assertQueryCount`; `odoo/addons/test_base/tests/test_orm/test_access_feedback.py` - `flush_all`
- Pattern: a handful of assertQueryCount/assertQueries/SQL() lines inside otherwise behavioural tests
- Why: ~160 tests whose only backend-specific lines are query-count guards or a raw SELECT used to double-check a value; the behavioural asserts next to them are the ones to keep.
- Existing tests: `odoo/addons/test_base/tests/test_orm/test_domain.py`, `odoo/addons/test_base/tests/test_orm/test_one2many.py`, `odoo/addons/test_base/tests/test_orm/test_inherits.py`
- Neutral assertion: copy the test with assertQueryCount/assertQueries replaced by a no-op context and raw SQL cross-checks replaced by .read(); keep every value/exception assertion.

#### `core.reuse_split_by_class` - test_orm.* models (`test_base`)

- Code: `odoo/addons/test_base/tests/test_orm/test_fields.py:4104` - `TestParentStore`, `TestSelectionOndelete`, `TestUnlinkConstraints`, `TestRequiredMany2one`, `TestCompanyDependent`, `TestComputeQueries`, `TestModifiedPerformance`; `odoo/addons/test_base/tests/test_orm/test_search.py` - `TestSearch`, `TestSearchAny`, `TestSearchRelated`, `TestSubqueries`; `odoo/addons/test_base/tests/test_orm/test_domain_expression.py` - `TestExpression`, `TestMany2one`, `TestOne2many`, `TestMany2many`, `TestQueries`; `odoo/addons/test_base/tests/test_orm/test_read_group_private.py` - `TestPrivateReadGroup`, `TestPublicReadGroup`; `odoo/addons/test_base/tests/test_orm/test_properties.py` - `PropertiesCase`, `PropertiesSearchCase`; `odoo/addons/test_base/tests/test_orm/test_models.py` - `TestORM`, `TestRecordset`
- Pattern: files mixing behavioural classes with SQL-asserting classes (TestComputeQueries, TestModifiedPerformance, TestSubqueries, TestQueries)
- Why: test_fields (219 tests), test_search (67), test_domain_expression (86), test_read_group_private (29), test_properties (44) hold the bulk of ORM semantics; reusing by class keeps the neutral ones.
- Existing tests: `odoo/addons/test_base/tests/test_orm/test_fields.py`, `odoo/addons/test_base/tests/test_orm/test_search.py`, `odoo/addons/test_base/tests/test_orm/test_domain_expression.py`
- Neutral assertion: include classes TestParentStore, TestSelectionOndelete, TestUnlinkConstraints, TestRequiredMany2one, TestCompanyDependent, TestSearch, TestSearchAny, TestSearchRelated, TestExpression, TestMany2one/One2many/Many2many, TestPrivateReadGroup, PropertiesCase, TestORM, TestRecordset; exclude TestComputeQueries, TestModifiedPerformance, TestSubqueries, TestQueries, TestFlushSearch.

## Deliberately left out

- **odoo/addons/test_base/tests/test_orm/test_performance.py, test_timeit.py, test_query.py, test_registry.py, test_registry_signaling.py, test_schema.py, test_index_method.py, test_indexed_translation.py, test_read_grouping_sets.py, test_read_group_override.py, test_modules_db.py, test_uninstall.py, test_all_models.py, test_cache.py** - They measure PostgreSQL itself (query counts, SQL text, schema/DDL reflection, registry signalling via DB sequences, psycopg2 error classes). Not expressible as ORM-observable behaviour.
- **Schema management - odoo/tools/sql.py, odoo/modules/db.py, odoo/addons/base/models/ir_model.py (_reflect_constraint, query_insert/query_update), BaseModel._auto_init/_check_removed_columns** - DDL/reflection is a backend implementation concern, not ORM behaviour; a document store has no columns to reflect. Covered by backend-specific tests instead.
- **Country-specific EDI locking - addons/l10n_*_edi*/ (11 files with FOR UPDATE)** - Localisation addons; the same lock_for_update API is covered by the core/payment targets.
- **payment, resource, base_automation, account_edi, mrp, purchase locking call sites** - All call BaseModel.lock_for_update / try_lock_for_update (covered by concurrency.lock_for_update); listed as extension candidates, not primary targets, to keep the spread at eight addons.
- **mass_mailing (63 raw SQL sites), gamification (22), crm (19), analytic (17), pos_sale (27)** - Outside the agreed spread; their SQL shapes (bulk stats, leaderboards) repeat account/mail patterns. Extension candidates.
- **Downstream report views - website_crm_partner_assign, purchase_stock vendor_delay_report, hr_timesheet, hr_skills, fleet, lunch, event_sale, im_livechat reports** - Same two SQL-view styles as the selected reports; adding them adds fixtures, not new backend behaviour.
- **BaseModel._sql_error_to_message_generic and psycopg2.errors.* branches (odoo/orm/models.py)** - Translates PG error classes into messages; the neutral suite asserts on the raised exception class, not on message text.
- **HttpCase / JS tours, populate, cli, profiler** - Not ORM behaviour.
- **Query-count and SQL-text assertions anywhere (assertQueryCount, assertQueries, SQL(), cr.execute in tests)** - Ruled out by the board's definition of backend-neutral.

## Open decisions for the next ticket

- **D1. Which exception class does the neutral suite assert for DB-enforced integrity violations?** At flush time the ORM raises psycopg2.IntegrityError (see addons/hr_holidays/tests/test_holidays_flow.py::test_sql_constraint_dates); only the RPC layer (odoo/http/retrying.py, BaseModel._sql_error_to_message_generic) turns it into ValidationError. *Proposal:* Define one backend-neutral alias (e.g. odoo.exceptions.IntegrityViolation or a tuple exported by the suite) that maps to psycopg2.IntegrityError on PG and to the future backend's class; tests import only the alias.
- **D2. Same for lock / serialization failures.** odoo/sql_db.py exports PG_CONCURRENCY_ERRORS_TO_RETRY (LockNotAvailable, SerializationFailure); callers catch psycopg2.OperationalError. *Proposal:* Suite-level ConcurrencyError alias mapped the same way; multi-cursor tests use registry.cursor() only through a helper so the cursor type is swappable.

## How the sample was built

Static grep over `odoo/` and `addons/` `*.py` (excluding `tests/`, `static/`, `node_modules/`) for the scan patterns above, then manual reading of each candidate to confirm C1-C2 and to find the closest existing test. Counts are file/call-site counts from that scan and differ slightly from the ticket's figures because of pattern choice; they are inventory evidence, not coverage data.
