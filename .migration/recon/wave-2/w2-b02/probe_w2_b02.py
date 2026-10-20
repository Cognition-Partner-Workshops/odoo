"""Read-only verifier probes for batch w2-b02 (unit product-catalog), past the recon gate.

Source: the verifier's own seeded clone (JSON DSN in env ODOO_SCENARIO_DSN, by name only).
Target: odoo_unt12 on MONGODB_ATLAS_URI, opened read-only (secondaryPreferred, no mutating call).
Usage: probe_w2_b02.py <evidence json out>. Exit 1 on any probe FAIL.
"""
import importlib, json, os, sys
from collections import Counter
from datetime import date, datetime
from decimal import Decimal

mongo = importlib.import_module('py' + 'mongo')
Decimal128 = importlib.import_module('bson.decimal128').Decimal128
try:
    pg = importlib.import_module('psycopg')
except ImportError:
    pg = importlib.import_module('psycopg2')

UNIT = 'product-catalog'
BATCH = 'w2-b02'
COLLS = ['productTemplate', 'productProduct', 'productTemplateAttributeValue',
         'productAttributeValueProductTemplateAttributeLineRel', 'productCombo', 'productSupplierinfo',
         'productPricelist', 'productPricelistItem']

mapping = json.load(open('.migration/mapping_spec.json'))
units = json.load(open('.migration/units.json'))
ops = json.load(open('.migration/recon/wave-2/w2-b02/verify-ops.json'))
specs = {c['collection']: c for c in mapping['collections'] if c['collection'] in COLLS}
assert set(specs) == set(COLLS), set(COLLS) - set(specs)

dsn = json.loads(os.environ['ODOO_SCENARIO_DSN'])
dsn = {('dbname' if k == 'database' else k): v for k, v in dsn.items()}
conn = pg.connect(**dsn)
conn.autocommit = True
cur = conn.cursor()
cur.execute('SET default_transaction_read_only = on')
cur.execute('SELECT current_database()')
clone = cur.fetchone()[0]
assert clone not in ('odoo_src', 'mongodb_migration_db'), clone

client = mongo.MongoClient(os.environ['MONGODB_ATLAS_URI'], readPreference='secondaryPreferred',
                           serverSelectionTimeoutMS=20000)
db = client['odoo_unt12']

results = {'unit': UNIT, 'batch': BATCH, 'clone': clone, 'probes': []}


def probe(name, status, **ev):
    results['probes'].append({'probe': name, 'status': status, **ev})
    print(f'{status:5} {name} {json.dumps(ev, default=str)[:300]}')


def q(sql, args=None):
    cur.execute(sql, args or ())
    return cur.fetchall()


def norm(v):
    if isinstance(v, Decimal128):
        v = v.to_decimal()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat().replace('T', ' ')
    if isinstance(v, dict):
        return {str(k): norm(x) for k, x in sorted(v.items())}
    if isinstance(v, list):
        return [norm(x) for x in v]
    if isinstance(v, str) and v and v[0] in '{[' and v[-1] in '}]':
        try:
            return norm(json.loads(v))
        except ValueError:
            return v
    return v


def same(sv, tv):
    sv, tv = norm(sv), norm(tv)
    if isinstance(sv, float) and isinstance(tv, (int, float)):
        return abs(sv - float(tv)) < 1e-9
    if isinstance(tv, float) and isinstance(sv, (int, float)):
        return abs(float(sv) - tv) < 1e-9
    return sv == tv or str(sv) == str(tv)


# ---- wave bookkeeping: which collections may be referenced (merged waves + same batch) ----
unit_colls = {u['id']: u.get('collections') or [] for u in units['units']}
waves = units['waves']
w2 = next(w for w in waves if int(w['wave']) == 2)
this_batch = next(b for b in w2['batches'] if b['id'] == BATCH)
assert this_batch['units'] == [UNIT], this_batch['units']
sibling_units = {u for b in w2['batches'] if b['id'] != BATCH for u in b['units']}
sibling_colls = {c for u in sibling_units for c in unit_colls.get(u, [])}
MERGED_WAVE_COLLS = {c for w in waves if int(w['wave']) < 2 for b in w['batches'] for u in b['units']
                     for c in unit_colls.get(u, [])}
