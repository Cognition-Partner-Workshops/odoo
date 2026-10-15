# Cross-addon dependency register — slice `product + uom`

Source of truth for this register is the ticket "Register cross-addon dependencies" on the
board; this file is the cited-evidence copy. Scope: the 33 `migrate` tables in
`.migration/table_buckets.json` (owners `product`, `uom`). Evidence was gathered read-only
from the `odoo_src` fixture (`.migration/fixtures/build_source.sh`, 70 installed modules,
Odoo 20.0) plus the addon sources under `addons/`.

Decision this register depends on (manager to confirm): the Mongo-backed ORM storage
path **keeps the PostgreSQL integer `id` as the document key** and leaves an id-only
shadow of each slice table in PostgreSQL during coexistence. Every disposition marked
`D1` or `D4` below relies on that; without it 53 FK columns and 3 SQL views break.

## Disposition codes

| code | meaning |
|------|---------|
| D1 `keep-fk-via-id-shadow` | out-of-scope table keeps its integer FK to a slice table; FK stays valid against the id shadow, join semantics move to the ORM |
| D2 `field-travels-with-document` | column/field added to a slice model by another addon; stored in the Mongo document (storage path must honour fields registered by any module, incl. company-dependent JSONB) |
| D3 `reference-out` | Many2one from a slice table to a `shared_postgresql`/`orm_framework` table; stored as integer reference, never embedded |
| D4 `framework-stays-pg` | `ir_*`/`mail_*` rows keyed `(model, res_id)` stay in PostgreSQL; need id preservation only |
| D5 `orm-write-routed` | out-of-scope code writes slice data through the ORM only; works unchanged once the storage path is in; add to recon scenarios |
| D6 `sql-reader-rewrite` | raw SQL / `_auto = False` reader joins slice tables; needs rewrite to ORM read or a full (not id-only) shadow |
| D7 `none-empty-or-uninstalled` | 0 rows in fixture and/or owning addon not installed; register only, no work this run |

## A. Out-of-scope tables that join to slice tables (inbound FKs, 36 tables / 53 columns)

Query: `pg_constraint contype='f'` where `confrelid` ∈ slice and `conrelid` ∉ slice;
buckets/owners from `.migration/table_buckets.json`.

| owner (bucket) | table | FK columns → slice table | rows | disp. |
|---|---|---|---|---|
| account (model_only) | account_move_line | product_id→product_product, product_uom_id→uom_uom | 174 | D1 |
| account (model_only) | product_taxes_rel | prod_id→product_template (m2m `product.template.taxes_id`, `addons/account/models/product.py`) | 74 | D1 |
| account (model_only) | product_supplier_taxes_rel | prod_id→product_template (`supplier_taxes_id`) | 74 | D1 |
| account (model_only) | account_account_tag_product_template_rel | product_template_id→product_template | 0 | D7 |
| account (model_only) | account_analytic_applicability | product_categ_id→product_category | 1 | D1 |
| account (model_only) | account_analytic_distribution_model | product_categ_id, product_id | 0 | D7 |
| analytic (shared_pg) | account_analytic_line | product_id, product_uom_id | 0 | D7 |
| barcodes (shared_pg) | barcode_rule | associated_uom_id→uom_uom | 34 | D1 |
| sale_edi_ubl (shared_pg) | customer_product_reference | product_id→product_product | 0 | D7 |
| account_payment (shared_pg) | payment_provider_product_pricelist_rel | product_pricelist_id→product_pricelist | 0 | D7 |
| sale (model_only) | sale_order | pricelist_id→product_pricelist | 25 | D1 |
| sale (model_only) | sale_order_line | product_id, product_uom_id, section_uom_id→uom_uom, combo_item_id→product_combo_item | 51 | D1 |
| sale (model_only) | product_optional_rel | src_id/dest_id→product_template (`optional_product_ids`, `addons/sale/models/product_template.py`) | 3 | D1 |
| sale (model_only) | product_template_attribute_value_sale_order_line_rel | →product_template_attribute_value | 0 | D7 |
| purchase (model_only) | purchase_order_line | product_id, uom_id | 32 | D1 |
| purchase (model_only) | product_template_attribute_value_purchase_order_line_rel | →product_template_attribute_value | 0 | D7 |
| purchase_stock (shared_pg) | product_supplierinfo_stock_replenishment_info_rel | →product_supplierinfo | 0 | D7 |
| stock (model_only) | stock_move | product_id, uom_id, packaging_uom_id→uom_uom | 137 | D1 |
| stock (model_only) | stock_move_line | product_id, uom_id | 105 | D1 |
| stock (model_only) | stock_quant | product_id | 57 | D1 |
| stock (model_only) | stock_lot | product_id | 4 | D1 |
| stock (model_only) | stock_warehouse_orderpoint | product_id, replenishment_uom_id, supplier_id→product_supplierinfo | 5 | D1 |
| stock (model_only) | stock_putaway_rule, stock_storage_category_capacity, stock_replenishment_option, stock_warn_insufficient_qty_scrap, product_replenish, stock_rules_report | product/category/supplierinfo/uom FKs | 0 each | D7 (transient wizards / empty) |
| stock (model_only) | stock_route_product, stock_route_categ, product_category_stock_picking_type_rel, product_label_layout_stock_move_rel, template_attribute_value_stock_move_rel | m2m rel tables | 0 each | D7 |
| stock_account (shared_pg) | product_value | product_id→product_product | 7 | D1 |
| base (shared_pg) | res_company | sale_discount_product_id→product_product (added by `sale`, `addons/sale/models/res_company.py`) | 3 | D1 |

