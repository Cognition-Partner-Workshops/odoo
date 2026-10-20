"""ORM scenario for batch w1-b05 (unit product-attributes) on the MongoDB storage path.

Run on the run branch against the worker's clone, whose documents are the loaded ones
(conf key mongodb_migration_db = <clone> keeps the collections unprefixed):

    /home/ubuntu/.venvs/odoo/bin/python odoo-bin shell -c <conf> -d <clone> --no-http \\
        < .migration/load/scenario_product_attributes.py

product.attribute is the root document, product.attribute.value its ``value`` array and the
product_tmpl_ids relation its ``productTemplateRel`` array. Reads are compared with the clone's
PostgreSQL rows (the clone still carries the legacy columns); every write happens in one
transaction that is rolled back at the end, and the collection is hashed before and after to show
the journal left the loaded documents untouched.
"""
import hashlib

from bson.json_util import dumps

cr = env.cr
st = env.registry.mongo_store
assert st.prefix == '', f"collections are prefixed {st.prefix!r}: set mongodb_migration_db to this database"
Attr = env['product.attribute'].with_context(active_test=False)
Value = env['product.attribute.value'].with_context(active_test=False)
coll = st.model_collection(Attr)
checks = []


def check(name, ok, detail=''):
    checks.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}{' -- ' + str(detail) if detail else ''}")


def snapshot():
    return hashlib.sha256(dumps(list(coll.find().sort('_id', 1)), sort_keys=True).encode()).hexdigest()


def sql(query, params=()):
    cr.execute(query, params)
    return cr.fetchall()


before = snapshot()

# 1. search order, counts and active_test against PostgreSQL
attr_ids = [r[0] for r in sql("SELECT id FROM product_attribute ORDER BY sequence, id")]
check("product.attribute search([]) order", Attr.search([]).ids == attr_ids, attr_ids)
check("product.attribute active_test", env['product.attribute'].search_count([]) == sql("SELECT count(*) FROM product_attribute WHERE active")[0][0])
value_ids = [r[0] for r in sql("SELECT v.id FROM product_attribute_value v JOIN product_attribute a ON a.id = v.attribute_id "
                               "ORDER BY a.sequence, a.id, v.sequence, v.id")]
check("product.attribute.value search([]) order (many2one into the parent, then sequence, id)", Value.search([]).ids == value_ids, len(value_ids))
check("product.attribute.value exists()", Value.browse(value_ids).exists().ids == value_ids and not Value.browse(max(value_ids) + 1000).exists())

# 2. field values against PostgreSQL rows
rows = sql("SELECT id, name->>'en_US', create_variant, display_type, sequence, active FROM product_attribute ORDER BY id")
attrs = Attr.browse([r[0] for r in rows])
check("product.attribute field values (translated name, selections)", all(
    (a.name, a.create_variant, a.display_type, a.sequence, a.active) == (r[1], r[2], r[3], r[4], r[5]) for a, r in zip(attrs, rows)),
    [(a.name, a.create_variant) for a in attrs][:3])
rows = sql("SELECT id, attribute_id, name->>'en_US', sequence, html_color, is_custom, default_extra_price FROM product_attribute_value ORDER BY id")
values = Value.browse([r[0] for r in rows])
check("product.attribute.value field values (parent many2one from the array; NULL reads as the field's falsy value)", all(
    (v.attribute_id.id, v.name, v.sequence, v.html_color, v.is_custom, v.default_extra_price)
    == (r[1], r[2], r[3] or 0, r[4] or False, r[5] or False, r[6] or 0.0)
    for v, r in zip(values, rows)), [(v.attribute_id.name, v.name) for v in values][:3])

# 3. one2many / many2many from the arrays
pg_values = dict(sql("SELECT attribute_id, array_agg(id ORDER BY sequence, id) FROM product_attribute_value GROUP BY 1"))
check("one2many value_ids = value array", all(a.value_ids.ids == pg_values.get(a.id, []) for a in attrs))
pg_rel = dict(sql("SELECT product_attribute_id, array_agg(product_template_id ORDER BY product_template_id) FROM product_attribute_product_template_rel GROUP BY 1"))
check("many2many product_tmpl_ids = productTemplateRel array", all(sorted(a.product_tmpl_ids.ids) == pg_rel.get(a.id, []) for a in attrs),
      {a.id: a.product_tmpl_ids.ids for a in attrs if a.product_tmpl_ids})
Tmpl = env['product.template'].with_context(active_test=False)
n_tmpl = sql("SELECT count(DISTINCT product_template_id) FROM product_attribute_product_template_rel")[0][0]
check("product.template domain on the junction array (PostgreSQL side of the relation)",
      Tmpl.search_count([('attribute_line_ids.attribute_id', 'in', attr_ids)]) == n_tmpl, n_tmpl)

