# Schema sign-off pack — s3.1 (board UNT12, ticket UNT12-9)

Plugin pinned at `9a584b4` (unpatched). Committed spec: **`map-draft-2`** (mapping_sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc`), rebuilt from the `map-draft-1` proposal (proposal on origin/mongo-run/unt12) by `.migration/rehearsal/scratch_draft2.sh` (plan decision `d-plugin-gap = accept-scratch-draft2`). Review page: `.migration/model_cards.md`. Tolerances `unt12-3` (sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea`, `aggregate_rel_tol` 1e-12; plan decision `d-float-aggregates = rel-tol-float8`).

## 1. Where this stands (read first)

- Every open item of `map-draft-1` has an answer: 11 answer lines in `.migration/answers.txt` plus 17 hand-written decisions in `.migration/design_decisions.json` (the answer lines compile to 182 decisions; map-draft-2 records 199 decisions in all). Applied by `scratch_draft2.sh` they leave **0 `modeling.unresolved` and 0 collection/embed open questions**.
- The pinned plugin refuses to apply them to `map-draft-1` as proposed (exit 1, `dangling references after decisions`, 299 referrer→target pairs pointing at collections of `--exclude-table` tables; transcript `.migration/rehearsal/patch_attempt.map-draft-1.txt`). Per `d-plugin-gap`, `map-draft-2` is built by `scratch_draft2.sh`, which filters those rows out of a copy of the proposal before patching (section 3); the recipe reproduces the committed sha256 byte for byte.
- `model_patch.py --check`: committed `map-draft-1` exits 1 (1460 `no rationale row`, 8 pending-decision lines, 0 other); committed `map-draft-2` exits 1 with **exactly 1460 `no rationale row` lines, 0 other failures and 0 open items** — the `g-model-evidence` gate as redefined by `d-plugin-gap` (section 2.3; transcript `.migration/rehearsal/check.map-draft-2.txt`).
- Local rehearsal (odoo_fixture → local mongo:7, `--target-class local`): 1709 documents in 66 collections; largest document 7585 bytes (0.0452% of 16 MB, `productAttribute`); longest array 46 elements (`accountFiscalPosition.accountTaxRel`). Recon fixture mode: map-draft-1 at tolerances unt12-2 **FAIL** (two float8 SUM rounding differences at zero tolerance), map-draft-2 at unt12-3 **PASS** (section 6). A fixture PASS/FAIL proves the load path only, never parity.
- Two model findings from the rehearsal, both answered in `design_decisions.json`: the proposal gives `accountMove` 67 indexes and MongoDB caps a collection at 64 (section 5.3); `account_partial_reconcile` has two parents and keeps its own collection (section 5.1).

## 2. Questions the schema step asked, and the answers

### 2.1 Count by kind

| kind | open in map-draft-1 | open in map-draft-2 |
|---|---|---|
| cascade_into_embed | 44 | 0 |
| embed_unbounded | 8 | 0 |
| extended_reference_candidate | 269 | 0 |
| fanout_unmeasured | 49 | 0 |
| lob | 13 | 0 |
| many_to_many_junction | 56 | 0 |
| nullable_unique_key | 7 | 0 |
| single_valued_index_key | 11 | 0 |
| source_index_not_exercised | 122 | 0 |
| transient_tables | 1 | 0 |

Total: **580** (65 spec-wide `modeling.unresolved`, 515 collection and embed `open_questions`) in 10 kinds → **0** after the answers. `known_incompatibilities`: the spec has no such key at this plugin version; the ddl/census findings surface as the kinds above.

### 2.2 Answer lines (`.migration/answers.txt`)

- `accept ownership`: manager s3.1 note, recommended default — the 8 assumed `ownership` embeds are Odoo relation tables (`*_rel`) and one pointer leaf (customer_product_reference) that only their parent writes; keep them embedded, the fan-out is a UI-maintained list bounded by policy max_embed_fanout=1000 and the local rehearsal checks the largest document
- `close many_to_many_junction`: manager s3.1 note, recommended default — junction arrays stay on the side the s2.2-confirmed hot/warm join reads chose (the proposer's junction_array side); no confirmed pattern reads the other side alone, so no reverse multikey index is added now
- `close embed_unbounded`: manager s3.1 note, recommended default — profile p50/p99/max per embed is in the review pack fan-out table; every measured max is far below policy max_embed_fanout=1000 and max_doc_bytes=2 MiB, the 7 embeds whose parents are empty in odoo_src are listed as unexercised, and the local rehearsal measures the largest document against 16 MB
- `close transient_tables`: manager s3.1 note, recommended default — the 88 TransientModel wizard tables are scratch state the framework autovacuum deletes; none must survive cutover
- `close extended_reference_candidate`: manager s3.1 note, recommended default — keep the reference, copy no fields: the ORM resolves these Many2one reads itself, and embed-level extended references are not supported by the patcher at plugin 9a584b4
- `close source_index_not_exercised`: manager s3.1 note, recommended default — keep every unexercised source index as proposed, except on account_move where the 13 unexercised source indexes (12 index entries) are dropped by index decisions in design_decisions.json: the proposal's 67 indexes exceed MongoDB's 64-per-collection limit (the local rehearsal hit CannotCreateIndex); elsewhere no workload export was taken on odoo_src, so no drop has evidence and any drop is a later index decision
- `close fanout_unmeasured`: manager s3.1 note, recommended default — these edges have 0 child rows in odoo_src (demo data), so the bound comes from the parent's UI-maintained relation list and policy max_embed_fanout=1000; these 49 edges also have 0 rows in odoo_fixture (the fixture's synthetic 60-line outlier is on product_supplierinfo, a referenced collection, not an embed; the longest embedded array in the rehearsal is 46), so the bound is confirmed by rule, not measured, and parity on the real estate is the recon harness's job, not this draft's
- `close cascade_into_embed`: manager s3.1 note, recommended default — keep the embeds; Odoo deletes relation rows through the ORM (unlink of the other side), not through the database cascade, so on the MongoDB storage path the same ORM step pulls the element from every parent document; listed in the review pack as a storage-path responsibility
- `close lob`: manager s3.1 note, recommended default — the 13 columns are TEXT/JSONB notes, descriptions and formulas (binaries live in the filestore, not in these tables); the measured maxima are in the data profile and the local rehearsal measures the largest document against 16 MB
- `close single_valued_index_key`: manager s3.1 note, recommended default — odoo_src has one company and one currency, so these index keys show one value; the access-index plan stays as proposed because a wider domain on the real estate only improves selectivity
- `close nullable_unique_key`: manager s3.1 note, recommended default — keep it unenforced on MongoDB: the source UNIQUE admits repeated NULLs and Odoo checks these constraints in the ORM; a partial unique index can be added later with an index decision once the real estate is confirmed NULL-free

### 2.3 Hand-written decisions (`.migration/design_decisions.json`)

- **reference** — reference account_partial_reconcile accountMoveLine
- **note** — FK edges into excluded tables (1460 census relationships)
- **note** — kpi_provider.get_kpi_summary runs without a registry (NOTES.md s2.3 row 23, blocked)
- **note** — stock post_init_hook reads product_product.qty_available raw (NOTES.md s2.3 row 28, blocked)
- **index** ×12 (drop) — remove the `accountMove` source-index entries no confirmed access pattern exercises (section 5.3).
- **index** — add `accountPartialReconcile` [['debitMoveId', 1]]: AccountMoveLine._compute_amount_residual filters account_partial_reconcile by debit_move_id (hot); the restored collection keeps the proposer's creditMoveId+exchangeMoveId, companyId, exchangeMoveId and fullReconcileId indexes but none led by debit_move_id, so the debit-side lookup needs one (credit side is covered by the creditMoveId+exchangeMoveId prefix)

Edges into excluded tables, what `--check` still lists after the answers:

| edge (child side → parent side) | edges |
|---|---|
| excluded → excluded | 1039 |
| collection → excluded | 257 |
| excluded → collection | 119 |
| embed → excluded | 42 |
| excluded → embed | 3 |

Total 1460. Most-referenced excluded parents: `res_users` (711), `res_company` (88), `res_partner` (74), `res_currency` (31), `ir_model` (26), `mail_message` (18), `res_country` (17), `res_groups` (16). Disposition (recorded as a `note` decision): excluded tables stay in PostgreSQL; FK columns into them remain integer id fields on the document, resolved by the ORM across stores; edges between two excluded tables are not modeled.

## 3. Plugin gap at the pinned SHA (not patched)

`model_proposal.py` builds every collection's `decision.references` from the raw table's foreign keys (`skills/schema-modeling/model_proposal.py:1734`, `t["foreign_keys"]`) after it has removed the excluded tables from the census (`_prepare_census`, lines 1162–1197), so `map-draft-1` carries 299 reference rows whose `to` is a collection that does not exist (`resUsers`, `resCompany`, `resPartner`, `resCurrency`, …). Two consequences:

1. `model_patch.py` runs `_check_references` (`model_patch.py:1743`) after every decision list and refuses the whole patch on these pre-existing rows, so **no `--answers` or `--decisions` run can be applied** to a spec proposed with `--exclude-table` targets that are FK parents. Repro: `model_patch.py --spec .migration/mapping_spec.json --decisions <one note decision> --out /tmp/x.json --version probe` → `dangling references after decisions`.
2. `check_spec` (`model_patch.py:1961`) skips relationships only for tables in `modeling.excluded` (written by the `exclude` decision) and never consults `modeling.excluded_tables` (written by `--exclude-table`), so every census FK touching an excluded table is a `no rationale row` failure (1460 here). The `exclude` decision cannot be used instead: it needs an existing collection and refuses one that is referenced (`decision refused: no collection named 'resUsers'`).

Plan decision `d-plugin-gap = accept-scratch-draft2`: the committed `map-draft-2` is the proposal with those 299 reference rows filtered out and the answers applied by the pinned patcher (`scratch_draft2.sh`, reproducible byte for byte); `g-model-evidence` is read as `--check` leaving only the 1460 excluded-table lines and 0 open items. The two plugin fixes stay open for the plugin repo.

## 4. Hot queries confirmed in s2.2

841 confirmed `hot` access patterns (35 raw SQL, 556 ORM calls, 250 stored relations; 719 reads, 122 writes) out of 2236 patterns. Grouped by source routine; every id is listed below the table.

