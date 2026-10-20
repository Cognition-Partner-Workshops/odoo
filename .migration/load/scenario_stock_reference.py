"""ORM scenario for batch w1-b01 (unit stock-reference) on the MongoDB storage path.

Run on the run branch against the worker's seeded clone, whose documents are the loaded ones
(conf key mongodb_migration_db = <clone> keeps the collections unprefixed):

    /home/ubuntu/.venvs/odoo/bin/python odoo-bin shell -c <conf> -d <clone> --no-http \\
        < .migration/load/scenario_stock_reference.py

Reads are compared with the clone's PostgreSQL rows (the clone still carries the legacy columns);
every write happens in one transaction that is rolled back at the end, and the documents are
hashed before and after to show the journal left the loaded collections untouched.
"""
import hashlib

from bson.json_util import dumps

cr = env.cr
st = env.registry.mongo_store
assert st.prefix == '', f"collections are prefixed {st.prefix!r}: set mongodb_migration_db to this database"
MODELS = {
    'stock.storage.category': 'name COLLATE "C", id',
    'stock.scrap.reason.tag': 'sequence, id',
    'return.reason': 'sequence, id',
}
checks = []


def check(name, ok, detail=''):
    checks.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}{' -- ' + str(detail) if detail else ''}")


def snapshot():
    return {m: hashlib.sha256(dumps(list(st.model_collection(env[m]).find().sort('_id', 1)), sort_keys=True).encode()).hexdigest()
            for m in MODELS}


def sql(query, params=()):
    cr.execute(query, params)
    return cr.fetchall()


before = snapshot()

# 1. search order and counts against PostgreSQL
for model, order in MODELS.items():
    M = env[model]
    pg_ids = [r[0] for r in sql(f"SELECT id FROM {M._table} ORDER BY {order}")]
    check(f"{model} search([]) order", M.search([]).ids == pg_ids, pg_ids)
    check(f"{model} search_count", M.search_count([]) == len(pg_ids))
    check(f"{model} exists()", M.browse(pg_ids).exists().ids == pg_ids and not M.browse(max(pg_ids) + 1000).exists())

# 2. field values against PostgreSQL rows
rows = sql("SELECT id, name, allow_new_product, max_weight, company_id FROM stock_storage_category ORDER BY id")
cats = env['stock.storage.category'].browse([r[0] for r in rows])
check("stock.storage.category field values", all(
    (c.name, c.allow_new_product, c.max_weight, c.company_id.id or None) == (r[1], r[2], float(r[3]), r[4])
    for c, r in zip(cats, rows)), [(c.name, c.max_weight) for c in cats][:2])
rows = sql("SELECT id, name->>'en_US', sequence, color FROM stock_scrap_reason_tag ORDER BY id")
tags = env['stock.scrap.reason.tag'].browse([r[0] for r in rows])
check("stock.scrap.reason.tag field values (translated name)", all(
    (t.name, t.sequence, t.color) == (r[1], r[2], r[3]) for t, r in zip(tags, rows)), [(t.name, t.color) for t in tags])
rows = sql("SELECT id, name->>'en_US', sequence FROM return_reason ORDER BY id")
reasons = env['return.reason'].browse([r[0] for r in rows])
check("return.reason field values", all((x.name, x.sequence) == (r[1], r[2]) for x, r in zip(reasons, rows)))

# 3. domains, read_group, translated search
Cat = env['stock.storage.category']
n_small = sql("SELECT count(*) FROM stock_storage_category WHERE name ILIKE %s", ('%small%',))[0][0]
check("ilike domain", Cat.search_count([('name', 'ilike', 'small')]) == n_small, n_small)
n_heavy = sql("SELECT count(*) FROM stock_storage_category WHERE max_weight > 1000")[0][0]
check("numeric domain on decimal field", Cat.search_count([('max_weight', '>', 1000)]) == n_heavy, n_heavy)
groups = Cat._read_group([], ['allow_new_product'], ['__count'])
pg_groups = sql("SELECT allow_new_product, count(*) FROM stock_storage_category GROUP BY 1 ORDER BY 1")
check("read_group by selection", sorted((g[0], g[1]) for g in groups) == [(r[0], r[1]) for r in pg_groups], groups)
Tag = env['stock.scrap.reason.tag']
check("translated name search", Tag.search([('name', '=', 'Expired')]).mapped('name') == ['Expired'])
check("name_search", [r[1] for r in Tag.name_search('Damaged')] == ['Damaged in transit'])

