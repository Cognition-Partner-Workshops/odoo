"""Tier-4 ORM scenario for unit product-taxonomy (w1-b02): the storage path serves
product.category / product.tag / product.base.unit from MongoDB.

Run from the run branch against a scratch clone of the fixture whose rows were loaded
into the target by load_unit.py (PostgreSQL rows are the oracle, MongoDB the system
under test); every write is rolled back so the loaded documents are left unchanged::

    odoo-bin shell -d <scratch db> --db_port=5433 --no-http -c <conf> < .migration/load/scenario_product_taxonomy.py

where ``<conf>`` sets ``mongodb_migration_db = <scratch db>``: only the migration database
reads the unprefixed spec collections, any other database gets its own ``<db_name>__`` namespace
(d-test-namespace = collection-prefix).
"""
from odoo.exceptions import ValidationError

checks = []


def check(name, ok, detail=''):
    checks.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'} {name}{': ' + str(detail) if detail else ''}")


cr = env.cr
Category, Tag, BaseUnit = env['product.category'], env['product.tag'], env['product.base.unit']
check('storage opt-in', all(m._storage == 'mongodb' for m in (Category, Tag, BaseUnit)))

# reads: every PostgreSQL row is served from the collection with the same values
cr.execute("SELECT id, parent_id, parent_path, name->>'en_US', company_id FROM product_category ORDER BY id")
pg_categories = cr.fetchall()
categories = Category.with_context(lang='en_US').search([], order='id')
check('category search = PostgreSQL rows',
      [(c.id, c.parent_id.id or None, c.parent_path, c.name, c.company_id.id or None) for c in categories] == pg_categories,
      f"{len(categories)} categories")
# default order `parent_id desc, name asc`: SQL recurses into the parent's order (its own
# parent_id term dropped, name reversed), NULL parents first on DESC
cr.execute("""SELECT c.id FROM product_category c LEFT JOIN product_category p ON p.id = c.parent_id
              ORDER BY p.name->>'en_US' DESC NULLS FIRST, c.name->>'en_US' ASC, c.id""")
pg_default_order = [r[0] for r in cr.fetchall()]
check('default order (parent_id desc, name asc) follows the parent order like SQL',
      Category.search([], order='parent_id desc, name asc, id').ids == pg_default_order)
root = categories.filtered(lambda c: not c.parent_id)[:1]
cr.execute("SELECT id FROM product_category WHERE parent_path LIKE %s ORDER BY id", (f"{root.parent_path}%",))
check('child_of uses parent_path', Category.search([('id', 'child_of', root.id)], order='id').ids == [r[0] for r in cr.fetchall()])
names = {row[0]: row[3] for row in pg_categories}
parents = {row[0]: row[1] for row in pg_categories}
leaf = categories.filtered(lambda c: c.parent_id)[:1] or root
chain, node = [], leaf.id
while node:
    chain.insert(0, names[node])
    node = parents[node]
check('complete_name computed through parent chain', leaf.complete_name == ' / '.join(chain), leaf.complete_name)
cr.execute("SELECT parent_id, COUNT(*) FROM product_category GROUP BY parent_id")
check('read_group on parent_id',
      {(p.id or None, n) for p, n in Category._read_group([], ['parent_id'], ['__count'])} == set(cr.fetchall()))

cr.execute("SELECT id, name->>'en_US', sequence, color, visible_to_customers FROM product_tag ORDER BY sequence, id")
pg_tags = cr.fetchall()
tags = Tag.with_context(lang='en_US').search([])
check('tag search (default order sequence, id) = PostgreSQL rows',
      [(t.id, t.name, t.sequence, t.color, t.visible_to_customers) for t in tags] == pg_tags, f"{len(tags)} tags")
cr.execute("SELECT id, name FROM product_tag ORDER BY id")
pg_names = dict(cr.fetchall())
check('translations travel with the document (name = {lang: value})',
      {d['_id']: d['name'] for d in env.registry.mongo_store.find(Tag, {})} == pg_names
      and any(len(n) > 1 for n in pg_names.values()), pg_names)