Addons present in `addons/` but **not installed** in the fixture (no tables, no rows):
`website_sale`, `point_of_sale`, `mrp`, `event_sale`, `repair`, `sale_loyalty`,
`stock_landed_costs`, `purchase_requisition`, `sale_margin` … — all `_inherit`
`product.template`/`product.product`/`uom.uom` (e.g. `addons/website_sale/models/product_template.py`,
`addons/point_of_sale/models/product_product.py`, `addons/mrp/models/product.py`).
Disposition D7 now; any later install registers new D2 fields and D1 FKs and must re-run
this register.

## B. Many2one columns pointing out of the slice (outbound FKs, 58 columns)

| target (bucket) | slice columns | disp. |
|---|---|---|
| res_users (shared_pg) | `create_uid`/`write_uid` on all 33 tables (44 cols) + `product_template.responsible_id` (company-dependent JSONB, added by `stock`) | D3 — audit refs; `responsible_id` is D2+D3 |
| res_company (shared_pg) | product_category, product_combo, product_combo_item, product_pricelist, product_pricelist_item, product_supplierinfo, product_template, product_uom `.company_id` | D3 |
| res_partner (shared_pg) | product_supplierinfo.partner_id | D3 |
| res_currency (shared_pg) | product_pricelist, product_pricelist_item, product_supplierinfo `.currency_id` | D3 |
| res_country_group (shared_pg) | res_country_group_pricelist_rel.res_country_group_id | D3 (rel table is slice-owned, migrates as array of ids) |
| ir_attachment (orm_framework) | product_document.ir_attachment_id (`_inherits`, `addons/product/models/product_document.py:11-13`) | D3+D4 — delegation inheritance: document stays in PG, `product.document` holds the id |
| ir_sequence (orm_framework) | product_template.lot_sequence_id | D3 |
| product_removal (model_only, stock) | product_category.removal_strategy_id (field added by `stock`) | D2+D3 — reference into a model-only addon |
| stock_package_type (model_only, stock) | uom_uom.package_type_id | D2+D3 |
| sale_order_line (model_only, sale) | product_attribute_custom_value.sale_order_line_id (`addons/sale/models/product_attribute_custom_value.py`) | D2+D3 — reverse dependency: slice row points into sale |

## C. Stored fields added to slice models by other modules (`ir_model_fields` ⋈ `ir_model_data`, 54 fields excl. `id` = 47 document fields D2 + 7 One2many inverses D1; `*` = company-dependent JSONB)

