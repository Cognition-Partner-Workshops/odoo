# UNT14-12 ORM conformance sweep

Odoo's own tests for the six scope addons and every installed bridge, one addon per run, on
PostgreSQL storage (baseline) and MongoDB storage. Base `mongo-run/unt13` at 66e6ff7, plugin
24191871106bd7bf9c15f3cea31980bc05b37f19, signed spec f372de32…5c50. Local evidence, not merge evidence.

## How it ran

- Every run used a fresh `createdb -T` copy of a template cloned from `odoo_fixture` (never `odoo_src`),
  then `odoo-bin -u <addon> --test-enable --test-tags /<addon> --stop-after-init` on that copy, one process at a time.
- MongoDB: local `mongo:7` on localhost, database `odoo_unt13`, each copy in its own `<copy>__` collection prefix.
  Every model whose table the signed spec maps (76 models, 71 collections, 22,757 documents seeded from the
  copy's own rows through the storage path's encoders) was opted in to `_storage = 'mongodb'` by an uncommitted
  local hook. No unit ticket has opted models in yet, so this is the only way to exercise the path end to end.
- The strict layout (PostgreSQL keeps only ids) cannot load the registry at all (U1 below). The Mongo column
  therefore ran with every stored column also mirrored to PostgreSQL as a shadow column, so raw SQL still works
  and the failures isolate the ORM-to-MongoDB path.
- On MongoDB most failures are `setUpClass` errors, which abort a whole test class before it counts any test,
  so the Mongo "run" counts are far below the PostgreSQL ones. Gap G2 alone hides most suites.

## Pass/fail per addon

| Addon | PostgreSQL | MongoDB | Mongo failures by class |
|---|---|---|---|
| uom | FAIL 0 run, 0 fail, 1 err | FAIL 0 run, 0 fail, 1 err | also-pg 1 |
| product | FAIL 155 run, 1 fail, 0 err | FAIL 28 run, 5 fail, 42 err | G1 24, G2 19, G3 2, also-pg 1, other 1 |
| account | FAIL 1154 run, 2 fail, 5 err | FAIL 43 run, 0 fail, 84 err | G2 80, G5 2, also-pg 2 |
| purchase | FAIL 124 run, 1 fail, 0 err | FAIL 2 run, 1 fail, 14 err | G1 2, G2 11, also-pg 1, other 1 |
| stock | FAIL 703 run, 8 fail, 6 err | FAIL 11 run, 0 fail, 47 err | G1 1, G2 32, G3 8, G4 3, G6 2, also-pg 1 |
| sale | FAIL 293 run, 1 fail, 0 err | FAIL 12 run, 2 fail, 37 err | G1 3, G2 33, also-pg 1, other 2 |
| stock_account | pass 240 run, 0 fail, 0 err | FAIL 0 run, 0 fail, 10 err | G2 10 |
| purchase_stock | FAIL 231 run, 1 fail, 2 err | FAIL 40 run, 1 fail, 25 err | G2 19, G3 1, G6 6 |
| sale_stock | FAIL 178 run, 1 fail, 0 err | FAIL 1 run, 0 fail, 17 err | G2 15, G3 2 |
| sale_purchase | pass 13 run, 0 fail, 0 err | FAIL 0 run, 0 fail, 2 err | G2 2 |
| sale_purchase_stock | pass 24 run, 0 fail, 0 err | FAIL 0 run, 0 fail, 4 err | G2 2, G3 2 |
| account_payment | FAIL 31 run, 0 fail, 1 err | FAIL 0 run, 0 fail, 3 err | G2 3 |
| account_edi_ubl_cii | FAIL 227 run, 2 fail, 1 err | FAIL 0 run, 0 fail, 35 err | G2 35 |
| account_qr_code_sepa | FAIL 4 run, 0 fail, 3 err | FAIL 0 run, 0 fail, 1 err | G2 1 |
| sale_edi_ubl | pass 1 run, 0 fail, 0 err | FAIL 0 run, 0 fail, 1 err | G2 1 |
| purchase_edi_ubl_bis3 | pass 5 run, 0 fail, 0 err | FAIL 0 run, 0 fail, 2 err | G2 2 |
| l10n_us_account | pass 0 run, 0 fail, 0 err | pass 0 run, 0 fail, 0 err | - |
| sale_sms | pass 0 run, 0 fail, 0 err | pass 0 run, 0 fail, 0 err | - |
| stock_sms | pass 0 run, 0 fail, 0 err | pass 0 run, 0 fail, 0 err | - |

Totals: PostgreSQL 3,383 tests run, 36 fail or error (17 fail, 19 error). MongoDB 137 tests run, 334 fail or error:
327 storage-path (G1-G6 and 4 not isolated), 7 also fail on PostgreSQL, 0 unit-specific in the mirrored run.

## Storage-path gaps (for the storage-path owner; manager routes)

Repro: `odoo-bin shell` on a seeded MongoDB copy. Each repro line was run: it raises on the MongoDB copy and the G1, G2, G4, G5, G7 lines pass on the PostgreSQL copy.

