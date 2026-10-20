"""Tier-4 ORM scenario for unit product-pricing (w3-b01): product.pricelist and
product.pricelist.item served from MongoDB by the storage path (no raw SQL in the unit).

Run twice and diff the ``VALUE`` lines: once from the run branch against a scratch clone of the
seeded odoo_src clone whose rows load_unit.py loaded into the target (MongoDB is the system under
test, the clone's PostgreSQL rows are the oracle for the ``check`` lines), once from the
pre-opt-in odoo-base worktree against another clone (PostgreSQL storage, the baseline for the
pricing computations, partner pricelist resolution and name_search that SQL cannot restate)::

    odoo-bin shell -d <scratch db> --db_port=5433 --no-http -c <conf> < .migration/load/scenario_product_pricing.py

where ``<conf>`` sets ``mongodb_migration_db = <scratch db>`` (prefixed namespace). Every write is
rolled back so the loaded documents are left unchanged.
"""
from decimal import Decimal
from datetime import datetime
from odoo.exceptions import UserError

checks = []


def check(name, ok, detail=''):
    checks.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'} {name}{': ' + str(detail) if detail else ''}")


def value(name, v):
    print(f"VALUE {name}: {v!r}")


cr = env.cr


def fetch(sql, params=()):
    # PostgreSQL rows are fetched before the ORM call: on the PostgreSQL worktree a search reuses the cursor
    cr.execute(sql, params)
    return cr.fetchall()


def norm(v):
    # False/None/0 all mean 'not set' across the two storages; numerics compare as float (Decimal128 vs numeric)
    if v is None or v is False or v == 0 or v == '':
        return None
    return float(v) if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool) else v

PL, Item = env['product.pricelist'], env['product.pricelist.item']
mongo = getattr(PL, '_storage', 'postgresql') == 'mongodb'
store = env.registry.mongo_store if mongo else None
print(f"storage: {'mongodb' if mongo else 'postgresql'}")
if mongo:
    check('storage opt-in', Item._storage == 'mongodb')
    before = {m._name: store.db[store.collection_name(m)].count_documents({}) for m in (PL, Item)}
    print('shadow columns', PL._shadow_columns, Item._shadow_columns)

# --- reads vs the clone's PostgreSQL rows (default orders; NULLS FIRST on DESC is PostgreSQL's default)
pg_rows = fetch("SELECT id, name->>'en_US', sequence, currency_id, company_id, active FROM product_pricelist ORDER BY sequence, id")
pg = pg_rows
pls = PL.with_context(active_test=False).search([])
check('pricelist search (sequence, id, name) = PostgreSQL rows',
      [(p.id, p.name, p.sequence, p.currency_id.id, p.company_id.id or None, p.active) for p in pls] == pg, f"{len(pls)} pricelists")
value('pricelist order', pls.ids)
value('active pricelists', PL.search([]).ids)
pg_rows = fetch("""SELECT id FROM product_pricelist_item ORDER BY applied_on, min_quantity DESC, categ_id DESC, id DESC""")
pg_order = [r[0] for r in pg_rows]
pg_rows = fetch("""SELECT id FROM product_pricelist_item ORDER BY applied_on, min_quantity DESC, categ_id DESC NULLS LAST, id DESC""")
pg_order_nulls_last = [r[0] for r in pg_rows]
items = Item.search([])
check('item default order (applied_on, min_quantity desc, categ_id desc, id desc) = PostgreSQL',
      items.ids == pg_order, f"orm={items.ids} pg={pg_order} pg_nulls_last={pg_order_nulls_last}")
value('item order', items.ids)
pg_rows = fetch("""SELECT id, pricelist_id, company_id, currency_id, categ_id, product_tmpl_id, product_id, uom_id, base_pricelist_id,
              applied_on, base, compute_price, min_quantity, fixed_price, price_discount, price_round, price_surcharge,
              price_min_margin, price_max_margin, date_start, date_end FROM product_pricelist_item ORDER BY id""")