| module | fields | disp. |
|---|---|---|
| account | product.category: property_account_expense_categ_id*, property_account_income_categ_id*, property_cost_method*, property_price_difference_account_id*, property_stock_journal*, property_stock_valuation_account_id*, property_valuation*; product.template: property_account_expense_id*, property_account_income_id*, taxes_id, supplier_taxes_id, account_tag_ids (`addons/account/models/product.py`) | D2 (m2m rel tables are D1, see A) |
| stock | product.category: packaging_reserve_method, removal_strategy_id, route_ids; product.template: tracking, responsible_id*, property_stock_inventory*, property_stock_production*, description_picking, description_pickingin, description_pickingout, route_ids, lot_sequence_id; product.product: lot_properties_definition; product.label.layout: move_ids, move_quantity, print_packaging; uom.uom.package_type_id (`addons/stock/models/product.py`, `addons/stock/models/product_strategy.py`) | D2 |
| stock (one2many) | product.category.putaway_rule_ids; product.product: orderpoint_ids, putaway_rule_ids, stock_move_ids, stock_quant_ids, storage_category_capacity_ids — not document fields; the inverse FK lives on the stock table (see A) | D1 |
| stock_account | product.template.lot_valuated, product.category.property_cost_method* (override of the `account` field, `addons/stock_account/models/product.py`) | D2 |
| sale | product.template: invoice_policy, reinvoice_policy, service_type, sale_delay*, optional_product_ids, sale_line_warn_msg (`addons/sale/models/product_template.py`); product.category: property_account_invoiced_not_delivered_id*, property_account_invoices_to_issue_id*; product.document.attached_on_sale; product.attribute.custom.value.sale_order_line_id | D2 |
| purchase | product.template: purchase_method, purchase_line_warn_msg; product.category: property_account_billed_not_received_id*, property_account_bills_to_receive_id* (`addons/purchase/models/product.py`) | D2 |
| purchase_stock | product.product.purchase_order_line_ids (one2many, inverse on purchase_order_line) | D1 |
| sale_purchase | product.template.service_tracking | D2 |
| account_edi_ubl_cii | uom.uom.unece_code | D2 |

17 distinct foreign fields are `company_dependent=True` (18 registrations: `property_cost_method` is
declared by `account` and re-declared by `stock_account`) and are physically JSONB columns in
PostgreSQL; with `product`'s own `standard_price` and `qty_available` that is 19 company-dependent
fields on the slice. 37 JSONB columns on slice tables in total; the rest are translated
`name`/`description*` and `properties`/`properties_definition`. There is **no `ir_property` and no
`ir_translation` table** in Odoo 20: both live inside the row as JSONB, so they travel
with the document (D2) — nothing to join.

## D. Out-of-scope code that writes slice data (installed addons, ORM only — no raw SQL writer found)

| writer | what it writes | disp. |
|---|---|---|
| `addons/stock_account/models/product.py:194-247` `_change_standard_price`, `:727-747` | `product.product.standard_price` (company-dependent JSONB), `product.template.lot_valuated`; triggered from `res.company._cron_post_stock_valuation` (cron, see F) and stock moves | D5 |
| `addons/stock_account/models/stock_lot.py:64-83` | mirrors `standard_price` from product to lot | D5 (reads) |
| `addons/stock/models/product.py:1054-1061` `_set_store_by` | `product.template.is_storable`, `tracking` | D5 |
| `addons/account/models/product.py:307-311` `write` | clears `taxes_id`/`supplier_taxes_id` on combo products | D5 |
| `addons/purchase/models/res_partner.py:66` | `product.supplierinfo.currency_id` when a partner changes currency | D5 |
| `addons/purchase_stock/models/stock_rule.py:185,375`, `addons/purchase/models/purchase_order_line.py:342` | read `product.supplierinfo` for procurement | D5 (reads) |
| `ir_model_data` rows owned by `sale` (4) and `stock` (6) for product/uom records | demo/data XML from other addons creating slice rows | D4 |

## E. `_auto = False` SQL readers of slice tables

PostgreSQL views in the fixture (3 of 5 touch the slice):

| view / model | source | joins | disp. |
|---|---|---|---|
| report_stock_quantity | `addons/stock/report/report_stock_quantity.py:9,36` | product_product, product_template, uom_uom | D6 |
| stock_avco_report | `addons/stock_account/report/stock_avco_audit_report.py:6,36` | product_product, product_template, product_category, uom_uom | D6 |
| vendor_delay_report | `addons/purchase_stock/report/vendor_delay_report.py:11,21` | product_product, product_template, product_category, uom_uom | D6 |

`_table_query` reports (not materialised as PG views, executed as subqueries at read time;
join slice tables through `product_id`/`product_uom_id` on their own lines):
`addons/sale/report/sale_report.py:14`, `addons/purchase/report/purchase_report.py:15`,
`addons/account/report/account_invoice_report.py:11` — D6.
`addons/purchase/models/purchase_bill_line_match.py:12,119-150` is also `_auto = False` but only
selects `product_id` from purchase_order_line/account_move_line without joining a slice table — D1.
Not-installed addons with the
same pattern: `addons/event_sale/report/event_sale_report.py`,
`addons/point_of_sale/report/pos_order_report.py` — D7.