| Gap | Count | Where it breaks | Example test | Minimal repro |
|---|---|---|---|---|
| G2 | 265 | `storage_mongodb.py:1422` `_many2many_condition`: `('country_group_ids', 'not any!', Query)` cannot run on MongoDB storage. Raised by every pricelist lookup, so most `setUpClass` die. | `setUpClass (account.tests.test_kpi_provider.TestKpiProvider)` | `env['product.pricelist'].search([('country_group_ids', '=', False)])` |
| G1 | 30 | `storage_mongodb.py:1275` `_translated_expr`: `KeyError: 'name'` ordering/searching `product.product` by the translated `name` it inherits from `product.template`. Also breaks product imports. | `product.tests.test_import_files.TestImportFiles.test_import_create_product_template_xls` | `env['product.product'].search([], order='name', limit=1)` |
| G3 | 15 | `storage_mongodb.py:1376` `_condition`: a condition whose value is raw `SQL` (`location_id child_of` recursive CTE in stock, `id any! SQL(...)` from product name search) cannot run on MongoDB storage. | `setUpClass (stock.tests.test_inventory.TestInventory)` | `env['product.product'].search([('is_storable', '=', True)], limit=1, order='id').qty_available` |
| G6 | 8 | `NotNullViolation` on mirrored `product_template.invoice_policy` when stock or purchase_stock tests create products before `sale` is loaded. Seen only with the full mirror, may be a harness artifact. | `setUpClass (stock.tests.test_proc_rule.TestProcRule)` | run `stock` tests on a mirrored copy |
| G4 | 3 | `storage_mongodb.py:1302` `_sort_stages`: cannot order by a non-stored field (`stock.picking.type` `is_favorite desc`, `product.document` `name`). | `stock.tests.test_picking_tours.TestStockPickingTour.test_generate_serial_1` | `env['stock.picking.type'].search([], order='is_favorite desc')` |
| G5 | 2 | `storage_mongodb.py:1383` `_condition`: `account.account` `('code', 'not in', [False])` (company-dependent field). | `account.tests.test_sequence.TestSequenceMixinConcurrency.test_sequence_concurency` | `env['account.account'].search([('code', 'not in', [False])])` |
| G7 | not counted | `domains.py:1112`: `display_name in [...]` on `product.template` unsupported, only under MongoDB storage. Found while isolating G1; its tests are counted under G1-G3. | - | `env['product.template'].search([('display_name', 'in', ['x'])])` |
| not isolated | 4 | Two product-catalog tours never become ready, one portal signature tour misses a filestore file, one import subtest. Probably fallout of G1/G2. | `sale.tests.test_sale_product_catalog...test_add_section_from_product_catalog_on_sale_order_tour` | rerun once G1/G2 are fixed |

## Unit-specific

- U1 (stock): with PostgreSQL keeping only ids, `-u` of the scope fails to load the registry:
  `report_stock_quantity` (`addons/stock/report/report_stock_quantity.py:194`) is a SQL view reading
  `stock_location.parent_path`, which is not a shadow column. The stock unit must declare the shadow columns its
  SQL views read. Only the first such view is observed; later ones are hidden behind it.
- No other unit-specific failures in the mirrored run.

## Also fail on PostgreSQL (not migration issues)

Environment: no wkhtmltopdf (PDF tests), clone databases without a filestore copy, and tests that run while
later modules are not loaded yet (`uom` `setUpClass`: `res_partner.autopost_bills` NOT NULL).
- uom: `setUpClass (TestUom)`
- product: `TestImportFiles.test_import_create_product_demo_xls [product.pricelist]`
- account: `test_invoice_report_without_invoice_date`, `test_audit_trail_attachment`, `test_audit_trail_write_attachment`, `setUpClass (TestAccountDigest)`, `setUpClass (TestKpiProvider)`, `test_compute_account_type_on_code_change`, `test_journal_sequence_format`
- purchase: `test_import_requests_for_quotation_template_xlsx`
- stock: `test_batch_validation_without_backorder`, `test_same_package_several_pickings`, `test_reordering_rule_3`, `test_replenishment_order_to_max`, `test_relocate`, `test_modified_global_route`, `test_cyclic_inventory`, `test_orderpoint_warning`, `test_reordering_rule_1`, `test_report_forecast_11_non_reserved_order`, `test_report_quantity_1..3`, `test_inventory_adjustment_apply_all`
- sale: `test_import_quotation_template_xlsx`
- purchase_stock: `test_vendor_delay_report_with_multi_location`, `test_2steps_and_partner_on_orderpoint`, `test_product_replenish_wizard_multiple_buy_routes`
- sale_stock: `test_download_label_logs_chatter_message`
- account_payment: `test_generate_and_send_invoice_with_qr_code`
- account_edi_ubl_cii: `test_invoice_deferred_dates`, `test_generate_pdf_when_xml_does_not_provide_one`, `test_import_invoice_auto_generate_pdf`
- account_qr_code_sepa: `test_out_invoice_create_refund_qr_code`, `test_sepa_qr_code_detection`, `test_sepa_qr_code_generation`

## Plugin findings

- P1 `hooks/mongo_guard.py:95` (`DB_NAME`): the short `-d` alternative reads the PostgreSQL database argument of
  `odoo-bin` as a MongoDB database whenever the same command text also names the Python Mongo driver and a write
  verb. Repro: one Bash command that writes a driver script naming only `odoo_unt13` and also runs `odoo-bin` with
  `-d` set to a scratch PostgreSQL copy is refused as "not in the committed allowed_targets databases"; the same
  two steps as separate commands pass. False positive: no write went outside `odoo_unt13`.