| file | routine / relation | kind | patterns | tables |
|---|---|---|---|---|
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._get_orderpoint_action | odoo | 13 | product_product, stock_location, stock_move, stock_quant, stock_warehouse, stock_warehouse_orderpoint |
| `addons/stock/models/stock_quant.py` | StockQuant.create | odoo | 9 | product_product, res_partner, stock_location, stock_lot, stock_package, stock_quant |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._action_done | odoo | 8 | stock_lot, stock_move, stock_move_line, stock_package_history |
| `addons/stock/models/stock_move.py` | StockMove._action_assign | odoo | 7 | stock_move, stock_move_line |
| `addons/stock_account/models/product.py` | ProductTemplate.write | odoo | 7 | product_category, product_product, stock_lot, stock_quant |
| `addons/account/models/account_move.py` | AccountMove._sync_dynamic_line | odoo | 6 | account_move_line |
| `addons/stock/models/product.py` | ProductProduct._compute_quantities_dict | odoo | 6 | stock_move, stock_move_line, stock_quant |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._auto_wave_lines_into_new_waves | odoo | 6 | stock_move_line, stock_picking_batch |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._log_message | odoo | 6 | res_partner, stock_location, stock_lot, stock_package |
| `addons/stock/models/stock_move_line.py` | StockMoveLine.create | odoo | 6 | stock_move, stock_picking |
| `addons/account/models/account_move.py` | AccountMove._get_chain_info | odoo | 5 | account_bank_statement_line, account_move |
| `addons/account/models/account_move.py` | AccountMove._recompute_cash_rounding_lines | odoo | 5 | account_account, account_move_line |
| `addons/account/models/account_move.py` | AccountMove._sync_non_deductible_base_lines | odoo | 5 | account_move_line |
| `addons/account/models/account_move.py` | AccountMove._sync_tax_lines | odoo | 5 | account_move_line |
| `addons/purchase_stock/models/stock_rule.py` | StockRule._run_buy | odoo | 5 | purchase_order, purchase_order_line |
| `addons/stock/models/stock_rule.py` | StockRule._search_rule | odoo | 5 | stock_rule |
| `addons/account/models/account_move.py` | AccountMove._update_sequence_made_gap | odoo | 4 | account_move |
| `addons/account/models/account_move_line.py` | AccountMoveLine.write | odoo | 4 | account_account, account_analytic_line, account_move_line |
| `addons/purchase_stock/models/res_partner.py` | ResPartner._compute_on_time_rate | odoo | 4 | purchase_order, purchase_order_line, stock_move |
| `addons/sale_stock/models/sale_order_line.py` | SaleOrderLine._compute_qty_at_date | odoo | 4 | sale_order_line, stock_move |
| `addons/stock/models/product.py` | ProductProduct._get_domain_locations | odoo | 4 | stock_location, stock_warehouse |
| `addons/stock/models/stock_location.py` | StockLocation._get_putaway_strategy | odoo | 4 | stock_move_line, stock_package, stock_quant |
| `addons/stock/models/stock_move.py` | StockMove._action_confirm | odoo | 4 | stock_move |
| `addons/stock/models/stock_move.py` | StockMove._do_unreserve | odoo | 4 | stock_move, stock_move_line |
| `addons/stock/models/stock_move.py` | StockMove._push_apply | odoo | 4 | stock_move, stock_package |
| `addons/account/models/account_bank_statement_line.py` | AccountBankStatementLine.create | odoo | 3 | account_bank_statement, account_journal, account_move_line |
| `addons/account/models/account_move.py` | AccountMove._create_opening_balance_bank_statements | odoo | 3 | account_bank_statement, account_bank_statement_line, account_journal |
| `addons/account/models/account_move.py` | AccountMove.write | odoo | 3 | account_move |
| `addons/account/models/account_move_line.py` | AccountMoveLine._reconcile_plan_with_sync | odoo | 3 | account_full_reconcile, account_move_line, account_partial_reconcile |
| `addons/account/models/account_payment.py` | AccountPayment._compute_stat_buttons_from_reconciliation | odoo | 3 | account_move, account_payment |
| `addons/product/models/product_product.py` | ProductProduct._compute_display_name | odoo | 3 | product_supplierinfo, res_partner |
| `addons/purchase/models/account_invoice.py` | AccountMove._match_purchase_orders | odoo | 3 | purchase_order |
| `addons/purchase_stock/models/purchase_order.py` | PurchaseOrder._get_picking_type | odoo | 3 | stock_picking_type, stock_warehouse |
| `addons/sale_stock/models/stock.py` | StockMove._compute_cogs_aml_ids | odoo | 3 | account_move_line, stock_move |
| `addons/stock/models/stock_location.py` | StockLocation._get_weight | odoo | 3 | stock_move_line, stock_quant |
| `addons/stock/models/stock_lot.py` | StockLot._product_qty | odoo | 3 | stock_move_line, stock_quant |
| `addons/stock/models/stock_move.py` | StockMove._action_done | odoo | 3 | stock_move_line, stock_quant |
| `addons/stock/models/stock_move.py` | StockMove._assign_picking | odoo | 3 | stock_move, stock_picking |
| `addons/stock/models/stock_move.py` | StockMove._compute_forecast_information | odoo | 3 | product_product, stock_move |
| `addons/stock/models/stock_move.py` | StockMove._merge_moves | odoo | 3 | stock_move |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._add_to_wave | odoo | 3 | stock_picking, stock_picking_batch |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._auto_wave_lines_into_existing_waves | odoo | 3 | stock_move_line, stock_picking_batch |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._free_reservation | odoo | 3 | stock_move_line |
| `addons/stock/models/stock_package.py` | StockPackage.write | odoo | 3 | stock_location, stock_package_type |
| `addons/stock/models/stock_picking.py` | StockPicking._find_auto_batch | odoo | 3 | stock_picking, stock_picking_batch |
| `addons/stock/models/stock_quant.py` | StockQuant._apply_inventory | odoo | 3 | stock_location, stock_move |
| `addons/stock/models/stock_rule.py` | StockRule._run_scheduler_tasks | odoo | 3 | stock_move, stock_warehouse_orderpoint |
| `addons/stock_account/models/product.py` | ProductProduct._compute_value | odoo | 3 | product_product |
| `addons/stock_account/models/product.py` | ProductProduct._run_avco | odoo | 3 | stock_move |
| `addons/account/models/account_analytic_plan.py` | AccountAnalyticApplicability._get_score | odoo | 2 | account_account, product_product |
| `addons/account/models/account_bank_statement.py` | AccountBankStatement._compute_balance_start | odoo | 2 | account_bank_statement_line, account_move |
| `addons/account/models/account_bank_statement_line.py` | AccountBankStatementLine._compute_running_balance | sql | 2 | account_bank_statement, account_bank_statement_line, account_move |
| `addons/account/models/account_bank_statement_line.py` | AccountBankStatementLine._get_default_amls_matching_domain | odoo | 2 | account_account, res_company |
| `addons/account/models/account_full_reconcile.py` | AccountFullReconcile.create | sql | 2 | account_move_line, account_partial_reconcile |
| `addons/account/models/account_move.py` | AccountMove._autopost_draft_entries | odoo | 2 | account_move |
| `addons/account/models/account_move.py` | AccountMove._compute_payment_state | odoo | 2 | account_move |
| `addons/account/models/account_move.py` | AccountMove._fetch_duplicate_reference | odoo | 2 | account_move |
| `addons/account/models/account_move.py` | AccountMove._get_all_reconciled_invoice_partials | odoo | 2 | account_move_line, res_currency |
| `addons/account/models/account_move.py` | AccountMove._get_all_reconciled_invoice_partials | sql | 2 | account_move_line, account_partial_reconcile |
| `addons/account/models/account_move.py` | AccountMove._get_last_sequence_domain | odoo | 2 | account_move |
| `addons/account/models/account_move.py` | AccountMove._move_dict_to_preview_vals | odoo | 2 | account_account, res_partner |
| `addons/account/models/account_move.py` | AccountMove._post | odoo | 2 | account_move, account_partial_reconcile |
| `addons/account/models/account_move.py` | AccountMove._prepare_epd_base_lines_for_taxes_computation_from_base_lines | odoo | 2 | account_account, account_tax |
| `addons/account/models/account_move.py` | AccountMove._remove_reconciliation_between_moves | odoo | 2 | account_move_line, account_partial_reconcile |
| `addons/account/models/account_move.py` | AccountMove._search_default_journal | odoo | 2 | account_journal |
| `addons/account/models/account_move.py` | AccountMove._stolen_move | odoo | 2 | account_move_line |
| `addons/account/models/account_move.py` | AccountMove._unlink_next_draft_auto_post_moves | odoo | 2 | account_move |
| `addons/account/models/account_move_line.py` | AccountMoveLine._compute_cumulated_balance | odoo | 2 | account_account, account_move_line |
| `addons/account/models/account_move_line.py` | AccountMoveLine._create_exchange_difference_moves | odoo | 2 | account_journal, account_move |
| `addons/account/models/account_move_line.py` | AccountMoveLine._inverse_analytic_distribution | odoo | 2 | account_analytic_line, account_move_line |
| `addons/account/models/account_move_line.py` | AccountMoveLine._optimize_reconciliation_plan | odoo | 2 | account_move_line |
| `addons/account/models/account_move_line.py` | AccountMoveLine.create | odoo | 2 | account_move, account_move_line |
| `addons/account/models/account_payment.py` | AccountPayment._compute_destination_account_id | odoo | 2 | account_account |
| `addons/account/models/account_payment.py` | AccountPayment._compute_stat_buttons_from_reconciliation | sql | 2 | account_account, account_move, account_move_line, account_partial_reconcile, account_payment |
| `addons/account/models/account_tax.py` | AccountTax._compute_tax_group_id | odoo | 2 | account_tax_group |
| `addons/account/models/partner.py` | ResPartner._credit_debit_get | odoo | 2 | res_partner |
| `addons/product/models/product_pricelist.py` | ProductPricelist._get_partner_pricelist_multi | odoo | 2 | res_partner |
| `addons/purchase/models/product.py` | ProductProduct._compute_forecasted_without_stock | odoo | 2 | purchase_order_line |
| `addons/purchase/models/purchase_order.py` | PurchaseOrder._create_downpayments | odoo | 2 | purchase_order_line |
| `addons/purchase_stock/models/product.py` | ProductProduct._compute_suggest_estimated_price | odoo | 2 | purchase_order, res_partner |
| `addons/purchase_stock/models/purchase_order_line.py` | PurchaseOrderLine._prepare_stock_move_vals | odoo | 2 | stock_location, stock_reference |
| `addons/sale/models/account_move_line.py` | AccountMoveLine._sale_create_reinvoice_sale_line | odoo | 2 | sale_order_line |
| `addons/sale/models/payment_transaction.py` | PaymentTransaction._compute_reference_prefix | odoo | 2 | payment_transaction, sale_order |
| `addons/sale/models/product_product.py` | ProductProduct._compute_forecasted_without_stock | odoo | 2 | sale_order_line |
| `addons/sale/models/sale_order.py` | SaleOrder._create_account_invoices | odoo | 2 | account_move |
| `addons/sale/models/utm_campaign.py` | UtmCampaign._compute_sale_invoiced_amount | odoo | 2 | utm_campaign |
| `addons/sale_purchase/models/sale_order_line.py` | SaleOrderLine._purchase_increase_ordered_qty | odoo | 2 | purchase_order_line |
| `addons/sale_stock/models/sale_order_line.py` | SaleOrderLine._get_outgoing_incoming_moves | odoo | 2 | stock_move |
| `addons/sale_stock/models/stock.py` | StockMove._reassign_sale_lines | odoo | 2 | sale_order_line, stock_move |
| `addons/stock/models/stock_move.py` | StockMove._action_reset_to_progress | odoo | 2 | stock_move |
| `addons/stock/models/stock_move.py` | StockMove._create_lot_ids_from_move_line_vals | odoo | 2 | stock_lot |
| `addons/stock/models/stock_move.py` | StockMove._get_available_move_lines_out | odoo | 2 | stock_move |
| `addons/stock/models/stock_move.py` | StockMove._set_quantity | odoo | 2 | stock_move_line |
| `addons/stock/models/stock_move.py` | StockMove.create | odoo | 2 | product_product, stock_picking |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._auto_wave | odoo | 2 | stock_move_line |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._merge_lines | odoo | 2 | stock_move_line |
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._compute_allowed_location_ids | odoo | 2 | stock_location, stock_warehouse |
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._compute_deadline_date | odoo | 2 | stock_move |
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._get_daily_demand | odoo | 2 | stock_move |
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._procure_orderpoint_confirm | odoo | 2 | stock_reference, stock_warehouse_orderpoint |
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._unlink_processed_orderpoints | odoo | 2 | stock_warehouse_orderpoint |
| `addons/stock/models/stock_package.py` | StockPackage._get_weight | odoo | 2 | stock_move_line, stock_package, stock_package_type |
| `addons/stock/models/stock_picking.py` | StockPicking._compute_state | odoo | 2 | stock_move |
| `addons/stock/models/stock_picking.py` | StockPicking._get_autoprint_report_actions | odoo | 2 | lot_label_layout, product_label_layout |
| `addons/stock/models/stock_picking.py` | StockPicking.write | odoo | 2 | stock_move, stock_picking_type |
| `addons/stock/models/stock_quant.py` | StockQuant._clean_reservations | odoo | 2 | product_product, product_template, stock_move_line, stock_quant |
| `addons/stock/models/stock_quant.py` | StockQuant._compute_sn_duplicated | odoo | 2 | stock_location, stock_quant |
| `addons/stock/models/stock_quant.py` | StockQuant._unlink_zero_quants | odoo | 2 | stock_quant |
| `addons/stock/models/stock_quant.py` | StockQuant._update_available_quantity | odoo | 2 | stock_quant |
| `addons/stock/models/stock_rule.py` | StockRule._create_mto_rule_if_not_exist | odoo | 2 | stock_rule |
| `addons/stock/models/stock_warehouse.py` | StockWarehouse._get_partner_locations | odoo | 2 | stock_location |
| `addons/stock_account/models/product.py` | ProductCategory.write | odoo | 2 | product_product, product_template, stock_lot |
| `addons/stock_account/models/product.py` | ProductProduct._change_standard_price | odoo | 2 | product_value, stock_lot |
| `addons/stock_account/models/product.py` | ProductProduct._get_fifo_stack | odoo | 2 | stock_move |
| `addons/stock_account/models/product_value.py` | ProductValue.create | odoo | 2 | stock_move |
| `addons/stock_account/models/stock_move.py` | StockMove._create_account_move | odoo | 2 | account_move, stock_move |
| `addons/stock_account/models/stock_move.py` | StockMove._set_value | odoo | 2 | product_product, stock_lot |
| `addons/stock_account/models/stock_move.py` | StockMove.search_remaining_qty | odoo | 2 | product_product, product_template |
| `addons/account/models/account_account.py` | AccountAccount._compute_current_balance | odoo | 1 | account_move_line |
| `addons/account/models/account_account.py` | AccountAccount._compute_opening_debit_credit | sql | 1 | account_move_line |
| `addons/account/models/account_account.py` | AccountAccount._compute_parent_ids | odoo | 1 | account_account |
| `addons/account/models/account_account.py` | AccountAccount._compute_related_taxes_amount | odoo | 1 | account_tax, account_tax_repartition_line |
| `addons/account/models/account_analytic_line.py` | account.analytic.line.general_account_id | orm | 1 | account_account, account_analytic_line |
| `addons/account/models/account_analytic_line.py` | account.analytic.line.journal_id | orm | 1 | account_analytic_line, account_journal |
| `addons/account/models/account_analytic_line.py` | account.analytic.line.move_line_id | orm | 1 | account_analytic_line, account_move_line |
| `addons/account/models/account_analytic_line.py` | account.analytic.line.product_id | orm | 1 | account_analytic_line, product_product |
| `addons/account/models/account_bank_statement.py` | AccountBankStatement._get_invalid_statement_ids | sql | 1 | account_bank_statement, account_journal, res_company, res_currency |
| `addons/account/models/account_bank_statement.py` | AccountBankStatement._get_previous_statement | odoo | 1 | account_bank_statement |
| `addons/account/models/account_bank_statement.py` | AccountBankStatement._hash_statement | odoo | 1 | account_bank_statement_line, account_move |
| `addons/account/models/account_bank_statement.py` | account.bank.statement.attachment_ids | orm | 1 | account_bank_statement, account_bank_statement_ir_attachment_rel, ir_attachment |
| `addons/account/models/account_bank_statement.py` | account.bank.statement.company_id | orm | 1 | account_bank_statement, res_company |
| `addons/account/models/account_bank_statement.py` | account.bank.statement.currency_id | orm | 1 | account_bank_statement, res_currency |
| `addons/account/models/account_bank_statement.py` | account.bank.statement.journal_id | orm | 1 | account_bank_statement, account_journal |
| `addons/account/models/account_bank_statement.py` | account.bank.statement.line_ids | orm | 1 | account_bank_statement, account_bank_statement_line |
| `addons/account/models/account_bank_statement_line.py` | AccountBankStatementLine._compute_running_balance | odoo | 1 | res_company |
| `addons/account/models/account_bank_statement_line.py` | AccountBankStatementLine._find_or_create_bank_account | odoo | 1 | res_partner_bank |
| `addons/account/models/account_bank_statement_line.py` | AccountBankStatementLine._get_default_journal | odoo | 1 | account_journal |
| `addons/account/models/account_bank_statement_line.py` | AccountBankStatementLine._get_default_statement | odoo | 1 | account_bank_statement_line, account_move |
| `addons/account/models/account_bank_statement_line.py` | AccountBankStatementLine.formatted_read_group | odoo | 1 | account_bank_statement_line |
| `addons/account/models/account_bank_statement_line.py` | account.bank.statement.line._inherits | orm | 1 | account_bank_statement_line, account_move |
| `addons/account/models/account_bank_statement_line.py` | account.bank.statement.line.company_id | orm | 1 | account_bank_statement_line, res_company |
| `addons/account/models/account_bank_statement_line.py` | account.bank.statement.line.currency_id | orm | 1 | account_bank_statement_line, res_currency |
| `addons/account/models/account_bank_statement_line.py` | account.bank.statement.line.foreign_currency_id | orm | 1 | account_bank_statement_line, res_currency |
| `addons/account/models/account_bank_statement_line.py` | account.bank.statement.line.journal_id | orm | 1 | account_bank_statement_line, account_journal |
| `addons/account/models/account_bank_statement_line.py` | account.bank.statement.line.partner_id | orm | 1 | account_bank_statement_line, res_partner |
| `addons/account/models/account_bank_statement_line.py` | account.bank.statement.line.payment_ids | orm | 1 | account_bank_statement_line, account_payment, account_payment_account_bank_statement_line_rel |
| `addons/account/models/account_bank_statement_line.py` | account.bank.statement.line.statement_id | orm | 1 | account_bank_statement, account_bank_statement_line |
| `addons/account/models/account_bank_statement_line.py` | account.move.statement_line_ids | orm | 1 | account_bank_statement_line, account_move |
| `addons/account/models/account_full_reconcile.py` | account.full.reconcile.partial_reconcile_ids | orm | 1 | account_full_reconcile, account_partial_reconcile |
| `addons/account/models/account_full_reconcile.py` | account.full.reconcile.reconciled_line_ids | orm | 1 | account_full_reconcile, account_move_line |
| `addons/account/models/account_lock_exception.py` | AccountLock_Exception._recreate | odoo | 1 | account_lock_exception |
| `addons/account/models/account_move.py` | AccountMove._compute_abnormal_warnings | odoo | 1 | account_move |
| `addons/account/models/account_move.py` | AccountMove._compute_abnormal_warnings | sql | 1 | account_move |
| `addons/account/models/account_move.py` | AccountMove._compute_fiscal_position_id | odoo | 1 | res_partner |
| `addons/account/models/account_move.py` | AccountMove._compute_invoice_cash_rounding_id | odoo | 1 | account_cash_rounding |
| `addons/account/models/account_move.py` | AccountMove._compute_linked_attachment_id | odoo | 1 | ir_attachment |
| `addons/account/models/account_move.py` | AccountMove._compute_payment_state | sql | 1 | account_account, account_move, account_move_line, account_partial_reconcile, account_payment |
| `addons/account/models/account_move.py` | AccountMove._compute_payments_widget_to_reconcile_info | odoo | 1 | account_move_line |
| `addons/account/models/account_move.py` | AccountMove._compute_reconciled_payment_ids | odoo | 1 | account_payment |
| `addons/account/models/account_move.py` | AccountMove._compute_reconciled_payment_ids | sql | 1 | account_account, account_move, account_move_line, account_partial_reconcile, account_payment |
| `addons/account/models/account_move.py` | AccountMove._copy_recurring_entries | sql | 1 | account_move |
| `addons/account/models/account_move.py` | AccountMove._create_cogs_lines | odoo | 1 | account_move_line |
| `addons/account/models/account_move.py` | AccountMove._detach_attachments | odoo | 1 | ir_attachment |
| `addons/account/models/account_move.py` | AccountMove._fetch_duplicate_reference | sql | 1 | account_move |
| `addons/account/models/account_move.py` | AccountMove._get_edi_creation | odoo | 1 | account_move |
| `addons/account/models/account_move.py` | AccountMove._get_invoice_counterpart_amls_for_early_payment_discount_per_payment_term_line | odoo | 1 | account_tax_repartition_line |
| `addons/account/models/account_move.py` | AccountMove._get_suitable_journal_ids | odoo | 1 | account_journal |
| `addons/account/models/account_move.py` | AccountMove._get_unbalanced_moves | sql | 1 | account_move, account_move_line, res_company, res_currency |
| `addons/account/models/account_move.py` | AccountMove._message_post_after_hook | odoo | 1 | account_move |
| `addons/account/models/account_move.py` | AccountMove._reverse_moves | odoo | 1 | account_move |
| `addons/account/models/account_move.py` | AccountMove._routing_check_route | odoo | 1 | res_company |
| `addons/account/models/account_move.py` | AccountMove._sync_dynamic_line_needed_values | odoo | 1 | account_move |
| `addons/account/models/account_move.py` | AccountMove._sync_invoice | odoo | 1 | account_move_line |
| `addons/account/models/account_move.py` | AccountMove._sync_unbalanced_lines | odoo | 1 | account_move_line |
| `addons/account/models/account_move.py` | AccountMove._unlink_next_draft_auto_post_moves | sql | 1 | account_move |
| `addons/account/models/account_move.py` | AccountMove._update_sequence_made_gap | sql | 1 | account_move |
| `addons/account/models/account_move.py` | AccountMove.action_post | odoo | 1 | validate_account_move |
| `addons/account/models/account_move.py` | AccountMove.create | odoo | 1 | account_move |
| `addons/account/models/account_move.py` | account.move.adjusting_entries_move_ids | orm | 1 | account_move, adjusting_entries__account_move |
| `addons/account/models/account_move.py` | account.move.adjusting_entry_origin_move_ids | orm | 1 | account_move, adjusting_entries__account_move |
| `addons/account/models/account_move.py` | account.move.attachment_ids | orm | 1 | account_move, ir_attachment |
| `addons/account/models/account_move.py` | account.move.auto_post_origin_id | orm | 1 | account_move |
| `addons/account/models/account_move.py` | account.move.commercial_partner_id | orm | 1 | account_move, res_partner |
| `addons/account/models/account_move.py` | account.move.company_id | orm | 1 | account_move, res_company |
| `addons/account/models/account_move.py` | account.move.currency_id | orm | 1 | account_move, res_currency |
| `addons/account/models/account_move.py` | account.move.exchange_diff_partial_ids | orm | 1 | account_move, account_partial_reconcile |
| `addons/account/models/account_move.py` | account.move.fiscal_position_id | orm | 1 | account_fiscal_position, account_move |
| `addons/account/models/account_move.py` | account.move.import_source_attachment_id | orm | 1 | account_move, ir_attachment |
| `addons/account/models/account_move.py` | account.move.invoice_cash_rounding_id | orm | 1 | account_cash_rounding, account_move |
| `addons/account/models/account_move.py` | account.move.invoice_incoterm_id | orm | 1 | account_incoterms, account_move |
| `addons/account/models/account_move.py` | account.move.invoice_line_ids | orm | 1 | account_move, account_move_line |
| `addons/account/models/account_move.py` | account.move.invoice_payment_term_id | orm | 1 | account_move, account_payment_term |
| `addons/account/models/account_move.py` | account.move.invoice_user_id | orm | 1 | account_move, res_users |
| `addons/account/models/account_move.py` | account.move.invoice_vendor_bill_id | orm | 1 | account_move |
| `addons/account/models/account_move.py` | account.move.journal_id | orm | 1 | account_journal, account_move |
| `addons/account/models/account_move.py` | account.move.line_ids | orm | 1 | account_move, account_move_line |
| `addons/account/models/account_move.py` | account.move.matched_payment_ids | orm | 1 | account_move, account_move__account_payment, account_payment |
| `addons/account/models/account_move.py` | account.move.origin_payment_id | orm | 1 | account_move, account_payment |
| `addons/account/models/account_move.py` | account.move.partner_bank_id | orm | 1 | account_move, res_partner_bank |
| `addons/account/models/account_move.py` | account.move.partner_id | orm | 1 | account_move, res_partner |
| `addons/account/models/account_move.py` | account.move.partner_shipping_id | orm | 1 | account_move, res_partner |
| `addons/account/models/account_move.py` | account.move.preferred_payment_method_line_id | orm | 1 | account_move, account_payment_method_line |
| `addons/account/models/account_move.py` | account.move.reversal_move_ids | orm | 1 | account_move |
| `addons/account/models/account_move.py` | account.move.reversed_entry_id | orm | 1 | account_move |
| `addons/account/models/account_move.py` | account.move.statement_line_id | orm | 1 | account_bank_statement_line, account_move |
| `addons/account/models/account_move.py` | account.move.tax_cash_basis_created_move_ids | orm | 1 | account_move |
| `addons/account/models/account_move.py` | account.move.tax_cash_basis_origin_move_id | orm | 1 | account_move |
| `addons/account/models/account_move.py` | account.move.tax_cash_basis_rec_id | orm | 1 | account_move, account_partial_reconcile |
| `addons/account/models/account_move_line.py` | AccountMoveLine._compute_account_id | odoo | 1 | account_account |
| `addons/account/models/account_move_line.py` | AccountMoveLine._compute_account_id | sql | 1 | account_account, account_account_res_company_rel, account_move_line |
| `addons/account/models/account_move_line.py` | AccountMoveLine._compute_amount_residual | sql | 1 | account_partial_reconcile, res_currency |
| `addons/account/models/account_move_line.py` | AccountMoveLine._compute_analytic_distribution | odoo | 1 | account_analytic_account |
| `addons/account/models/account_move_line.py` | AccountMoveLine._compute_balance | odoo | 1 | account_move_line |
| `addons/account/models/account_move_line.py` | AccountMoveLine._compute_parent_id | odoo | 1 | account_move_line |
| `addons/account/models/account_move_line.py` | AccountMoveLine._create_analytic_lines | odoo | 1 | account_analytic_line |
| `addons/account/models/account_move_line.py` | AccountMoveLine._filter_reconciled_by_number | odoo | 1 | account_move_line |
| `addons/account/models/account_move_line.py` | AccountMoveLine._inverse_analytic_distribution | sql | 1 | account_move_line |
| `addons/account/models/account_move_line.py` | AccountMoveLine._prepare_analytic_distribution_line | odoo | 1 | account_analytic_account |
| `addons/account/models/account_move_line.py` | AccountMoveLine._reconcile_marked | odoo | 1 | account_move_line |
| `addons/account/models/account_move_line.py` | AccountMoveLine._reconciled_by_number | odoo | 1 | account_move_line |
| `addons/account/models/account_move_line.py` | AccountMoveLine.invalidate_model | odoo | 1 | account_move |
| `addons/account/models/account_move_line.py` | AccountMoveLine.invalidate_recordset | odoo | 1 | account_move |
| `addons/account/models/account_move_line.py` | account.move.line.account_id | orm | 1 | account_account, account_move_line |
| `addons/account/models/account_move_line.py` | account.move.line.analytic_line_ids | orm | 1 | account_analytic_line, account_move_line |
| `addons/account/models/account_move_line.py` | account.move.line.cogs_origin_id | orm | 1 | account_move_line |
| `addons/account/models/account_move_line.py` | account.move.line.currency_id | orm | 1 | account_move_line, res_currency |
| `addons/account/models/account_move_line.py` | account.move.line.full_reconcile_id | orm | 1 | account_full_reconcile, account_move_line |
| `addons/account/models/account_move_line.py` | account.move.line.group_tax_id | orm | 1 | account_move_line, account_tax |
| `addons/account/models/account_move_line.py` | account.move.line.matched_credit_ids | orm | 1 | account_move_line, account_partial_reconcile |
| `addons/account/models/account_move_line.py` | account.move.line.matched_debit_ids | orm | 1 | account_move_line, account_partial_reconcile |
| `addons/account/models/account_move_line.py` | account.move.line.move_id | orm | 1 | account_move, account_move_line |
| `addons/account/models/account_move_line.py` | account.move.line.partner_id | orm | 1 | account_move_line, res_partner |
| `addons/account/models/account_move_line.py` | account.move.line.payment_id | orm | 1 | account_move_line, account_payment |
| `addons/account/models/account_move_line.py` | account.move.line.product_id | orm | 1 | account_move_line, product_product |
| `addons/account/models/account_move_line.py` | account.move.line.product_uom_id | orm | 1 | account_move_line, uom_uom |
| `addons/account/models/account_move_line.py` | account.move.line.reconcile_model_id | orm | 1 | account_move_line, account_reconcile_model |
| `addons/account/models/account_move_line.py` | account.move.line.search_account_id | orm | 1 | account_account, account_move_line |
| `addons/account/models/account_move_line.py` | account.move.line.statement_line_id | orm | 1 | account_bank_statement_line, account_move_line |
| `addons/account/models/account_move_line.py` | account.move.line.tax_ids | orm | 1 | account_move_line, account_move_line_account_tax_rel, account_tax |
| `addons/account/models/account_move_line.py` | account.move.line.tax_line_id | orm | 1 | account_move_line, account_tax |
| `addons/account/models/account_move_line.py` | account.move.line.tax_repartition_line_id | orm | 1 | account_move_line, account_tax_repartition_line |
| `addons/account/models/account_move_line.py` | account.move.line.tax_tag_ids | orm | 1 | account_account_tag, account_account_tag_account_move_line_rel, account_move_line |
| `addons/account/models/account_move_line_tax_details.py` | AccountMoveLine._get_query_tax_details | sql | 1 | account_move, account_move_line_account_tax_rel, account_tax, account_tax_filiation_rel, account_tax_repartition_line, res_currency |
| `addons/account/models/account_partial_reconcile.py` | AccountPartialReconcile._get_cash_basis_base_line_grouping_key_from_vals | odoo | 1 | account_tax |
| `addons/account/models/account_partial_reconcile.py` | AccountPartialReconcile._get_cash_basis_tax_line_grouping_key_from_vals | odoo | 1 | account_tax |
| `addons/account/models/account_partial_reconcile.py` | AccountPartialReconcile._update_matching_number | odoo | 1 | account_move_line |
| `addons/account/models/account_partial_reconcile.py` | AccountPartialReconcile._update_matching_number | sql | 1 | account_move_line |
| `addons/account/models/account_partial_reconcile.py` | account.partial.reconcile.company_id | orm | 1 | account_partial_reconcile, res_company |
| `addons/account/models/account_partial_reconcile.py` | account.partial.reconcile.credit_currency_id | orm | 1 | account_partial_reconcile, res_currency |
| `addons/account/models/account_partial_reconcile.py` | account.partial.reconcile.credit_move_id | orm | 1 | account_move_line, account_partial_reconcile |
| `addons/account/models/account_partial_reconcile.py` | account.partial.reconcile.debit_currency_id | orm | 1 | account_partial_reconcile, res_currency |
| `addons/account/models/account_partial_reconcile.py` | account.partial.reconcile.debit_move_id | orm | 1 | account_move_line, account_partial_reconcile |
| `addons/account/models/account_partial_reconcile.py` | account.partial.reconcile.exchange_move_id | orm | 1 | account_move, account_partial_reconcile |
| `addons/account/models/account_partial_reconcile.py` | account.partial.reconcile.full_reconcile_id | orm | 1 | account_full_reconcile, account_partial_reconcile |
| `addons/account/models/account_payment.py` | AccountPayment._compute_available_journal_ids | odoo | 1 | account_journal |
| `addons/account/models/account_payment.py` | AccountPayment._compute_journal_id | odoo | 1 | account_journal |
| `addons/account/models/account_payment.py` | AccountPayment._fetch_duplicate_reference | odoo | 1 | account_payment |
| `addons/account/models/account_payment.py` | AccountPayment._fetch_duplicate_reference | sql | 1 | account_payment |
| `addons/account/models/account_payment.py` | account.move.payment_ids | orm | 1 | account_move, account_payment |
| `addons/account/models/account_payment.py` | account.payment.attachment_ids | orm | 1 | account_payment, ir_attachment |
| `addons/account/models/account_payment.py` | account.payment.commercial_partner_id | orm | 1 | account_payment, res_partner |
| `addons/account/models/account_payment.py` | account.payment.company_id | orm | 1 | account_payment, res_company |
| `addons/account/models/account_payment.py` | account.payment.currency_id | orm | 1 | account_payment, res_currency |
| `addons/account/models/account_payment.py` | account.payment.destination_account_id | orm | 1 | account_account, account_payment |
| `addons/account/models/account_payment.py` | account.payment.invoice_ids | orm | 1 | account_move, account_move__account_payment, account_payment |
| `addons/account/models/account_payment.py` | account.payment.journal_id | orm | 1 | account_journal, account_payment |
| `addons/account/models/account_payment.py` | account.payment.move_id | orm | 1 | account_move, account_payment |
| `addons/account/models/account_payment.py` | account.payment.outstanding_account_id | orm | 1 | account_account, account_payment |
| `addons/account/models/account_payment.py` | account.payment.paired_internal_transfer_payment_id | orm | 1 | account_payment |
| `addons/account/models/account_payment.py` | account.payment.partner_bank_id | orm | 1 | account_payment, res_partner_bank |
| `addons/account/models/account_payment.py` | account.payment.partner_id | orm | 1 | account_payment, res_partner |
| `addons/account/models/account_payment.py` | account.payment.payment_method_line_id | orm | 1 | account_payment, account_payment_method_line |
| `addons/account/models/account_payment.py` | account.payment.return_partner_bank_id | orm | 1 | account_payment, res_partner_bank |
| `addons/account/models/account_report.py` | AccountReportExpression._get_matching_tags | odoo | 1 | account_account_tag |
| `addons/account/models/account_tax.py` | AccountTax._get_tax_totals_summary | odoo | 1 | account_tax_group |
| `addons/account/models/account_tax.py` | AccountTax._prepare_tax_lines | odoo | 1 | res_currency |
| `addons/account/models/account_tax.py` | AccountTax._track_execute | odoo | 1 | account_tax |
| `addons/account/models/company.py` | ResCompany._get_user_lock_date | odoo | 1 | account_lock_exception |
| `addons/account/models/mail_message.py` | MailMessage._compute_account_audit_log_restricted | odoo | 1 | mail_message |
| `addons/account/models/partner.py` | AccountFiscalPosition._compute_foreign_vat_header_mode | odoo | 1 | account_tax |
| `addons/account/models/partner.py` | ResPartner._compute_days_sales_outstanding | odoo | 1 | account_move |
| `addons/account/models/partner.py` | ResPartner._credit_debit_get | sql | 1 | account_account |
| `addons/account/models/partner.py` | ResPartner._has_invoice | odoo | 1 | account_move |
| `addons/account/models/partner.py` | ResPartner._increase_rank | odoo | 1 | res_partner |
| `addons/account/models/partner.py` | ResPartner._invoice_total | sql | 1 | account_move, res_company, res_currency_rate, res_partner |
| `addons/account/models/res_currency.py` | ResCurrency._get_raw_rates | sql | 1 | res_company |
| `addons/account/models/res_currency.py` | ResCurrency._has_accounting_entries | odoo | 1 | account_move_line |
| `addons/account/models/res_partner_bank.py` | ResPartnerBank._compute_duplicate_bank_partner_ids | odoo | 1 | res_partner |
| `addons/account/models/res_partner_bank.py` | ResPartnerBank._compute_duplicate_bank_partner_ids | sql | 1 | res_partner_bank |
| `addons/account_edi_ubl_cii/models/account_move.py` | AccountMove._post_process_link_to_purchase_order | odoo | 1 | account_move |
| `addons/product/models/product_attribute_value.py` | ProductAttributeValue._compute_default_extra_price_changed | odoo | 1 | product_template_attribute_value |
| `addons/product/models/product_document.py` | ProductDocument._compute_variant_attribute_value_ids | odoo | 1 | product_product |
| `addons/product/models/product_pricelist.py` | ProductPricelist._compute_price_rule_multi | odoo | 1 | product_pricelist |
| `addons/product/models/product_pricelist.py` | ProductPricelist._get_related_uoms | odoo | 1 | product_pricelist_item |
| `addons/product/models/product_pricelist_item.py` | ProductPricelistItem._compute_price_before_discount | odoo | 1 | product_pricelist_item |
| `addons/product/models/product_template.py` | ProductTemplate._compute_quantities_dict | odoo | 1 | product_product |
| `addons/product/models/product_template.py` | ProductTemplate._get_variant_for_combination | odoo | 1 | product_product |
| `addons/product/models/product_template.py` | ProductTemplate._get_variant_id_for_combination | odoo | 1 | product_product |
| `addons/purchase/models/account_invoice.py` | account.move.line.purchase_line_id | orm | 1 | account_move_line, purchase_order_line |
| `addons/purchase/models/product.py` | ProductProduct._compute_purchased_product_qty | odoo | 1 | purchase_order, purchase_order_line |
| `addons/purchase/models/product.py` | ProductProduct._has_confirmed_purchase | odoo | 1 | purchase_order, purchase_order_line |
| `addons/purchase/models/product.py` | ProductTemplate._has_confirmed_purchase | odoo | 1 | product_product, purchase_order, purchase_order_line |
| `addons/purchase/models/purchase_bill_line_match.py` | PurchaseBillLineMatch._action_create_bill_from_po_lines | odoo | 1 | account_move |
| `addons/purchase/models/purchase_bill_line_match.py` | PurchaseBillLineMatch._select_am_line | sql | 1 | account_move, account_move_line |
| `addons/purchase/models/purchase_bill_line_match.py` | PurchaseBillLineMatch._select_po_line | sql | 1 | purchase_order, purchase_order_line |
| `addons/purchase/models/purchase_order.py` | PurchaseOrder._fetch_duplicate_orders | sql | 1 | purchase_order |
| `addons/purchase/models/purchase_order.py` | PurchaseOrder._get_orders_to_remind | odoo | 1 | purchase_order |
| `addons/purchase/models/purchase_order.py` | PurchaseOrder.create | odoo | 1 | purchase_order |
| `addons/purchase/models/purchase_order.py` | PurchaseOrder.create_document_from_attachment | odoo | 1 | ir_attachment |
| `addons/purchase/models/purchase_order.py` | purchase.order.company_id | orm | 1 | purchase_order, res_company |
| `addons/purchase/models/purchase_order.py` | purchase.order.currency_id | orm | 1 | purchase_order, res_currency |
| `addons/purchase/models/purchase_order.py` | purchase.order.fiscal_position_id | orm | 1 | account_fiscal_position, purchase_order |
| `addons/purchase/models/purchase_order.py` | purchase.order.incoterm_id | orm | 1 | account_incoterms, purchase_order |
| `addons/purchase/models/purchase_order.py` | purchase.order.invoice_ids | orm | 1 | account_move, account_move_purchase_order_rel, purchase_order |
| `addons/purchase/models/purchase_order.py` | purchase.order.order_line | orm | 1 | purchase_order, purchase_order_line |
| `addons/purchase/models/purchase_order.py` | purchase.order.partner_id | orm | 1 | purchase_order, res_partner |
| `addons/purchase/models/purchase_order.py` | purchase.order.payment_term_id | orm | 1 | account_payment_term, purchase_order |
| `addons/purchase/models/purchase_order.py` | purchase.order.user_id | orm | 1 | purchase_order, res_users |
| `addons/purchase/models/purchase_order_line.py` | PurchaseOrderLine._get_accrual_line_ids | odoo | 1 | purchase_order_line |
| `addons/purchase/models/purchase_order_line.py` | purchase.order.line.accrual_move_ids | orm | 1 | account_move, purchase_order_line, purchase_order_line_accrual_move_rel |
| `addons/purchase/models/purchase_order_line.py` | purchase.order.line.company_id | orm | 1 | purchase_order_line, res_company |
| `addons/purchase/models/purchase_order_line.py` | purchase.order.line.invoice_lines | orm | 1 | account_move_line, purchase_order_line |
| `addons/purchase/models/purchase_order_line.py` | purchase.order.line.order_id | orm | 1 | purchase_order, purchase_order_line |
| `addons/purchase/models/purchase_order_line.py` | purchase.order.line.partner_id | orm | 1 | purchase_order_line, res_partner |
| `addons/purchase/models/purchase_order_line.py` | purchase.order.line.product_id | orm | 1 | product_product, purchase_order_line |
| `addons/purchase/models/purchase_order_line.py` | purchase.order.line.product_no_variant_attribute_value_ids | orm | 1 | product_template_attribute_value, product_template_attribute_value_purchase_order_line_rel, purchase_order_line |
| `addons/purchase/models/purchase_order_line.py` | purchase.order.line.tax_ids | orm | 1 | account_tax, account_tax_purchase_order_line_rel, purchase_order_line |
| `addons/purchase/models/purchase_order_line.py` | purchase.order.line.uom_id | orm | 1 | purchase_order_line, uom_uom |
| `addons/purchase_stock/models/product.py` | ProductProduct._compute_monthly_demand | odoo | 1 | stock_move |
| `addons/purchase_stock/models/product.py` | ProductProduct._get_quantity_in_progress | odoo | 1 | purchase_order_line |
| `addons/purchase_stock/models/product.py` | ProductSupplierinfo._compute_last_purchase_date | odoo | 1 | purchase_order, purchase_order_line |
| `addons/purchase_stock/models/purchase_order.py` | PurchaseOrder._log_decrease_ordered_quantity | odoo | 1 | purchase_order_line |
| `addons/purchase_stock/models/purchase_order.py` | purchase.order.dest_address_id | orm | 1 | purchase_order, res_partner |
| `addons/purchase_stock/models/purchase_order.py` | purchase.order.picking_ids | orm | 1 | purchase_order, purchase_order_stock_picking_rel, stock_picking |
| `addons/purchase_stock/models/purchase_order.py` | purchase.order.picking_type_id | orm | 1 | purchase_order, stock_picking_type |
| `addons/purchase_stock/models/purchase_order.py` | purchase.order.reference_ids | orm | 1 | purchase_order, stock_reference, stock_reference_purchase_rel |
| `addons/purchase_stock/models/purchase_order_line.py` | PurchaseOrderLine._create_stock_moves | odoo | 1 | stock_move |
| `addons/purchase_stock/models/purchase_order_line.py` | purchase.order.line.forecasted_location_id | orm | 1 | purchase_order_line, stock_location |
| `addons/purchase_stock/models/purchase_order_line.py` | purchase.order.line.move_dest_ids | orm | 1 | purchase_order_line, stock_move, stock_move_created_purchase_line_rel |
| `addons/purchase_stock/models/purchase_order_line.py` | purchase.order.line.move_ids | orm | 1 | purchase_order_line, stock_move |
| `addons/purchase_stock/models/purchase_order_line.py` | purchase.order.line.orderpoint_id | orm | 1 | purchase_order_line, stock_warehouse_orderpoint |
| `addons/purchase_stock/models/res_partner.py` | ResPartner._compute_display_name | odoo | 1 | product_product |
| `addons/purchase_stock/models/stock.py` | StockLot._compute_purchase_order_ids | odoo | 1 | stock_move_line |
| `addons/purchase_stock/models/stock.py` | StockWarehouseOrderpoint._compute_days_to_order | odoo | 1 | stock_rule |
| `addons/purchase_stock/models/stock.py` | stock.warehouse.orderpoint.supplier_id | orm | 1 | product_supplierinfo, stock_warehouse_orderpoint |
| `addons/purchase_stock/models/stock_move.py` | StockMove._action_synch_order | odoo | 1 | purchase_order_line |
| `addons/purchase_stock/models/stock_move.py` | StockMove._get_value_from_account_move | odoo | 1 | account_move_line |
| `addons/purchase_stock/models/stock_move.py` | stock.move.created_purchase_line_ids | orm | 1 | purchase_order_line, stock_move, stock_move_created_purchase_line_rel |
| `addons/purchase_stock/models/stock_move.py` | stock.move.purchase_line_id | orm | 1 | purchase_order_line, stock_move |
| `addons/purchase_stock/models/stock_rule.py` | StockRule.run | odoo | 1 | stock_warehouse |
| `addons/sale/models/account_analytic_line.py` | AccountAnalyticLine._sync_so_accounts_and_partners | odoo | 1 | account_analytic_plan |
| `addons/sale/models/account_analytic_line.py` | account.analytic.line.order_id | orm | 1 | account_analytic_line, sale_order |
| `addons/sale/models/account_analytic_line.py` | account.analytic.line.reinvoice_move_id | orm | 1 | account_analytic_line, account_move |
| `addons/sale/models/account_analytic_line.py` | account.analytic.line.so_line | orm | 1 | account_analytic_line, sale_order_line |
| `addons/sale/models/account_move.py` | AccountMove._get_reinvoiced_analytic_lines_to_link | odoo | 1 | account_analytic_line |
| `addons/sale/models/account_move.py` | account.move.team_id | orm | 1 | account_move, crm_team |
| `addons/sale/models/account_move_line.py` | AccountMoveLine._get_discount_lines | odoo | 1 | account_move_line |
| `addons/sale/models/account_move_line.py` | AccountMoveLine._sale_prepare_sale_line_values | odoo | 1 | sale_order_line |
| `addons/sale/models/account_move_line.py` | account.move.line.sale_line_ids | orm | 1 | account_move_line, sale_order_line, sale_order_line_invoice_rel |
| `addons/sale/models/payment_transaction.py` | PaymentTransaction._compute_sale_order_reference | odoo | 1 | account_journal |
| `addons/sale/models/res_partner.py` | ResPartner._compute_credit_to_invoice | odoo | 1 | sale_order |
| `addons/sale/models/res_partner.py` | ResPartner._has_order | odoo | 1 | sale_order |
| `addons/sale/models/sale_order.py` | SaleOrder._action_cancel | odoo | 1 | sale_order |
| `addons/sale/models/sale_order.py` | SaleOrder._compute_invoice_status | odoo | 1 | sale_order_line |
| `addons/sale/models/sale_order.py` | SaleOrder._create_down_payment_lines_from_base_lines | odoo | 1 | sale_order_line |
| `addons/sale/models/sale_order.py` | SaleOrder._create_down_payment_section_line_if_needed | odoo | 1 | sale_order_line |
| `addons/sale/models/sale_order.py` | SaleOrder._fetch_duplicate_orders | sql | 1 | sale_order |
| `addons/sale/models/sale_order.py` | SaleOrder._get_confirmation_template | odoo | 1 | mail_template |
| `addons/sale/models/sale_order.py` | SaleOrder._get_invoiceable_lines | odoo | 1 | sale_order_line |
| `addons/sale/models/sale_order.py` | SaleOrder._get_or_create_analytic_account | odoo | 1 | account_analytic_account |
| `addons/sale/models/sale_order.py` | SaleOrder.batch_onchange_sol | odoo | 1 | sale_order_line |
| `addons/sale/models/sale_order.py` | SaleOrder.create_document_from_attachment | odoo | 1 | ir_attachment |
| `addons/sale/models/sale_order.py` | sale.order.analytic_account_id | orm | 1 | account_analytic_account, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.company_id | orm | 1 | res_company, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.currency_id | orm | 1 | res_currency, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.fiscal_position_id | orm | 1 | account_fiscal_position, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.incoterm | orm | 1 | account_incoterms, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.journal_id | orm | 1 | account_journal, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.order_line | orm | 1 | sale_order, sale_order_line |
| `addons/sale/models/sale_order.py` | sale.order.partner_id | orm | 1 | res_partner, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.partner_invoice_id | orm | 1 | res_partner, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.partner_shipping_id | orm | 1 | res_partner, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.payment_term_id | orm | 1 | account_payment_term, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.pending_email_template_id | orm | 1 | mail_template, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.preferred_payment_method_line_id | orm | 1 | account_payment_method_line, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.pricelist_id | orm | 1 | product_pricelist, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.team_id | orm | 1 | crm_team, sale_order |
| `addons/sale/models/sale_order.py` | sale.order.transaction_ids | orm | 1 | payment_transaction, sale_order, sale_order_transaction_rel |
| `addons/sale/models/sale_order.py` | sale.order.user_id | orm | 1 | res_users, sale_order |
| `addons/sale/models/sale_order_line.py` | SaleOrderLine._get_accrual_line_ids | odoo | 1 | sale_order_line |
| `addons/sale/models/sale_order_line.py` | SaleOrderLine._get_delivered_quantity_by_analytic | odoo | 1 | account_analytic_line |
| `addons/sale/models/sale_order_line.py` | sale.order.line.accrual_move_ids | orm | 1 | account_move, sale_order_line, sale_order_line_accrual_move_rel |
| `addons/sale/models/sale_order_line.py` | sale.order.line.analytic_line_ids | orm | 1 | account_analytic_line, sale_order_line |
| `addons/sale/models/sale_order_line.py` | sale.order.line.combo_item_id | orm | 1 | product_combo_item, sale_order_line |
| `addons/sale/models/sale_order_line.py` | sale.order.line.invoice_lines | orm | 1 | account_move_line, sale_order_line, sale_order_line_invoice_rel |
| `addons/sale/models/sale_order_line.py` | sale.order.line.linked_line_id | orm | 1 | sale_order_line |
| `addons/sale/models/sale_order_line.py` | sale.order.line.linked_line_ids | orm | 1 | sale_order_line |
| `addons/sale/models/sale_order_line.py` | sale.order.line.order_id | orm | 1 | sale_order, sale_order_line |
| `addons/sale/models/sale_order_line.py` | sale.order.line.product_custom_attribute_value_ids | orm | 1 | product_attribute_custom_value, sale_order_line |
| `addons/sale/models/sale_order_line.py` | sale.order.line.product_id | orm | 1 | product_product, sale_order_line |
| `addons/sale/models/sale_order_line.py` | sale.order.line.product_no_variant_attribute_value_ids | orm | 1 | product_template_attribute_value, product_template_attribute_value_sale_order_line_rel, sale_order_line |
| `addons/sale/models/sale_order_line.py` | sale.order.line.product_uom_id | orm | 1 | sale_order_line, uom_uom |
| `addons/sale/models/sale_order_line.py` | sale.order.line.section_uom_id | orm | 1 | sale_order_line, uom_uom |
| `addons/sale/models/sale_order_line.py` | sale.order.line.tax_ids | orm | 1 | account_tax, account_tax_sale_order_line_rel, sale_order_line |
| `addons/sale/models/utm_campaign.py` | UtmCampaign._compute_sale_invoiced_amount | sql | 1 | account_move, account_move_line, res_currency_rate |
| `addons/sale_edi_ubl/models/customer_product_reference.py` | CustomerProductReference.create_or_update_product_reference | odoo | 1 | customer_product_reference |
| `addons/sale_purchase/models/purchase_order.py` | purchase.order.line.sale_line_id | orm | 1 | purchase_order_line, sale_order_line |
| `addons/sale_purchase/models/sale_order.py` | SaleOrder._activity_cancel_on_purchase | odoo | 1 | product_product, product_template, purchase_order_line |
| `addons/sale_purchase/models/sale_order_line.py` | SaleOrderLine._create_purchase_order | odoo | 1 | purchase_order |
| `addons/sale_purchase/models/sale_order_line.py` | SaleOrderLine._purchase_decrease_ordered_qty | odoo | 1 | purchase_order_line |
| `addons/sale_purchase/models/sale_order_line.py` | SaleOrderLine._purchase_service_create | odoo | 1 | purchase_order_line |
| `addons/sale_purchase/models/sale_order_line.py` | SaleOrderLine._purchase_service_match_purchase_order | odoo | 1 | purchase_order_line |
| `addons/sale_purchase/models/sale_order_line.py` | sale.order.line.purchase_line_ids | orm | 1 | purchase_order_line, sale_order_line |
| `addons/sale_purchase_stock/models/purchase_order.py` | PurchaseOrderLine._prepare_stock_moves | odoo | 1 | stock_location |
| `addons/sale_purchase_stock/models/purchase_order.py` | PurchaseOrderLine._vendor_lang_procurement_values | odoo | 1 | sale_order_line |
| `addons/sale_stock/models/sale_order.py` | SaleOrder._log_decrease_ordered_quantity | odoo | 1 | sale_order_line |
| `addons/sale_stock/models/sale_order.py` | SaleOrder.write | odoo | 1 | res_partner |
| `addons/sale_stock/models/sale_order.py` | sale.order.picking_ids | orm | 1 | sale_order, stock_picking |
| `addons/sale_stock/models/sale_order.py` | sale.order.stock_reference_ids | orm | 1 | sale_order, stock_reference, stock_reference_sale_rel |
| `addons/sale_stock/models/sale_order.py` | sale.order.warehouse_id | orm | 1 | sale_order, stock_warehouse |
| `addons/sale_stock/models/sale_order_line.py` | SaleOrderLine._action_launch_stock_rule | odoo | 1 | stock_reference |
| `addons/sale_stock/models/sale_order_line.py` | SaleOrderLine._compute_warehouse_id | odoo | 1 | stock_rule |
| `addons/sale_stock/models/sale_order_line.py` | SaleOrderLine._read_qties | odoo | 1 | sale_order_line |
| `addons/sale_stock/models/sale_order_line.py` | sale.order.line.move_ids | orm | 1 | sale_order_line, stock_move |
| `addons/sale_stock/models/sale_order_line.py` | sale.order.line.route_ids | orm | 1 | sale_order_line, sale_order_line_stock_route_rel, stock_route |
| `addons/sale_stock/models/sale_order_line.py` | sale.order.line.warehouse_id | orm | 1 | sale_order_line, stock_warehouse |
| `addons/sale_stock/models/stock.py` | StockLot._compute_sale_order_ids | odoo | 1 | sale_order_line, stock_location, stock_move, stock_move_line, stock_picking |
| `addons/sale_stock/models/stock.py` | StockMove._action_synch_order | odoo | 1 | sale_order_line |
| `addons/sale_stock/models/stock.py` | StockMove._get_sale_order_lines | odoo | 1 | stock_move |
| `addons/sale_stock/models/stock.py` | StockPicking._action_done | odoo | 1 | sale_order_line |
| `addons/sale_stock/models/stock.py` | StockPicking._set_sale_id | odoo | 1 | stock_reference |
| `addons/sale_stock/models/stock.py` | stock.move.sale_line_id | orm | 1 | sale_order_line, stock_move |
| `addons/sale_stock/models/stock.py` | stock.picking.return_reason_id | orm | 1 | return_reason, stock_picking |
| `addons/sale_stock/models/stock.py` | stock.picking.sale_id | orm | 1 | sale_order, stock_picking |
| `addons/stock/models/product.py` | ProductProduct._get_domain_locations_new | odoo | 1 | stock_location |
| `addons/stock/models/product.py` | ProductTemplate._set_tracking | odoo | 1 | product_template |
| `addons/stock/models/res_company.py` | ResCompany._compute_default_stock_location_id | odoo | 1 | stock_warehouse |
| `addons/stock/models/res_company.py` | ResCompany._compute_scrap_location_id | odoo | 1 | stock_location |
| `addons/stock/models/stock_location.py` | StockLocation._compute_child_internal_location_ids | odoo | 1 | stock_location |
| `addons/stock/models/stock_location.py` | StockLocation._compute_is_empty | odoo | 1 | stock_location, stock_quant |
| `addons/stock/models/stock_location.py` | StockLocation._compute_warehouse_id | odoo | 1 | stock_warehouse |
| `addons/stock/models/stock_location.py` | StockRoute._compute_warehouses | odoo | 1 | stock_warehouse |
| `addons/stock/models/stock_lot.py` | StockLot._compute_is_scrap | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_lot.py` | StockLot._find_delivery_ids_by_lot | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_lot.py` | StockLot._get_delivery_move_lines_by_lot | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_lot.py` | StockLot._get_next_serial | odoo | 1 | stock_lot |
| `addons/stock/models/stock_lot.py` | StockLot.write | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_lot.py` | stock.lot.company_id | orm | 1 | res_company, stock_lot |
| `addons/stock/models/stock_lot.py` | stock.lot.location_id | orm | 1 | stock_location, stock_lot |
| `addons/stock/models/stock_lot.py` | stock.lot.partner_ids | orm | 1 | res_partner, res_partner_stock_lot_rel, stock_lot |
| `addons/stock/models/stock_lot.py` | stock.lot.product_id | orm | 1 | product_product, stock_lot |
| `addons/stock/models/stock_lot.py` | stock.lot.quant_ids | orm | 1 | stock_lot, stock_quant |
| `addons/stock/models/stock_move.py` | StockMove._action_cancel | odoo | 1 | stock_move |
| `addons/stock/models/stock_move.py` | StockMove._action_reset_to_draft | odoo | 1 | stock_move |
| `addons/stock/models/stock_move.py` | StockMove._action_scrap | odoo | 1 | stock_move |
| `addons/stock/models/stock_move.py` | StockMove._compute_lot_ids | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_move.py` | StockMove._compute_quantity | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_move.py` | StockMove._get_orderpoints_to_update | odoo | 1 | stock_warehouse_orderpoint |
| `addons/stock/models/stock_move.py` | StockMove._prepare_procurement_qty | odoo | 1 | product_product |
| `addons/stock/models/stock_move.py` | StockMove._prepare_procurement_values | odoo | 1 | stock_package |
| `addons/stock/models/stock_move.py` | StockMove._recompute_state | odoo | 1 | stock_move |
| `addons/stock/models/stock_move.py` | StockMove._rollup_move_dests_fetch | odoo | 1 | stock_move |
| `addons/stock/models/stock_move.py` | StockMove._rollup_move_origs_fetch | odoo | 1 | stock_move |
| `addons/stock/models/stock_move.py` | StockMove._set_lot_ids | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_move.py` | StockMove._split | odoo | 1 | stock_move |
| `addons/stock/models/stock_move.py` | StockMove._trigger_assign | odoo | 1 | stock_move |
| `addons/stock/models/stock_move.py` | StockMove._trigger_scheduler | odoo | 1 | stock_warehouse_orderpoint |
| `addons/stock/models/stock_move.py` | StockMove._update_reserved_quantity | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_move.py` | stock.move.company_id | orm | 1 | res_company, stock_move |
| `addons/stock/models/stock_move.py` | stock.move.forecasted_location_id | orm | 1 | stock_location, stock_move |
| `addons/stock/models/stock_move.py` | stock.move.location_dest_id | orm | 1 | stock_location, stock_move |
| `addons/stock/models/stock_move.py` | stock.move.location_id | orm | 1 | stock_location, stock_move |
| `addons/stock/models/stock_move.py` | stock.move.move_dest_ids | orm | 1 | stock_move, stock_move_move_rel |
| `addons/stock/models/stock_move.py` | stock.move.move_line_ids | orm | 1 | stock_move, stock_move_line |
| `addons/stock/models/stock_move.py` | stock.move.move_orig_ids | orm | 1 | stock_move, stock_move_move_rel |
| `addons/stock/models/stock_move.py` | stock.move.never_product_template_attribute_value_ids | orm | 1 | product_template_attribute_value, stock_move, template_attribute_value_stock_move_rel |
| `addons/stock/models/stock_move.py` | stock.move.orderpoint_id | orm | 1 | stock_move, stock_warehouse_orderpoint |
| `addons/stock/models/stock_move.py` | stock.move.origin_returned_move_id | orm | 1 | stock_move |
| `addons/stock/models/stock_move.py` | stock.move.packaging_uom_id | orm | 1 | stock_move, uom_uom |
| `addons/stock/models/stock_move.py` | stock.move.partner_id | orm | 1 | res_partner, stock_move |
| `addons/stock/models/stock_move.py` | stock.move.picking_id | orm | 1 | stock_move, stock_picking |
| `addons/stock/models/stock_move.py` | stock.move.picking_type_id | orm | 1 | stock_move, stock_picking_type |
| `addons/stock/models/stock_move.py` | stock.move.product_id | orm | 1 | product_product, stock_move |
| `addons/stock/models/stock_move.py` | stock.move.reference_ids | orm | 1 | stock_move, stock_reference, stock_reference_move_rel |
| `addons/stock/models/stock_move.py` | stock.move.restrict_partner_id | orm | 1 | res_partner, stock_move |
| `addons/stock/models/stock_move.py` | stock.move.returned_move_ids | orm | 1 | stock_move |
| `addons/stock/models/stock_move.py` | stock.move.route_ids | orm | 1 | stock_move, stock_route, stock_route_move |
| `addons/stock/models/stock_move.py` | stock.move.rule_id | orm | 1 | stock_move, stock_rule |
| `addons/stock/models/stock_move.py` | stock.move.scrap_reason_tag_ids | orm | 1 | stock_move, stock_move_stock_scrap_reason_tag_rel, stock_scrap_reason_tag |
| `addons/stock/models/stock_move.py` | stock.move.uom_id | orm | 1 | stock_move, uom_uom |
| `addons/stock/models/stock_move.py` | stock.move.warehouse_id | orm | 1 | stock_move, stock_warehouse |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._copy_quant_info | odoo | 1 | stock_quant |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._create_and_assign_production_lot | odoo | 1 | stock_lot |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._get_default_dest_location | odoo | 1 | stock_location |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._get_lines_not_entire_pack | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._prepare_package_history_vals | odoo | 1 | stock_package |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._split | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_move_line.py` | StockMoveLine._split_in_chunk | odoo | 1 | stock_package |
| `addons/stock/models/stock_move_line.py` | StockMoveLine.write | odoo | 1 | stock_package |
| `addons/stock/models/stock_move_line.py` | stock.move.line.company_id | orm | 1 | res_company, stock_move_line |
| `addons/stock/models/stock_move_line.py` | stock.move.line.consume_line_ids | orm | 1 | stock_move_line, stock_move_line_consume_rel |
| `addons/stock/models/stock_move_line.py` | stock.move.line.location_dest_id | orm | 1 | stock_location, stock_move_line |
| `addons/stock/models/stock_move_line.py` | stock.move.line.location_id | orm | 1 | stock_location, stock_move_line |
| `addons/stock/models/stock_move_line.py` | stock.move.line.lot_id | orm | 1 | stock_lot, stock_move_line |
| `addons/stock/models/stock_move_line.py` | stock.move.line.move_id | orm | 1 | stock_move, stock_move_line |
| `addons/stock/models/stock_move_line.py` | stock.move.line.owner_id | orm | 1 | res_partner, stock_move_line |
| `addons/stock/models/stock_move_line.py` | stock.move.line.package_history_id | orm | 1 | stock_move_line, stock_package_history |
| `addons/stock/models/stock_move_line.py` | stock.move.line.package_id | orm | 1 | stock_move_line, stock_package |
| `addons/stock/models/stock_move_line.py` | stock.move.line.picking_id | orm | 1 | stock_move_line, stock_picking |
| `addons/stock/models/stock_move_line.py` | stock.move.line.produce_line_ids | orm | 1 | stock_move_line, stock_move_line_consume_rel |
| `addons/stock/models/stock_move_line.py` | stock.move.line.product_id | orm | 1 | product_product, stock_move_line |
| `addons/stock/models/stock_move_line.py` | stock.move.line.result_package_id | orm | 1 | stock_move_line, stock_package |
| `addons/stock/models/stock_move_line.py` | stock.move.line.uom_id | orm | 1 | stock_move_line, uom_uom |
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._compute_location_id | odoo | 1 | stock_warehouse |
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._compute_rules | odoo | 1 | stock_rule |
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._compute_warehouse_id | odoo | 1 | stock_warehouse |
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._get_orderpoint_locations | odoo | 1 | stock_location |
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._get_orderpoint_products | odoo | 1 | product_product, product_template |
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._get_qty_to_order | odoo | 1 | product_product |
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._get_replenishment_order_notification | odoo | 1 | stock_move |
| `addons/stock/models/stock_orderpoint.py` | StockWarehouseOrderpoint._prepare_procurement_values | odoo | 1 | stock_reference |
| `addons/stock/models/stock_orderpoint.py` | stock.warehouse.orderpoint.company_id | orm | 1 | res_company, stock_warehouse_orderpoint |
| `addons/stock/models/stock_orderpoint.py` | stock.warehouse.orderpoint.location_id | orm | 1 | stock_location, stock_warehouse_orderpoint |
| `addons/stock/models/stock_orderpoint.py` | stock.warehouse.orderpoint.product_id | orm | 1 | product_product, stock_warehouse_orderpoint |
| `addons/stock/models/stock_orderpoint.py` | stock.warehouse.orderpoint.replenishment_uom_id | orm | 1 | stock_warehouse_orderpoint, uom_uom |
| `addons/stock/models/stock_orderpoint.py` | stock.warehouse.orderpoint.route_id | orm | 1 | stock_route, stock_warehouse_orderpoint |
| `addons/stock/models/stock_orderpoint.py` | stock.warehouse.orderpoint.warehouse_id | orm | 1 | stock_warehouse, stock_warehouse_orderpoint |
| `addons/stock/models/stock_package.py` | StockPackage._compute_all_children_package_ids | odoo | 1 | stock_package |
| `addons/stock/models/stock_package.py` | StockPackage._compute_move_line_ids | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_package.py` | StockPackage._compute_picking_ids | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_package.py` | StockPackage.create | odoo | 1 | stock_package_type |
| `addons/stock/models/stock_package_type.py` | StockPackageType._compute_display_name | odoo | 1 | stock_package_type |
| `addons/stock/models/stock_picking.py` | StockPicking._action_done | odoo | 1 | stock_picking |
| `addons/stock/models/stock_picking.py` | StockPicking._compute_bulk_weight | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_picking.py` | StockPicking._compute_delay_alert_date | odoo | 1 | stock_move |
| `addons/stock/models/stock_picking.py` | StockPicking._default_picking_type_id | odoo | 1 | stock_picking_type |
| `addons/stock/models/stock_picking.py` | StockPicking._get_lot_move_lines_for_sanity_check | odoo | 1 | stock_move_line |
| `addons/stock/models/stock_picking.py` | StockPicking._get_packages_for_print | odoo | 1 | stock_package |
| `addons/stock/models/stock_picking.py` | StockPicking._get_show_allocation | odoo | 1 | stock_move |
| `addons/stock/models/stock_picking.py` | StockPicking._has_scrap_move | odoo | 1 | stock_move |
| `addons/stock/models/stock_picking.py` | StockPicking._intercompany_unpack | odoo | 1 | res_company |
| `addons/stock/models/stock_picking.py` | StockPicking._log_less_quantities_than_expected | odoo | 1 | stock_move |
| `addons/stock/models/stock_picking.py` | StockPicking._sanity_check | odoo | 1 | stock_picking |
| `addons/stock/models/stock_picking.py` | StockPicking.assign_batch_user | odoo | 1 | stock_picking |
| `addons/stock/models/stock_picking.py` | StockPicking.create | odoo | 1 | stock_picking_type |
| `addons/stock/models/stock_picking.py` | stock.picking.backorder_id | orm | 1 | stock_picking |
| `addons/stock/models/stock_picking.py` | stock.picking.backorder_ids | orm | 1 | stock_picking |
| `addons/stock/models/stock_picking.py` | stock.picking.batch_id | orm | 1 | stock_picking, stock_picking_batch |
| `addons/stock/models/stock_picking.py` | stock.picking.company_id | orm | 1 | res_company, stock_picking |
| `addons/stock/models/stock_picking.py` | stock.picking.location_dest_id | orm | 1 | stock_location, stock_picking |
| `addons/stock/models/stock_picking.py` | stock.picking.location_id | orm | 1 | stock_location, stock_picking |
| `addons/stock/models/stock_picking.py` | stock.picking.move_ids | orm | 1 | stock_move, stock_picking |
| `addons/stock/models/stock_picking.py` | stock.picking.move_line_ids | orm | 1 | stock_move_line, stock_picking |
| `addons/stock/models/stock_picking.py` | stock.picking.owner_id | orm | 1 | res_partner, stock_picking |
| `addons/stock/models/stock_picking.py` | stock.picking.package_history_ids | orm | 1 | stock_package_history, stock_package_history_stock_picking_rel, stock_picking |
| `addons/stock/models/stock_picking.py` | stock.picking.partner_id | orm | 1 | res_partner, stock_picking |
| `addons/stock/models/stock_picking.py` | stock.picking.picking_type_id | orm | 1 | stock_picking, stock_picking_type |
| `addons/stock/models/stock_picking.py` | stock.picking.return_id | orm | 1 | stock_picking |
| `addons/stock/models/stock_picking.py` | stock.picking.return_ids | orm | 1 | stock_picking |
| `addons/stock/models/stock_picking.py` | stock.picking.user_id | orm | 1 | res_users, stock_picking |
| `addons/stock/models/stock_picking_batch.py` | StockPickingBatch._compute_allowed_picking_ids | odoo | 1 | stock_picking |
| `addons/stock/models/stock_picking_type.py` | StockPickingType._compute_warehouse_id | odoo | 1 | stock_warehouse |
| `addons/stock/models/stock_quant.py` | StockQuant._gather | odoo | 1 | stock_quant |
| `addons/stock/models/stock_quant.py` | StockQuant._get_quants_by_products_locations | odoo | 1 | stock_quant |
| `addons/stock/models/stock_quant.py` | StockQuant._merge_quants | sql | 1 | stock_quant |
| `addons/stock/models/stock_quant.py` | StockQuant._run_least_packages_removal_strategy_astar | odoo | 1 | stock_quant |
| `addons/stock/models/stock_quant.py` | StockQuant._set_view_context | odoo | 1 | stock_warehouse |
| `addons/stock/models/stock_quant.py` | StockQuant._unlink_zero_quants | sql | 1 | stock_quant |
| `addons/stock/models/stock_quant.py` | StockQuant.check_quantity | odoo | 1 | stock_quant |
| `addons/stock/models/stock_quant.py` | StockQuant.move_quants | odoo | 1 | stock_move |
| `addons/stock/models/stock_quant.py` | stock.quant.location_id | orm | 1 | stock_location, stock_quant |
| `addons/stock/models/stock_quant.py` | stock.quant.lot_id | orm | 1 | stock_lot, stock_quant |
| `addons/stock/models/stock_quant.py` | stock.quant.owner_id | orm | 1 | res_partner, stock_quant |
| `addons/stock/models/stock_quant.py` | stock.quant.package_id | orm | 1 | stock_package, stock_quant |
| `addons/stock/models/stock_quant.py` | stock.quant.product_id | orm | 1 | product_product, stock_quant |
| `addons/stock/models/stock_quant.py` | stock.quant.user_id | orm | 1 | res_users, stock_quant |
| `addons/stock/models/stock_replenish_mixin.py` | StockReplenishMixin._compute_allowed_route_ids | odoo | 1 | stock_route |
| `addons/stock/models/stock_rule.py` | StockRule._run_pull | odoo | 1 | stock_move |
| `addons/stock/models/stock_rule.py` | StockRule._search_rule_for_warehouses | odoo | 1 | stock_rule |
| `addons/stock_account/models/account_move.py` | account.move.product_value_id | orm | 1 | account_move, product_value |
| `addons/stock_account/models/account_move.py` | account.move.stock_move_ids | orm | 1 | account_move, stock_move |
| `addons/stock_account/models/account_move_line.py` | account.move.line.stock_move_id | orm | 1 | account_move_line, stock_move |
| `addons/stock_account/models/analytic_account.py` | AccountAnalyticAccount._perform_analytic_distribution | odoo | 1 | account_analytic_account |
| `addons/stock_account/models/product.py` | ProductProduct._correct_inventory_valuation | odoo | 1 | stock_move |
| `addons/stock_account/models/product.py` | ProductProduct._get_last_in | odoo | 1 | stock_move |
| `addons/stock_account/models/product.py` | ProductProduct._get_last_product_value | odoo | 1 | product_value |
| `addons/stock_account/models/product.py` | ProductProduct._get_std_price_history_by_product | odoo | 1 | product_value |
| `addons/stock_account/models/product.py` | ProductProduct._get_stock_moves_with_valuation_by_product | odoo | 1 | stock_move |
| `addons/stock_account/models/product.py` | ProductProduct._update_standard_price | odoo | 1 | product_product |
| `addons/stock_account/models/product.py` | ProductProduct._with_valuation_context | odoo | 1 | stock_location |
| `addons/stock_account/models/product.py` | ProductProduct.write | odoo | 1 | product_template |
| `addons/stock_account/models/product_value.py` | product.value.account_move_id | orm | 1 | account_move, product_value |
| `addons/stock_account/models/product_value.py` | product.value.company_id | orm | 1 | product_value, res_company |
| `addons/stock_account/models/product_value.py` | product.value.lot_id | orm | 1 | product_value, stock_lot |
| `addons/stock_account/models/product_value.py` | product.value.move_id | orm | 1 | product_value, stock_move |
| `addons/stock_account/models/product_value.py` | product.value.product_id | orm | 1 | product_product, product_value |
| `addons/stock_account/models/product_value.py` | product.value.user_id | orm | 1 | product_value, res_users |
| `addons/stock_account/models/stock_lot.py` | StockLot._change_standard_price | odoo | 1 | product_value |
| `addons/stock_account/models/stock_move.py` | StockMove._clear_journal_entries | odoo | 1 | account_move |
| `addons/stock_account/models/stock_move.py` | StockMove._create_analytic_move | odoo | 1 | account_analytic_line |
| `addons/stock_account/models/stock_move.py` | StockMove._get_in_move_lines | odoo | 1 | stock_move_line |
| `addons/stock_account/models/stock_move.py` | StockMove._get_manual_value | odoo | 1 | product_value |
| `addons/stock_account/models/stock_move.py` | StockMove._inverse_value_manual | odoo | 1 | product_value |
| `addons/stock_account/models/stock_move.py` | StockMove._prepare_analytic_lines | odoo | 1 | account_analytic_line |
| `addons/stock_account/models/stock_move.py` | stock.move.account_move_id | orm | 1 | account_move, stock_move |
| `addons/stock_account/models/stock_move.py` | stock.move.analytic_account_line_ids | orm | 1 | account_analytic_line, account_analytic_line_stock_move_rel, stock_move |
| `addons/stock_account/models/stock_move.py` | stock.move.invoice_line_ids | orm | 1 | account_move_line, stock_move |
| `addons/stock_account/models/stock_move.py` | stock.move.product_value_ids | orm | 1 | product_value, stock_move |
| `addons/stock_account/models/stock_move_line.py` | StockMoveLine.write | odoo | 1 | stock_move |

