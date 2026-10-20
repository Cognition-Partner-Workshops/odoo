"""Tier-4 ORM scenario for unit product-supplierinfo (w3-b02): product.supplierinfo served from
MongoDB, the store-agnostic vendor-code branch of product.product._search_display_name, the
name_search fallback through product_tmpl_id.seller_ids, _select_seller, the record rule, the D5
writer of purchase (partner currency -> seller currency, PostgreSQL + MongoDB in one request) and
ondelete='cascade' from a wave 2 template document.

Run from the run branch against a scratch clone of the seeded odoo_src clone whose rows were
loaded into the target by load_unit.py (PostgreSQL rows are the oracle, MongoDB the system
under test); every write is rolled back::

    odoo-bin shell -d <scratch db> --db_port=5433 --no-http -c <conf> < .migration/load/scenario_product_supplierinfo.py

where ``<conf>`` sets ``mongodb_migration_db = <scratch db>``. The same script run from
``../odoo-base`` (PostgreSQL storage, no conf) on another clone of the seeded source prints the
same ``RESULT`` lines: diff them for the baseline comparison the batch notes ask for.
"""
import datetime

checks = []


def check(name, ok, detail=''):
    checks.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'} {name}{': ' + str(detail) if detail else ''}")


def result(name, value):
    print(f"RESULT {name}: {value}")   # store-independent lines, diffed against the baseline run


cr = env.cr
Seller, T, P = env['product.supplierinfo'], env['product.template'], env['product.product']
mongo = Seller._storage == 'mongodb'
store = env.registry.mongo_store if mongo else None
coll = store.db[store.collection_name(Seller)] if mongo else None
print(f"storage: {Seller._storage}")
if mongo:
    check('storage opt-in', True)
    check('shadow table is id only (no D6 reader)', not Seller._shadow_columns, Seller._shadow_columns)
    before = coll.count_documents({})

cr.execute("""SELECT id, partner_id, product_tmpl_id, product_id, product_code, product_name, min_qty, price, discount,
              currency_id, company_id, uom_id, sequence, delay, date_start, date_end
              FROM product_supplierinfo ORDER BY sequence, min_qty DESC, price, id""")
pg_rows = cr.fetchall()
orm_rows = [(s.id, s.partner_id.id, s.product_tmpl_id.id, s.product_id.id or None, s.product_code or None, s.product_name or None,
             s.min_qty, s.price, s.discount or None, s.currency_id.id, s.company_id.id or None, s.uom_id.id, s.sequence, s.delay,
             s.date_start or None, s.date_end or None) for s in Seller.search([])]
check('seller search (default order sequence, min_qty DESC, price, id) = PostgreSQL rows', orm_rows == pg_rows, f"{len(orm_rows)} sellers")
result('sellers in default order', [r[0] for r in orm_rows])

seeded = Seller.search([('product_code', '=like', 'SCN-VC-%')], order='id')
check('seeded sellers present (variant-level, windowed, discounted, EUR)', len(seeded) == 4 and all(s.discount > 0 and s.currency_id.name == 'EUR' for s in seeded), seeded.ids)
variant_seller = seeded.filtered('product_id')[:1]
vendor, variant, code = variant_seller.partner_id, variant_seller.product_id, variant_seller.product_code
check('_rec_name = partner_id through res_partner (PostgreSQL, two-step)', variant_seller.display_name.startswith(vendor.display_name), variant_seller.display_name)
cr.execute("SELECT s.id FROM product_supplierinfo s JOIN res_partner p ON p.id = s.partner_id WHERE p.name ILIKE %s", (f'%{vendor.name}%',))
pg_ns, ns = {r[0] for r in cr.fetchall()}, {i for i, _ in Seller.name_search(vendor.name, limit=None)}
check('supplierinfo name_search through the vendor name', ns == pg_ns, f'orm-pg {sorted(ns - pg_ns)} pg-orm {sorted(pg_ns - ns)}')

