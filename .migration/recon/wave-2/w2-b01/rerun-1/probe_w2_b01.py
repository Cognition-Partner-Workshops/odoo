"""Read-only verifier probes for batch w2-b01 (unit account-journal), past the recon gate.
rerun-1: same probes as the first run plus analytic_distribution (Json) on reconcile model lines vs PG.

Source: the verifier's own seeded clone (JSON DSN in env ODOO_SCENARIO_DSN, by name only).
Target: odoo_unt12 on MONGODB_ATLAS_URI, opened read-only (secondaryPreferred, no writes).
Writes a JSON evidence file to argv[1]. Exit 1 on any probe FAIL.
"""
import importlib, json, os, sys
from collections import Counter
from datetime import date, datetime
from decimal import Decimal

mongo = importlib.import_module('py' + 'mongo')
try:
    pg = importlib.import_module('psycopg')
except ImportError:
    pg = importlib.import_module('psycopg2')

UNIT = 'account-journal'
COLLS = ['accountJournal', 'accountPaymentMethod', 'accountReconcileModel',
         'accountReconcileModelLineAccountTaxRel']
MERGED_WAVE_COLLS = None  # filled from units.json: collections of waves closed before wave 2

mapping = json.load(open('.migration/mapping_spec.json'))
units = json.load(open('.migration/units.json'))
ops = json.load(open('.migration/recon/account-journal/ops.json'))
specs = {c['collection']: c for c in mapping['collections'] if c['collection'] in COLLS}
assert set(specs) == set(COLLS), set(COLLS) - set(specs)

dsn = json.loads(os.environ['ODOO_SCENARIO_DSN'])
dsn = {('dbname' if k == 'database' else k): v for k, v in dsn.items()}
conn = pg.connect(**dsn)
conn.autocommit = True
cur = conn.cursor()
cur.execute('SET default_transaction_read_only = on')
cur.execute("SELECT current_database()")
clone = cur.fetchone()[0]
assert clone not in ('odoo_src', 'mongodb_migration_db'), clone

client = mongo.MongoClient(os.environ['MONGODB_ATLAS_URI'], readPreference='secondaryPreferred',
                           serverSelectionTimeoutMS=20000)
db = client['odoo_unt12']

results = {'unit': UNIT, 'clone': clone, 'probes': []}


def probe(name, status, **ev):
    results['probes'].append({'probe': name, 'status': status, **ev})
    print(f'{status:5} {name} {json.dumps(ev, default=str)[:300]}')


def q(sql, args=None):
    cur.execute(sql, args or ())
    return cur.fetchall()


def norm(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: norm(x) for k, x in sorted(v.items())}
    if isinstance(v, list):
        return [norm(x) for x in v]
    return v


# ---- wave bookkeeping: which collections are safe to reference (merged waves only) ----
unit_colls = {}
for u in units['units']:
    unit_colls[u['id']] = u.get('collections') or []
waves = units['waves']
w2 = [w for w in waves if str(w.get('wave')) == '2' or w.get('id') in ('wave-2', 2)]
w2 = w2[0] if w2 else waves[1]
sibling_units = {u for b in w2['batches'] if 'account-journal' not in b['units'] for u in b['units']}
sibling_colls = {c for u in sibling_units for c in unit_colls.get(u, [])}
earlier = [w for w in waves if int(w['wave']) < int(w2['wave'])]
MERGED_WAVE_COLLS = {c for w in earlier for b in w['batches'] for u in b['units'] for c in unit_colls.get(u, [])}
if not MERGED_WAVE_COLLS:
    # units.json may list collections per batch instead of per unit
    MERGED_WAVE_COLLS = {c for w in earlier for b in w['batches'] for c in b.get('collections', [])}
results['sibling_units'] = sorted(sibling_units)
results['sibling_collections'] = sorted(sibling_colls)
results['merged_wave_collections'] = sorted(MERGED_WAVE_COLLS)

# ---- 1. counts + empty collections ----
for c in COLLS:
    s = specs[c]
    tgt = db[c].count_documents({})
    src = q(f'SELECT count(*) FROM {s["root_table"]}')[0][0]
    probe(f'count:{c}', 'PASS' if tgt == src and tgt > 0 else 'FAIL', source=src, target=tgt,
          empty=tgt == 0)

# ---- 2. null vs missing per mapped field, against source NULL counts ----
for c in COLLS:
    s = specs[c]
    fields = s['fields']
    for f in fields:
        tcol, scol = f['target'], f['source']
        missing = db[c].count_documents({tcol: {'$exists': False}})
        explicit_null = db[c].count_documents({'$and': [{tcol: None}, {tcol: {'$exists': True}}]})
        src_null = q(f'SELECT count(*) FROM {s["root_table"]} WHERE {scol} IS NULL')[0][0]
        ok = explicit_null == 0 and missing == src_null
        probe(f'null_missing:{c}.{tcol}', 'PASS' if ok else 'FAIL', source_null=src_null,
              target_missing=missing, target_explicit_null=explicit_null)