pg_items = pg_rows
orm_items = [(i.id, i.pricelist_id.id, i.company_id.id, i.currency_id.id, i.categ_id.id, i.product_tmpl_id.id, i.product_id.id,
              i.uom_id.id, i.base_pricelist_id.id, i.applied_on, i.base, i.compute_price, i.min_quantity, i.fixed_price,
              i.price_discount, i.price_round, i.price_surcharge, i.price_min_margin, i.price_max_margin,
              i.date_start, i.date_end) for i in Item.search([], order='id')]
check('item fields = PostgreSQL rows', [tuple(map(norm, r)) for r in orm_items] == [tuple(map(norm, r)) for r in pg_items],
      f"{len(orm_items)} items")

# --- domain branches: = False on nullable references (null vs missing), parent_of, dotted traversal
pg_rows = fetch("SELECT id FROM product_pricelist_item WHERE categ_id IS NULL ORDER BY id")
check("categ_id = False matches missing keys", Item.search([('categ_id', '=', False)], order='id').ids == [r[0] for r in pg_rows])
pg_rows = fetch("SELECT id FROM product_pricelist_item WHERE product_id IS NOT NULL ORDER BY id")
check("product_id != False", Item.search([('product_id', '!=', False)], order='id').ids == [r[0] for r in pg_rows])
pg_rows = fetch("SELECT id FROM product_pricelist WHERE company_id IS NULL ORDER BY id")
check("pricelist company_id = False", PL.search([('company_id', '=', False)], order='id').ids == [r[0] for r in pg_rows])
furniture = env['product.category'].search([('name', '=', 'Furniture')], limit=1)
office = env['product.category'].search([('parent_id', '=', furniture.id)], order='id', limit=1)
pg_rows = fetch("SELECT id FROM product_pricelist_item WHERE categ_id IN %s ORDER BY id", (tuple(furniture.parent_path.split('/')[:-1] and [int(x) for x in office.parent_path.split('/')[:-1]]),))
check("categ_id parent_of (Office -> Furniture)", Item.search([('categ_id', 'parent_of', office.ids)], order='id').ids == [r[0] for r in pg_rows])
chair = env['product.template'].search([('categ_id', 'child_of', furniture.id)], order='id', limit=1)
variant = chair.product_variant_id
pg_rows = fetch("SELECT i.id FROM product_pricelist_item i JOIN product_product p ON p.id = i.product_id WHERE p.product_tmpl_id = %s ORDER BY i.id", (chair.id,))
check("product_id.product_tmpl_id traversal", Item.search([('product_id.product_tmpl_id', 'in', chair.ids)], order='id').ids == [r[0] for r in pg_rows])
pg_rows = fetch("SELECT id FROM product_pricelist_item WHERE date_start IS NULL OR date_start <= %s ORDER BY id", ('2026-06-01 00:00:00',))
check("date_start = False | <= date", Item.search(['|', ('date_start', '=', False), ('date_start', '<=', datetime(2026, 6, 1))], order='id').ids == [r[0] for r in pg_rows])
pg_rows = fetch("SELECT id FROM product_pricelist_item WHERE min_quantity = 0 OR min_quantity <= 2 ORDER BY id")
value('min_quantity = 0 | <= 2 ids', Item.search(['|', ('min_quantity', '=', 0), ('min_quantity', '<=', 2)], order='id').ids)
value('min_quantity <= 2 ids', Item.search([('min_quantity', '<=', 2)], order='id').ids)
value('min_quantity = 0 ids', Item.search([('min_quantity', '=', 0)], order='id').ids)
value('min_quantity > 1.5 ids', Item.search([('min_quantity', '>', 1.5)], order='id').ids)
check("min_quantity = 0 | <= qty (Decimal128)", Item.search(['|', ('min_quantity', '=', 0), ('min_quantity', '<=', 2)], order='id').ids == [r[0] for r in pg_rows])
pg_rows = fetch("""SELECT id FROM product_pricelist_item WHERE compute_price = 'discount' AND price_discount > 0 AND COALESCE(price_round, 0) = 0
              AND COALESCE(price_surcharge, 0) = 0 AND COALESCE(price_min_margin, 0) = 0 AND COALESCE(price_max_margin, 0) = 0 ORDER BY id""")