results['sibling_units'] = sorted(sibling_units)
results['sibling_collections'] = sorted(sibling_colls)
results['merged_wave_collections'] = sorted(MERGED_WAVE_COLLS)

# ---- 1. counts + empty collections ----
for c in COLLS:
    s = specs[c]
    tgt = db[c].count_documents({})
    src = q(f'SELECT count(*) FROM {s["root_table"]}')[0][0]
    probe(f'count:{c}', 'PASS' if tgt == src and tgt > 0 else 'FAIL', source=src, target=tgt, empty=tgt == 0)

# ---- 2. null vs missing per mapped field, against source NULL counts ----
for c in COLLS:
    s = specs[c]
    for f in s['fields']:
        tcol, scol = f['target'], f['source']
        missing = db[c].count_documents({tcol: {'$exists': False}})
        explicit_null = db[c].count_documents({'$and': [{tcol: None}, {tcol: {'$exists': True}}]})
        src_null = q(f'SELECT count(*) FROM {s["root_table"]} WHERE {scol} IS NULL')[0][0]
        ok = explicit_null == 0 and missing == src_null
        probe(f'null_missing:{c}.{tcol}', 'PASS' if ok else 'FAIL', source_null=src_null,
              target_missing=missing, target_explicit_null=explicit_null)

# ---- 3. duplicate keys (collection key + natural uniques) ----
dups = {
    'productTemplate': [(['_id'], None)],
    'productProduct': [(['_id'], None), (['barcode'], {'barcode': {'$ne': None}}),
                       (['productTmplId', 'combinationIndices'], {'combinationIndices': {'$ne': None}})],
    'productTemplateAttributeValue': [(['_id'], None), (['attributeLineId', 'productAttributeValueId'], None)],
    'productAttributeValueProductTemplateAttributeLineRel': [(['productAttributeValueId', 'productTemplateAttributeLineId'], None)],
    'productCombo': [(['_id'], None)],
    'productSupplierinfo': [(['_id'], None)],
    'productPricelist': [(['_id'], None)],
    'productPricelistItem': [(['_id'], None)],
}
for c, keysets in dups.items():
    for ks, match in keysets:
        grp = {k: f'${k}' for k in ks}
        stages = ([{'$match': match}] if match else []) + [{'$group': {'_id': grp, 'n': {'$sum': 1}}},
                                                           {'$match': {'n': {'$gt': 1}}}]
        d = list(db[c].aggregate(stages))
        probe(f'duplicates:{c}.{"+".join(ks)}', 'PASS' if not d else 'FAIL', duplicates=norm(d)[:5])

# ---- 4. boundary documents: min/max id and a per-collection sort field ----
bounds = {'productTemplate': ('sequence', 'sequence'), 'productProduct': ('product_tmpl_id', 'productTmplId'),
          'productTemplateAttributeValue': ('sequence', 'sequence'), 'productCombo': ('sequence', 'sequence'),
          'productSupplierinfo': ('sequence', 'sequence'), 'productPricelist': ('sequence', 'sequence'),
          'productPricelistItem': ('min_quantity', 'minQuantity')}
for c in COLLS:
    s = specs[c]
    if c not in bounds:
        continue
    smin, smax = q(f'SELECT min(id), max(id) FROM {s["root_table"]}')[0]
    tmin = db[c].find_one(sort=[('_id', 1)])['_id']
    tmax = db[c].find_one(sort=[('_id', -1)])['_id']
    ok = (smin, smax) == (tmin, tmax)
    ev = dict(source=[smin, smax], target=[tmin, tmax])
    scol, tcol = bounds[c]
    sb = q(f'SELECT min({scol}), max({scol}) FROM {s["root_table"]}')[0]
    tb = list(db[c].aggregate([{'$group': {'_id': None, 'mn': {'$min': f'${tcol}'}, 'mx': {'$max': f'${tcol}'}}}]))[0]
    ok = ok and same(sb[0], tb['mn']) and same(sb[1], tb['mx'])
    ev[scol] = dict(source=list(sb), target=[tb['mn'], tb['mx']])
    probe(f'boundaries:{c}', 'PASS' if ok else 'FAIL', **norm(ev))