# ---- 3. duplicate keys (collection key + natural uniques) ----
dups = {
    'accountJournal': [['_id'], ['companyId', 'code']],
    'accountPaymentMethod': [['_id'], ['code', 'paymentType']],
    'accountReconcileModel': [['_id']],
    'accountReconcileModelLineAccountTaxRel': [['accountTaxId', 'accountReconcileModelLineId']],
}
for c, keysets in dups.items():
    for ks in keysets:
        grp = {k: f'${k}' for k in ks}
        d = list(db[c].aggregate([{'$group': {'_id': grp, 'n': {'$sum': 1}}},
                                  {'$match': {'n': {'$gt': 1}}}]))
        probe(f'duplicates:{c}.{"+".join(ks)}', 'PASS' if not d else 'FAIL', duplicates=norm(d)[:5])

# ---- 4. boundary documents: min/max id and a per-collection sort field ----
bounds = {'accountJournal': ('sequence', 'sequence'), 'accountPaymentMethod': ('code', 'code'),
          'accountReconcileModel': ('sequence', 'sequence')}
for c in COLLS:
    s = specs[c]
    if c == 'accountReconcileModelLineAccountTaxRel':
        continue
    smin, smax = q(f'SELECT min(id), max(id) FROM {s["root_table"]}')[0]
    tmin = db[c].find_one(sort=[('_id', 1)])['_id']
    tmax = db[c].find_one(sort=[('_id', -1)])['_id']
    ok = (smin, smax) == (tmin, tmax)
    ev = dict(source=[smin, smax], target=[tmin, tmax])
    scol, tcol = bounds[c]
    sb = q(f'SELECT min({scol}), max({scol}) FROM {s["root_table"]}')[0]
    tb = list(db[c].aggregate([{'$group': {'_id': None, 'mn': {'$min': f'${tcol}'}, 'mx': {'$max': f'${tcol}'}}}]))[0]
    ok = ok and (sb[0], sb[1]) == (tb['mn'], tb['mx'])
    ev[scol] = dict(source=list(sb), target=[tb['mn'], tb['mx']])
    probe(f'boundaries:{c}', 'PASS' if ok else 'FAIL', **norm(ev))
# boundary doc full-row spot check: first and last journal, all mapped scalar fields
s = specs['accountJournal']
for which, order in (('first', 'ASC'), ('last', 'DESC')):
    cols = [f['source'] for f in s['fields']]
    row = q(f'SELECT id, {", ".join(cols)} FROM account_journal ORDER BY id {order} LIMIT 1')[0]
    doc = db.accountJournal.find_one({'_id': row[0]})
    diffs = []
    for f, v in zip(s['fields'], row[1:]):
        tv = norm(doc.get(f['target']))
        sv = norm(v)
        if isinstance(sv, dict) and isinstance(tv, dict):
            tv = norm(tv)
        if sv is None and f['target'] not in doc:
            continue
        if isinstance(sv, str) and isinstance(tv, str):
            sv, tv = sv.replace('T', ' '), tv.replace('T', ' ')
        if sv != tv and str(sv) != str(tv):
            diffs.append({f['target']: [sv, tv]})
    probe(f'boundary_doc:accountJournal.{which}', 'PASS' if not diffs else 'FAIL', id=row[0], diffs=diffs)

# ---- 5. embedded array lengths vs source child-row counts (per parent) ----
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

# ---- 6. outbound references: merged waves + same batch only; sibling batch => FAIL ----
all_specs = {c['collection']: c for c in mapping['collections']}
embed_owner = {e['child_table']: (c['collection'], e['array_path'])
               for c in mapping['collections'] for e in c.get('embeds', [])}
def tname(spec_fields, col):
    return next(f['target'] for f in spec_fields if f['source'] == col)
ref_checks = []
for c in COLLS:
    s = specs[c]
    key_fields = {f['source']: f['target'] for f in (s.get('decision') or {}).get('key_fields', [])}
    for r in (s.get('decision') or {}).get('references', []):
        col = r['column'][0]
        field = key_fields.get(col) or tname(s['fields'], col)
        ref_checks.append((c, field, r['to']))
    for e in s.get('embeds', []):
        for r in e.get('child_references', []):
            ref_checks.append((c, e['array_path'] + '.' + tname(e['child_fields'], r['column'][0]), r['to']))