value('is_plain_discount ids', Item.search([('is_plain_discount', '=', True)], order='id').ids)
value('price_round = 0 ids (NULL column in PostgreSQL)', Item.search([('price_round', '=', 0)], order='id').ids)
value('price_round = False ids', Item.search([('price_round', '=', False)], order='id').ids)
value('price_round != 0 ids', Item.search([('price_round', '!=', 0)], order='id').ids)
check("is_plain_discount searchable (_search_is_plain_discount)", Item.search([('is_plain_discount', '=', True)], order='id').ids == [r[0] for r in pg_rows])
pg_rows = fetch("SELECT p.id FROM product_pricelist p JOIN res_country_group_pricelist_rel r ON r.pricelist_id = p.id WHERE r.res_country_group_id = %s ORDER BY p.id", (env.ref('base.europe').id,))
check("country_group_ids in (embedded array)", PL.search([('country_group_ids', 'in', env.ref('base.europe').ids)], order='id').ids == [r[0] for r in pg_rows])
pg_rows = fetch("SELECT p.id FROM product_pricelist p WHERE NOT EXISTS (SELECT 1 FROM res_country_group_pricelist_rel r WHERE r.pricelist_id = p.id) AND p.active ORDER BY p.id")
check("country_group_ids = False (empty array)", PL.search([('country_group_ids', '=', False)], order='id').ids == [r[0] for r in pg_rows])
france = env.ref('base.fr')
check("country_group_ids.country_ids traversal (France -> Europe)", PL.search([('country_group_ids.country_ids', '=', france.id)]).mapped('name') == ['Europe Wholesale'])
pg_rows = fetch("SELECT pricelist_id, COUNT(*) FROM product_pricelist_item GROUP BY 1")
check('read_group items by pricelist_id', {(p.id, n) for p, n in Item._read_group([], ['pricelist_id'], ['__count'])} == set(pg_rows))

# --- name_search through currency_id (_rec_names_search), translated name
value('name_search EUR', PL.name_search('EUR'))
value('name_search Wholesale', PL.name_search('Wholesale'))
value('name_search fr', PL.with_context(lang='fr_FR').name_search('grossistes'))
value('display_name fr', PL.with_context(lang='fr_FR').search([('name', 'ilike', 'Europe')]).mapped('display_name'))
value('item display_name', Item.search([], order='id').mapped('display_name'))

# --- pricing: applicable rules and computed prices (baseline = same script on the pre-opt-in worktree)
europe = PL.search([('name', '=', 'Europe Wholesale')])
us_company = PL.with_company(2).search([('name', '=', 'US Company Retail')])
fixture_pl = PL.search([], order='id', limit=1)
for qty, date in ((1, datetime(2026, 6, 1)), (5, datetime(2026, 6, 1)), (1, datetime(2027, 3, 1))):
    rules = europe._get_applicable_rules(variant, qty, date, uom=variant.uom_id)
    value(f'europe rules chair qty={qty} date={date.date()}', rules.ids)
    value(f'europe price chair qty={qty} date={date.date()}', europe._get_product_price(variant, qty, uom=variant.uom_id, date=date))
other = env['product.product'].search([('categ_id', 'not in', env['product.category'].search([('id', 'child_of', furniture.id)]).ids), ('sale_ok', '=', True)], order='id', limit=1)
value('europe rules non-furniture', europe._get_applicable_rules(other, 1, datetime(2026, 6, 1)).ids)
value('europe price non-furniture', europe._get_product_price(other, 1, date=datetime(2026, 6, 1)))
value('fixture price product 38', fixture_pl._get_product_price(env['product.product'].search([('product_tmpl_id', '=', 38)], limit=1), 1))
us = us_company.with_company(2)
for qty in (1, 2):
    value(f'us-company rules chair qty={qty}', us._get_applicable_rules(variant, qty, datetime(2026, 6, 1)).ids)
    value(f'us-company price chair qty={qty} (base=pricelist Europe, discount+round+surcharge+margins)', us._get_product_price(variant, qty, date=datetime(2026, 6, 1)))
value('price_rule_multi all pricelists', {k: {pl: (round(p, 2), r) for pl, (p, r) in v.items()} for k, v in PL._compute_price_rule_multi(variant, 2, date=datetime(2026, 6, 1)).items()})
value('country pricelist multi (fr, us)', {k: v.id for k, v in PL._get_country_pricelist_multi([france.id, env.ref('base.us').id]).items()})
partner = env['res.partner'].search([('country_id', '=', france.id)], order='id', limit=1) or env['res.partner'].search([], order='id', limit=1)
value('partner pricelist multi', PL._get_partner_pricelist_multi(partner.ids)[partner.id].id)