# 4. domains, read_group, translated search, cross-store readers
n_nv = sql("SELECT count(*) FROM product_attribute WHERE create_variant = 'no_variant'")[0][0]
check("selection domain", Attr.search_count([('create_variant', '=', 'no_variant')]) == n_nv, n_nv)
n_like = sql("SELECT count(*) FROM product_attribute WHERE name->>'en_US' ILIKE %s", ('%col%',))[0][0]
check("ilike domain on translated name", Attr.search_count([('name', 'ilike', 'col')]) == n_like, n_like)
groups = Attr._read_group([], ['create_variant'], ['__count'])
pg_groups = sql("SELECT create_variant, count(*) FROM product_attribute GROUP BY 1 ORDER BY 1")
check("read_group by selection", sorted((g[0], g[1]) for g in groups) == [(r[0], r[1]) for r in pg_groups], groups)
n_custom = sql("SELECT count(*) FROM product_attribute_value WHERE is_custom")[0][0]
check("boolean domain on the embedded model", Value.search_count([('is_custom', '=', True)]) == n_custom, n_custom)
first = attrs[0]
check("domain on the embedded model by parent", Value.search([('attribute_id', '=', first.id)]).ids == pg_values.get(first.id, []))
check("name_search", [r[0] for r in Attr.name_search(first.name)] == Attr.search([('name', 'ilike', first.name)]).ids)
Line = env['product.template.attribute.line']
n_lines = sql("SELECT count(*) FROM product_template_attribute_line l JOIN product_attribute a ON a.id = l.attribute_id WHERE a.create_variant = 'always'")[0][0]
check("product.template.attribute.line (PostgreSQL) domain through many2one into MongoDB",
      Line.search_count([('attribute_id.create_variant', '=', 'always')]) == n_lines, n_lines)
check("line.attribute_id / value_ids read through MongoDB", all(
    l.attribute_id.name and set(l.value_ids.ids) <= set(pg_values.get(l.attribute_id.id, [])) for l in Line.search([])))

# 5. writes through the storage path, then rolled back
new = Attr.create({'name': 'Scenario finish', 'create_variant': 'no_variant', 'sequence': 1,
                   'value_ids': [(0, 0, {'name': 'Matte', 'sequence': 2}), (0, 0, {'name': 'Gloss', 'sequence': 1, 'html_color': '#ffffff'})]})
env.flush_all()
doc = coll.find_one({'_id': new.id})
check("create writes a document + shadow row", doc and doc['name'] == {'en_US': 'Scenario finish'} and doc['createVariant'] == 'no_variant'
      and sql("SELECT count(*) FROM product_attribute WHERE id = %s", (new.id,))[0][0] == 1, doc)
check("one2many create pushes value elements", sorted(e['name']['en_US'] for e in doc.get('value', [])) == ['Gloss', 'Matte']
      and all(set(e) >= {'id', 'name', 'sequence'} for e in doc['value'])
      and sql("SELECT count(*) FROM product_attribute_value WHERE id IN %s", (tuple(new.value_ids.ids),))[0][0] == 2, doc.get('value'))
by_sequence = Value.search([('attribute_id', '=', new.id)])
check("value order inside the parent (search: sequence, id)", by_sequence.mapped('name') == ['Gloss', 'Matte'] and set(by_sequence.ids) == set(new.value_ids.ids))
check("search sees the new attribute first (sequence 1)", Attr.search([]).ids[0] == new.id)
gloss = by_sequence[0]
gloss.write({'sequence': 5, 'default_extra_price': 2.5})
env.flush_all()
doc = coll.find_one({'_id': new.id})
elem = next(e for e in doc['value'] if e['id'] == gloss.id)
check("write updates the array element", elem['sequence'] == 5 and elem['defaultExtraPrice'] == 2.5
      and Value.search([('attribute_id', '=', new.id)]).mapped('name') == ['Matte', 'Gloss'], elem)
new.write({'name': 'Scenario finish renamed'})
env.flush_all()
check("write updates the root document", coll.find_one({'_id': new.id})['name'] == {'en_US': 'Scenario finish renamed'})
tmpl = Tmpl.create({'name': 'Scenario template', 'attribute_line_ids': [(0, 0, {'attribute_id': new.id, 'value_ids': [(6, 0, new.value_ids.ids)]})]})
env.flush_all()
doc = coll.find_one({'_id': new.id})
check("stored computed many2many pushes a junction element", [e.get('productTemplateId') for e in doc.get('productTemplateRel', [])] == [tmpl.id]
      and new.product_tmpl_ids == tmpl, doc.get('productTemplateRel'))
tmpl.attribute_line_ids.unlink()
env.flush_all()
check("relation removal pulls the junction element", not coll.find_one({'_id': new.id}).get('productTemplateRel') and not new.product_tmpl_ids)
try:
    with cr.savepoint():
        Attr.create({'name': 'Multi with variants', 'display_type': 'multi', 'create_variant': 'always'})
    check("multi display_type with variants refused (CHECK mirrored by @api.constrains)", False)
except Exception as exc:  # noqa: BLE001
    check("multi display_type with variants refused (CHECK mirrored by @api.constrains)", type(exc).__name__ == 'ValidationError', type(exc).__name__)
gloss.unlink()
env.flush_all()
check("unlink pulls the element + shadow row", [e['id'] for e in coll.find_one({'_id': new.id})['value']] == new.value_ids.ids
      and len(new.value_ids) == 1 and sql("SELECT count(*) FROM product_attribute_value WHERE id = %s", (gloss.id,))[0][0] == 0)
remaining = new.value_ids.ids
new.unlink()
env.flush_all()
check("unlink removes document + shadow rows (values cascade)", coll.find_one({'_id': new.id}) is None
      and sql("SELECT count(*) FROM product_attribute WHERE id = %s", (new.id,))[0][0] == 0
      and sql("SELECT count(*) FROM product_attribute_value WHERE id IN %s", (tuple(remaining),))[0][0] == 0
      and not Value.search([('id', 'in', remaining)]))
cr.rollback()
after = snapshot()
check("rollback leaves the loaded collection byte-identical", before == after, after)
print(f"{sum(checks)}/{len(checks)} checks passed")
assert all(checks)