Raw SQL in out-of-scope addons that reads/writes slice tables directly (bypasses the ORM):

| code | SQL | disp. |
|---|---|---|
| `addons/account/models/product.py:243-258` `_check_uom_not_in_invoice` (constraint on `uom_id`) | joins account_move_line → product_product → product_template → uom_uom | D6 — must become an ORM read (search on account.move.line) or needs a full shadow; runs on every uom change |
| `addons/stock/__init__.py:46,83-92` `_create_inventory_adjustment` (post-init / uninstall hooks) | `SELECT id, qty_available FROM product_product`, `UPDATE product_product SET qty_available = …::jsonb` | D6 — lifecycle only (install/uninstall of `stock`); not exercised during the run, but blocks (un)installing `stock` on a Mongo-backed slice |

In-scope raw SQL inside the slice itself (`addons/product/models/product_template.py:403,413,969`,
`product_product.py:1134-1141`, `product_combo.py:55`) is the storage-path ticket's problem,
listed here only so it is not lost.

## F. Framework rows (`ir_*`, `mail_*`) keyed to slice records

| table | rows for slice models | disp. |
|---|---|---|
| ir_model_data | product=260, uom=30, sale=4, stock=6 (xmlids of slice records) | D4 |
| ir_attachment | product.template=156, product.product=46, product.attribute.value=8 (images via `image.mixin`, `addons/product/models/product_template.py`, `product_product.py`) | D4 |
| mail_message | product.template=123, product.product=99, product.category=8, product.pricelist=1 (`mail.thread`/`mail.activity.mixin`) | D4 |
| mail_followers / mail_activity | 0 | D7 |
| ir_default | 12 defaults on `product.category.property_*` and `product.template.property_stock_*` | D4 |
| ir_sequence | product_template.lot_sequence_id reference | D3 |
| triggers on slice tables | 0 user-defined | — |

## G. Scheduled jobs (`ir_cron` → `ir_act_server.model_id`, 25 jobs)

No cron targets a `product.*` or `uom.*` model. Indirect readers/writers of slice data:

| cron | model | effect on slice | disp. |
|---|---|---|---|
| Account: Inventory Valuation Closing | res.company `_cron_post_stock_valuation` | reads `standard_price`/cost method, may call `_change_standard_price` (D above) | D5 |
| Procurement: run scheduler | stock.rule `run_scheduler` | reads product routes, supplierinfo, uom; writes stock_move/orderpoint (D1 tables) | D5 |
| Purchase reminder | purchase.order | reads product names/uom | D5 |
| Account: Post draft entries / Send invoices | account.move | reads product, taxes, uom | D5 |
| Base: Auto-vacuum | ir.autovacuum | GCs `ir_attachment`/`mail_*` rows incl. those keyed to slice records | D4 |
| remaining 19 (mail, discuss, digest, payment, sms, resource, users, publisher_warranty) | — | no slice access | — |

## Summary for the plan

- 53 inbound FK columns from 36 out-of-scope tables → D1 (keep integer ids, id-shadow in PG).
- 58 outbound Many2one columns → D3 references; 2 point *into* model-only addons (sale/stock).
- 54 foreign-module stored fields: 47 are document fields (17 company-dependent) + 37 JSONB columns → D2, must be honoured by the ORM storage path; the other 7 are One2many inverses whose FK lives on a stock/purchase table → D1.
- 5 ORM writers in stock_account/stock/account/purchase → D5, add to recon scenarios.
- 3 PG views + 3 `_table_query` reports + 2 raw-SQL paths (account uom constraint, stock lifecycle hooks) → D6, rewrite or full shadow.
- ~530 `ir_model_data`/`ir_attachment`/`mail_message`/`ir_default` rows → D4.
- 0 direct crons; 4 indirect → D5. 0 triggers.

## H. Units and wave proposal (`units.json`)

Derived from `map-draft-5` as accepted (no remodeling). Unit = the addon models that opt in to `_storage = "mongodb"`, their stored computed/related fields and raw SQL, plus the collections and spec arrays they own; every relation table in the `migrate` bucket is assigned to the unit owning the array that absorbs it (33 tables, each exactly once; 20 collections). `model_only` collections are never units — they appear per unit under `cross_boundary` (D1–D7 codes from this register). Machine-readable detail per unit (models, tables, write targets, fixture rows, raw SQL dispositions, cross-boundary lists, recon risks, depends_on) is in `units.json`.