# 4. cross-store readers: stock.location (PostgreSQL) -> storage category, capacity ordered by the many2one,
#    sale_stock StockPicking._create_return exists() probe (addons/sale_stock/models/stock.py:355)
Loc = env['stock.location']
n_loc = sql("SELECT count(*) FROM stock_location WHERE storage_category_id IS NOT NULL")[0][0]
check("stock.location domain on many2one into MongoDB", Loc.search_count([('storage_category_id', '!=', False)]) == n_loc, n_loc)
check("stock.location domain by category name (two-step)", Loc.search_count([('storage_category_id.name', 'ilike', 'frequency')]) == n_loc)
check("one2many location_ids from the MongoDB side", sum(len(c.location_ids) for c in cats) == n_loc)
Cap = env['stock.storage.category.capacity']
check("capacity search ordered by many2one into MongoDB", Cap.search([]).ids == [r[0] for r in sql(
    "SELECT c.id FROM stock_storage_category_capacity c LEFT JOIN stock_storage_category s ON s.id = c.storage_category_id "
    "ORDER BY s.name COLLATE \"C\", s.id, c.id")])
check("_create_return exists() probe", env['return.reason'].browse(int(reasons[0].id)).exists()
      and not env['return.reason'].browse(10 ** 6).exists())

# 5. writes through the storage path, then rolled back
new_tag = Tag.create({'name': 'Scenario tag', 'sequence': 1, 'color': 7})
new_cat = Cat.create({'name': 'Scenario category', 'max_weight': 12.5, 'allow_new_product': 'same'})
env.flush_all()
doc = st.model_collection(Tag).find_one({'_id': new_tag.id})
check("create writes a document + shadow row", doc and doc['name'] == {'en_US': 'Scenario tag'} and doc['color'] == 7
      and sql("SELECT count(*) FROM stock_scrap_reason_tag WHERE id = %s", (new_tag.id,))[0][0] == 1, doc)
cdoc = st.model_collection(Cat).find_one({'_id': new_cat.id})
check("decimal field stored as Decimal128 at the field's digits", type(cdoc['maxWeight']).__name__ == 'Decimal128'
      and str(cdoc['maxWeight']) == '12.50', cdoc.get('maxWeight'))
check("search sees the new rows in order", Tag.search([]).ids[0] == new_tag.id and new_cat in Cat.search([('name', 'ilike', 'scenario')]))
new_tag.write({'name': 'Scenario tag renamed', 'sequence': 99})
new_tag.with_context(lang='en_US').name  # noqa: B018
env.flush_all()
doc = st.model_collection(Tag).find_one({'_id': new_tag.id})
check("write updates the document", doc['name'] == {'en_US': 'Scenario tag renamed'} and doc['sequence'] == 99 and Tag.search([]).ids[-1] == new_tag.id)
loc = Loc.create({'name': 'Scenario shelf', 'usage': 'internal', 'storage_category_id': new_cat.id})
check("PostgreSQL row referencing a MongoDB record", loc.storage_category_id.name == 'Scenario category' and new_cat.location_ids == loc)
try:
    with cr.savepoint():
        Tag.create({'name': 'Expired'})
        env.flush_all()
    check("unique natural key refused", False)
except Exception as exc:  # noqa: BLE001
    # a duplicate-key refusal (E11000) and nothing else counts; it surfaces as the driver's error, not a ValidationError
    check("unique natural key refused", 'E11000' in str(exc) or 'duplicate key' in str(exc), type(exc).__name__)
try:
    with cr.savepoint():
        Cat.create({'name': 'Negative', 'max_weight': -10})
    check("negative max_weight refused (CHECK mirrored by _check_max_weight)", False)
except Exception as exc:  # noqa: BLE001
    check("negative max_weight refused (CHECK mirrored by _check_max_weight)", type(exc).__name__ == 'ValidationError', type(exc).__name__)
new_tag = Tag.create({'name': 'Scenario tag 2'})
new_tag.unlink()
env.flush_all()
check("unlink removes document + shadow row", st.model_collection(Tag).find_one({'_id': new_tag.id}) is None
      and sql("SELECT count(*) FROM stock_scrap_reason_tag WHERE id = %s", (new_tag.id,))[0][0] == 0)
cr.rollback()
after = snapshot()
check("rollback leaves the loaded collections byte-identical", before == after, after)
print(f"{sum(checks)}/{len(checks)} checks passed")
assert all(checks)