<details><summary>All hot pattern ids</summary>

| id | kind | op | tables | source |
|---|---|---|---|---|
| ap-aa61d73cac | odoo | read | account_account | addons/account/models/account_account.py:408-408 |
| ap-79bddd3503 | odoo | read | account_move_line | addons/account/models/account_account.py:591-594 |
| ap-03abdc46d5 | odoo | read | account_tax, account_tax_repartition_line | addons/account/models/account_account.py:602-605 |
| ap-78b6334b16 | sql | read | account_move_line | addons/account/models/account_account.py:624-633 |
| ap-a76eeaf979 | orm | read | account_analytic_line, product_product | addons/account/models/account_analytic_line.py:12-12 |
| ap-6690e47831 | orm | read | account_analytic_line, account_account | addons/account/models/account_analytic_line.py:19-19 |
| ap-3d515c7c9b | orm | read | account_analytic_line, account_journal | addons/account/models/account_analytic_line.py:27-27 |
| ap-6d454ea2f1 | orm | read | account_analytic_line, account_move_line | addons/account/models/account_analytic_line.py:40-40 |
| ap-790d027ffe | odoo | read | product_product | addons/account/models/account_analytic_plan.py:62-62 |
| ap-49c85bfc09 | odoo | read | account_account | addons/account/models/account_analytic_plan.py:63-63 |
| ap-5b704e249b | orm | read | account_bank_statement, res_company | addons/account/models/account_bank_statement.py:57-57 |
| ap-6f1ef832fb | orm | read | account_bank_statement, res_currency | addons/account/models/account_bank_statement.py:62-62 |
| ap-12b968183b | orm | read | account_bank_statement, account_journal | addons/account/models/account_bank_statement.py:67-67 |
| ap-1f1c61c856 | orm | read | account_bank_statement, account_bank_statement_line | addons/account/models/account_bank_statement.py:73-73 |
| ap-5dcbdefed8 | orm | read | account_bank_statement, account_bank_statement_ir_attachment_rel, ir_attachment | addons/account/models/account_bank_statement.py:104-104 |
| ap-11b4cf154f | odoo | read | account_bank_statement_line, account_move | addons/account/models/account_bank_statement.py:171-176 |
| ap-d1eba15ae4 | odoo | read | account_bank_statement_line, account_move | addons/account/models/account_bank_statement.py:191-191 |
| ap-c24fdd8c80 | odoo | read | account_bank_statement_line, account_move | addons/account/models/account_bank_statement.py:283-288 |
| ap-0b8afe5700 | odoo | read | account_bank_statement | addons/account/models/account_bank_statement.py:309-317 |
| ap-67c225acdb | sql | read | account_bank_statement, res_company, account_journal, res_currency | addons/account/models/account_bank_statement.py:331-353 |
| ap-c024f6e211 | orm | read | account_bank_statement_line, account_move | addons/account/models/account_bank_statement_line.py:24-24 |
| ap-806c4808f5 | orm | read | account_bank_statement_line, account_journal | addons/account/models/account_bank_statement_line.py:30-30 |
| ap-998b89c58b | orm | read | account_bank_statement_line, res_company | addons/account/models/account_bank_statement_line.py:37-37 |
| ap-e1f1071630 | orm | read | account_bank_statement_line, account_bank_statement | addons/account/models/account_bank_statement_line.py:44-44 |
| ap-8fb825a9d1 | orm | read | account_bank_statement_line, account_payment_account_bank_statement_line_rel, account_payment | addons/account/models/account_bank_statement_line.py:51-51 |
| ap-5ce0120f78 | orm | read | account_bank_statement_line, res_partner | addons/account/models/account_bank_statement_line.py:59-59 |
| ap-05dbd25557 | orm | read | account_bank_statement_line, res_currency | addons/account/models/account_bank_statement_line.py:74-74 |
| ap-9adf2edb77 | orm | read | account_bank_statement_line, res_currency | addons/account/models/account_bank_statement_line.py:87-87 |
| ap-6d82125057 | odoo | read | res_company | addons/account/models/account_bank_statement_line.py:190-190 |
| ap-db3acd193b | sql | read | account_bank_statement | addons/account/models/account_bank_statement_line.py:202-210 |
| ap-df503eb9d4 | sql | read | account_bank_statement_line, account_move, account_bank_statement | addons/account/models/account_bank_statement_line.py:224-240 |
| ap-00fe7560b6 | odoo | read | account_bank_statement | addons/account/models/account_bank_statement_line.py:370-370 |
| ap-cd704703b5 | odoo | read | account_journal | addons/account/models/account_bank_statement_line.py:380-380 |
| ap-dfb0238f9f | odoo | write | account_move_line | addons/account/models/account_bank_statement_line.py:410-410 |
| ap-055e70da5e | odoo | read | account_bank_statement_line | addons/account/models/account_bank_statement_line.py:456-456 |
| ap-1ba9155b8a | odoo | read | res_partner_bank | addons/account/models/account_bank_statement_line.py:504-508 |
| ap-53d1ac9cbd | odoo | read | account_account | addons/account/models/account_bank_statement_line.py:517-520 |
| ap-d804e29188 | odoo | read | res_company | addons/account/models/account_bank_statement_line.py:530-530 |
| ap-b29d6312bd | odoo | read | account_journal | addons/account/models/account_bank_statement_line.py:546-549 |
| ap-a1bbff280e | odoo | read | account_bank_statement_line, account_move | addons/account/models/account_bank_statement_line.py:553-559 |
| ap-2faa204cc9 | orm | read | account_move, account_bank_statement_line | addons/account/models/account_bank_statement_line.py:877-877 |
| ap-6c8e652bd0 | orm | read | account_full_reconcile, account_partial_reconcile | addons/account/models/account_full_reconcile.py:11-11 |
| ap-11c8a9ab26 | orm | read | account_full_reconcile, account_move_line | addons/account/models/account_full_reconcile.py:12-12 |
| ap-51a9b57993 | sql | write | account_move_line | addons/account/models/account_full_reconcile.py:30-35 |
| ap-a64e670e35 | sql | write | account_partial_reconcile | addons/account/models/account_full_reconcile.py:39-44 |
| ap-99c1c1874b | odoo | write | account_lock_exception | addons/account/models/account_lock_exception.py:225-225 |
| ap-d073d62fce | orm | read | account_move, account_journal | addons/account/models/account_move.py:170-170 |
| ap-18e967e25a | orm | read | account_move, res_company | addons/account/models/account_move.py:189-189 |
| ap-8569b8030a | orm | read | account_move, account_move_line | addons/account/models/account_move.py:195-195 |
| ap-677571f568 | orm | read | account_move, account_partial_reconcile | addons/account/models/account_move.py:203-203 |
| ap-bd6328e31d | orm | read | account_move, account_payment | addons/account/models/account_move.py:210-210 |
| ap-be33d2c7cd | orm | read | account_move, account_move__account_payment, account_payment | addons/account/models/account_move.py:217-217 |
| ap-cd9c23ce45 | orm | read | account_move, account_bank_statement_line | addons/account/models/account_move.py:233-233 |
| ap-8ec09c9ed6 | orm | read | account_move, adjusting_entries__account_move, account_move | addons/account/models/account_move.py:245-245 |
| ap-48c26ea5f1 | orm | read | account_move, adjusting_entries__account_move, account_move | addons/account/models/account_move.py:257-257 |
| ap-2efecc1ea3 | orm | read | account_move, account_partial_reconcile | addons/account/models/account_move.py:273-273 |
| ap-1df4eed58e | orm | read | account_move, account_move | addons/account/models/account_move.py:278-278 |
| ap-14a2b74e32 | orm | read | account_move, account_move | addons/account/models/account_move.py:285-285 |
| ap-fa0d506c5d | orm | read | account_move, account_move | addons/account/models/account_move.py:313-313 |
| ap-f414c1612f | orm | read | account_move, ir_attachment | addons/account/models/account_move.py:342-342 |
| ap-537f423ff3 | orm | read | account_move, account_move_line | addons/account/models/account_move.py:375-375 |
| ap-aeb0356bf3 | orm | read | account_move, account_payment_term | addons/account/models/account_move.py:415-415 |
| ap-db2e74b8a4 | orm | read | account_move, res_partner | addons/account/models/account_move.py:429-429 |
| ap-76b6b4dbb5 | orm | read | account_move, res_partner | addons/account/models/account_move.py:440-440 |
| ap-4778a9c62c | orm | read | account_move, res_partner | addons/account/models/account_move.py:447-447 |
| ap-4cf19d9787 | orm | read | account_move, res_partner_bank | addons/account/models/account_move.py:454-454 |
| ap-c275f73b6d | orm | read | account_move, account_fiscal_position | addons/account/models/account_move.py:466-466 |
| ap-6da2826b00 | orm | read | account_move, account_payment_method_line | addons/account/models/account_move.py:526-526 |
| ap-f8ee5c0d46 | orm | read | account_move, res_currency | addons/account/models/account_move.py:539-539 |
| ap-eb28d05514 | orm | read | account_move, account_move | addons/account/models/account_move.py:653-653 |
| ap-c8565bca28 | orm | read | account_move, account_move | addons/account/models/account_move.py:661-661 |
| ap-508bdf9bf5 | orm | read | account_move, account_move | addons/account/models/account_move.py:665-665 |
| ap-c8b408e2bd | orm | read | account_move, res_users | addons/account/models/account_move.py:713-713 |
| ap-260ae94861 | orm | read | account_move, ir_attachment | addons/account/models/account_move.py:722-722 |
| ap-76fa4b7db1 | orm | read | account_move, account_incoterms | addons/account/models/account_move.py:735-735 |
| ap-83087f8613 | orm | read | account_move, account_cash_rounding | addons/account/models/account_move.py:750-750 |
| ap-42ff96381c | odoo | read | account_journal | addons/account/models/account_move.py:973-973 |
| ap-ecef275d92 | odoo | read | account_journal | addons/account/models/account_move.py:976-976 |
| ap-42d4d69a48 | odoo | read | res_partner | addons/account/models/account_move.py:1088-1091 |
| ap-933cdf46cd | odoo | read | account_move | addons/account/models/account_move.py:1280-1280 |
| ap-ae23fe7d28 | odoo | read | account_move | addons/account/models/account_move.py:1281-1281 |
| ap-7a016c696d | sql | read | account_partial_reconcile, account_move_line, account_account, account_move, account_payment | addons/account/models/account_move.py:1293-1311 |
| ap-2fe270474e | odoo | read | account_move_line | addons/account/models/account_move.py:1525-1525 |
| ap-dc29093a9b | odoo | read | account_tax | addons/account/models/account_move.py:1733-1733 |
| ap-68b825c31d | odoo | read | account_account | addons/account/models/account_move.py:1742-1742 |
| ap-1c6e5e7db3 | sql | read | account_move | addons/account/models/account_move.py:2218-2235 |
| ap-1e5373733a | odoo | read | account_move | addons/account/models/account_move.py:2242-2242 |
| ap-83fd081220 | odoo | read | account_move | addons/account/models/account_move.py:2242-2242 |
| ap-a83df34c3a | odoo | read | ir_attachment | addons/account/models/account_move.py:2346-2350 |
| ap-ed93e81707 | odoo | read | account_move | addons/account/models/account_move.py:2372-2372 |
| ap-ed2145faeb | sql | read | account_move | addons/account/models/account_move.py:2388-2416 |
| ap-edadd0c846 | sql | read | account_payment, account_move, account_move_line, account_partial_reconcile, account_account | addons/account/models/account_move.py:2509-2530 |
| ap-639e079ac4 | odoo | read | account_payment | addons/account/models/account_move.py:2534-2534 |
| ap-c0330ef9f2 | odoo | read | account_cash_rounding | addons/account/models/account_move.py:2574-2580 |
| ap-a130618f01 | sql | read | account_move_line, account_move, res_company, res_currency | addons/account/models/account_move.py:2954-2965 |
| ap-fd3604363e | odoo | read | account_account | addons/account/models/account_move.py:3200-3203 |
| ap-f788aa0ffb | odoo | write | account_move_line | addons/account/models/account_move.py:3216-3216 |
| ap-d18479bd54 | odoo | write | account_move_line | addons/account/models/account_move.py:3222-3222 |
| ap-9c52d8584f | odoo | write | account_move_line | addons/account/models/account_move.py:3232-3232 |
| ap-3376607a6d | odoo | write | account_move_line | addons/account/models/account_move.py:3243-3243 |
| ap-1b07febd75 | odoo | write | account_move_line | addons/account/models/account_move.py:3303-3303 |
| ap-823648ed19 | odoo | read | account_move | addons/account/models/account_move.py:3337-3337 |
| ap-5a11cc3e22 | odoo | write | account_move_line | addons/account/models/account_move.py:3549-3549 |
| ap-c54e3c32b4 | odoo | read | account_move_line | addons/account/models/account_move.py:3549-3549 |
| ap-bf08b1cc9c | odoo | write | account_move_line | addons/account/models/account_move.py:3551-3551 |
| ap-2a2d7fb3d6 | odoo | read | account_move_line | addons/account/models/account_move.py:3551-3551 |
| ap-de1f1f8612 | odoo | write | account_move_line | addons/account/models/account_move.py:3553-3553 |
| ap-a3e0e72d45 | odoo | write | account_move_line | addons/account/models/account_move.py:3644-3644 |
| ap-2171a25398 | odoo | read | account_move_line | addons/account/models/account_move.py:3644-3644 |
| ap-46a02c58c8 | odoo | write | account_move_line | addons/account/models/account_move.py:3646-3646 |
| ap-07bf01427b | odoo | write | account_move_line | addons/account/models/account_move.py:3648-3648 |
| ap-93bfea849e | odoo | read | account_move_line | addons/account/models/account_move.py:3648-3648 |
| ap-54cf0ffa69 | odoo | read | account_move_line | addons/account/models/account_move.py:3694-3694 |
| ap-df05efd8f7 | odoo | write | account_move_line | addons/account/models/account_move.py:3743-3745 |
| ap-7e9e646f0d | odoo | read | account_move_line | addons/account/models/account_move.py:3743-3743 |
| ap-7bff8befd8 | odoo | write | account_move_line | addons/account/models/account_move.py:3747-3747 |
| ap-6fd3b59f00 | odoo | read | account_move_line | addons/account/models/account_move.py:3747-3747 |
| ap-eb0f38f9ee | odoo | write | account_move_line | addons/account/models/account_move.py:3749-3752 |
| ap-3754a7ca82 | odoo | read | account_move_line | addons/account/models/account_move.py:3780-3780 |
| ap-ee4f15a744 | odoo | read | account_move_line | addons/account/models/account_move.py:3961-3961 |
| ap-84842d6695 | odoo | read | account_move_line | addons/account/models/account_move.py:3963-3963 |
| ap-43b8254383 | odoo | read | account_move | addons/account/models/account_move.py:3985-3985 |
| ap-3c17d7e0e5 | odoo | read | account_move | addons/account/models/account_move.py:4081-4081 |
| ap-63ea2df1a7 | odoo | read | account_move | addons/account/models/account_move.py:4110-4110 |
| ap-d0d582d220 | odoo | read | account_move | addons/account/models/account_move.py:4111-4111 |
| ap-c5efdcc80b | odoo | read | account_move | addons/account/models/account_move.py:4331-4331 |
| ap-a9daf20dfc | odoo | read | account_move | addons/account/models/account_move.py:4333-4333 |
| ap-9db6694b1e | odoo | read | account_move | addons/account/models/account_move.py:4757-4771 |
| ap-94a418de70 | odoo | read | account_move | addons/account/models/account_move.py:4781-4784 |
| ap-a63dfc2975 | odoo | read | account_move | addons/account/models/account_move.py:4798-4798 |
| ap-6cc4d7af4d | odoo | read | account_move | addons/account/models/account_move.py:4799-4799 |
| ap-6dea0f0694 | odoo | read | account_bank_statement_line | addons/account/models/account_move.py:4819-4822 |
| ap-b2d176d8f7 | sql | read | account_move | addons/account/models/account_move.py:4948-4957 |
| ap-6ed250b746 | odoo | write | account_move | addons/account/models/account_move.py:5077-5077 |
| ap-ec2eaad68a | odoo | read | account_tax_repartition_line | addons/account/models/account_move.py:5349-5349 |
| ap-26541a49e3 | sql | read | account_partial_reconcile, account_move_line | addons/account/models/account_move.py:5541-5619 |
| ap-d62ff6e982 | sql | read | account_partial_reconcile, account_move_line | addons/account/models/account_move.py:5627-5705 |
| ap-cf931fd0d8 | odoo | read | account_move_line | addons/account/models/account_move.py:5735-5735 |
| ap-b08e18d8db | odoo | read | res_currency | addons/account/models/account_move.py:5736-5736 |
| ap-743774bdc7 | odoo | write | account_move | addons/account/models/account_move.py:5916-5924 |
| ap-d5861cab48 | odoo | write | account_move_line | addons/account/models/account_move.py:6016-6016 |
| ap-8e3301bf1d | odoo | write | account_partial_reconcile | addons/account/models/account_move.py:6325-6325 |
| ap-8d20d85b6a | odoo | write | account_move | addons/account/models/account_move.py:6327-6330 |
| ap-aea7b579c2 | odoo | read | account_move | addons/account/models/account_move.py:6420-6420 |
| ap-204199cf95 | odoo | read | account_move | addons/account/models/account_move.py:6449-6449 |
| ap-883de01e1e | sql | read | account_move | addons/account/models/account_move.py:6457-6482 |
| ap-2e74224ea5 | odoo | read | account_move | addons/account/models/account_move.py:6496-6496 |
| ap-c93f6dba26 | odoo | read | account_move | addons/account/models/account_move.py:6501-6501 |
| ap-97193cebd7 | odoo | write | validate_account_move | addons/account/models/account_move.py:6827-6829 |
| ap-3bb73e6f77 | odoo | write | account_partial_reconcile | addons/account/models/account_move.py:6907-6910 |
| ap-ccf6ea8fbc | odoo | read | account_partial_reconcile, account_move_line | addons/account/models/account_move.py:6907-6910 |
| ap-224d19f8d8 | odoo | read | ir_attachment | addons/account/models/account_move.py:6994-6998 |
| ap-aa37b28f6d | sql | read | account_move | addons/account/models/account_move.py:7023-7036 |
| ap-b56056ede6 | odoo | write | account_move | addons/account/models/account_move.py:7039-7039 |
| ap-f2abb1beec | odoo | read | account_move | addons/account/models/account_move.py:7039-7039 |
| ap-e1c0386030 | odoo | read | account_move | addons/account/models/account_move.py:7191-7191 |
| ap-a62f664084 | odoo | read | account_move | addons/account/models/account_move.py:7192-7192 |
| ap-53aebe940a | odoo | read | account_journal | addons/account/models/account_move.py:7270-7273 |
| ap-340c3dd035 | odoo | read | res_partner | addons/account/models/account_move.py:7533-7533 |
| ap-c7b6cb0b16 | odoo | read | account_account | addons/account/models/account_move.py:7534-7534 |
| ap-fce63c688a | odoo | read | account_journal | addons/account/models/account_move.py:7776-7780 |
| ap-fc7d46c138 | odoo | read | account_bank_statement_line | addons/account/models/account_move.py:7797-7800 |
| ap-23443cb9d4 | odoo | write | account_bank_statement | addons/account/models/account_move.py:7822-7835 |
| ap-d7dd31e20a | odoo | read | res_company | addons/account/models/account_move.py:7926-7926 |
| ap-700f579275 | odoo | write | account_move | addons/account/models/account_move.py:8036-8036 |
| ap-a22653c9c3 | orm | read | account_move_line, account_move | addons/account/models/account_move_line.py:42-42 |
| ap-fb06c549ac | orm | read | account_move_line, account_account | addons/account/models/account_move_line.py:104-104 |
| ap-4921ee56b8 | orm | read | account_move_line, account_account | addons/account/models/account_move_line.py:119-119 |
| ap-2274871a1b | orm | read | account_move_line, res_currency | addons/account/models/account_move_line.py:177-177 |
| ap-631129f889 | orm | read | account_move_line, res_partner | addons/account/models/account_move_line.py:184-184 |
| ap-df130193c6 | orm | read | account_move_line, account_reconcile_model | addons/account/models/account_move_line.py:193-193 |
| ap-b0c97b5375 | orm | read | account_move_line, account_payment | addons/account/models/account_move_line.py:200-200 |
| ap-e6d7f50564 | orm | read | account_move_line, account_bank_statement_line | addons/account/models/account_move_line.py:207-207 |
| ap-4125f28dcc | orm | read | account_move_line, account_move_line_account_tax_rel, account_tax | addons/account/models/account_move_line.py:226-226 |
| ap-82c87f2050 | orm | read | account_move_line, account_tax | addons/account/models/account_move_line.py:237-237 |
| ap-b024dbedf5 | orm | read | account_move_line, account_tax | addons/account/models/account_move_line.py:243-243 |
| ap-d82ab1eb3c | orm | read | account_move_line, account_tax_repartition_line | addons/account/models/account_move_line.py:259-259 |
| ap-01e0cb8e17 | orm | read | account_move_line, account_account_tag_account_move_line_rel, account_account_tag | addons/account/models/account_move_line.py:267-267 |
| ap-1f42f55124 | orm | read | account_move_line, account_full_reconcile | addons/account/models/account_move_line.py:293-293 |
| ap-6e13815921 | orm | read | account_move_line, account_partial_reconcile | addons/account/models/account_move_line.py:300-300 |
| ap-740d8839f7 | orm | read | account_move_line, account_partial_reconcile | addons/account/models/account_move_line.py:306-306 |
| ap-9bcd3a4102 | orm | read | account_move_line, product_product | addons/account/models/account_move_line.py:420-420 |
| ap-4450e2bc30 | orm | read | account_move_line, uom_uom | addons/account/models/account_move_line.py:429-429 |
| ap-b0e429bff2 | orm | read | account_move_line, account_move_line | addons/account/models/account_move_line.py:443-443 |
| ap-475de06500 | orm | read | account_move_line, account_analytic_line | addons/account/models/account_move_line.py:498-498 |
| ap-a544c22975 | sql | read | account_move_line, account_account, account_account_res_company_rel | addons/account/models/account_move_line.py:729-757 |
| ap-d57b9d3cf7 | odoo | read | account_account | addons/account/models/account_move_line.py:777-777 |
| ap-af6165f1a0 | odoo | read | account_move_line | addons/account/models/account_move_line.py:851-851 |
| ap-5b0177d13f | odoo | read | account_account | addons/account/models/account_move_line.py:1047-1047 |
| ap-db7bc90c0f | odoo | read | account_move_line | addons/account/models/account_move_line.py:1061-1077 |
| ap-8eda2da30f | sql | read | account_partial_reconcile, res_currency | addons/account/models/account_move_line.py:1176-1196 |
| ap-67a731b85d | odoo | read | account_analytic_account | addons/account/models/account_move_line.py:1605-1607 |
| ap-0f3613f52d | odoo | read | account_move_line | addons/account/models/account_move_line.py:1694-1694 |
| ap-29ea2d7f28 | odoo | read | account_move_line | addons/account/models/account_move_line.py:1799-1801 |
| ap-bd2b5ba705 | sql | read | account_move_line | addons/account/models/account_move_line.py:1803-1803 |
| ap-239d5deac9 | odoo | write | account_analytic_line | addons/account/models/account_move_line.py:1811-1811 |
| ap-7886f22a96 | odoo | read | account_move | addons/account/models/account_move_line.py:2003-2003 |
| ap-be5ba06236 | odoo | read | account_move | addons/account/models/account_move_line.py:2014-2014 |
| ap-1eb4d2004b | odoo | read | account_move | addons/account/models/account_move_line.py:2154-2154 |
| ap-44204ef231 | odoo | read | account_move_line | addons/account/models/account_move_line.py:2172-2172 |
| ap-e52784e3d9 | odoo | read | account_account | addons/account/models/account_move_line.py:2190-2190 |
| ap-8af43ac11f | odoo | read | account_move_line | addons/account/models/account_move_line.py:2257-2257 |
| ap-f040d9b5bf | odoo | read | account_move_line | addons/account/models/account_move_line.py:2281-2281 |
| ap-a155c4c5df | odoo | write | account_analytic_line | addons/account/models/account_move_line.py:2284-2284 |
| ap-449aabccc2 | odoo | read | account_move_line | addons/account/models/account_move_line.py:3070-3070 |
| ap-49c405e77f | odoo | read | account_move_line | addons/account/models/account_move_line.py:3097-3097 |
| ap-45a73fe337 | odoo | write | account_partial_reconcile | addons/account/models/account_move_line.py:3187-3187 |
| ap-a687be7c07 | odoo | read | account_move_line | addons/account/models/account_move_line.py:3269-3269 |
| ap-eff4d2bd2b | odoo | write | account_full_reconcile | addons/account/models/account_move_line.py:3289-3289 |
| ap-e521ec78cf | odoo | read | account_journal | addons/account/models/account_move_line.py:3444-3444 |
| ap-5941b4afef | odoo | write | account_move | addons/account/models/account_move_line.py:3458-3458 |
| ap-7e7dc57f40 | odoo | read | account_move_line | addons/account/models/account_move_line.py:3499-3503 |
| ap-8f35551ff3 | odoo | write | account_analytic_line | addons/account/models/account_move_line.py:3559-3559 |
| ap-4db45d18f3 | odoo | read | account_analytic_account | addons/account/models/account_move_line.py:3584-3584 |
| ap-a4eab69b69 | odoo | read | account_move_line | addons/account/models/account_move_line.py:3741-3745 |
| ap-f342e768f9 | odoo | read | account_move_line | addons/account/models/account_move_line.py:3756-3756 |
| ap-88ec676b2a | sql | read | account_tax_filiation_rel, account_tax, account_tax_repartition_line, account_move_line_account_tax_rel, account_move, res_currency | addons/account/models/account_move_line_tax_details.py:49-218 |
| ap-f2058228b6 | orm | read | account_partial_reconcile, account_move_line | addons/account/models/account_partial_reconcile.py:17-17 |
| ap-cd15324270 | orm | read | account_partial_reconcile, account_move_line | addons/account/models/account_partial_reconcile.py:20-20 |
| ap-10ed5363ce | orm | read | account_partial_reconcile, account_full_reconcile | addons/account/models/account_partial_reconcile.py:23-23 |
| ap-851f8a1049 | orm | read | account_partial_reconcile, account_move | addons/account/models/account_partial_reconcile.py:26-26 |
| ap-d120374dc0 | orm | read | account_partial_reconcile, res_currency | addons/account/models/account_partial_reconcile.py:38-38 |
| ap-d61f122a7b | orm | read | account_partial_reconcile, res_currency | addons/account/models/account_partial_reconcile.py:43-43 |
| ap-ea7a788fb8 | orm | read | account_partial_reconcile, res_company | addons/account/models/account_partial_reconcile.py:61-61 |
| ap-4c17725b5c | sql | write | account_move_line | addons/account/models/account_partial_reconcile.py:226-234 |
| ap-49f69263e7 | odoo | read | account_move_line | addons/account/models/account_partial_reconcile.py:235-235 |
| ap-6ce33d35f9 | odoo | read | account_tax | addons/account/models/account_partial_reconcile.py:470-470 |
| ap-da98fe2404 | odoo | read | account_tax | addons/account/models/account_partial_reconcile.py:501-501 |
| ap-8dd54614e8 | orm | read | account_payment, account_move | addons/account/models/account_payment.py:18-18 |
| ap-31126a5fbf | orm | read | account_payment, account_journal | addons/account/models/account_payment.py:24-24 |
| ap-00be8b8853 | orm | read | account_payment, res_company | addons/account/models/account_payment.py:31-31 |
| ap-b9c0406856 | orm | read | account_payment, res_partner_bank | addons/account/models/account_payment.py:64-64 |
| ap-7542b4445e | orm | read | account_payment, res_partner_bank | addons/account/models/account_payment.py:71-71 |
| ap-9cc0fe971f | orm | read | account_payment, account_payment | addons/account/models/account_payment.py:82-82 |
| ap-cb36f5476c | orm | read | account_payment, account_payment_method_line | addons/account/models/account_payment.py:96-96 |
| ap-c6f4cc30c3 | orm | read | account_payment, res_currency | addons/account/models/account_payment.py:133-133 |
| ap-8e42f873a9 | orm | read | account_payment, res_partner | addons/account/models/account_payment.py:139-139 |
| ap-4c4c6c5dc6 | orm | read | account_payment, res_partner | addons/account/models/account_payment.py:145-145 |
| ap-82e8b76a2d | orm | read | account_payment, account_account | addons/account/models/account_payment.py:155-155 |
| ap-4718bbc6e1 | orm | read | account_payment, account_account | addons/account/models/account_payment.py:164-164 |
| ap-89702f81ce | orm | read | account_payment, account_move__account_payment, account_move | addons/account/models/account_payment.py:174-174 |
| ap-787a60ae3b | orm | read | account_payment, ir_attachment | addons/account/models/account_payment.py:233-233 |
| ap-97596faca8 | odoo | read | account_journal | addons/account/models/account_payment.py:484-487 |
| ap-c0ea4eb79e | odoo | read | account_journal | addons/account/models/account_payment.py:664-669 |
| ap-6ad40487ae | odoo | read | account_account | addons/account/models/account_payment.py:700-703 |
| ap-f44302c9b4 | odoo | read | account_account | addons/account/models/account_payment.py:709-712 |
| ap-a4c6850d29 | sql | read | account_payment, account_move, account_move_line, account_partial_reconcile, account_account | addons/account/models/account_payment.py:761-784 |
| ap-77330a4eff | odoo | read | account_payment | addons/account/models/account_payment.py:794-794 |
| ap-ddf30a7edf | odoo | read | account_move | addons/account/models/account_payment.py:796-796 |
| ap-2d64a5635f | odoo | read | account_move | addons/account/models/account_payment.py:798-798 |
| ap-49ad6ad0c7 | sql | read | account_payment, account_move, account_move_line, account_account, account_partial_reconcile | addons/account/models/account_payment.py:804-825 |
| ap-951168c9cc | sql | read | account_payment | addons/account/models/account_payment.py:901-914 |
| ap-563e98b2db | odoo | read | account_payment | addons/account/models/account_payment.py:921-921 |
| ap-6a368aeacc | orm | read | account_move, account_payment | addons/account/models/account_payment.py:1330-1330 |
| ap-c03b41e616 | odoo | read | account_account_tag | addons/account/models/account_report.py:1004-1004 |
| ap-a9b6ff729a | odoo | read | account_tax_group | addons/account/models/account_tax.py:288-291 |
| ap-2fc9856c38 | odoo | read | account_tax_group | addons/account/models/account_tax.py:291-294 |
| ap-aa39982607 | odoo | read | account_tax | addons/account/models/account_tax.py:420-420 |
| ap-c89342efe2 | odoo | read | account_tax_group | addons/account/models/account_tax.py:3017-3017 |
| ap-1b7fa09d61 | odoo | read | res_currency | addons/account/models/account_tax.py:3152-3152 |
| ap-6fbef4e734 | odoo | read | account_lock_exception | addons/account/models/company.py:764-775 |
| ap-fe1cc326bc | odoo | read | mail_message | addons/account/models/mail_message.py:105-105 |
| ap-8bf1cbdf9f | odoo | read | account_tax | addons/account/models/partner.py:96-96 |
| ap-94cb591b8b | sql | read | account_account | addons/account/models/partner.py:404-413 |
| ap-37c4d3ca8f | odoo | read | res_partner | addons/account/models/partner.py:418-418 |
| ap-f0c865d48f | odoo | read | res_partner | addons/account/models/partner.py:420-420 |
| ap-6035eebd4c | sql | read | account_move, res_partner, res_company, res_currency_rate | addons/account/models/partner.py:480-501 |
| ap-5bfeb939a1 | odoo | read | account_move | addons/account/models/partner.py:517-526 |
| ap-d0f11a73a9 | odoo | read | account_move | addons/account/models/partner.py:788-797 |
| ap-c7c8cf1018 | odoo | read | res_partner | addons/account/models/partner.py:916-917 |
| ap-d86b9d1419 | odoo | read | account_move_line | addons/account/models/res_currency.py:42-42 |
| ap-a631d88c65 | sql | read | res_company | addons/account/models/res_currency.py:52-62 |
| ap-c9120ba8bd | sql | read | res_partner_bank | addons/account/models/res_partner_bank.py:73-89 |
| ap-223e4d7a51 | odoo | read | res_partner | addons/account/models/res_partner_bank.py:95-95 |
| ap-2948c5ff4f | odoo | read | account_move | addons/account_edi_ubl_cii/models/account_move.py:200-206 |
| ap-ad74c5fa25 | odoo | read | product_template_attribute_value | addons/product/models/product_attribute_value.py:84-87 |
| ap-835a985a2b | odoo | read | product_product | addons/product/models/product_document.py:37-37 |
| ap-02f15f126e | odoo | read | product_pricelist | addons/product/models/product_pricelist.py:364-364 |
| ap-e0ff6aa544 | odoo | read | res_partner | addons/product/models/product_pricelist.py:444-444 |
| ap-a1d432fcbb | odoo | read | res_partner | addons/product/models/product_pricelist.py:452-452 |
| ap-6d30561534 | odoo | read | product_pricelist_item | addons/product/models/product_pricelist.py:514-514 |
| ap-8d251368b5 | odoo | read | product_pricelist_item | addons/product/models/product_pricelist_item.py:671-671 |
| ap-a9c3365cdf | odoo | read | res_partner | addons/product/models/product_product.py:1038-1038 |
| ap-09c47bf055 | odoo | read | product_supplierinfo | addons/product/models/product_product.py:1051-1054 |
| ap-ad4c0ff60e | odoo | read | product_supplierinfo | addons/product/models/product_product.py:1063-1063 |
| ap-a01c9c81f8 | odoo | read | product_product | addons/product/models/product_template.py:497-497 |
| ap-f1a0c81054 | odoo | read | product_product | addons/product/models/product_template.py:1467-1467 |
| ap-c00a67babe | odoo | read | product_product | addons/product/models/product_template.py:1544-1544 |
| ap-67c5e14f01 | odoo | read | purchase_order | addons/purchase/models/account_invoice.py:509-510 |
| ap-fdeff92149 | odoo | read | purchase_order | addons/purchase/models/account_invoice.py:515-516 |
| ap-72bf676b4d | odoo | read | purchase_order | addons/purchase/models/account_invoice.py:568-568 |
| ap-afbb82d651 | orm | read | account_move_line, purchase_order_line | addons/purchase/models/account_invoice.py:662-662 |
| ap-9aacde08f2 | odoo | read | purchase_order_line, product_product, purchase_order | addons/purchase/models/product.py:64-70 |
| ap-3909ae44ab | odoo | read | purchase_order_line, purchase_order | addons/purchase/models/product.py:91-91 |
| ap-f9ff65cd75 | odoo | read | purchase_order_line | addons/purchase/models/product.py:117-117 |
| ap-679716d679 | odoo | read | purchase_order_line | addons/purchase/models/product.py:127-131 |
| ap-6256822170 | odoo | read | purchase_order_line, purchase_order | addons/purchase/models/product.py:196-202 |
| ap-d66e054f0a | sql | read | purchase_order_line, purchase_order | addons/purchase/models/purchase_bill_line_match.py:98-124 |
| ap-1aa74fe987 | sql | read | account_move_line, account_move | addons/purchase/models/purchase_bill_line_match.py:128-154 |
| ap-b40fff4f8f | odoo | write | account_move | addons/purchase/models/purchase_bill_line_match.py:178-182 |
| ap-2c782191fc | orm | read | purchase_order, res_partner | addons/purchase/models/purchase_order.py:94-94 |
| ap-16252200d7 | orm | read | purchase_order, res_currency | addons/purchase/models/purchase_order.py:101-101 |
| ap-f39ad8cae1 | orm | read | purchase_order, purchase_order_line | addons/purchase/models/purchase_order.py:121-121 |
| ap-d802e51a76 | orm | read | purchase_order, account_move_purchase_order_rel, account_move | addons/purchase/models/purchase_order.py:130-130 |
| ap-8535eb79c5 | orm | read | purchase_order, account_fiscal_position | addons/purchase/models/purchase_order.py:147-147 |
| ap-dc16c66ebb | orm | read | purchase_order, account_payment_term | addons/purchase/models/purchase_order.py:168-168 |
| ap-f718e5f811 | orm | read | purchase_order, account_incoterms | addons/purchase/models/purchase_order.py:169-169 |
| ap-c0eb0675ea | orm | read | purchase_order, res_users | addons/purchase/models/purchase_order.py:174-174 |
| ap-d985ab90dc | orm | read | purchase_order, res_company | addons/purchase/models/purchase_order.py:177-177 |
| ap-c7ed2ebc41 | sql | read | purchase_order | addons/purchase/models/purchase_order.py:401-417 |
| ap-9e16f9aeda | odoo | read | purchase_order | addons/purchase/models/purchase_order.py:456-456 |
| ap-006cfdf34d | odoo | write | purchase_order_line | addons/purchase/models/purchase_order.py:803-803 |
| ap-dfcac37551 | odoo | write | purchase_order_line | addons/purchase/models/purchase_order.py:813-813 |
| ap-d4e4e0d265 | odoo | read | purchase_order | addons/purchase/models/purchase_order.py:1194-1199 |
| ap-644c46ed72 | odoo | read | ir_attachment | addons/purchase/models/purchase_order.py:1428-1428 |
| ap-98d45243ee | orm | read | purchase_order_line, account_tax_purchase_order_line_rel, account_tax | addons/purchase/models/purchase_order_line.py:39-39 |
| ap-fe36f32789 | orm | read | purchase_order_line, uom_uom | addons/purchase/models/purchase_order_line.py:49-49 |
| ap-33fdb29d0a | orm | read | purchase_order_line, product_product | addons/purchase/models/purchase_order_line.py:50-50 |
| ap-23cd668997 | orm | read | purchase_order_line, purchase_order | addons/purchase/models/purchase_order_line.py:66-66 |
| ap-bfaa3c95dd | orm | read | purchase_order_line, res_company | addons/purchase/models/purchase_order_line.py:68-68 |
| ap-4f2ea0774d | orm | read | purchase_order_line, account_move_line | addons/purchase/models/purchase_order_line.py:71-71 |
| ap-4827514c12 | orm | read | purchase_order_line, purchase_order_line_accrual_move_rel, account_move | addons/purchase/models/purchase_order_line.py:102-102 |
| ap-7dec3023a1 | orm | read | purchase_order_line, res_partner | addons/purchase/models/purchase_order_line.py:118-118 |
| ap-6c0398e62c | orm | read | purchase_order_line, product_template_attribute_value_purchase_order_line_rel, product_template_attribute_value | addons/purchase/models/purchase_order_line.py:141-141 |
| ap-855eb392d6 | odoo | read | purchase_order_line | addons/purchase/models/purchase_order_line.py:403-403 |
| ap-8e704493a3 | odoo | read | res_partner | addons/purchase_stock/models/product.py:77-77 |
| ap-5f784ad29a | odoo | read | purchase_order | addons/purchase_stock/models/product.py:78-78 |
| ap-17914bce37 | odoo | read | stock_move | addons/purchase_stock/models/product.py:123-123 |
| ap-2fc7ac0f1d | odoo | read | purchase_order_line | addons/purchase_stock/models/product.py:172-174 |
| ap-67759b268f | odoo | read | purchase_order, purchase_order_line | addons/purchase_stock/models/product.py:265-270 |
| ap-b5c9285e29 | orm | read | purchase_order, purchase_order_stock_picking_rel, stock_picking | addons/purchase_stock/models/purchase_order.py:21-21 |
| ap-f7ea5162eb | orm | read | purchase_order, res_partner | addons/purchase_stock/models/purchase_order.py:22-22 |
| ap-5da1679386 | orm | read | purchase_order, stock_picking_type | addons/purchase_stock/models/purchase_order.py:23-23 |
| ap-bed9a1ffe6 | orm | read | purchase_order, stock_reference_purchase_rel, stock_reference | addons/purchase_stock/models/purchase_order.py:27-27 |
| ap-6dfc35d977 | odoo | read | purchase_order_line | addons/purchase_stock/models/purchase_order.py:335-335 |
| ap-1b95fd0fff | odoo | read | stock_picking_type, stock_warehouse | addons/purchase_stock/models/purchase_order.py:379-379 |
| ap-4f56bc8486 | odoo | read | stock_picking_type | addons/purchase_stock/models/purchase_order.py:381-381 |
| ap-a74a27465e | odoo | read | stock_picking_type | addons/purchase_stock/models/purchase_order.py:383-383 |
| ap-4cf9f1fd3d | orm | read | purchase_order_line, stock_move | addons/purchase_stock/models/purchase_order_line.py:30-30 |
| ap-4e78b5b8b4 | orm | read | purchase_order_line, stock_warehouse_orderpoint | addons/purchase_stock/models/purchase_order_line.py:31-31 |
| ap-72ab1e8d34 | orm | read | purchase_order_line, stock_move_created_purchase_line_rel, stock_move | addons/purchase_stock/models/purchase_order_line.py:32-32 |
| ap-6c821e6d70 | orm | read | purchase_order_line, stock_location | addons/purchase_stock/models/purchase_order_line.py:37-37 |
| ap-f45ae3fe58 | odoo | write | stock_reference | addons/purchase_stock/models/purchase_order_line.py:319-319 |
| ap-6d7b168ebc | odoo | read | stock_location | addons/purchase_stock/models/purchase_order_line.py:322-322 |
| ap-d1d2b678c0 | odoo | write | stock_move | addons/purchase_stock/models/purchase_order_line.py:417-417 |
| ap-07ec3e816d | odoo | read | purchase_order_line, purchase_order | addons/purchase_stock/models/res_partner.py:43-50 |
| ap-aaa5c9c9a1 | odoo | read | stock_move | addons/purchase_stock/models/res_partner.py:52-54 |
| ap-4be103ad4a | odoo | read | purchase_order_line | addons/purchase_stock/models/res_partner.py:56-56 |
| ap-ce890f071b | odoo | read | stock_move | addons/purchase_stock/models/res_partner.py:57-57 |
| ap-2b61bcd114 | odoo | read | product_product | addons/purchase_stock/models/res_partner.py:101-101 |
| ap-142644d2e4 | orm | read | stock_warehouse_orderpoint, product_supplierinfo | addons/purchase_stock/models/stock.py:159-159 |
| ap-ba0e05969d | odoo | read | stock_rule | addons/purchase_stock/models/stock.py:197-197 |
| ap-14c0987cb2 | odoo | read | stock_move_line | addons/purchase_stock/models/stock.py:373-373 |
| ap-9df040bd32 | orm | read | stock_move, purchase_order_line | addons/purchase_stock/models/stock_move.py:13-13 |
| ap-a698ff795a | orm | read | stock_move, stock_move_created_purchase_line_rel, purchase_order_line | addons/purchase_stock/models/stock_move.py:16-16 |
| ap-7a88a2c50b | odoo | write | purchase_order_line | addons/purchase_stock/models/stock_move.py:107-107 |
| ap-cb8f8071e2 | odoo | read | account_move_line | addons/purchase_stock/models/stock_move.py:234-234 |
| ap-d6d37839f0 | odoo | read | stock_warehouse | addons/purchase_stock/models/stock_rule.py:53-53 |
| ap-2e0a3380ba | odoo | read | purchase_order | addons/purchase_stock/models/stock_rule.py:100-100 |
| ap-9b540be124 | odoo | write | purchase_order | addons/purchase_stock/models/stock_rule.py:114-114 |
| ap-979d20edbf | odoo | write | purchase_order | addons/purchase_stock/models/stock_rule.py:124-124 |
| ap-7921fc9f3e | odoo | write | purchase_order | addons/purchase_stock/models/stock_rule.py:126-126 |
| ap-c8c273f41c | odoo | write | purchase_order_line | addons/purchase_stock/models/stock_rule.py:163-163 |
| ap-fdfbc6663f | orm | read | account_analytic_line, account_move | addons/sale/models/account_analytic_line.py:11-11 |
| ap-01a846fa62 | orm | read | account_analytic_line, sale_order_line | addons/sale/models/account_analytic_line.py:19-19 |
| ap-1dd4989e61 | orm | read | account_analytic_line, sale_order | addons/sale/models/account_analytic_line.py:29-29 |
| ap-f0bdd20bd0 | odoo | read | account_analytic_plan | addons/sale/models/account_analytic_line.py:245-247 |
| ap-f9fbb76aa9 | orm | read | account_move, crm_team | addons/sale/models/account_move.py:11-11 |
| ap-48197f0a6a | odoo | read | account_analytic_line | addons/sale/models/account_move.py:296-299 |
| ap-7445ec9313 | orm | read | account_move_line, sale_order_line_invoice_rel, sale_order_line | addons/sale/models/account_move_line.py:12-12 |
| ap-2c6738953b | odoo | read | sale_order_line | addons/sale/models/account_move_line.py:169-177 |
| ap-219d3d75dd | odoo | write | sale_order_line | addons/sale/models/account_move_line.py:206-206 |
| ap-733cb83598 | odoo | read | sale_order_line | addons/sale/models/account_move_line.py:230-232 |
| ap-ed4ff849d8 | odoo | read | account_move_line | addons/sale/models/account_move_line.py:307-307 |
| ap-3f1c69a45d | odoo | read | account_journal | addons/sale/models/payment_transaction.py:37-39 |
| ap-809799fea1 | odoo | read | payment_transaction | addons/sale/models/payment_transaction.py:254-254 |
| ap-63fbe48895 | odoo | read | sale_order | addons/sale/models/payment_transaction.py:255-255 |
| ap-2dd0228bc2 | odoo | read | sale_order_line | addons/sale/models/product_product.py:62-62 |
| ap-25d437007c | odoo | read | sale_order_line | addons/sale/models/product_product.py:74-78 |
| ap-1f46e682a6 | odoo | read | sale_order | addons/sale/models/res_partner.py:72-75 |
| ap-74ba152ac5 | odoo | read | sale_order | addons/sale/models/res_partner.py:102-115 |
| ap-0ce76669f5 | orm | read | sale_order, res_company | addons/sale/models/sale_order.py:73-73 |
| ap-a9a72f8664 | orm | read | sale_order, res_partner | addons/sale/models/sale_order.py:76-76 |
| ap-9cfc83e371 | orm | read | sale_order, mail_template | addons/sale/models/sale_order.py:131-131 |
| ap-7fb2274f5f | orm | read | sale_order, account_journal | addons/sale/models/sale_order.py:179-179 |
| ap-94e28b9892 | orm | read | sale_order, res_partner | addons/sale/models/sale_order.py:210-210 |
| ap-3b5452bb93 | orm | read | sale_order, res_partner | addons/sale/models/sale_order.py:221-221 |
| ap-e85f9278c2 | orm | read | sale_order, account_fiscal_position | addons/sale/models/sale_order.py:233-233 |
| ap-4ef3dc1eed | orm | read | sale_order, account_payment_term | addons/sale/models/sale_order.py:244-244 |
| ap-152d7bea23 | orm | read | sale_order, account_payment_method_line | addons/sale/models/sale_order.py:254-254 |
| ap-0595b8aab2 | orm | read | sale_order, product_pricelist | addons/sale/models/sale_order.py:264-264 |
| ap-f8b4b59ef9 | orm | read | sale_order, res_currency | addons/sale/models/sale_order.py:277-277 |
| ap-e9ad917c5b | orm | read | sale_order, res_users | addons/sale/models/sale_order.py:291-291 |
| ap-5488e096ec | orm | read | sale_order, crm_team | addons/sale/models/sale_order.py:306-306 |
| ap-715fb44fc8 | orm | read | sale_order, account_incoterms | addons/sale/models/sale_order.py:320-320 |
| ap-8c623bead4 | orm | read | sale_order, sale_order_line | addons/sale/models/sale_order.py:339-339 |
| ap-fa9cad8cb5 | orm | read | sale_order, sale_order_transaction_rel, payment_transaction | addons/sale/models/sale_order.py:383-383 |
| ap-4cba00f058 | orm | read | sale_order, account_analytic_account | addons/sale/models/sale_order.py:493-493 |
| ap-61a99239cd | odoo | read | sale_order_line | addons/sale/models/sale_order.py:885-888 |
| ap-9a70dc2092 | sql | read | sale_order | addons/sale/models/sale_order.py:1062-1077 |
| ap-b00706269a | odoo | read | mail_template | addons/sale/models/sale_order.py:1603-1603 |
| ap-b920e9be6d | odoo | write | sale_order | addons/sale/models/sale_order.py:1800-1800 |
| ap-9ee3d3fad2 | odoo | read | sale_order_line | addons/sale/models/sale_order.py:2013-2013 |
| ap-ddfed5b353 | odoo | read | account_move | addons/sale/models/sale_order.py:2023-2023 |
| ap-6dc7b1aa3b | odoo | write | account_move | addons/sale/models/sale_order.py:2027-2027 |
| ap-1198cf57cd | odoo | read | ir_attachment | addons/sale/models/sale_order.py:2371-2371 |
| ap-30fe2cdd3d | odoo | write | sale_order_line | addons/sale/models/sale_order.py:2551-2560 |
| ap-2a858961c8 | odoo | write | sale_order_line | addons/sale/models/sale_order.py:2576-2579 |
| ap-17f5d29b39 | odoo | write | account_analytic_account | addons/sale/models/sale_order.py:2676-2678 |
| ap-cf7adcda60 | odoo | read | sale_order_line | addons/sale/models/sale_order.py:2820-2821 |
| ap-9269702715 | orm | read | sale_order_line, sale_order | addons/sale/models/sale_order_line.py:42-42 |
| ap-9f57896b13 | orm | read | sale_order_line, product_product | addons/sale/models/sale_order_line.py:98-98 |
| ap-501963510f | orm | read | sale_order_line, product_attribute_custom_value | addons/sale/models/sale_order_line.py:124-124 |
| ap-579fad14ad | orm | read | sale_order_line, product_template_attribute_value_sale_order_line_rel, product_template_attribute_value | addons/sale/models/sale_order_line.py:137-137 |
| ap-4368efbeb3 | orm | read | sale_order_line, uom_uom | addons/sale/models/sale_order_line.py:163-163 |
| ap-12a7901415 | orm | read | sale_order_line, sale_order_line | addons/sale/models/sale_order_line.py:179-179 |
| ap-b055f1ae04 | orm | read | sale_order_line, sale_order_line | addons/sale/models/sale_order_line.py:187-187 |
| ap-e7eca60a63 | orm | read | sale_order_line, product_combo_item | addons/sale/models/sale_order_line.py:199-199 |
| ap-2610191490 | orm | read | sale_order_line, account_tax_sale_order_line_rel, account_tax | addons/sale/models/sale_order_line.py:202-202 |
| ap-8b7567057e | orm | read | sale_order_line, account_analytic_line | addons/sale/models/sale_order_line.py:324-324 |
| ap-aadcf0fad7 | orm | read | sale_order_line, sale_order_line_invoice_rel, account_move_line | addons/sale/models/sale_order_line.py:328-328 |
| ap-bd6f06c82f | orm | read | sale_order_line, sale_order_line_accrual_move_rel, account_move | addons/sale/models/sale_order_line.py:367-367 |
| ap-0479d8d8ff | orm | read | sale_order_line, uom_uom | addons/sale/models/sale_order_line.py:435-435 |
| ap-bcfdabc4e0 | odoo | read | account_analytic_line | addons/sale/models/sale_order_line.py:1220-1224 |
| ap-6425e63a06 | odoo | read | sale_order_line | addons/sale/models/sale_order_line.py:1642-1642 |
| ap-df4935887a | sql | read | account_move_line, account_move, res_currency_rate | addons/sale/models/utm_campaign.py:57-78 |
| ap-3c99c9aaf8 | odoo | read | utm_campaign | addons/sale/models/utm_campaign.py:86-86 |
| ap-98863b7997 | odoo | read | utm_campaign | addons/sale/models/utm_campaign.py:88-88 |
| ap-23771f574a | odoo | write | customer_product_reference | addons/sale_edi_ubl/models/customer_product_reference.py:43-47 |
| ap-c727cbe64e | orm | read | purchase_order_line, sale_order_line | addons/sale_purchase/models/purchase_order.py:93-93 |
| ap-a08fa60429 | odoo | read | purchase_order_line, product_product, product_template | addons/sale_purchase/models/sale_order.py:63-68 |
| ap-6729ae4f94 | orm | read | sale_order_line, purchase_order_line | addons/sale_purchase/models/sale_order_line.py:15-15 |
| ap-0ac575ad00 | odoo | read | purchase_order_line | addons/sale_purchase/models/sale_order_line.py:82-82 |
| ap-ab6f68356c | odoo | read | purchase_order_line | addons/sale_purchase/models/sale_order_line.py:106-106 |
| ap-611ece6f56 | odoo | write | purchase_order_line | addons/sale_purchase/models/sale_order_line.py:109-109 |
| ap-2424d2d0e9 | odoo | read | purchase_order_line | addons/sale_purchase/models/sale_order_line.py:225-236 |
| ap-89e8582012 | odoo | write | purchase_order | addons/sale_purchase/models/sale_order_line.py:240-240 |
| ap-e924e22779 | odoo | write | purchase_order_line | addons/sale_purchase/models/sale_order_line.py:280-280 |
| ap-9d6d6b2a1a | odoo | read | stock_location | addons/sale_purchase_stock/models/purchase_order.py:25-25 |
| ap-2fa91180e2 | odoo | read | sale_order_line | addons/sale_purchase_stock/models/purchase_order.py:65-65 |
| ap-7ad164ebf1 | orm | read | sale_order, stock_warehouse | addons/sale_stock/models/sale_order.py:23-23 |
| ap-2b0c524176 | orm | read | sale_order, stock_picking | addons/sale_stock/models/sale_order.py:29-29 |
| ap-351f091bba | orm | read | sale_order, stock_reference_sale_rel, stock_reference | addons/sale_stock/models/sale_order.py:37-37 |
| ap-50b1dc702c | odoo | read | res_partner | addons/sale_stock/models/sale_order.py:153-153 |
| ap-f51975133a | odoo | read | sale_order_line | addons/sale_stock/models/sale_order.py:317-317 |
| ap-bcb2813eea | orm | read | sale_order_line, sale_order_line_stock_route_rel, stock_route | addons/sale_stock/models/sale_order_line.py:16-16 |
| ap-a4bb9c9b35 | orm | read | sale_order_line, stock_move | addons/sale_stock/models/sale_order_line.py:17-17 |
| ap-6b089a40f9 | orm | read | sale_order_line, stock_warehouse | addons/sale_stock/models/sale_order_line.py:20-20 |
| ap-fbd0384caa | odoo | read | stock_rule | addons/sale_stock/models/sale_order_line.py:37-40 |
| ap-66c652d84b | odoo | read | sale_order_line | addons/sale_stock/models/sale_order_line.py:63-67 |
| ap-9c85f75672 | odoo | read | sale_order_line | addons/sale_stock/models/sale_order_line.py:79-79 |
| ap-bb08829742 | odoo | read | stock_move | addons/sale_stock/models/sale_order_line.py:84-84 |
| ap-affb9d74e4 | odoo | read | stock_move | addons/sale_stock/models/sale_order_line.py:87-87 |
| ap-70d6a93927 | odoo | read | stock_move | addons/sale_stock/models/sale_order_line.py:94-94 |
| ap-ae9a99a83f | odoo | read | stock_move | addons/sale_stock/models/sale_order_line.py:360-360 |
| ap-a80d10964e | odoo | read | stock_move | addons/sale_stock/models/sale_order_line.py:360-360 |
| ap-0c8431d589 | odoo | write | stock_reference | addons/sale_stock/models/sale_order_line.py:397-397 |
| ap-5b5bb5b361 | orm | read | stock_move, sale_order_line | addons/sale_stock/models/stock.py:17-17 |
| ap-72858c83f2 | odoo | read | account_move_line | addons/sale_stock/models/stock.py:22-24 |
| ap-a77ea3f6fd | odoo | read | stock_move | addons/sale_stock/models/stock.py:35-35 |
| ap-6bc9689fa5 | odoo | read | account_move_line | addons/sale_stock/models/stock.py:36-36 |
| ap-eb0a11d015 | odoo | write | sale_order_line | addons/sale_stock/models/stock.py:144-144 |
| ap-1e1d03b4ae | odoo | read | stock_move | addons/sale_stock/models/stock.py:174-174 |
| ap-9c2511c38c | odoo | read | sale_order_line | addons/sale_stock/models/stock.py:212-216 |
| ap-c038400fcf | odoo | read | stock_move | addons/sale_stock/models/stock.py:224-224 |
| ap-773a4315ad | orm | read | stock_picking, sale_order | addons/sale_stock/models/stock.py:262-262 |
| ap-29d21d6f45 | orm | read | stock_picking, return_reason | addons/sale_stock/models/stock.py:264-264 |
| ap-7dca867d7d | odoo | write | stock_reference | addons/sale_stock/models/stock.py:295-298 |
| ap-c73911efc0 | odoo | write | sale_order_line | addons/sale_stock/models/stock.py:346-346 |
| ap-b22f300e19 | odoo | read | stock_move_line, stock_move, sale_order_line, stock_picking, stock_location | addons/sale_stock/models/stock.py:421-426 |
| ap-d600bad055 | odoo | read | stock_move | addons/stock/models/product.py:221-221 |
| ap-47bf807f63 | odoo | read | stock_move | addons/stock/models/product.py:222-222 |
| ap-a8ee48791e | odoo | read | stock_quant | addons/stock/models/product.py:223-223 |
| ap-242c4125ba | odoo | read | stock_quant | addons/stock/models/product.py:228-228 |
| ap-bb8000a349 | odoo | read | stock_move_line | addons/stock/models/product.py:236-236 |
| ap-0f7abb85b4 | odoo | read | stock_move_line | addons/stock/models/product.py:239-239 |
| ap-3074de65e3 | odoo | read | stock_warehouse | addons/stock/models/product.py:383-383 |
| ap-f08391fd76 | odoo | read | stock_location | addons/stock/models/product.py:386-386 |
| ap-d52b09755d | odoo | read | stock_location | addons/stock/models/product.py:389-389 |
| ap-4ee701d730 | odoo | read | stock_warehouse | addons/stock/models/product.py:398-400 |
| ap-af5ecb76a1 | odoo | read | stock_location | addons/stock/models/product.py:407-407 |
| ap-9050eade40 | odoo | write | product_template | addons/stock/models/product.py:1047-1047 |
| ap-7b052621a6 | odoo | read | stock_location | addons/stock/models/res_company.py:62-62 |
| ap-d3503c9731 | odoo | read | stock_warehouse | addons/stock/models/res_company.py:68-68 |
| ap-84c4804d4c | odoo | read | stock_quant, stock_location | addons/stock/models/stock_location.py:137-140 |
| ap-9e9efc32b3 | odoo | read | stock_warehouse | addons/stock/models/stock_location.py:166-166 |
| ap-47a4eca4a2 | odoo | read | stock_location | addons/stock/models/stock_location.py:183-183 |
| ap-9f0d90fc5b | odoo | read | stock_move_line, stock_package | addons/stock/models/stock_location.py:335-339 |
| ap-ae302515d1 | odoo | read | stock_quant, stock_package | addons/stock/models/stock_location.py:340-343 |
| ap-3f2d02d65f | odoo | read | stock_move_line | addons/stock/models/stock_location.py:348-353 |
| ap-282705e95e | odoo | read | stock_quant | addons/stock/models/stock_location.py:354-357 |
| ap-09a9c30f9e | odoo | read | stock_quant | addons/stock/models/stock_location.py:481-484 |
| ap-7836c5df30 | odoo | read | stock_move_line | addons/stock/models/stock_location.py:486-489 |
| ap-23054f4583 | odoo | read | stock_move_line | addons/stock/models/stock_location.py:490-493 |
| ap-23d50cea88 | odoo | read | stock_warehouse | addons/stock/models/stock_location.py:546-546 |
| ap-a62b71d7ac | orm | read | stock_lot, product_product | addons/stock/models/stock_lot.py:44-44 |
| ap-3cd3699209 | orm | read | stock_lot, stock_quant | addons/stock/models/stock_lot.py:52-52 |
| ap-c0a7b7e4cf | orm | read | stock_lot, res_company | addons/stock/models/stock_lot.py:56-56 |
| ap-73ea4aa589 | orm | read | stock_lot, res_partner_stock_lot_rel, res_partner | addons/stock/models/stock_lot.py:59-59 |
| ap-2e91e0597e | orm | read | stock_lot, stock_location | addons/stock/models/stock_lot.py:61-61 |
| ap-dc2c4e6175 | odoo | read | stock_lot | addons/stock/models/stock_lot.py:109-111 |
| ap-c06b25224f | odoo | read | stock_move_line | addons/stock/models/stock_lot.py:187-187 |
| ap-8a0e7151a1 | odoo | read | stock_move_line | addons/stock/models/stock_lot.py:204-204 |
| ap-77c129b1f6 | odoo | read | stock_quant | addons/stock/models/stock_lot.py:251-251 |
| ap-c4e78dbc34 | odoo | read | stock_move_line | addons/stock/models/stock_lot.py:258-258 |
| ap-ee271aaafe | odoo | read | stock_move_line | addons/stock/models/stock_lot.py:259-259 |
| ap-816f4dca8d | odoo | read | stock_move_line | addons/stock/models/stock_lot.py:348-348 |
| ap-0a3eac02a2 | odoo | read | stock_move_line | addons/stock/models/stock_lot.py:395-395 |
| ap-d6ddec72d0 | orm | read | stock_move, res_company | addons/stock/models/stock_move.py:36-36 |
| ap-f00b5d11b0 | orm | read | stock_move, product_product | addons/stock/models/stock_move.py:40-40 |
| ap-7d1afb4aed | orm | read | stock_move, template_attribute_value_stock_move_rel, product_template_attribute_value | addons/stock/models/stock_move.py:47-47 |
| ap-8e1b25d497 | orm | read | stock_move, uom_uom | addons/stock/models/stock_move.py:68-68 |
| ap-856e70e191 | orm | read | stock_move, stock_location | addons/stock/models/stock_move.py:76-76 |
| ap-1754af1064 | orm | read | stock_move, stock_location | addons/stock/models/stock_move.py:82-82 |
| ap-89360e2c20 | orm | read | stock_move, stock_location | addons/stock/models/stock_move.py:86-86 |
| ap-793621a87c | orm | read | stock_move, res_partner | addons/stock/models/stock_move.py:93-93 |
| ap-38b4ab2a40 | orm | read | stock_move, stock_move_move_rel, stock_move | addons/stock/models/stock_move.py:98-98 |
| ap-9430e41616 | orm | read | stock_move, stock_move_move_rel, stock_move | addons/stock/models/stock_move.py:102-102 |
| ap-36d0095021 | orm | read | stock_move, stock_picking | addons/stock/models/stock_move.py:106-106 |
| ap-a514343b43 | orm | read | stock_move, stock_reference_move_rel, stock_reference | addons/stock/models/stock_move.py:141-141 |
| ap-92accea444 | orm | read | stock_move, stock_rule | addons/stock/models/stock_move.py:143-143 |
| ap-f785c53a01 | orm | read | stock_move, stock_picking_type | addons/stock/models/stock_move.py:150-150 |
| ap-c22666d116 | orm | read | stock_move, stock_move_line | addons/stock/models/stock_move.py:153-153 |
| ap-dce24c2c53 | orm | read | stock_move, stock_move | addons/stock/models/stock_move.py:155-155 |
| ap-718e4843a6 | orm | read | stock_move, stock_move | addons/stock/models/stock_move.py:158-158 |
| ap-8a46d47f4e | orm | read | stock_move, res_partner | addons/stock/models/stock_move.py:163-163 |
| ap-c9cacf080a | orm | read | stock_move, stock_route_move, stock_route | addons/stock/models/stock_move.py:166-166 |
| ap-45f9228a92 | orm | read | stock_move, stock_warehouse | addons/stock/models/stock_move.py:168-168 |
| ap-78f371230b | orm | read | stock_move, stock_warehouse_orderpoint | addons/stock/models/stock_move.py:193-193 |
| ap-d98abf32a5 | orm | read | stock_move, uom_uom | addons/stock/models/stock_move.py:198-198 |
| ap-4c026e2942 | orm | read | stock_move, stock_move_stock_scrap_reason_tag_rel, stock_scrap_reason_tag | addons/stock/models/stock_move.py:203-203 |
| ap-40e9965b67 | odoo | read | stock_move_line | addons/stock/models/stock_move.py:455-458 |
| ap-21d788dfd5 | odoo | write | stock_move_line | addons/stock/models/stock_move.py:485-485 |
| ap-34fc93c68a | odoo | read | stock_move_line | addons/stock/models/stock_move.py:485-485 |
| ap-d59d94dfe2 | odoo | read | product_product | addons/stock/models/stock_move.py:560-563 |
| ap-09928f5c9b | odoo | read | product_product | addons/stock/models/stock_move.py:560-560 |
| ap-e27e3bbe6d | odoo | read | stock_move | addons/stock/models/stock_move.py:603-603 |
| ap-63364d8074 | odoo | read | stock_move_line | addons/stock/models/stock_move.py:633-636 |
| ap-c77d9cbf9d | odoo | read | stock_move_line | addons/stock/models/stock_move.py:675-675 |
| ap-e04db45006 | odoo | read | stock_picking | addons/stock/models/stock_move.py:857-857 |
| ap-bfad084b22 | odoo | read | product_product | addons/stock/models/stock_move.py:864-864 |
| ap-44a500acd0 | odoo | read | stock_warehouse_orderpoint | addons/stock/models/stock_move.py:962-962 |
| ap-f59df8e282 | odoo | read | stock_move | addons/stock/models/stock_move.py:1092-1092 |
| ap-c97213301a | odoo | read | stock_move_line | addons/stock/models/stock_move.py:1101-1101 |
| ap-976c504a96 | odoo | read | stock_move | addons/stock/models/stock_move.py:1102-1102 |
| ap-4a5b8d0552 | odoo | write | stock_move_line | addons/stock/models/stock_move.py:1104-1104 |
| ap-ccc1092819 | odoo | read | stock_lot | addons/stock/models/stock_move.py:1135-1139 |
| ap-ac9a3585d5 | odoo | write | stock_lot | addons/stock/models/stock_move.py:1146-1146 |
| ap-cfe7f82f94 | odoo | read | stock_package | addons/stock/models/stock_move.py:1297-1298 |
| ap-41a312c8df | odoo | read | stock_move | addons/stock/models/stock_move.py:1319-1319 |
| ap-19ba8b0399 | odoo | write | stock_move | addons/stock/models/stock_move.py:1320-1320 |
| ap-90c42b7ef5 | odoo | write | stock_move | addons/stock/models/stock_move.py:1321-1321 |
| ap-d8e8212cab | odoo | write | stock_move | addons/stock/models/stock_move.py:1435-1435 |
| ap-72225df6f7 | odoo | write | stock_move | addons/stock/models/stock_move.py:1438-1438 |
| ap-4c2b2064a0 | odoo | write | stock_move | addons/stock/models/stock_move.py:1472-1472 |
| ap-325eb98ca1 | odoo | write | stock_move | addons/stock/models/stock_move.py:1648-1648 |
| ap-806d4f7d16 | odoo | write | stock_picking | addons/stock/models/stock_move.py:1656-1656 |
| ap-8c10a06627 | odoo | write | stock_move | addons/stock/models/stock_move.py:1658-1658 |
| ap-1aadb28e3d | odoo | read | stock_move | addons/stock/models/stock_move.py:1804-1804 |
| ap-533e035f98 | odoo | read | stock_move | addons/stock/models/stock_move.py:1815-1815 |
| ap-b74be0422a | odoo | read | stock_move | addons/stock/models/stock_move.py:1815-1815 |
| ap-d85d70f316 | odoo | read | stock_move | addons/stock/models/stock_move.py:1824-1824 |
| ap-112b2573d4 | odoo | read | product_product | addons/stock/models/stock_move.py:1887-1887 |
| ap-f513aa9d51 | odoo | read | stock_package | addons/stock/models/stock_move.py:1923-1923 |
| ap-6962ef9138 | odoo | write | stock_move_line | addons/stock/models/stock_move.py:1997-1997 |
| ap-b6234dbad2 | odoo | read | stock_move | addons/stock/models/stock_move.py:2106-2106 |
| ap-005ba74bff | odoo | read | stock_move | addons/stock/models/stock_move.py:2106-2106 |
| ap-a54c96f7d0 | odoo | write | stock_move_line | addons/stock/models/stock_move.py:2247-2247 |
| ap-47ee649541 | odoo | write | stock_move_line | addons/stock/models/stock_move.py:2266-2266 |
| ap-a04542661d | odoo | write | stock_move | addons/stock/models/stock_move.py:2267-2267 |
| ap-5a6bd21e18 | odoo | read | stock_move | addons/stock/models/stock_move.py:2267-2267 |
| ap-5befd5e830 | odoo | write | stock_move | addons/stock/models/stock_move.py:2268-2268 |
| ap-29d57729f7 | odoo | read | stock_move | addons/stock/models/stock_move.py:2268-2268 |
| ap-c1d5ba10ea | odoo | read | stock_move | addons/stock/models/stock_move.py:2271-2271 |
| ap-16985b2760 | odoo | write | stock_move | addons/stock/models/stock_move.py:2313-2316 |
| ap-3a9eaf1463 | odoo | write | stock_move | addons/stock/models/stock_move.py:2326-2326 |
| ap-df7cf100d1 | odoo | write | stock_move | addons/stock/models/stock_move.py:2329-2329 |
| ap-35f403deeb | odoo | write | stock_move | addons/stock/models/stock_move.py:2333-2333 |
| ap-291049e984 | odoo | write | stock_move_line | addons/stock/models/stock_move.py:2369-2369 |
| ap-9089f537df | odoo | read | stock_move_line | addons/stock/models/stock_move.py:2369-2369 |
| ap-495441c7ba | odoo | read | stock_quant | addons/stock/models/stock_move.py:2381-2386 |
| ap-6545c9af7d | odoo | write | stock_move | addons/stock/models/stock_move.py:2524-2524 |
| ap-3338bfdcc9 | odoo | read | stock_move | addons/stock/models/stock_move.py:2553-2553 |
| ap-c0a5b0d21c | odoo | read | stock_warehouse_orderpoint | addons/stock/models/stock_move.py:2737-2743 |
| ap-4c706431b2 | odoo | read | stock_move | addons/stock/models/stock_move.py:2770-2772 |
| ap-a1805b3d2f | odoo | read | stock_move | addons/stock/models/stock_move.py:2782-2782 |
| ap-44f3aa25e7 | odoo | read | stock_move | addons/stock/models/stock_move.py:2792-2792 |
| ap-10eae0760b | odoo | write | stock_move | addons/stock/models/stock_move.py:2968-2968 |
| ap-340da22b20 | orm | read | stock_move_line, stock_picking | addons/stock/models/stock_move_line.py:21-21 |
| ap-d222f905a2 | orm | read | stock_move_line, stock_move | addons/stock/models/stock_move_line.py:27-27 |
| ap-bd043c414a | orm | read | stock_move_line, res_company | addons/stock/models/stock_move_line.py:30-30 |
| ap-fdfbc9228c | orm | read | stock_move_line, product_product | addons/stock/models/stock_move_line.py:31-31 |
| ap-4ea3591b9d | orm | read | stock_move_line, uom_uom | addons/stock/models/stock_move_line.py:33-33 |
| ap-40da2962f3 | orm | read | stock_move_line, stock_package | addons/stock/models/stock_move_line.py:45-45 |
| ap-1f8c1f305b | orm | read | stock_move_line, stock_lot | addons/stock/models/stock_move_line.py:49-49 |
| ap-3ec24e1222 | orm | read | stock_move_line, stock_package | addons/stock/models/stock_move_line.py:53-53 |
| ap-8b007992d4 | orm | read | stock_move_line, stock_package_history | addons/stock/models/stock_move_line.py:59-59 |
| ap-864db3d990 | orm | read | stock_move_line, res_partner | addons/stock/models/stock_move_line.py:63-63 |
| ap-92ac553af1 | orm | read | stock_move_line, stock_location | addons/stock/models/stock_move_line.py:67-67 |
| ap-6202cd0762 | orm | read | stock_move_line, stock_location | addons/stock/models/stock_move_line.py:71-71 |
| ap-421ebb1c77 | orm | read | stock_move_line, stock_move_line_consume_rel, stock_move_line | addons/stock/models/stock_move_line.py:86-86 |
| ap-fcb63b0689 | orm | read | stock_move_line, stock_move_line_consume_rel, stock_move_line | addons/stock/models/stock_move_line.py:87-87 |
| ap-87d70dc981 | odoo | read | stock_location | addons/stock/models/stock_move_line.py:302-302 |
| ap-5c352a1c7b | odoo | read | stock_move | addons/stock/models/stock_move_line.py:352-352 |
| ap-133a6b7fa6 | odoo | read | stock_picking | addons/stock/models/stock_move_line.py:354-354 |
| ap-0d6bcee4d0 | odoo | read | stock_move | addons/stock/models/stock_move_line.py:356-356 |
| ap-37aee9dc32 | odoo | write | stock_move | addons/stock/models/stock_move_line.py:368-368 |
| ap-d36ab7b9e4 | odoo | read | stock_move | addons/stock/models/stock_move_line.py:410-410 |
| ap-a021437d31 | odoo | read | stock_move | addons/stock/models/stock_move_line.py:411-411 |
| ap-330abc3818 | odoo | read | stock_package | addons/stock/models/stock_move_line.py:446-446 |
| ap-5fe08406e9 | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:648-648 |
| ap-7d3211ad67 | odoo | read | stock_lot | addons/stock/models/stock_move_line.py:649-653 |
| ap-dc1e3402a3 | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:665-665 |
| ap-7b51a3a54f | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:674-674 |
| ap-16b923f20a | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:676-676 |
| ap-ded7c9c634 | odoo | write | stock_move_line | addons/stock/models/stock_move_line.py:677-677 |
| ap-13fe8995b9 | odoo | write | stock_package_history | addons/stock/models/stock_move_line.py:692-692 |
| ap-0462dcfd23 | odoo | read | stock_move | addons/stock/models/stock_move_line.py:717-717 |
| ap-744f8f1ab0 | odoo | write | stock_lot | addons/stock/models/stock_move_line.py:804-804 |
| ap-2f645449d1 | odoo | read | stock_lot | addons/stock/models/stock_move_line.py:812-812 |
| ap-6993d707bc | odoo | read | stock_location | addons/stock/models/stock_move_line.py:814-814 |
| ap-0b66ca1dba | odoo | read | stock_location | addons/stock/models/stock_move_line.py:816-816 |
| ap-fba13cd108 | odoo | read | stock_package | addons/stock/models/stock_move_line.py:818-818 |
| ap-b740e3d577 | odoo | read | stock_package | addons/stock/models/stock_move_line.py:820-820 |
| ap-9e94e435a3 | odoo | read | res_partner | addons/stock/models/stock_move_line.py:822-822 |
| ap-7c69882c73 | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:866-866 |
| ap-3e091d057e | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:884-884 |
| ap-7be1dfc726 | odoo | write | stock_move_line | addons/stock/models/stock_move_line.py:890-890 |
| ap-9fa9ebc253 | odoo | read | stock_package | addons/stock/models/stock_move_line.py:1020-1020 |
| ap-c462e480c0 | odoo | read | stock_quant | addons/stock/models/stock_move_line.py:1045-1045 |
| ap-871bfa5836 | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:1116-1116 |
| ap-b2791712bb | odoo | write | stock_move_line | addons/stock/models/stock_move_line.py:1291-1291 |
| ap-ac0e2b4257 | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:1294-1294 |
| ap-922a3d600f | odoo | write | stock_move_line | addons/stock/models/stock_move_line.py:1310-1313 |
| ap-d06d0893fc | odoo | write | stock_package | addons/stock/models/stock_move_line.py:1343-1345 |
| ap-138586b06f | odoo | write | stock_picking_batch | addons/stock/models/stock_move_line.py:1374-1379 |
| ap-8597db435d | odoo | read | stock_picking | addons/stock/models/stock_move_line.py:1432-1432 |
| ap-cd1ca2cf2e | odoo | write | stock_picking | addons/stock/models/stock_move_line.py:1432-1432 |
| ap-a2d378aa5b | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:1490-1490 |
| ap-122f8ce796 | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:1493-1493 |
| ap-cc40d90ed5 | odoo | read | stock_picking_batch | addons/stock/models/stock_move_line.py:1545-1545 |
| ap-a70cf05501 | odoo | read | stock_picking_batch | addons/stock/models/stock_move_line.py:1566-1566 |
| ap-2076ef86fb | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:1609-1609 |
| ap-6dd8da05fb | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:1643-1643 |
| ap-6356be1879 | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:1683-1683 |
| ap-5b6a1fd72f | odoo | write | stock_picking_batch | addons/stock/models/stock_move_line.py:1690-1694 |
| ap-d47aeb6c62 | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:1715-1715 |
| ap-721b413561 | odoo | read | stock_move_line | addons/stock/models/stock_move_line.py:1719-1719 |
| ap-a60a66bc14 | odoo | write | stock_picking_batch | addons/stock/models/stock_move_line.py:1720-1724 |
| ap-ef8b906ae1 | orm | read | stock_warehouse_orderpoint, stock_warehouse | addons/stock/models/stock_orderpoint.py:38-38 |
| ap-1939276256 | orm | read | stock_warehouse_orderpoint, stock_location | addons/stock/models/stock_orderpoint.py:42-42 |
| ap-08e02b8bcd | orm | read | stock_warehouse_orderpoint, product_product | addons/stock/models/stock_orderpoint.py:47-47 |
| ap-26e55eaa4f | orm | read | stock_warehouse_orderpoint, uom_uom | addons/stock/models/stock_orderpoint.py:89-89 |
| ap-7a7c7363d6 | orm | read | stock_warehouse_orderpoint, res_company | addons/stock/models/stock_orderpoint.py:93-93 |
| ap-7a9d5f8919 | orm | read | stock_warehouse_orderpoint, stock_route | addons/stock/models/stock_orderpoint.py:101-101 |
| ap-0feef34e5a | odoo | read | stock_warehouse | addons/stock/models/stock_orderpoint.py:139-139 |
| ap-889683d397 | odoo | read | stock_location | addons/stock/models/stock_orderpoint.py:143-143 |
| ap-37192b58c4 | odoo | read | stock_move | addons/stock/models/stock_orderpoint.py:183-183 |
| ap-2d7077c2ec | odoo | read | stock_move | addons/stock/models/stock_orderpoint.py:184-184 |
| ap-7839642a20 | odoo | read | stock_rule | addons/stock/models/stock_orderpoint.py:231-231 |
| ap-a90792feea | odoo | read | stock_warehouse | addons/stock/models/stock_orderpoint.py:299-301 |
| ap-437b2a949b | odoo | read | stock_warehouse | addons/stock/models/stock_orderpoint.py:311-313 |
| ap-2570a812e5 | odoo | read | product_product | addons/stock/models/stock_orderpoint.py:510-510 |
| ap-7e583b7379 | odoo | read | stock_warehouse_orderpoint | addons/stock/models/stock_orderpoint.py:544-544 |
| ap-2e48d89f8a | odoo | read | stock_location | addons/stock/models/stock_orderpoint.py:572-572 |
| ap-7437b5abc1 | odoo | read | stock_quant | addons/stock/models/stock_orderpoint.py:577-577 |
| ap-33ecc184e7 | odoo | read | stock_move | addons/stock/models/stock_orderpoint.py:580-580 |
| ap-96e44c566c | odoo | read | stock_move | addons/stock/models/stock_orderpoint.py:583-583 |
| ap-90e6d47f17 | odoo | read | stock_warehouse_orderpoint | addons/stock/models/stock_orderpoint.py:593-595 |
| ap-744e2ebe35 | odoo | read | stock_warehouse_orderpoint | addons/stock/models/stock_orderpoint.py:600-600 |
| ap-309e6e2c15 | odoo | read | product_product | addons/stock/models/stock_orderpoint.py:615-615 |
| ap-9ef763da2a | odoo | read | product_product | addons/stock/models/stock_orderpoint.py:616-619 |
| ap-c831fdef4e | odoo | read | product_product | addons/stock/models/stock_orderpoint.py:632-632 |
| ap-9fb042a024 | odoo | read | stock_location | addons/stock/models/stock_orderpoint.py:640-640 |
| ap-3affa127b5 | odoo | read | stock_warehouse | addons/stock/models/stock_orderpoint.py:643-643 |
| ap-dc890c5c83 | odoo | write | stock_warehouse_orderpoint | addons/stock/models/stock_orderpoint.py:648-648 |
| ap-278e421980 | odoo | read | stock_move | addons/stock/models/stock_orderpoint.py:669-669 |
| ap-691a232b51 | odoo | read | stock_warehouse_orderpoint | addons/stock/models/stock_orderpoint.py:702-702 |
| ap-0aa02b1f5f | odoo | write | stock_warehouse_orderpoint | addons/stock/models/stock_orderpoint.py:705-705 |
| ap-a8af599b42 | odoo | read | stock_reference | addons/stock/models/stock_orderpoint.py:725-725 |
| ap-8a8ebef025 | odoo | read | stock_warehouse_orderpoint | addons/stock/models/stock_orderpoint.py:742-742 |
| ap-7ed29ee9f2 | odoo | read | stock_reference | addons/stock/models/stock_orderpoint.py:749-749 |
| ap-92cac90fc0 | odoo | read | product_product, product_template | addons/stock/models/stock_orderpoint.py:818-818 |
| ap-994e3fe5f9 | odoo | read | stock_location | addons/stock/models/stock_orderpoint.py:821-821 |
| ap-8bd520b07c | odoo | read | stock_move | addons/stock/models/stock_orderpoint.py:878-881 |
| ap-9cf87a6334 | odoo | read | stock_move | addons/stock/models/stock_orderpoint.py:882-885 |
| ap-e1d1c49eb5 | odoo | read | stock_package | addons/stock/models/stock_package.py:65-65 |
| ap-593163b70a | odoo | read | stock_move_line | addons/stock/models/stock_package.py:146-148 |
| ap-c35f435045 | odoo | read | stock_move_line | addons/stock/models/stock_package.py:174-176 |
| ap-9e72170bdc | odoo | read | stock_package_type | addons/stock/models/stock_package.py:284-284 |
| ap-5925b00b61 | odoo | read | stock_package_type | addons/stock/models/stock_package.py:292-292 |
| ap-bb5566b7c3 | odoo | read | stock_package_type | addons/stock/models/stock_package.py:294-294 |
| ap-b95ea708f6 | odoo | read | stock_location | addons/stock/models/stock_package.py:305-305 |
| ap-3a3b9f574b | odoo | read | stock_package, stock_package_type | addons/stock/models/stock_package.py:441-444 |
| ap-09b0296f85 | odoo | read | stock_move_line | addons/stock/models/stock_package.py:447-451 |
| ap-8f418b263f | odoo | read | stock_package_type | addons/stock/models/stock_package_type.py:72-72 |
| ap-c9bcaeb5e8 | odoo | read | stock_picking_type | addons/stock/models/stock_picking.py:29-32 |
| ap-c27198be57 | orm | read | stock_picking, stock_picking | addons/stock/models/stock_picking.py:40-40 |
| ap-9742dc412c | orm | read | stock_picking, stock_picking | addons/stock/models/stock_picking.py:45-45 |
| ap-5dbd958d3a | orm | read | stock_picking, stock_picking | addons/stock/models/stock_picking.py:46-46 |
| ap-f89f518b13 | orm | read | stock_picking, stock_picking | addons/stock/models/stock_picking.py:48-48 |
| ap-43ada59fc1 | orm | read | stock_picking, stock_location | addons/stock/models/stock_picking.py:89-89 |
| ap-be079baacd | orm | read | stock_picking, stock_location | addons/stock/models/stock_picking.py:93-93 |
| ap-b0e21811fa | orm | read | stock_picking, stock_move | addons/stock/models/stock_picking.py:97-97 |
| ap-0774fcf099 | orm | read | stock_picking, stock_picking_type | addons/stock/models/stock_picking.py:100-100 |
| ap-4c74a2d5da | orm | read | stock_picking, res_partner | addons/stock/models/stock_picking.py:111-111 |
| ap-9250f166d5 | orm | read | stock_picking, res_company | addons/stock/models/stock_picking.py:114-114 |
| ap-7a7320fd3a | orm | read | stock_picking, res_users | addons/stock/models/stock_picking.py:117-117 |
| ap-804d99edb3 | orm | read | stock_picking, stock_move_line | addons/stock/models/stock_picking.py:122-122 |
| ap-f69d68bdb6 | orm | read | stock_picking, stock_package_history_stock_picking_rel, stock_package_history | addons/stock/models/stock_picking.py:124-124 |
| ap-fe5580ced5 | orm | read | stock_picking, res_partner | addons/stock/models/stock_picking.py:131-131 |
| ap-3ed0c155f9 | orm | read | stock_picking, stock_picking_batch | addons/stock/models/stock_picking.py:154-154 |
| ap-ba31a2f488 | odoo | read | stock_move | addons/stock/models/stock_picking.py:254-254 |
| ap-684a17edac | odoo | read | stock_move | addons/stock/models/stock_picking.py:347-347 |
| ap-da1d56981d | odoo | read | stock_move | addons/stock/models/stock_picking.py:373-373 |
| ap-26e8f00432 | odoo | read | stock_move_line | addons/stock/models/stock_picking.py:393-397 |
| ap-9c260a7f9a | odoo | read | stock_move | addons/stock/models/stock_picking.py:451-454 |
| ap-e9267c7bd2 | odoo | read | stock_move | addons/stock/models/stock_picking.py:606-613 |
| ap-ee89af1171 | odoo | read | stock_picking_type | addons/stock/models/stock_picking.py:659-659 |
| ap-6ffccee5dc | odoo | read | stock_picking_type | addons/stock/models/stock_picking.py:689-689 |
| ap-3acc1fc18f | odoo | write | stock_move | addons/stock/models/stock_picking.py:716-716 |
| ap-ebe9dd9052 | odoo | write | stock_picking | addons/stock/models/stock_picking.py:1012-1012 |
| ap-86c165a694 | odoo | read | res_company | addons/stock/models/stock_picking.py:1050-1050 |
| ap-0d59dccdb6 | odoo | read | stock_move_line | addons/stock/models/stock_picking.py:1125-1125 |
| ap-3fc479ed0a | odoo | read | stock_picking | addons/stock/models/stock_picking.py:1131-1131 |
| ap-930ca1ee22 | odoo | read | stock_move | addons/stock/models/stock_picking.py:1549-1549 |
| ap-ff0d50d8cc | odoo | write | product_label_layout | addons/stock/models/stock_picking.py:1907-1912 |
| ap-e820a27b63 | odoo | write | lot_label_layout | addons/stock/models/stock_picking.py:1921-1925 |
| ap-2fc3dbd319 | odoo | read | stock_package | addons/stock/models/stock_picking.py:1945-1945 |
| ap-0b3b94936b | odoo | write | stock_picking | addons/stock/models/stock_picking.py:1987-1987 |
| ap-5fb7e4a97f | odoo | read | stock_picking_batch | addons/stock/models/stock_picking.py:2060-2060 |
| ap-40f78a3283 | odoo | read | stock_picking | addons/stock/models/stock_picking.py:2074-2074 |
| ap-a19937633d | odoo | write | stock_picking_batch | addons/stock/models/stock_picking.py:2079-2079 |
| ap-79c3a54029 | odoo | read | stock_picking | addons/stock/models/stock_picking_batch.py:124-124 |
| ap-796e6d7ffc | odoo | read | stock_warehouse | addons/stock/models/stock_picking_type.py:508-508 |
| ap-ccbbc6e504 | orm | read | stock_quant, product_product | addons/stock/models/stock_quant.py:47-47 |
| ap-01e8a1ea1c | orm | read | stock_quant, stock_location | addons/stock/models/stock_quant.py:59-59 |
| ap-ef3cb9e8ce | orm | read | stock_quant, stock_lot | addons/stock/models/stock_quant.py:66-66 |
| ap-e912058230 | orm | read | stock_quant, stock_package | addons/stock/models/stock_quant.py:72-72 |
| ap-b82c123b12 | orm | read | stock_quant, res_partner | addons/stock/models/stock_quant.py:76-76 |
| ap-9d064ad46a | orm | read | stock_quant, res_users | addons/stock/models/stock_quant.py:117-117 |
| ap-b0c81b3313 | odoo | read | stock_quant, stock_location | addons/stock/models/stock_quant.py:253-253 |
| ap-50948e099c | odoo | read | stock_quant | addons/stock/models/stock_quant.py:255-255 |
| ap-6b3c674ad0 | odoo | read | product_product | addons/stock/models/stock_quant.py:307-307 |
| ap-39350fedfb | odoo | read | stock_location | addons/stock/models/stock_quant.py:308-308 |
| ap-b406800b2c | odoo | read | stock_lot | addons/stock/models/stock_quant.py:309-309 |
| ap-79faf536c1 | odoo | read | stock_package | addons/stock/models/stock_quant.py:310-310 |
| ap-4b755ba320 | odoo | read | res_partner | addons/stock/models/stock_quant.py:311-311 |
| ap-a450c93827 | odoo | read | stock_lot | addons/stock/models/stock_quant.py:319-319 |
| ap-733e7dd27f | odoo | write | stock_lot | addons/stock/models/stock_quant.py:322-322 |
| ap-d74fa3de24 | odoo | write | stock_quant | addons/stock/models/stock_quant.py:328-328 |
| ap-cbe7734584 | odoo | write | stock_quant | addons/stock/models/stock_quant.py:331-331 |
| ap-43ef592899 | odoo | read | stock_quant | addons/stock/models/stock_quant.py:628-632 |
| ap-8cc1772f15 | odoo | read | stock_quant | addons/stock/models/stock_quant.py:716-716 |
| ap-de6293535c | odoo | read | stock_quant | addons/stock/models/stock_quant.py:820-820 |
| ap-8ddc5d76ff | odoo | read | stock_quant | addons/stock/models/stock_quant.py:957-961 |
| ap-b3062b85ba | odoo | read | stock_location | addons/stock/models/stock_quant.py:1038-1038 |
| ap-1df74682d4 | odoo | write | stock_move | addons/stock/models/stock_quant.py:1058-1058 |
| ap-e5fe5c25da | odoo | write | stock_location | addons/stock/models/stock_quant.py:1063-1063 |
| ap-62d328bcdf | odoo | write | stock_quant | addons/stock/models/stock_quant.py:1122-1122 |
| ap-3b595bd66e | odoo | write | stock_quant | addons/stock/models/stock_quant.py:1136-1136 |
| ap-199c091ebc | sql | read | stock_quant | addons/stock/models/stock_quant.py:1164-1167 |
| ap-cc1eaf64cc | odoo | read | stock_quant | addons/stock/models/stock_quant.py:1170-1170 |
| ap-67df3f22cb | odoo | write | stock_quant | addons/stock/models/stock_quant.py:1171-1171 |
| ap-5e853b01b9 | odoo | read | stock_quant | addons/stock/models/stock_quant.py:1175-1179 |
| ap-862b4630a0 | odoo | read | stock_move_line, product_product, product_template | addons/stock/models/stock_quant.py:1180-1188 |
| ap-728ff0f0ee | sql | read | stock_quant | addons/stock/models/stock_quant.py:1217-1226 |
| ap-8ecaf1eaad | odoo | read | stock_warehouse | addons/stock/models/stock_quant.py:1330-1330 |
| ap-6781c22ac8 | odoo | write | stock_move | addons/stock/models/stock_quant.py:1598-1598 |
| ap-bd802cf6aa | odoo | read | stock_route | addons/stock/models/stock_replenish_mixin.py:21-21 |
| ap-60d3d1a928 | odoo | read | stock_rule | addons/stock/models/stock_rule.py:206-212 |
| ap-3260ed2c08 | odoo | write | stock_rule | addons/stock/models/stock_rule.py:214-214 |
| ap-835de33986 | odoo | write | stock_move | addons/stock/models/stock_rule.py:287-287 |
| ap-6a29a6418b | odoo | read | stock_rule | addons/stock/models/stock_rule.py:498-503 |
| ap-b791e30943 | odoo | read | stock_rule | addons/stock/models/stock_rule.py:528-528 |
| ap-81624e44ca | odoo | read | stock_rule | addons/stock/models/stock_rule.py:532-532 |
| ap-15c85dc6e0 | odoo | read | stock_rule | addons/stock/models/stock_rule.py:536-536 |
| ap-8bbb6c34dc | odoo | read | stock_rule | addons/stock/models/stock_rule.py:540-540 |
| ap-51e448e236 | odoo | read | stock_rule | addons/stock/models/stock_rule.py:542-542 |
| ap-f4420f71ed | odoo | read | stock_warehouse_orderpoint | addons/stock/models/stock_rule.py:687-687 |
| ap-6355b88298 | odoo | read | stock_move | addons/stock/models/stock_rule.py:698-699 |
| ap-486dcc6e1a | odoo | read | stock_move | addons/stock/models/stock_rule.py:701-701 |
| ap-cd292c8a48 | odoo | read | stock_location | addons/stock/models/stock_warehouse.py:759-759 |
| ap-89edc150a1 | odoo | read | stock_location | addons/stock/models/stock_warehouse.py:761-761 |
| ap-c0324faa37 | orm | read | account_move, stock_move | addons/stock_account/models/account_move.py:7-7 |
| ap-69842f42e9 | orm | read | account_move, product_value | addons/stock_account/models/account_move.py:9-9 |
| ap-2a07f87211 | orm | read | account_move_line, stock_move | addons/stock_account/models/account_move_line.py:7-7 |
| ap-584492e808 | odoo | read | account_analytic_account | addons/stock_account/models/analytic_account.py:58-58 |
| ap-1329666a53 | odoo | read | product_category | addons/stock_account/models/product.py:40-40 |
| ap-a234c90276 | odoo | read | stock_quant | addons/stock_account/models/product.py:50-55 |
| ap-29ef6efdee | odoo | read | product_product | addons/stock_account/models/product.py:66-66 |
| ap-442ed0038c | odoo | read | stock_lot | addons/stock_account/models/product.py:67-69 |
| ap-4c12e7cbc7 | odoo | read | stock_lot | addons/stock_account/models/product.py:73-75 |
| ap-8daae14356 | odoo | read | product_product | addons/stock_account/models/product.py:77-77 |
| ap-6ab5eed038 | odoo | read | stock_lot | addons/stock_account/models/product.py:79-79 |
| ap-fe660a73e8 | odoo | read | product_product | addons/stock_account/models/product.py:129-133 |
| ap-e31962cded | odoo | read | product_product | addons/stock_account/models/product.py:135-139 |
| ap-ff7e614dcb | odoo | read | product_product | addons/stock_account/models/product.py:168-168 |
| ap-8087c12a32 | odoo | write | product_template | addons/stock_account/models/product.py:203-203 |
| ap-db2e5aa270 | odoo | write | product_value | addons/stock_account/models/product.py:240-240 |
| ap-4817f92699 | odoo | read | stock_lot | addons/stock_account/models/product.py:242-243 |
| ap-3aa1477662 | odoo | read | stock_move | addons/stock_account/models/product.py:272-272 |
| ap-8474090c5f | odoo | read | stock_move | addons/stock_account/models/product.py:283-283 |
| ap-0b7e44e496 | odoo | read | product_value | addons/stock_account/models/product.py:286-289 |
| ap-f0d0139aef | odoo | read | product_value | addons/stock_account/models/product.py:308-308 |
| ap-5a54c7e225 | odoo | read | stock_move | addons/stock_account/models/product.py:316-316 |
| ap-d8dd35a2cf | odoo | read | stock_location | addons/stock_account/models/product.py:320-320 |
| ap-5c8b70e289 | odoo | read | stock_move | addons/stock_account/models/product.py:424-428 |
| ap-d39ea58dad | odoo | read | stock_move | addons/stock_account/models/product.py:442-442 |
| ap-2b9d90951c | odoo | read | stock_move | addons/stock_account/models/product.py:457-457 |
| ap-a3ecf0b2de | odoo | read | stock_move | addons/stock_account/models/product.py:701-701 |
| ap-3e9cd528e7 | odoo | read | stock_move | addons/stock_account/models/product.py:716-716 |
| ap-3dcae47161 | odoo | read | product_product | addons/stock_account/models/product.py:731-731 |
| ap-7e3fa619a9 | odoo | read | product_product, product_template | addons/stock_account/models/product.py:770-770 |
| ap-2773b0a107 | odoo | read | stock_lot | addons/stock_account/models/product.py:777-777 |
| ap-b8ab191cf5 | orm | read | product_value, product_product | addons/stock_account/models/product_value.py:17-17 |
| ap-48e973ebf2 | orm | read | product_value, stock_lot | addons/stock_account/models/product_value.py:19-19 |
| ap-6e17ba73ee | orm | read | product_value, stock_move | addons/stock_account/models/product_value.py:20-20 |
| ap-22be87ad99 | orm | read | product_value, res_company | addons/stock_account/models/product_value.py:29-29 |
| ap-d8b1fc7b40 | orm | read | product_value, res_users | addons/stock_account/models/product_value.py:34-34 |
| ap-e4911d3bd1 | orm | read | product_value, account_move | addons/stock_account/models/product_value.py:46-46 |
| ap-7d4804ee3a | odoo | read | stock_move | addons/stock_account/models/product_value.py:94-94 |
| ap-84c3a6d2da | odoo | read | stock_move | addons/stock_account/models/product_value.py:119-119 |
| ap-19d7f9cb9b | odoo | write | product_value | addons/stock_account/models/stock_lot.py:112-112 |
| ap-720d4a9705 | orm | read | stock_move, account_analytic_line_stock_move_rel, account_analytic_line | addons/stock_account/models/stock_move.py:60-60 |
| ap-dd21d0e395 | orm | read | stock_move, account_move | addons/stock_account/models/stock_move.py:61-61 |
| ap-408ab770d0 | orm | read | stock_move, account_move_line | addons/stock_account/models/stock_move.py:62-62 |
| ap-dbbd65bee0 | orm | read | stock_move, product_value | addons/stock_account/models/stock_move.py:63-63 |
| ap-8ec0b90e68 | odoo | read | product_product | addons/stock_account/models/stock_move.py:68-68 |
| ap-91c4bb31bc | odoo | read | product_product, product_template | addons/stock_account/models/stock_move.py:70-70 |
| ap-76ac140249 | odoo | write | product_value | addons/stock_account/models/stock_move.py:229-233 |
| ap-c1b0c248c7 | odoo | write | account_move | addons/stock_account/models/stock_move.py:276-282 |
| ap-661aec8756 | odoo | read | stock_move | addons/stock_account/models/stock_move.py:283-283 |
| ap-7a14f2e06a | odoo | write | account_analytic_line | addons/stock_account/models/stock_move.py:294-294 |
| ap-09e6bb79b3 | odoo | read | product_product | addons/stock_account/models/stock_move.py:436-436 |
| ap-86ee0e44ee | odoo | read | stock_lot | addons/stock_account/models/stock_move.py:437-437 |
| ap-f3e3301b56 | odoo | read | product_value | addons/stock_account/models/stock_move.py:555-555 |
| ap-d46182826c | odoo | read | stock_move_line | addons/stock_account/models/stock_move.py:642-642 |
| ap-1cd34b6798 | odoo | write | account_analytic_line | addons/stock_account/models/stock_move.py:737-737 |
| ap-79cd8ff278 | odoo | write | account_move | addons/stock_account/models/stock_move.py:786-786 |
| ap-bbe41cbe8a | odoo | read | stock_move | addons/stock_account/models/stock_move_line.py:30-30 |