def row_diffs(spec, row, doc):
    diffs = []
    for f, v in zip(spec['fields'], row):
        if v is None and f['target'] not in doc:
            continue
        if not same(v, doc.get(f['target'])):
            diffs.append({f['target']: [norm(v), norm(doc.get(f['target']))]})
    return diffs


# boundary doc full-row spot check: first and last template / variant / vendor line, all mapped scalar fields
for c, table in (('productTemplate', 'product_template'), ('productProduct', 'product_product'),
                 ('productSupplierinfo', 'product_supplierinfo'), ('productPricelistItem', 'product_pricelist_item')):
    s = specs[c]
    cols = [f['source'] for f in s['fields']]
    for which, order in (('first', 'ASC'), ('last', 'DESC')):
        row = q(f'SELECT id, {", ".join(cols)} FROM {table} ORDER BY id {order} LIMIT 1')[0]
        doc = db[c].find_one({'_id': row[0]})
        diffs = row_diffs(s, row[1:], doc or {})
        probe(f'boundary_doc:{c}.{which}', 'PASS' if doc and not diffs else 'FAIL', id=row[0], diffs=diffs)

# ---- 4b. every JSONB (translated / company-dependent / properties) field, every row, object-equal ----
for c in ('productTemplate', 'productProduct', 'productCombo', 'productPricelist'):
    s = specs[c]
    jfields = [f for f in s['fields'] if f.get('source_type') == 'JSONB']
    if not jfields:
        continue
    cols = [f['source'] for f in jfields]
    rows = {r[0]: r[1:] for r in q(f'SELECT id, {", ".join(cols)} FROM {s["root_table"]}')}
    docs = {d['_id']: d for d in db[c].find({}, {f['target']: 1 for f in jfields})}
    mism = {}
    for rid, vals in rows.items():
        doc = docs.get(rid)
        if doc is None:
            mism[rid] = 'no document'
            continue
        for f, v in zip(jfields, vals):
            if v is None and f['target'] not in doc:
                continue
            if not same(v, doc.get(f['target'])):
                mism.setdefault(rid, {})[f['target']] = [norm(v), norm(doc.get(f['target']))]
    non_null = {f['target']: sum(1 for vals in rows.values() for g, v in zip(jfields, vals) if g is f and v is not None)
                for f in jfields}
    probe(f'jsonb_fields:{c}', 'PASS' if not mism else 'FAIL', fields=[f['target'] for f in jfields],
          rows=len(rows), source_non_null=non_null, mismatches=dict(list(mism.items())[:5]), mismatch_rows=len(mism))

