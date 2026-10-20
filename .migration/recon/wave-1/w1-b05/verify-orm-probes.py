"""Read-only ORM probes for w1-b05 on the MongoDB storage path (verifier, UNT12-30).

    /home/ubuntu/.venvs/odoo/bin/python odoo-bin shell -c <conf> -d <verifier clone> --no-http \
        < .migration/recon/wave-1/w1-b05/verify-orm-probes.py

The conf names the clone in mongodb_migration_db so the ORM reads the unprefixed loaded
collections. Every ORM read is compared with the clone's PostgreSQL rows by exact equality; the
cursor is rolled back at the end and nothing is written on either side.
"""
import json
import sys

cr = env.cr
st = env.registry.mongo_store
assert st.prefix == '', f"collections are prefixed {st.prefix!r}"
Attr = env['product.attribute'].with_context(active_test=False)
Value = env['product.attribute.value'].with_context(active_test=False)
Line = env['product.template.attribute.line'].with_context(active_test=False)
probes, findings = [], []


def ok(name, passed, evidence):
    probes.append({'probe': name, 'pass': bool(passed), 'evidence': evidence})
    if not passed:
        findings.append(f"{name}: {evidence}")


def sql(q, *a):
    cr.execute(q, a)
    return cr.fetchall()


ok('storage_path_active', Attr._storage == 'mongodb' and Value._storage == 'mongodb' and Line._storage != 'mongodb',
   f"product.attribute={Attr._storage} product.attribute.value={Value._storage} product.template.attribute.line={getattr(Line, '_storage', None)}")

n_pg = sql("SELECT count(*) FROM product_attribute")[0][0]
n_orm = Attr.search_count([])
n_doc = st.model_collection(Attr).count_documents({})
ok('product.attribute.count', n_pg == n_orm == n_doc, f'pg={n_pg} orm_search_count={n_orm} documents={n_doc}')
ok('product.attribute.ids', Attr.search([]).ids == [r[0] for r in sql("SELECT id FROM product_attribute ORDER BY sequence, id")], 'search([]) ids vs ORDER BY sequence, id')
nv_pg = sql("SELECT count(*) FROM product_attribute_value")[0][0]
ok('product.attribute.value.count', nv_pg == Value.search_count([]), f'pg={nv_pg} orm={Value.search_count([])}')

# product.template.attribute.line.value_ids (many2many kept in PostgreSQL) vs the rel table
rel = sql("SELECT product_template_attribute_line_id, product_attribute_value_id FROM product_attribute_value_product_template_attribute_line_rel")
pg_by_line = {}
for line_id, value_id in rel:
    pg_by_line.setdefault(line_id, set()).add(value_id)
line_ids = [r[0] for r in sql("SELECT id FROM product_template_attribute_line ORDER BY id")]
orm_by_line = {l.id: set(l.value_ids.ids) for l in Line.browse(line_ids)}
ok('product.template.attribute.line.value_ids', orm_by_line == {i: pg_by_line.get(i, set()) for i in line_ids},
   f'lines={len(line_ids)} rel_rows={len(rel)} orm_pairs={sum(len(v) for v in orm_by_line.values())} '
   f'mismatching_lines={[i for i in line_ids if orm_by_line[i] != pg_by_line.get(i, set())][:10]}')
ok('product.template.attribute.line.value_ids.expected_shape', len(rel) == 24 and len(pg_by_line) == 9, f'rel_rows={len(rel)} lines_with_values={len(pg_by_line)} (manager expects 24 across 9)')

# product.attribute.value.pav_attribute_line_ids (inverse side, read through the storage path) vs the rel table
pg_by_value = {}
for line_id, value_id in rel:
    pg_by_value.setdefault(value_id, set()).add(line_id)