</details>

## 5. Model choices for sign-off

### 5.1 `account_partial_reconcile` keeps its own collection (manager note 2)

The proposer embedded it under `account_move_line` through `debit_move_id` only. The confirmed hot reads `ap-26541a49e3` and `ap-d62ff6e982` (`AccountMove._get_all_reconciled_invoice_partials`) and `ap-8eda2da30f` (`AccountMoveLine._compute_amount_residual`) filter on both `debit_move_id` and `credit_move_id`; a partial has two parents. The `reference` decision restores `accountPartialReconcile` as a collection referenced from both sides (map-draft-2: 66 collections, 76 embeds; map-draft-1: 65 / 77). Indexes on the restored collection: [['creditMoveId', 1], ['exchangeMoveId', 1]], [['companyId', 1]], [['exchangeMoveId', 1]], [['fullReconcileId', 1]], [['debitMoveId', 1]] (the `debitMoveId` one is an added index decision; `odoo_fixture` has 0 partial reconciles, so the fixture does not exercise these reads).

### 5.2 Blocked register items (NOTES.md §s2.3 rows 23 and 28; manager note 3)

- **kpi_provider.get_kpi_summary runs without a registry (NOTES.md s2.3 row 23, blocked)** — Model-side answer: no spec change. The KPI query reads account_move.state, account_move.review_state, account_move.journal_id, account_move.statement_line_id, account_journal.type and account_bank_statement_line.is_reconciled; all six stay top-level fields of the accountMove, accountJournal and accountBankStatementLine collections (none is embedded), so the HTTP-layer endpoint can run the same filters as one aggregation on accountMove with $lookup on accountJournal and accountBankStatementLine, no registry needed. The information_schema probe that guards it becomes a check that the three collections exist. Until that rewrite ships, the endpoint returns [] (its own 'module not installed' path) once account_move leaves PostgreSQL; the PG id shadow cannot serve it because it has no state/journal columns. (evidence `addons/account/models/kpi_provider.py:31-71`)
- **stock post_init_hook reads product_product.qty_available raw (NOTES.md s2.3 row 28, blocked)** — Model-side answer: no spec change, an ordering rule for the plan. _create_inventory_adjustment reads the pre-stock stored JSONB column product_product.qty_available at `-i stock` time only. The rule: on every database that can install stock, stock is installed before product_product opts into MongoDB (fresh installs: `-i stock` before the product unit migrates; existing databases already have stock), so the hook always finds the column in PostgreSQL. This order must hold without exception: once product_product is Mongo-backed its PostgreSQL shadow keeps id only, the hook's SELECT fails with `column qty_available does not exist` (it does not return an empty result), and `-i stock` aborts. If the wave plan cannot guarantee the order, row 28 stays blocked and the storage-path wave owns a rewrite of the hook (detect a Mongo-backed product_product and skip or read the stored quantities from the product documents); that is ORM code and is not written here. The productProduct collection does not need a qty_available field: with stock installed the field is computed from stock_quant. (evidence `addons/stock/__init__.py:46-65`)