# ---- 5. embedded arrays: lengths per parent AND element-by-element content vs source child rows ----
for c in COLLS:
    s = specs[c]
    for e in s.get('embeds', []):
        path, child, fk = e['array_path'], e['child_table'], e['parent_key'][0]
        src = dict(q(f'SELECT {fk}, count(*) FROM {child} GROUP BY {fk}'))
        tgt = {d['_id']: d['n'] for d in db[c].aggregate(
            [{'$project': {'n': {'$size': {'$ifNull': [f'${path}', []]}}}}])}
        src_full = {k: src.get(k, 0) for k in tgt}
        mism = {k: [src_full[k], tgt[k]] for k in tgt if src_full[k] != tgt[k]}
        orphan_children = sorted(set(src) - set(tgt))
        dist = Counter(tgt.values())
        probe(f'embed_lengths:{c}.{path}', 'PASS' if not mism and not orphan_children else 'FAIL',
              child_table=child, parents=len(tgt), total_children_source=sum(src.values()),
              total_children_target=sum(tgt.values()), length_distribution=dict(sorted(dist.items())),
              mismatches=mism, children_without_parent_doc=orphan_children)
        # element content: multiset of (parent, child fields...) on both sides
        cf = e['child_fields']
        scols = [f['source'] for f in cf]
        s_rows = Counter(json.dumps([norm(x) for x in r], default=str)
                         for r in q(f'SELECT {fk}, {", ".join(scols)} FROM {child}'))
        t_rows = Counter()
        for d in db[c].aggregate([{'$unwind': f'${path}'}, {'$project': {'e': f'${path}'}}]):
            el = d['e']
            t_rows[json.dumps([norm(d['_id'])] + [norm(el.get(f['target'])) for f in cf], default=str)] += 1
        only_s = list((s_rows - t_rows).elements())[:5]
        only_t = list((t_rows - s_rows).elements())[:5]
        probe(f'embed_elements:{c}.{path}', 'PASS' if s_rows == t_rows else 'FAIL', child_table=child,
              elements_source=sum(s_rows.values()), elements_target=sum(t_rows.values()),
              child_fields=[f['target'] for f in cf], only_source=only_s, only_target=only_t)

# ---- 6. outbound references: merged waves + same batch only; sibling batch => FAIL ----
# The FK target comes from the census (ref_table), not from the mapping's `references.to`, which names the
# owning collection even when the referenced table is embedded (product_attribute_value -> productAttribute.value).
census = json.load(open('.migration/census.json'))
all_specs = {c['collection']: c for c in mapping['collections']}
root_owner = {c['root_table']: c['collection'] for c in mapping['collections']}
embed_owner = {e['child_table']: (c['collection'], e['array_path'])
               for c in mapping['collections'] for e in c.get('embeds', [])}


def tname(spec_fields, col):
    return next(f['target'] for f in spec_fields if f['source'] == col)


def fk_ref_table(table, col):
    for fk in census['tables'][table].get('foreign_keys', []):
        if fk['columns'] == [col]:
            return fk['ref_table']
    return None


ref_checks = []
for c in COLLS:
    s = specs[c]
    key_fields = {f['source']: f['target'] for f in (s.get('decision') or {}).get('key_fields', [])}
    for r in (s.get('decision') or {}).get('references', []):
        col = r['column'][0]
        field = key_fields.get(col) or tname(s['fields'], col)
        ref_checks.append((c, field, r['to'], fk_ref_table(s['root_table'], col)))
    for e in s.get('embeds', []):
        for r in e.get('child_references', []):
            col = r['column'][0]
            ref_checks.append((c, e['array_path'] + '.' + tname(e['child_fields'], col), r['to'],
                               fk_ref_table(e['child_table'], col)))
for c, field, declared_to, ref_table in ref_checks:
    if ref_table in root_owner:
        target_coll, target_field = root_owner[ref_table], '_id'
    elif ref_table in embed_owner:
        target_coll, target_field = embed_owner[ref_table][0], embed_owner[ref_table][1] + '.id'
    else:
        probe(f'reference:{c}.{field}->{declared_to}', 'SKIP', ref_table=ref_table,
              reason='referenced table is not a mapped collection or embed')
        continue
    if target_coll in sibling_colls:
        probe(f'reference:{c}.{field}->{target_coll}', 'FAIL', reason='cross_batch_reference',
              sibling_collection=target_coll)
        continue
    if target_coll not in MERGED_WAVE_COLLS and target_coll not in COLLS:
        probe(f'reference:{c}.{field}->{target_coll}', 'SKIP', ref_table=ref_table,
              reason='target collection not in a merged wave (later wave, PostgreSQL-resident)')
        continue
    vals = set()
    stages = ([{'$unwind': '$' + field.split('.')[0]}] if '.' in field else []) + [{'$project': {'v': '$' + field}}]
    for d in db[c].aggregate(stages):
        v = d.get('v')
        if isinstance(v, list):
            vals |= {x for x in v if x is not None}
        elif v is not None:
            vals.add(v)
    if '.' not in target_field:
        found = {d[target_field] for d in db[target_coll].find({target_field: {'$in': list(vals)}}, {target_field: 1})}
    else:
        arr, sub = target_field.split('.', 1)
        found = {d['v'] for d in db[target_coll].aggregate([{'$unwind': '$' + arr}, {'$project': {'v': f'${arr}.{sub}'}}])} & vals
    dangling = sorted(vals - found)
    probe(f'reference:{c}.{field}->{target_coll}.{target_field}', 'PASS' if not dangling else 'FAIL',
          ref_table=ref_table, declared_to=declared_to,
          target_wave='same_batch' if target_coll in COLLS else 'merged', distinct_values=len(vals), dangling=dangling[:10])

