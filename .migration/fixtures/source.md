# Source fixture: `odoo_src`

Read-only legacy source for the run. Local PostgreSQL 16 cluster on port 5433
(the image's PG14 owns 5432), database `odoo_src`, Odoo 20.0 from this branch.

## Build

```sh
sudo pg_ctlcluster 16 main start
ODOO_PG_RO_DSN=... .migration/fixtures/build_source.sh   # secret ODOO_PG_RO_DSN
```

The script is idempotent. On a fresh VM it runs:

```sh
dropdb --if-exists odoo_src
/home/ubuntu/.venvs/odoo/bin/python odoo-bin --addons-path=addons,odoo/addons \
  -d odoo_src --db_port=5433 -i product,uom,sale,purchase,stock,account --with-demo --stop-after-init
/home/ubuntu/.venvs/odoo/bin/python odoo-bin shell --addons-path=addons,odoo/addons \
  -d odoo_src --db_port=5433 < .migration/fixtures/exercise_source.py
```

then (re)applies the `odoo_ro` role and grants and prints the row counts. When the
database already carries `ir_config_parameter` `migration.fixture_source = 2`
(`MARKER_VERSION` in the script) the install and exercise steps are skipped, so a
rerun changes nothing; an `odoo_src` built by the older product + uom fixture
(marker `1`) is dropped and rebuilt.

Odoo 20.0 installs without demo data by default, so `--with-demo` replaces the
`--without-demo=` form from the plan.

## Addons

Requested: `product`, `uom`, `sale`, `purchase`, `stock`, `account` (modeling scope;
the code migration scope stays `product` + `uom`). Installed with dependencies and
auto-installs (70 modules): account, account_edi_ubl_cii, account_payment,
account_qr_code_sepa, analytic, api_doc, auth_passkey, auth_passkey_portal, auth_signup,
auth_totp, auth_totp_mail, auth_totp_portal, barcodes, barcodes_gs1_nomenclature, base,
base_address_extended, base_import, base_import_module, base_install_request,
base_report_wkhtmltox, base_setup, bus, digest, google_gmail, html_editor, http_routing,
iap, iap_mail, l10n_us, l10n_us_account, mail, mail_bot, microsoft_outlook,
mysubscription, onboarding, partner_autocomplete, payment, phone_validation, portal,
portal_discuss, privacy_lookup, product, purchase, purchase_edi_ubl_bis3, purchase_stock,
resource, resource_mail, rpc, sale, sale_edi_ubl, sale_purchase, sale_purchase_stock,
sale_sms, sale_stock, sales_team, sms, spreadsheet, spreadsheet_account,
spreadsheet_dashboard, spreadsheet_dashboard_account, spreadsheet_dashboard_sale,
spreadsheet_dashboard_stock_account, stock, stock_account, stock_sms, uom, utm, web,
web_tour, web_unsplash.

## ORM flows (`exercise_source.py`)

Create a product category and a storable product template, change its price
(tracked), post a chatter message, change the price of demo product
`product_product_3`, archive demo product `product_product_9`, create a pricelist
with a fixed-price item. These fill `mail_message` with tracking and comment rows.

Then, on the fixture product: a purchase order from `base.res_partner_12` for 20
units, confirmed and its receipt validated (`stock_picking` done, `stock_move_line`
and `stock_quant` rows); a sale order to `base.res_partner_2` for 5 units, confirmed
(`sale.order` state `sale`, a delivery picking and its moves); the sale invoiced
through `_create_invoices()` and posted (`account_move` / `account_move_line`).
The script asserts each state before setting the marker.

## Read-only role

`odoo_ro`: LOGIN, NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOINHERIT,
`default_transaction_read_only = on`; CONNECT on `odoo_src`, USAGE on schema
`public`, SELECT on every table in `public`; CREATE on `public` revoked from
PUBLIC. Its DSN is the secret `ODOO_PG_RO_DSN` in the plugin's JSON PostgreSQL
secret shape (`{"user":"odoo_ro","password":"<password>","host":"localhost","port":5433,"database":"odoo_src"}`;
`parse_postgresql_secret` rejects `postgresql://` URLs); the script reads the
password from that secret, so every VM gets the same DSN.

## Row counts (fresh build; a rerun prints the same until someone writes to `odoo_src`)

| table | rows |
| --- | --- |
| product_template | 38 |
| product_product | 48 |
| product_category | 8 |
| uom_uom | 30 |
| sale_order | 25 |
| sale_order_line | 51 |
| purchase_order | 17 |
| purchase_order_line | 32 |
| stock_picking | 85 |
| stock_move | 137 |
| stock_move_line | 105 |
| stock_quant | 57 |
| account_move | 60 |
| account_move_line | 174 |
| mail_message | 1282 |