value_ids = [r[0] for r in sql("SELECT id FROM product_attribute_value ORDER BY id")]
orm_by_value = {v.id: set(v.pav_attribute_line_ids.ids) for v in Value.browse(value_ids)}
ok('product.attribute.value.pav_attribute_line_ids', orm_by_value == {i: pg_by_value.get(i, set()) for i in value_ids},
   f'values={len(value_ids)} orm_pairs={sum(len(v) for v in orm_by_value.values())} '
   f'mismatching_values={[i for i in value_ids if orm_by_value[i] != pg_by_value.get(i, set())][:10]}')
ok('rel_pairs_symmetric', {(l, v) for l, vs in orm_by_line.items() for v in vs} == {(l, v) for v, ls in orm_by_value.items() for l in ls} == set(rel),
   f'pairs={len(rel)}')

# value -> attribute and attribute -> value_ids on the storage path vs PostgreSQL
pg_attr_of_value = dict(sql("SELECT id, attribute_id FROM product_attribute_value"))
ok('product.attribute.value.attribute_id', {v.id: v.attribute_id.id for v in Value.browse(value_ids)} == pg_attr_of_value, f'values={len(value_ids)}')
pg_values_of_attr = {}
for v, a in pg_attr_of_value.items():
    pg_values_of_attr.setdefault(a, set()).add(v)
attr_ids = [r[0] for r in sql("SELECT id FROM product_attribute ORDER BY id")]
ok('product.attribute.value_ids', {a.id: set(a.value_ids.ids) for a in Attr.browse(attr_ids)} == {i: pg_values_of_attr.get(i, set()) for i in attr_ids}, f'attributes={len(attr_ids)}')
pg_tmpl = {}
for a, t in sql("SELECT product_attribute_id, product_template_id FROM product_attribute_product_template_rel"):
    pg_tmpl.setdefault(a, set()).add(t)
ok('product.attribute.product_tmpl_ids', {a.id: set(a.product_tmpl_ids.ids) for a in Attr.browse(attr_ids)} == {i: pg_tmpl.get(i, set()) for i in attr_ids}, f'pairs={sum(len(v) for v in pg_tmpl.values())}')

# scalar spot checks through the ORM against PostgreSQL
pg_scalars = {r[0]: (r[1], r[2], r[3], r[4]) for r in sql("SELECT id, name->>'en_US', sequence, create_variant, display_type FROM product_attribute")}
orm_scalars = {a.id: (a.name, a.sequence, a.create_variant, a.display_type) for a in Attr.browse(attr_ids)}
ok('product.attribute.scalars', orm_scalars == pg_scalars, f'differing={[i for i in attr_ids if orm_scalars[i] != pg_scalars[i]][:10]}')
# PostgreSQL NULL reads as the ORM's falsy default (integer 0, boolean False, float 0.0, char False)
pg_vscalars = {r[0]: (r[1], r[2] if r[2] is not None else 0, r[3] if r[3] is not None else False, bool(r[4]), float(r[5]) if r[5] is not None else 0.0)
               for r in sql("SELECT id, name->>'en_US', sequence, html_color, is_custom, default_extra_price FROM product_attribute_value")}
orm_vscalars = {v.id: (v.name, v.sequence, v.html_color, v.is_custom, v.default_extra_price) for v in Value.browse(value_ids)}
_vdiff = [i for i in value_ids if orm_vscalars[i] != pg_vscalars[i]]
ok('product.attribute.value.scalars', not _vdiff, f'differing={_vdiff[:10]}' + (f' e.g. orm={orm_vscalars[_vdiff[0]]!r} pg={pg_vscalars[_vdiff[0]]!r}' if _vdiff else ''))

ok('relation_collection_zero_documents', st.db['productAttributeValueProductTemplateAttributeLineRel'].count_documents({}) == 0,
   f"documents={st.db['productAttributeValueProductTemplateAttributeLineRel'].count_documents({})}")

cr.rollback()
print('ORM_PROBES_JSON ' + json.dumps({'probes': probes, 'findings': findings}, default=str))
print(f"# orm probes={len(probes)} passed={sum(p['pass'] for p in probes)} failed={len(findings)}", file=sys.stderr)