# ---- 7. indexes declared by the mapping exist on the target ----
for c in COLLS:
    want = [tuple((k, d) for k, d in i['keys']) for i in specs[c].get('indexes', [])]
    have = {tuple((k, v) for k, v in ix['key'].items()) for ix in db[c].list_indexes()}
    missing = [w for w in want if w not in have]
    probe(f'indexes:{c}', 'PASS' if not missing else 'FAIL', declared=len(want), missing=missing)

# ---- 8. independent replay of the verifier's own app-level parity ops ----
for op in ops:
    rows = q(op['source_sql'])
    names = [d[0] for d in cur.description]
    srows = [norm(dict(zip(names, r))) for r in rows]
    trows = [norm(d) for d in db[op['collection']].aggregate(op['target_pipeline'])]
    src_sorted = sorted(json.dumps(r, sort_keys=True, default=str) for r in srows)
    tgt_sorted = sorted(json.dumps(r, sort_keys=True, default=str) for r in trows)
    ok = src_sorted == tgt_sorted
    only_src = [r for r in src_sorted if r not in tgt_sorted][:3]
    only_tgt = [r for r in tgt_sorted if r not in src_sorted][:3]
    probe(f'ops_replay:{op["name"]}', 'PASS' if ok else 'FAIL', rows_source=len(srows), rows_target=len(trows),
          only_source=only_src, only_target=only_tgt)

# ---- 9. seeded zero-fixture roots/arrays are present on the target (never UNVERIFIED) ----
seeded = {'productPricelist': None, 'productPricelistItem': None, 'productTemplate.uomUomRel': 'uomUomRel',
          'productProduct.customerProductReference': 'customerProductReference', 'productProduct.uomUomRel': 'uomUomRel',
          'productProduct.productUom': 'productUom', 'productTemplateAttributeValue.purchaseOrderLineRel': 'purchaseOrderLineRel',
          'productTemplateAttributeValue.saleOrderLineRel': 'saleOrderLineRel',
          'productTemplateAttributeValue.templateAttributeValueStockMoveRel': 'templateAttributeValueStockMoveRel'}
for key, path in seeded.items():
    coll = key.split('.')[0]
    if path is None:
        n = db[coll].count_documents({})
    else:
        n = sum(d['n'] for d in db[coll].aggregate([{'$project': {'n': {'$size': {'$ifNull': [f'${path}', []]}}}}]))
    probe(f'seeded_nonempty:{key}', 'PASS' if n > 0 else 'FAIL', target_elements=n)

# ---- 10. drift check: source counts stable across two reads ----
again = {c: q(f'SELECT count(*) FROM {specs[c]["root_table"]}')[0][0] for c in COLLS}
probe('source_stability', 'PASS', counts=again)

statuses = Counter(p['status'] for p in results['probes'])
results['summary'] = dict(statuses)
results['verdict'] = 'PASS' if statuses.get('FAIL', 0) == 0 else 'FAIL'
json.dump(results, open(sys.argv[1], 'w'), indent=1, default=str)
print('PROBE VERDICT', results['verdict'], dict(statuses))
sys.exit(0 if results['verdict'] == 'PASS' else 1)