| unit | depth | models (`_storage` opt-in) | collections | owned relation tables | raw SQL / views | §D arrays (recon risk) |
|---|---|---|---|---|---|---|
| `uom` | 0 | uom.uom | uomUom | — | none in addons/uom; S: `_check_uom_not_in_invoice`, 3 views read `factor` | 0 |
| `product-taxonomy` | 0 | product.category, product.tag, product.base.unit | productCategory, productTag, productBaseUnit | — | S: stock_avco_report reads `property_cost_method` | 1 (`productCategory.routeIds`, stock-owned) |
| `product-attributes` | 0 | product.attribute, product.attribute.value, update.product.attribute.value | productAttribute, productAttributeValue, updateProductAttributeValue | product_attribute_product_template_rel | — | 1 |
| `product-catalog` | 1 | product.template + product.product (`_inherits`), product.template.attribute.line, product.template.attribute.value, product.document, product.uom | productTemplate, productProduct, productTemplateAttributeLine, productTemplateAttributeValue, productDocument, productUom | product_variant_combination, product_product_uom_uom_rel, product_tag_product_product_rel, product_tag_product_template_rel, product_template_uom_uom_rel, product_combo_product_template_rel, product_attribute_value_product_template_attribute_line_rel, product_template_attribute_excluded_value_ids_rel | R: product_template.py:102,108,401-413 (`_compute_sql` currency), 960-975 (`_search_display_name` UNION); product_product.py:185-201 (`_search_is_in_catalog_order` subselect), 1128-1145 (UNION + supplierinfo subselect). S: 3 views, 3 `_table_query` reports. B: stock install/uninstall hook (`addons/stock/__init__.py:46,83-92`, operational block at cutover) | 12 (4 of them account/sale/stock-owned) |
| `product-pricing` | 2 | product.pricelist, product.pricelist.item | productPricelist, productPricelistItem | res_country_group_pricelist_rel | — | 1 |
| `product-supplierinfo` | 2 | product.supplierinfo | productSupplierinfo | — | R (ported in catalog): product_product.py:1134-1145 subselect; S: vendor_delay_report | 0 |
| `product-combo` | 2 | product.combo, product.combo.item | productCombo, productComboItem | — | R: product_combo.py:22,53-55 (`_compute_sql` currency) | 0 |
| `product-variant-extras` | 2 | product.attribute.custom.value, product.label.layout | productAttributeCustomValue, productLabelLayout | product_label_layout_product_{product,template,uom}_rel | — | 4 (1 stock-owned) |

Waves (width 4, one dependency depth per wave, unique write targets; all units depend on the ORM storage-path ticket):

| wave | batches | preflight (pinned `wave-preflight/preflight.py`) |
|---|---|---|
| 1 | w1-b01 `uom`, w1-b02 `product-taxonomy`, w1-b03 `product-attributes` | `wave 1 OK: 3 batches, manifest_sha ea9f6b868dc7` |
| 2 | w2-b01 `product-catalog` (alone by design: every depth-2 unit references it, and it carries all R rewrites and both full-shadow tables) | `wave 2 OK: 1 batches, manifest_sha 0b73271c13bf` |
| 3 | w3-b01 `product-pricing`, w3-b02 `product-supplierinfo`, w3-b03 `product-combo`, w3-b04 `product-variant-extras` | `wave 3 OK: 4 batches, manifest_sha 3548af4a78e1`; negative control (w3-b02 claiming w3-b01 targets) → exit 1 write-target collision |

Wave specs are scratch files for the launcher (not committed; `units.json` `waves[].batches` is the source). Open items carried to the storage-path ticket / manager, not decided here: (1) seven spec arrays on slice documents absorb relation tables whose declaring side is `model_only` (D1) — `productTemplate.{accountTagIds,taxesId,supplierTaxesId,optionalProductIds,routeIds}`, `productCategory.routeIds`, `productLabelLayout.moveIds` — runtime writes keep landing in the PG relation table, so strict recon on them is point-in-time only; (2) the fixture has 0 rows in 11 of the 33 tables (per unit under `recon_risks.fixture_zero_rows`), so strict recon there is schema-only until the unit run adds scenario rows.