# --- multi-company visibility (ir.rule: company_id in companies | False) and _check_company_auto
pg_rows = fetch("SELECT id FROM product_pricelist WHERE active AND (company_id IS NULL OR company_id = 1) ORDER BY id")
admin = env.ref('base.user_admin')  # the shell env is the superuser, which bypasses record rules
value('admin companies', admin.company_ids.ids)
check('company 1 sees company-less + own pricelists', PL.with_user(admin).with_context(allowed_company_ids=[1]).search([], order='id').ids == [r[0] for r in pg_rows])
pg_rows = fetch("SELECT id FROM product_pricelist_item WHERE company_id IS NULL OR company_id = 2 ORDER BY id")
check('company 2 sees its items', Item.with_user(admin).with_context(allowed_company_ids=[2]).search([], order='id').ids == [r[0] for r in pg_rows])
check('company 1 cannot read company-2 pricelist', not PL.with_user(admin).with_context(allowed_company_ids=[1]).search([('id', '=', us_company.id)]))

# --- writes through the storage path, rolled back
with cr.savepoint(flush=False):
    if mongo:
        for m in (PL, Item):
            pg_rows = fetch("""SELECT column_name FROM information_schema.columns WHERE table_name = %s AND is_nullable = 'NO' AND column_name != 'id'""", (m._table,))
            for (column,) in pg_rows:
                if column not in m._shadow_columns:
                    cr.execute(f'ALTER TABLE "{m._table}" ALTER COLUMN "{column}" DROP NOT NULL')
    new_pl = PL.with_context(tracking_disable=True, mail_create_nolog=True).create({'name': 'Scenario PL', 'sequence': 1, 'country_group_ids': [(6, 0, env.ref('base.europe').ids)]})
    new_item = Item.create({'pricelist_id': new_pl.id, 'applied_on': '3_global', 'compute_price': 'markup', 'price_markup': 20.0, 'min_quantity': 3})
    env.flush_all()
    if mongo:
        doc = store.db[store.collection_name(PL)].find_one({'_id': new_pl.id})
        check('pricelist create: document with embedded country group array', doc and doc.get('resCountryGroupPricelistRel') == [{'resCountryGroupId': env.ref('base.europe').id}], doc)
        idoc = store.db[store.collection_name(Item)].find_one({'_id': new_item.id})
        check('item create: document (NULL omitted, Decimal128)', idoc and 'categId' not in idoc and str(idoc.get('minQuantity')) == '3.00', idoc)
    check('new pricelist first in default order (sequence 1)', PL.search([], limit=1) == new_pl)
    value('new item price_discount (markup -> negative discount)', new_item.price_discount)
    try:
        with cr.savepoint(flush=False):
            Item.create({'pricelist_id': us_company.id, 'applied_on': '3_global', 'compute_price': 'discount', 'base': 'pricelist', 'base_pricelist_id': fixture_pl.id, 'price_discount': 1})
            env.flush_all()
        check('_check_company_auto rejects a cross-company base pricelist', False)
    except UserError as e:
        check('_check_company_auto rejects a cross-company base pricelist', True, type(e).__name__)
    new_item.write({'min_quantity': 4, 'categ_id': furniture.id})
    env.flush_all()
    check('write recomputes applied_on', new_item.applied_on == '2_product_category')
    new_pl.unlink()
    env.flush_all()
    if mongo:
        check('unlink cascades item document', not store.db[store.collection_name(Item)].find_one({'_id': new_item.id}) and not store.db[store.collection_name(PL)].find_one({'_id': new_pl.id}))
    check('unlink cascades item', not Item.search([('id', '=', new_item.id)]))
env.invalidate_all()
cr.rollback()
if mongo:
    after = {m._name: store.db[store.collection_name(m)].count_documents({}) for m in (PL, Item)}
    check('loaded collections unchanged after rollback', before == after, after)
failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed" + (f"; FAILED: {failed}" if failed else ''))
if failed:
    raise SystemExit(1)