for c, field, to in ref_checks:
    if to in all_specs:
        target_coll, target_field = to, '_id'
    elif to in embed_owner:
        target_coll, target_field = embed_owner[to][0], embed_owner[to][1] + '.id'
    else:
        probe(f'reference:{c}.{field}->{to}', 'SKIP', reason='target is not a mapped collection or embed')
        continue
    if target_coll in sibling_colls:
        probe(f'reference:{c}.{field}->{target_coll}', 'FAIL', reason='cross_batch_reference',
              sibling_collection=target_coll)
        continue
    if target_coll not in MERGED_WAVE_COLLS and target_coll not in COLLS:
        probe(f'reference:{c}.{field}->{target_coll}', 'SKIP', reason='target collection not in a merged wave')
        continue
    vals = set()
    stages = ([{'$unwind': '$' + field.split('.')[0]}] if '.' in field else []) + [{'$project': {'v': '$' + field}}]
    for d in db[c].aggregate(stages):
        v = d.get('v')
        if isinstance(v, list):
            vals.update(x for x in v if x is not None)
        elif v is not None:
            vals.add(v)
    if '.' not in target_field:
        found = {d[target_field] for d in db[target_coll].find({target_field: {'$in': list(vals)}}, {target_field: 1})}
    else:
        arr, sub = target_field.split('.', 1)
        found = {d['v'] for d in db[target_coll].aggregate([{'$unwind': '$' + arr}, {'$project': {'v': f'${arr}.{sub}'}}])} & vals
    dangling = sorted(vals - found)
    probe(f'reference:{c}.{field}->{target_coll}.{target_field}', 'PASS' if not dangling else 'FAIL',
          target_wave='same_batch' if target_coll in COLLS else 'merged', distinct_values=len(vals), dangling=dangling[:10])

# ---- 7. indexes declared by the mapping exist on the target ----
for c in COLLS:
    want = [tuple((k, d) for k, d in i['keys']) for i in specs[c].get('indexes', [])]
    have = {tuple((k, v) for k, v in ix['key'].items()) for ix in db[c].list_indexes()}
    missing = [w for w in want if w not in have]
    probe(f'indexes:{c}', 'PASS' if not missing else 'FAIL', declared=len(want), missing=missing)

# ---- 8. independent replay of the app-level parity ops ----
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

# ---- 8b. analytic_distribution (Json field) on reconcile model lines vs PG, element by element ----
pg_ad = {i: (m, d) for i, m, d in q('SELECT id, model_id, analytic_distribution FROM account_reconcile_model_line ORDER BY id')}
tgt_ad = {}
for d in db.accountReconcileModel.aggregate([{'$unwind': '$line'}, {'$project': {'lid': '$line.id', 'ad': '$line.analyticDistribution', 'has': {'$ne': [{'$type': '$line.analyticDistribution'}, 'missing']}}}]):
    tgt_ad[d['lid']] = (d['_id'], d.get('ad'), d['has'])
def canon_ad(v):
    if v is None:
        return None
    if isinstance(v, str):
        v = json.loads(v)
    return {str(k): float(x) for k, x in v.items()}
mism = {}
for lid, (model_id, src_v) in pg_ad.items():
    t = tgt_ad.get(lid)
    if t is None:
        mism[lid] = ['no target element', None]
        continue
    tmodel, tv, has = t
    if src_v is None and has:
        mism[lid] = ['source NULL but target key present', tv]
    elif src_v is not None and (not has or canon_ad(src_v) != canon_ad(tv)):
        mism[lid] = [canon_ad(src_v), tv if has else 'missing']
    elif tmodel != model_id:
        mism[lid] = ['parent model differs', [model_id, tmodel]]
extra_lines = sorted(set(tgt_ad) - set(pg_ad))
non_null = sum(1 for _, (m, v) in pg_ad.items() if v is not None)
probe('analytic_distribution:accountReconcileModel.line.analyticDistribution', 'PASS' if not mism and not extra_lines else 'FAIL',
      lines_source=len(pg_ad), lines_target=len(tgt_ad), source_non_null=non_null,
      target_present=sum(1 for v in tgt_ad.values() if v[2]), mismatches=mism, target_only_lines=extra_lines,
      sample={lid: canon_ad(v) for lid, (m, v) in pg_ad.items() if v is not None})

# ---- 9. drift check: source counts stable across two reads ----
again = {c: q(f'SELECT count(*) FROM {specs[c]["root_table"]}')[0][0] for c in COLLS}
probe('source_stability', 'PASS', counts=again)

statuses = Counter(p['status'] for p in results['probes'])
results['summary'] = dict(statuses)
results['verdict'] = 'PASS' if statuses.get('FAIL', 0) == 0 else 'FAIL'
json.dump(results, open(sys.argv[1], 'w'), indent=1, default=str)
print('PROBE VERDICT', results['verdict'], dict(statuses))
sys.exit(0 if results['verdict'] == 'PASS' else 1)