No ORM code is written here; both are model-side answers for the plan.

### 5.3 Index cap: `accountMove`

map-draft-1 proposes 67 indexes on `accountMove` (origins: access 34, reference_fk 18, source_index 15). MongoDB allows 64 per collection including `_id`; loading odoo_fixture refused 4 of them (`CannotCreateIndex`, code 67) and the recon reported them as `index_missing`. The index decisions remove the 12 entries that carry the 13 unexercised source indexes (their `source_index_not_exercised` questions), leaving 55. Highest index counts in map-draft-2: `accountMove` 55, `accountMoveLine` 36, `stockMove` 32, `saleOrder` 29, `stockWarehouse` 26.

## 6. Local rehearsal (fixture mode, local target)

Source `odoo_fixture` (odoo_fixture, built by `.migration/fixtures/build_fixture.sh` from `odoo_src` as a template), target local `mongo:7` from the plugin's `docker-compose.local.yml`, loaded by `.migration/rehearsal/load_fixture.py` straight from the spec. Numbers below are from `rehearsal.map-draft-2.json`; `rehearsal.map-draft-1.json` holds the proposal's run.

|  | map-draft-1 | map-draft-2 |
|---|---|---|
| collections loaded | 65 | 66 |
| documents | 1709 | 1709 |
| largest document (bytes) | 7585 (productAttribute) | 7585 (productAttribute) |
| largest document, % of 16 MB | 0.0452 | 0.0452 |
| longest array | 46 (accountFiscalPosition.accountTaxRel) | 46 (accountFiscalPosition.accountTaxRel) |
| indexes created / in spec | 631 / 635 (4 refused) | 623 / 623 (0 refused) |
| recon verdict | FAIL | PASS |