cr.execute("""SELECT DISTINCT product_tmpl_id FROM product_supplierinfo
              WHERE partner_id = %s AND (product_code ILIKE %s OR product_name ILIKE %s)""", (vendor.id, f'%{code}%', f'%{code}%'))
tmpl_by_code = [r[0] for r in cr.fetchall()]
cr.execute("SELECT id FROM product_product WHERE active AND product_tmpl_id = ANY(%s) ORDER BY id", (tmpl_by_code,))
expected_by_code = [r[0] for r in cr.fetchall()]
found = P.with_context(partner_id=vendor.id).search([('display_name', 'ilike', code)], order='id')
check('_search_display_name vendor branch by product_code (partner_id in context)', found.ids == expected_by_code and variant.id in found.ids, found.ids)
result('display_name ilike product_code with partner_id', found.ids)
name = variant_seller.product_name
cr.execute("""SELECT DISTINCT product_tmpl_id FROM product_supplierinfo
              WHERE partner_id = %s AND (product_code ILIKE %s OR product_name ILIKE %s)""", (vendor.id, f'%{name}%', f'%{name}%'))
cr.execute("SELECT id FROM product_product WHERE active AND product_tmpl_id = ANY(%s) ORDER BY id", ([r[0] for r in cr.fetchall()],))
expected_by_name = [r[0] for r in cr.fetchall()]
found = P.with_context(partner_id=vendor.id).search([('display_name', 'ilike', name)], order='id')
check('_search_display_name vendor branch by product_name', found.ids == expected_by_name, found.ids)
result('display_name ilike product_name with partner_id', found.ids)
ns = sorted(i for i, _ in P.with_context(partner_id=vendor.id).name_search(code))
check('name_search vendor fallback (product_tmpl_id.seller_ids any) by product_code', ns == expected_by_code, ns)
result('name_search product_code with partner_id', ns)
check('no partner_id in context: display_name search does not match the vendor code', not P.search([('display_name', 'ilike', code)]))
check('no partner_id in context: name_search does not match the vendor code', not P.name_search(code))
other = Seller.search([('partner_id', '!=', vendor.id)], order='id', limit=1).partner_id
check('other vendor in context: the code is not found', not P.with_context(partner_id=other.id).search([('display_name', 'ilike', code)]))
neg = P.with_context(partner_id=vendor.id).search([('display_name', 'not ilike', code)], order='id')
result('display_name not ilike product_code with partner_id (seller_ids any)', neg.ids)
result('display_name not ilike product_code without partner_id', P.search([('display_name', 'not ilike', code)], order='id').ids)

tmpl = variant.product_tmpl_id
other_variant = P.with_context(active_test=False).search([('product_tmpl_id', '=', tmpl.id), ('id', '!=', variant.id)], order='id', limit=1) or variant
for qty, date, prod, partner in ((1.0, '2026-06-01', variant, vendor), (25.0, '2026-06-01', variant, vendor), (25.0, '2027-06-01', variant, vendor),
                                 (25.0, False, variant, vendor), (1.0, '2026-06-01', variant, False), (25.0, '2026-06-01', other_variant, vendor)):
    d = datetime.date.fromisoformat(date) if date else False
    sel = prod._select_seller(partner_id=partner, quantity=qty, date=d, uom_id=prod.uom_id)
    result(f'_select_seller(qty={qty}, date={date}, variant={prod.id}, vendor={bool(partner)})',
           sel and sorted((k, getattr(v, 'id', v)) for k, v in sel.items()))   # _get_seller_info() dict (None: no seller); records as ids
result('_prepare_sellers(variant)', variant._prepare_sellers().ids)
result('_prepare_sellers(other variant)', other_variant._prepare_sellers().ids)
cr.execute("SELECT id FROM product_supplierinfo WHERE product_tmpl_id = %s ORDER BY sequence, min_qty DESC, price, id", (tmpl.id,))
check('template.seller_ids (One2many into this collection) = PostgreSQL', tmpl.seller_ids.ids == [r[0] for r in cr.fetchall()])