check('name_search on tag', Tag.name_search(pg_tags[0][1])[0][0] == pg_tags[0][0] if pg_tags else False)
check('search on boolean', Tag.search([('visible_to_customers', '=', False)]).ids == [r[0] for r in pg_tags if not r[4]])

cr.execute("SELECT id, name->>'en_US' FROM product_base_unit ORDER BY name->>'en_US'")
pg_units = cr.fetchall()
env['res.lang']._activate_lang('fr_FR')  # rolled back with the rest of the scenario
cr.execute("SELECT id FROM product_tag ORDER BY COALESCE(name->>'fr_FR', name->>'en_US'), id")
pg_fr_order = [r[0] for r in cr.fetchall()]  # fetch before the ORM reuses the cursor
check('translated sort (fr_FR) falls back to en_US like SQL',
      Tag.with_context(lang='fr_FR').search([], order='name, id').ids == pg_fr_order)
check('base unit search (order name) = PostgreSQL rows',
      [(u.id, u.name) for u in BaseUnit.with_context(lang='en_US').search([])] == pg_units, f"{len(pg_units)} units")

# writes: shadow id allocation, document write, rollback replays the undo log
store = env.registry.mongo_store
before = {m._name: store.count(m, {}) for m in (Category, Tag, BaseUnit)}
with cr.savepoint():
    tag = Tag.create({'name': 'w1-b02 scenario', 'sequence': 99})
    cr.execute("SELECT id FROM product_tag WHERE id = %s", (tag.id,))
    check('create: id from the shadow sequence', cr.fetchone() == (tag.id,))
    doc = store.find(Tag, {'_id': tag.id})
    check('create: document written', doc and doc[0]['name'] == {'en_US': 'w1-b02 scenario'} and doc[0]['sequence'] == 99)
    tag.write({'visible_to_customers': False, 'color': '#000000'})
    tag.flush_recordset()
    doc = store.find(Tag, {'_id': tag.id})[0]
    check('write: document updated', doc['visibleToCustomers'] is False and doc['color'] == '#000000')
    check('search after write (read-your-writes)', tag in Tag.search([('color', '=', '#000000')]))
    try:
        with cr.savepoint():
            Tag.create({'name': 'w1-b02 scenario'})
        check('unique tag name enforced by the collection index', False)
    except ValidationError as exc:
        check('unique tag name enforced by the collection index', True, str(exc)[:60])
    child = Category.create({'name': 'w1-b02 child', 'parent_id': root.id})
    doc = store.find(Category, {'_id': child.id})[0]
    check('create category: parent_path computed', doc['parentPath'] == f"{root.parent_path}{child.id}/" and doc['parentId'] == root.id)
    root.write({'property_cost_method': 'fifo', 'product_properties_definition': [{'name': 'w1b02_prop', 'type': 'char', 'string': 'W1B02'}]})
    root.flush_recordset()
    cr.execute("SELECT property_cost_method->>%s FROM product_category WHERE id = %s", (str(env.company.id), root.id))
    check('D6 shadow column property_cost_method written through to PostgreSQL', cr.fetchone() == ('fifo',))
    check('property definition read from the document',
          env['product.template'].get_property_definition('product_properties.w1b02_prop').get('string') == 'W1B02')
    unit = BaseUnit.create({'name': 'w1-b02 unit'})
    unit.unlink()
    check('unlink base unit: document and shadow row removed',
          not store.find(BaseUnit, {'_id': unit.id}) and not cr.execute("SELECT 1 FROM product_base_unit WHERE id = %s", (unit.id,)) and not cr.fetchone())
# roll everything back: the undo log must leave the collections as loaded
cr.rollback()
after = {m._name: store.count(m, {}) for m in (Category, Tag, BaseUnit)}
check('rollback replays the undo log: collections unchanged', before == after, after)
cr.execute("SELECT COUNT(*) FROM product_tag WHERE name->>'en_US' = 'w1-b02 scenario'")
check('rollback removed the shadow rows', cr.fetchone() == (0,))

failed = [n for n, ok in checks if not ok]
print(f"scenario: {len(checks) - len(failed)}/{len(checks)} checks passed" + (f"; FAILED: {failed}" if failed else ''))