Recon tiers (`.migration/rehearsal/recon/<unit>/result.json`, redacted values; map-draft-2 run: tolerances `unt12-3` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea`, mapping_sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc`, 17 UNVERIFIED warnings for collections with 0 fixture rows):

| spec | tier | checks | result | findings |
|---|---|---|---|---|
| map-draft-1 | 1 | 142 | PASS |  |
| map-draft-1 | 2 | 764 | FAIL (2) | accountBankStatementLine aggregate_sum field amount_residual->amountResidual; purchaseOrderLine aggregate_sum field technical_price_unit->technicalPriceUnit |
| map-draft-1 | 3 | 2516 | PASS |  |
| map-draft-2 | 1 | 142 | PASS |  |
| map-draft-2 | 2 | 776 | PASS |  |
| map-draft-2 | 3 | 2516 | PASS |  |

The Tier 2 findings are `SUM()` of float8 columns compared at `aggregate_rel_tol: 0`: PostgreSQL sums in row order and MongoDB `$sum` in document order, so the two doubles differ in the last place (seen with `--raw-values` on the map-draft-1 run: -5081.860000000001 vs -5081.86 on `account_bank_statement_line.amount_residual`, 11979.099999999999 vs 11979.1 on `purchase_order_line.technical_price_unit`). Tier 3 keyed diffs pass on every row, so the values themselves match. Plan decision `d-float-aggregates = rel-tol-float8`: tolerances `unt12-3` set `aggregate_rel_tol` to 1e-12, everything else unchanged; the map-draft-2 run passes every tier. Note: the pinned harness applies `aggregate_rel_tol` to every numeric aggregate (`_agg_close` in `recon/tiers.py`: min/max/sum of int, numeric and float alike), not to float8 only; at 1e-12 relative it only absorbs last-place double rounding.

