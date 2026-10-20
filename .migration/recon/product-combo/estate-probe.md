# w3-b03 estate probe (product-combo)

Pre-opt-in baseline: `odoo_w3b03_src` = `createdb -T odoo_src` + the merged `seed_scenario_rows.py` through the
`odoo-base` (SOURCE_COMMIT 03a3cb561ac, PostgreSQL storage) shell. Reader counts from that shell
(`search_count([])`, `estate-readers.baseline.txt`):

| reader | pre-opt-in |
|---|---|
| sale.report | 51 |
| purchase.report | 32 |
| account.invoice.report | 62 |
| purchase.bill.line.match | 27 |
| report.stock.quantity | 5263 (date-window view; wave 2 saw 5268 on 2026-10-19) |
| stock.avco.report | 7 |
| vendor.delay.report | 10 |

## `-u product,sale` on the full-estate clone at run-branch tip 3c87755: PASS, readers 7/7 equal

Run in a fresh session after plugin PR #111 (guard fix, `_repo_root` reads the policy from the checkout the command
runs in). Every Mongo write below ran from `/home/ubuntu/repos/odoo` with `origin/HEAD` -> `mongo-run/20261014`; the
hook allowed them (the earlier refusal, recorded in commit 49dbcd8, is resolved and no longer an open gap).

Recipe (`estate-readers.log`, `estate-update.log`, `estate-precopy.py`, `estate-readers.py`, `estate-unprefixed-digest.py`):

0. `python estate-unprefixed-digest.py` took a content digest of the 15 unprefixed collections (count + sha256 over the
   canonical extended JSON of every document sorted by `_id`; `DIGEST-BEFORE` lines).
1. `createdb -T odoo_w3b03_src odoo_w3b03_estate`; conf `mongodb_migration_db = odoo_migration`, so the clone's
   namespace is `odoo_w3b03_estate__*`.
2. `python estate-precopy.py odoo_w3b03_estate` copied the 15 unprefixed collections of waves 1-3 (13 + `productCombo`,
   `productComboItem`) into that namespace, counts equal on both sides (`PRECOPY` lines).
3. `odoo-bin -c estate.conf -d odoo_w3b03_estate -u product,sale --stop-after-init`: exit 0 in 58.4 s, the update log
   holds only the known `unknown option 'mongodb_migration_db'` config warning (0 ERROR / Traceback lines).
4. `odoo-bin shell ... < estate-readers.py` on the opted-in clone; the same seven counts from the `odoo-base` shell on
   `odoo_w3b03_src` the same day (`estate-readers.baseline.txt`).

| reader | pre-opt-in (`odoo_w3b03_src`) | opted-in (`odoo_w3b03_estate`) |
|---|---|---|
| sale.report | 51 | 51 |
| purchase.report | 32 | 32 |
| account.invoice.report | 62 | 62 |
| purchase.bill.line.match | 27 | 27 |
| report.stock.quantity | 5263 | 5263 (same day) |
| stock.avco.report | 7 | 7 |
| vendor.delay.report | 10 | 10 |

On the opted-in clone `product.combo` reads 4 ORM rows / 4 documents and `product.combo.item` 10 / 10 from the prefixed
namespace (`STORE prefix 'odoo_w3b03_estate__'`); the shadow tables carry the declared `_shadow_columns`
(`product_combo`: `company_id`, `name`, `sequence`; `product_combo_item`: `company_id`, `combo_id`, `product_id`,
`extra_price`) and the four seeded combos read back with their company, currency, item count and base price
(`COMBOS` line). The 15 unprefixed collections are unchanged after the run by count **and content**: the digest taken again after the
readers is byte-identical to the one taken before the pre-copy (`UNPREFIXED ... unchanged` lines,
`estate-unprefixed.digest.json`), so the run neither added, removed nor edited a document outside the clone's namespace.
None of the seven readers reads `product_combo` / `product_combo_item` in SQL (no D6 reader for the unit). The
`odoo_w3b03_estate__*` collections were dropped after the run (session-owned scratch namespace; Atlas collection cap).

## Combo readers on a fresh opted-in database (not blocked)

`createdb odoo_w3b03_sale` + `-i sale --test-enable --test-tags /sale:TestSaleComboConfigurator,/sale:TestSaleOrderComboLinkedLines,/sale:TestSaleComboMultiCurrency,/product:TestProductCombo`
from the batch branch (prefixed namespace `odoo_w3b03_sale__*`, conf `mongodb_migration_db = odoo_migration`):
**0 failed, 0 error(s) of 17 tests** (`sale-combo-tests.log`).

## `-i product,uom --test-enable` on a fresh opted-in database

See `odoo-tests.md`.
