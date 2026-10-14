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
  -d odoo_src --db_port=5433 -i product,uom --with-demo --stop-after-init
/home/ubuntu/.venvs/odoo/bin/python odoo-bin shell --addons-path=addons,odoo/addons \
  -d odoo_src --db_port=5433 < .migration/fixtures/exercise_source.py
```

then (re)applies the `odoo_ro` role and grants and prints the row counts. When the
database already carries `ir_config_parameter` `migration.fixture_source = 1` the
install and exercise steps are skipped, so a rerun changes nothing.

Odoo 20.0 installs without demo data by default, so `--with-demo` replaces the
`--without-demo=` form from the plan.

## Addons

Requested: `product`, `uom`. Installed with dependencies and auto-installs
(30 modules): api_doc, auth_passkey, auth_signup, auth_totp, auth_totp_mail, base,
base_import, base_import_module, base_install_request, base_report_wkhtmltox,
base_setup, bus, google_gmail, html_editor, iap, iap_mail, mail, mail_bot,
microsoft_outlook, mysubscription, partner_autocomplete, phone_validation,
privacy_lookup, product, rpc, sms, uom, web, web_tour, web_unsplash.

## ORM flows (`exercise_source.py`)

Create a product category and a product template, change its price (tracked),
post a chatter message, change the price of demo product `product_product_3`,
archive demo product `product_product_9`, create a pricelist with a fixed-price
item. These fill `mail_message` with tracking and comment rows.

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
| product_template | 35 |
| product_product | 45 |
| product_category | 8 |
| uom_uom | 30 |
| mail_message | 322 |