Environment note: the local container aborted once with a WiredTiger `Too many open files` panic while building the committed spec's ~630 indexes (the container's default `nofile` limit, not a model property); it was restarted with a compose override file raising `ulimits.nofile` to 65536 (the plugin's compose file is untouched) and the runs above completed on that container.

Collections with 0 documents in odoo_fixture (17): `accountCashRounding`, `accountFullReconcile`, `accountJournalGroup`, `accountLockException`, `accountPayment`, `accountReconcileModelLineAccountTaxRel`, `accountReportExpression`, `accountReportExternalValue`, `productBaseUnit`, `productPricelist`, `productPricelistItem`, `productTag`, `stockPackageHistory`, `stockPutawayRule`, `stockScrapReasonTag`, `stockStorageCategoryCapacity`, `accountPartialReconcile`.

Per collection:

| collection | documents | max doc bytes | indexes created/spec | embeds (max array) |
|---|---|---|---|---|
| accountTaxRepartitionLine | 228 | 237 | 4/4 |  |
| accountAccount | 184 | 518 | 11/11 | resCompanyRel 1, accountTag 1, taxDefaultRel 0 |
| accountMoveLine | 171 | 1217 | 36/36 | accountTaxRel 2 |
| stockMove | 135 | 1082 | 32/32 | accountAnalyticLineStockMoveRel 0, createdPurchaseLineRel 0, moveRel 0, stockScrapReasonTagRel 0 |
| stockMoveLine | 103 | 404 | 26/26 | consumeRel 0 |
| productSupplierinfo | 88 | 320 | 6/6 |  |
| stockPicking | 83 | 530 | 19/19 |  |
| accountMove | 59 | 1774 | 55/55 | accountPayment 0, purchaseOrderRel 0, adjustingEntriesAccountMove 0 |
| stockQuant | 59 | 379 | 13/13 |  |
| accountTax | 57 | 2343 | 15/15 | alternatives 1, filiationRel 0, purchaseOrderLineRel 24, saleOrderLineRel 36, productSupplierTaxesRel 36, productTaxesRel 36 |
| saleOrderLine | 50 | 1126 | 14/14 | productAttributeCustomValue 0, accrualMoveRel 0, invoiceRel 0, stockRouteRel 0 |
| productProduct | 48 | 574 | 13/13 | customerProductReference 0, uomUomRel 0, productUom 0, productVariantCombination 2 |
| productTemplate | 38 | 1306 | 16/16 | productOptionalRel 2, attributeLine 2, uomUomRel 0 |
| stockLocation | 32 | 460 | 16/16 | stockPickingTypeRel 0 |
| purchaseOrderLine | 31 | 847 | 14/14 | accrualMoveRel 0 |
| uomUom | 30 | 277 | 4/4 |  |
| accountTaxGroup | 26 | 195 | 2/2 |  |
| productAttributeValueProductTemplateAttributeLineRel | 24 | 70 | 2/2 |  |
| productTemplateAttributeValue | 24 | 432 | 8/8 | productTemplateAttributeExcludedValueIdsRel 1, purchaseOrderLineRel 0, saleOrderLineRel 0, templateAttributeValueStockMoveRel 0 |
| saleOrder | 24 | 1020 | 29/29 | tagRel 2, transactionRel 0 |
| stockReference | 23 | 245 | 3/3 | moveRel 4, purchaseRel 1, saleRel 1 |
| accountBankStatementLine | 18 | 478 | 13/13 |  |
| purchaseOrder | 16 | 844 | 25/25 | stockPickingRel 1 |
| stockPickingType | 16 | 1221 | 10/10 | pickingTypeFavoriteUserRel 0 |
| accountJournal | 14 | 703 | 19/19 | accountReconcileModelRel 0 |
| productAttribute | 14 | 7585 | 3/3 | productTemplateRel 2, value 40 |
| accountIncoterms | 11 | 158 | 1/1 |  |
| accountPaymentTerm | 11 | 787 | 2/2 | line 2 |
| accountAccountTag | 8 | 281 | 3/3 | accountMoveLineRel 0, accountTaxRepartitionLineRel 0, productTemplateRel 0 |
| accountReconcileModel | 8 | 1003 | 3/3 | resPartnerRel 0, line 2 |
| stockRule | 8 | 450 | 13/13 |  |
| productCategory | 7 | 603 | 6/6 | stockPickingTypeRel 0 |
| productValue | 6 | 333 | 9/9 |  |
| stockRoute | 6 | 402 | 11/11 | categ 0, move 0, product 0, warehouse 2 |
| stockStorageCategory | 6 | 182 | 1/1 |  |
| returnReason | 5 | 167 | 0/0 |  |
| stockWarehouseOrderpoint | 5 | 469 | 11/11 |  |
| accountFiscalPosition | 4 | 1541 | 6/6 | account 0, resCountryStateRel 0, accountTaxRel 46 |
| accountReport | 4 | 1303 | 5/5 | column 2, line 0, sectionRel 0 |
| productRemoval | 4 | 159 | 0/0 |  |
| stockLot | 4 | 189 | 7/7 |  |
| productCombo | 3 | 633 | 3/3 | item 3, productTemplateRel 1 |
| accountBankStatement | 2 | 403 | 7/7 | irAttachmentRel 1 |
| accountPaymentMethod | 2 | 523 | 4/4 | line 2 |
| productDocument | 2 | 152 | 1/1 |  |
| stockPackage | 2 | 259 | 8/8 |  |
| stockPackageType | 2 | 317 | 3/3 | stockPutawayRuleRel 0, stockRouteRel 0 |
| stockPickingBatch | 2 | 248 | 7/7 |  |
| stockWarehouse | 2 | 589 | 26/26 | stockWhResupplyTable 0 |
| accountCashRounding | 0 | 0 | 5/5 | resCurrencyRel 0, resPartnerCategoryRel 0, accountPaymentMethodLineRel 0 |
| accountFullReconcile | 0 | 0 | 0/0 |  |
| accountJournalGroup | 0 | 0 | 1/1 |  |
| accountLockException | 0 | 0 | 4/4 |  |
| accountPayment | 0 | 0 | 20/20 | accountBankStatementLineRel 0 |
| accountReconcileModelLineAccountTaxRel | 0 | 0 | 2/2 |  |
| accountReportExpression | 0 | 0 | 3/3 |  |
| accountReportExternalValue | 0 | 0 | 3/3 |  |
| productBaseUnit | 0 | 0 | 0/0 |  |
| productPricelist | 0 | 0 | 4/4 |  |
| productPricelistItem | 0 | 0 | 10/10 |  |
| productTag | 0 | 0 | 3/3 | productProductRel 0, productTemplateRel 0 |
| stockPackageHistory | 0 | 0 | 8/8 | stockPickingRel 0 |
| stockPutawayRule | 0 | 0 | 6/6 |  |
| stockScrapReasonTag | 0 | 0 | 1/1 |  |
| stockStorageCategoryCapacity | 0 | 0 | 3/3 |  |
| accountPartialReconcile | 0 | 0 | 5/5 |  |

## 7. Fan-out per embed (profile p50 / p99 / max on odoo_src; fixture max)

76 embeds in map-draft-2. `parents` is the profiled parent-row count; an embed with 0 parents in odoo_src is **unexercised** by the fixture (section 8). `embed bytes max` is the profiled embedded-child byte total per parent.

| collection | array | child table | rule | basis | parents | p50 | p99 | max | embed bytes max | fixture max | unexercised |
|---|---|---|---|---|---|---|---|---|---|---|---|
| accountAccount | resCompanyRel | account_account_res_company_rel | read_together | derived | 184 | 1 | 1 | 1 | 8 | 1 |  |
| accountAccount | accountTag | account_account_account_tag | junction_array | derived | 184 | 0 | 1 | 1 | 8 | 1 |  |
| accountAccount | taxDefaultRel | account_account_tax_default_rel | junction_array | derived | 184 | 0 | 0 | 0 | 0 | 0 |  |
| accountAccountTag | accountMoveLineRel | account_account_tag_account_move_line_rel | junction_array | derived | 8 | 0 | 0 | 0 | 0 | 0 |  |
| accountAccountTag | accountTaxRepartitionLineRel | account_account_tag_account_tax_repartition_line_rel | junction_array | derived | 8 | 0 | 0 | 0 | 0 | 0 |  |
| accountAccountTag | productTemplateRel | account_account_tag_product_template_rel | junction_array | derived | 8 | 0 | 0 | 0 | 0 | 0 |  |
| accountBankStatement | irAttachmentRel | account_bank_statement_ir_attachment_rel | ownership | derived | 2 | 1 | 1 | 1 | 8 | 1 |  |
| accountCashRounding | resCurrencyRel | account_cash_rounding_res_currency_rel | ownership | assumed | 0 |  |  |  | 0 | 0 | yes |
| accountCashRounding | resPartnerCategoryRel | account_cash_rounding_res_partner_category_rel | ownership | assumed | 0 |  |  |  | 0 | 0 | yes |
| accountCashRounding | accountPaymentMethodLineRel | account_cash_rounding_account_payment_method_line_rel | junction_array | derived | 0 |  |  |  | 0 | 0 | yes |
| accountFiscalPosition | account | account_fiscal_position_account | read_together | derived | 4 | 0 | 0 | 0 | 0 | 0 |  |
| accountFiscalPosition | resCountryStateRel | account_fiscal_position_res_country_state_rel | ownership | assumed | 4 | 0 | 0 | 0 | 0 | 0 |  |
| accountFiscalPosition | accountTaxRel | account_fiscal_position_account_tax_rel | junction_array | derived | 4 | 2 | 46 | 46 | 368 | 46 |  |
| accountJournal | accountReconcileModelRel | account_journal_account_reconcile_model_rel | junction_array | derived | 14 | 0 | 0 | 0 | 0 | 0 |  |
| accountMove | accountPayment | account_move__account_payment | junction_array | derived | 59 | 0 | 0 | 0 | 0 | 0 |  |
| accountMove | purchaseOrderRel | account_move_purchase_order_rel | junction_array | derived | 59 | 0 | 0 | 0 | 0 | 0 |  |
| accountMove | adjustingEntriesAccountMove | adjusting_entries__account_move | junction_array | derived | 59 | 0 | 0 | 0 | 0 | 0 |  |
| accountMoveLine | accountTaxRel | account_move_line_account_tax_rel | junction_array | derived | 171 | 0 | 1 | 2 | 16 | 2 |  |
| accountPayment | accountBankStatementLineRel | account_payment_account_bank_statement_line_rel | junction_array | derived | 0 |  |  |  | 0 | 0 | yes |
| accountPaymentMethod | line | account_payment_method_line | read_together | derived | 2 | 2 | 2 | 2 | 110 | 2 |  |
| accountPaymentTerm | line | account_payment_term_line | read_together | derived | 11 | 1 | 2 | 2 | 144 | 2 |  |
| accountReconcileModel | resPartnerRel | account_reconcile_model_res_partner_rel | ownership | assumed | 8 | 0 | 0 | 0 | 0 | 0 |  |
| accountReconcileModel | line | account_reconcile_model_line | read_together | derived | 8 | 1 | 2 | 2 | 195 | 2 |  |
| accountReport | column | account_report_column | read_together | derived | 4 | 2 | 2 | 2 | 140 | 2 |  |
| accountReport | line | account_report_line | read_together | derived | 4 | 0 | 0 | 0 | 0 | 0 |  |
| accountReport | sectionRel | account_report_section_rel | junction_array | derived | 4 | 0 | 0 | 0 | 0 | 0 |  |
| accountTax | alternatives | account_tax_alternatives | junction_array | derived | 57 | 0 | 1 | 1 | 8 | 1 |  |
| accountTax | filiationRel | account_tax_filiation_rel | junction_array | derived | 57 | 0 | 0 | 0 | 0 | 0 |  |
| accountTax | purchaseOrderLineRel | account_tax_purchase_order_line_rel | junction_array | derived | 57 | 0 | 24 | 24 | 192 | 24 |  |
| accountTax | saleOrderLineRel | account_tax_sale_order_line_rel | junction_array | derived | 57 | 0 | 36 | 36 | 288 | 36 |  |
| accountTax | productSupplierTaxesRel | product_supplier_taxes_rel | junction_array | derived | 57 | 0 | 36 | 36 | 288 | 36 |  |
| accountTax | productTaxesRel | product_taxes_rel | junction_array | derived | 57 | 0 | 36 | 36 | 288 | 36 |  |
| productAttribute | productTemplateRel | product_attribute_product_template_rel | junction_array | derived | 14 | 0 | 2 | 2 | 16 | 2 |  |
| productAttribute | value | product_attribute_value | read_together | derived | 14 | 4 | 40 | 40 | 2456 | 40 |  |
| productCategory | stockPickingTypeRel | product_category_stock_picking_type_rel | junction_array | derived | 7 | 0 | 0 | 0 | 0 | 0 |  |
| productCombo | item | product_combo_item | read_together | derived | 3 | 3 | 3 | 3 | 119 | 3 |  |
| productCombo | productTemplateRel | product_combo_product_template_rel | junction_array | derived | 3 | 1 | 1 | 1 | 8 | 1 |  |
| productProduct | customerProductReference | customer_product_reference | ownership | assumed | 47 | 0 | 0 | 0 | 0 | 0 |  |
| productProduct | uomUomRel | product_product_uom_uom_rel | junction_array | derived | 47 | 0 | 0 | 0 | 0 | 0 |  |
| productProduct | productUom | product_uom | read_together | derived | 47 | 0 | 0 | 0 | 0 | 0 |  |
| productProduct | productVariantCombination | product_variant_combination | junction_array | derived | 47 | 0 | 2 | 2 | 16 | 2 |  |
| productTag | productProductRel | product_tag_product_product_rel | junction_array | derived | 0 |  |  |  | 0 | 0 | yes |
| productTag | productTemplateRel | product_tag_product_template_rel | junction_array | derived | 0 |  |  |  | 0 | 0 | yes |
| productTemplate | productOptionalRel | product_optional_rel | junction_array | derived | 37 | 0 | 2 | 2 | 16 | 2 |  |
| productTemplate | attributeLine | product_template_attribute_line | read_together | derived | 37 | 0 | 2 | 2 | 90 | 2 |  |
| productTemplate | uomUomRel | product_template_uom_uom_rel | junction_array | derived | 37 | 0 | 0 | 0 | 0 | 0 |  |
| productTemplateAttributeValue | productTemplateAttributeExcludedValueIdsRel | product_template_attribute_excluded_value_ids_rel | junction_array | derived | 24 | 0 | 1 | 1 | 8 | 1 |  |
| productTemplateAttributeValue | purchaseOrderLineRel | product_template_attribute_value_purchase_order_line_rel | junction_array | derived | 24 | 0 | 0 | 0 | 0 | 0 |  |
| productTemplateAttributeValue | saleOrderLineRel | product_template_attribute_value_sale_order_line_rel | junction_array | derived | 24 | 0 | 0 | 0 | 0 | 0 |  |
| productTemplateAttributeValue | templateAttributeValueStockMoveRel | template_attribute_value_stock_move_rel | junction_array | derived | 24 | 0 | 0 | 0 | 0 | 0 |  |
| purchaseOrder | stockPickingRel | purchase_order_stock_picking_rel | junction_array | derived | 16 | 0 | 1 | 1 | 8 | 1 |  |
| purchaseOrderLine | accrualMoveRel | purchase_order_line_accrual_move_rel | junction_array | derived | 31 | 0 | 0 | 0 | 0 | 0 |  |
| saleOrder | tagRel | sale_order_tag_rel | ownership | derived | 24 | 0 | 2 | 2 | 16 | 2 |  |
| saleOrder | transactionRel | sale_order_transaction_rel | ownership | assumed | 24 | 0 | 0 | 0 | 0 | 0 |  |
| saleOrderLine | productAttributeCustomValue | product_attribute_custom_value | read_together | derived | 50 | 0 | 0 | 0 | 0 | 0 |  |
| saleOrderLine | accrualMoveRel | sale_order_line_accrual_move_rel | junction_array | derived | 50 | 0 | 0 | 0 | 0 | 0 |  |
| saleOrderLine | invoiceRel | sale_order_line_invoice_rel | junction_array | derived | 50 | 0 | 0 | 0 | 0 | 0 |  |
| saleOrderLine | stockRouteRel | sale_order_line_stock_route_rel | junction_array | derived | 50 | 0 | 0 | 0 | 0 | 0 |  |
| stockLocation | stockPickingTypeRel | stock_location_stock_picking_type_rel | junction_array | derived | 32 | 0 | 0 | 0 | 0 | 0 |  |
| stockMove | accountAnalyticLineStockMoveRel | account_analytic_line_stock_move_rel | ownership | assumed | 135 | 0 | 0 | 0 | 0 | 0 |  |
| stockMove | createdPurchaseLineRel | stock_move_created_purchase_line_rel | junction_array | derived | 135 | 0 | 0 | 0 | 0 | 0 |  |
| stockMove | moveRel | stock_move_move_rel | junction_array | derived | 135 | 0 | 0 | 0 | 0 | 0 |  |
| stockMove | stockScrapReasonTagRel | stock_move_stock_scrap_reason_tag_rel | junction_array | derived | 135 | 0 | 0 | 0 | 0 | 0 |  |
| stockMoveLine | consumeRel | stock_move_line_consume_rel | junction_array | derived | 103 | 0 | 0 | 0 | 0 | 0 |  |
| stockPackageHistory | stockPickingRel | stock_package_history_stock_picking_rel | junction_array | derived | 0 |  |  |  | 0 | 0 | yes |
| stockPackageType | stockPutawayRuleRel | stock_package_type_stock_putaway_rule_rel | junction_array | derived | 2 | 0 | 0 | 0 | 0 | 0 |  |
| stockPackageType | stockRouteRel | stock_package_type_stock_route_rel | junction_array | derived | 2 | 0 | 0 | 0 | 0 | 0 |  |
| stockPickingType | pickingTypeFavoriteUserRel | picking_type_favorite_user_rel | ownership | assumed | 16 | 0 | 0 | 0 | 0 | 0 |  |
| stockReference | moveRel | stock_reference_move_rel | junction_array | derived | 23 | 2 | 4 | 4 | 32 | 4 |  |
| stockReference | purchaseRel | stock_reference_purchase_rel | junction_array | derived | 23 | 0 | 1 | 1 | 8 | 1 |  |
| stockReference | saleRel | stock_reference_sale_rel | junction_array | derived | 23 | 1 | 1 | 1 | 8 | 1 |  |
| stockRoute | categ | stock_route_categ | junction_array | derived | 6 | 0 | 0 | 0 | 0 | 0 |  |
| stockRoute | move | stock_route_move | junction_array | derived | 6 | 0 | 0 | 0 | 0 | 0 |  |
| stockRoute | product | stock_route_product | junction_array | derived | 6 | 0 | 0 | 0 | 0 | 0 |  |
| stockRoute | warehouse | stock_route_warehouse | junction_array | derived | 6 | 1 | 2 | 2 | 16 | 2 |  |
| stockWarehouse | stockWhResupplyTable | stock_wh_resupply_table | junction_array | derived | 2 | 0 | 0 | 0 | 0 | 0 |  |

Policy: `max_embed_fanout` 1000, `max_doc_bytes` 2097152. Highest profiled max: 46; highest fixture max: 46.

## 8. Embeds the fixture does not exercise (manager note 4)

7 embeds have no parent rows in odoo_src, so neither the profile nor the fixture measures their fan-out; they are accepted on the schema rule alone and must be watched in the first live recon:

| collection | array | child table | rule | basis |
|---|---|---|---|---|
| accountCashRounding | resCurrencyRel | account_cash_rounding_res_currency_rel | ownership | assumed |
| accountCashRounding | resPartnerCategoryRel | account_cash_rounding_res_partner_category_rel | ownership | assumed |
| accountCashRounding | accountPaymentMethodLineRel | account_cash_rounding_account_payment_method_line_rel | junction_array | derived |
| accountPayment | accountBankStatementLineRel | account_payment_account_bank_statement_line_rel | junction_array | derived |
| productTag | productProductRel | product_tag_product_product_rel | junction_array | derived |
| productTag | productTemplateRel | product_tag_product_template_rel | junction_array | derived |
| stockPackageHistory | stockPickingRel | stock_package_history_stock_picking_rel | junction_array | derived |

## 9. Commands run

```
PLUGIN=/home/ubuntu/plugin-9a584b4 (git worktree of mongo-migration-plugin at 9a584b4)
.migration/fixtures/build_source.sh && .migration/fixtures/build_fixture.sh            # odoo_src, odoo_fixture on PG16:5433
docker compose -f $PLUGIN/skills/schema-modeling/docker-compose.local.yml up -d mongo   # local mongo:7
$PY $PLUGIN/skills/schema-modeling/model_patch.py --spec .migration/mapping_spec.json --answers .migration/answers.txt \
    --decisions .migration/design_decisions.json --out .migration/mapping_spec.json --version map-draft-2 \
    --data-profile .migration/data_profile.json --census .migration/census.json --access-patterns .migration/access_patterns.json
    -> refused (patch_attempt.map-draft-1.txt); .migration/rehearsal/scratch_draft2.sh rebuilds map-draft-2 (d-plugin-gap)
$PY $PLUGIN/skills/schema-modeling/model_patch.py --spec <spec> --data-profile ... --census ... --access-patterns ... --check
$PY .migration/rehearsal/load_fixture.py --spec <spec> --source-dsn-secret ODOO_PG_FIXTURE_DSN --target-uri-secret MONGO_LOCAL_URI --target-db odoo_unt12 --out <json>
recon run --unit <unit> --family postgresql --mapping <spec> --tolerances .migration/recon_tolerances.json \
    --canonicalization <postgresql profile recon_canonicalization rules> --mode fixture --source-dsn-secret ODOO_PG_FIXTURE_DSN \
    --target-uri-secret MONGO_LOCAL_URI --target-db odoo_unt12 --target-class local --allowed-targets-file .migration/allowed_targets.json --seed 1
python3 .migration/review_pack.py
```
`ODOO_PG_FIXTURE_DSN` is the `ODOO_PG_RO_DSN` JSON with `database` set to `odoo_fixture`, exported per shell; `MONGO_LOCAL_URI=mongodb://127.0.0.1:27017`. Secrets by name only. Nothing wrote to `odoo_src` or to Atlas.