admin = env.ref('base.user_admin')
cr.execute("SELECT count(*) FROM product_supplierinfo WHERE company_id IS NULL OR company_id = ANY(%s)", (admin.company_ids.ids,))
pg_rule_count = cr.fetchone()[0]
check("record rule 'product supplierinfo company rule' (company_id parent_of, PostgreSQL comodel)",
      Seller.with_user(admin).search_count([]) == pg_rule_count)

# writes through the storage path, all rolled back (contract §6 non-atomic D5 writer: purchase res_partner.py
# writes res_partner (PostgreSQL) and every seller's currency (MongoDB) in one request)


class Rollback(Exception):
    pass


def doc_currency():
    return sorted(d['currencyId'] for d in coll.find({'partnerId': vendor.id}, {'currencyId': 1})) if mongo else None


usd, eur = env.ref('base.USD'), env.ref('base.EUR')
pg_currency_before = sorted(Seller.search([('partner_id', '=', vendor.id)]).mapped('currency_id.id'))
doc_currency_before = doc_currency()
try:
    with cr.savepoint(flush=False):
        vendor.write({'property_purchase_currency_id': usd.id})
        env.flush_all()
        sellers = Seller.search([('partner_id', '=', vendor.id)])
        check('D5 writer: partner currency change updates every seller currency (ORM)', all(s.currency_id == usd for s in sellers), len(sellers))
        if mongo:
            check('D5 writer: seller documents carry the new currencyId', doc_currency() == [usd.id] * len(sellers), doc_currency())
        check('D5 writer: partner column written', vendor.property_purchase_currency_id == usd)
        raise Rollback()
except Rollback:
    pass
env.invalidate_all()
check('D5 writer rollback: partner currency restored', vendor.property_purchase_currency_id != usd)
check('D5 writer rollback: seller currencies restored (ORM)',
      sorted(Seller.search([('partner_id', '=', vendor.id)]).mapped('currency_id.id')) == pg_currency_before)
if mongo:
    check('D5 writer rollback: seller documents restored', doc_currency() == doc_currency_before, doc_currency())

# ondelete='cascade' from a wave 2 template document: no PostgreSQL FK does it any more
try:
    with cr.savepoint(flush=False):
        if mongo:
            # the scratch clone still has the full PostgreSQL tables: relax their NOT NULL columns as
            # _auto_init_mongodb's shadow shape does (DDL, rolled back with the savepoint)
            for m in (T, P, Seller):
                cr.execute("""SELECT column_name FROM information_schema.columns WHERE table_name = %s
                              AND is_nullable = 'NO' AND column_name != 'id'""", (m._table,))
                for (column,) in cr.fetchall():
                    if column not in m._shadow_columns:
                        cr.execute(f'ALTER TABLE "{m._table}" ALTER COLUMN "{column}" DROP NOT NULL')
        new_tmpl = T.create({'name': 'SCN cascade template', 'type': 'consu'})
        new_seller = Seller.create({'partner_id': vendor.id, 'product_tmpl_id': new_tmpl.id, 'price': 1.0, 'currency_id': eur.id,
                                    'product_code': 'SCN-CASCADE'})
        env.flush_all()
        if mongo:
            check('seller create: document written', coll.find_one({'_id': new_seller.id, 'productCode': 'SCN-CASCADE'}) is not None)
        new_tmpl.unlink()
        env.flush_all()
        check('template unlink cascades to its sellers (ORM)', not Seller.with_context(active_test=False).search([('id', '=', new_seller.id)]))
        if mongo:
            check('template unlink cascades to the seller document', coll.find_one({'_id': new_seller.id}) is None)
        raise Rollback()
except Rollback:
    pass
except Exception as e:  # noqa: BLE001 - a storage-path miss is a shared finding (reported, not fixed here) but still a failed check
    check('cascade unlink block ran without error', False, f'{type(e).__name__}: {e}')
env.invalidate_all()
cr.rollback()
if mongo:
    after = coll.count_documents({})
    check('loaded collection unchanged after rollback', before == after, after)
failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed" + (f"; FAILED: {failed}" if failed else ''))
if failed:
    raise SystemExit(1)
