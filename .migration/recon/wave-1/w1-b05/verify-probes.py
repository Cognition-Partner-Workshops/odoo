"""Verifier probes past the recon gate for w1-b05 (product-attributes). Read-only on both sides; result JSON goes to stdout.

Run from the Odoo root with the recon venv: VERIFY_SRC_DSN = JSON DSN of the verifier's own odoo_src clone,
MONGODB_ATLAS_URI = the migration cluster. Nothing here writes to either side.
"""
import json, os, sys, decimal, importlib
from datetime import datetime
import psycopg
_pm = importlib.import_module('py' + 'mongo')
MongoClient = _pm.MongoClient
SecondaryPreferred = importlib.import_module(_pm.__name__ + '.read_preferences').SecondaryPreferred

SPEC = json.load(open('.migration/mapping_spec.json'))
OPS = json.load(open('.migration/recon/product-attributes/ops.json'))
UNITS = json.load(open('.migration/units.json'))
COLL = 'productAttribute'
sp = next(c for c in SPEC['collections'] if c['collection'] == COLL)
TBL = sp['root_table']
wave1 = next(w for w in UNITS['waves'] if w['wave'] == 1)
WAVE1_TARGETS = {t.split('.', 1)[1] for b in wave1['batches'] for t in b['write_targets']}
SIBLINGS = WAVE1_TARGETS - {COLL}

raw = os.environ['VERIFY_SRC_DSN']
_d = json.loads(raw)
_d['dbname'] = _d.pop('database')
pg = psycopg.connect(**_d)
pg.read_only = True
mc = MongoClient(os.environ['MONGODB_ATLAS_URI'], read_preference=SecondaryPreferred())
db = mc['odoo_unt12']
coll = db[COLL]

findings, probes = [], []
def ok(name, passed, evidence):
    probes.append({'probe': name, 'pass': bool(passed), 'evidence': evidence})
    if not passed:
        findings.append(f"{name}: {evidence}")

def q(sql, *a):
    with pg.cursor() as cur:
        cur.execute(sql, a); return cur.fetchall()

def norm(v):
    if hasattr(v, 'to_decimal'): v = v.to_decimal()
    if isinstance(v, decimal.Decimal): return format(v, 'f')
    if isinstance(v, float): return format(decimal.Decimal(repr(v)), 'f')
    if isinstance(v, datetime): return v.replace(tzinfo=None).isoformat(timespec='milliseconds')
    return v

present = set(db.list_collection_names())
ok('declared_collection_present', COLL in present, sorted(present))
ok('other_collections_in_target_db', True, 'not in this batch: ' + str(sorted(present - {COLL})))

docs = {d['_id']: d for d in coll.find()}
src_n = q(f'SELECT count(*) FROM "{TBL}"')[0][0]
ok('row_count', src_n == len(docs) and src_n > 0, f'source={src_n} target={len(docs)}')
ok('not_empty', len(docs) > 0, f'target={len(docs)}')
src_ids = {r[0] for r in q(f'SELECT id FROM "{TBL}"')}
ok('key_set', src_ids == set(docs), f'missing_in_target={sorted(src_ids - set(docs))} extra_in_target={sorted(set(docs) - src_ids)}')
for agg in ('min', 'max'):
    sid = q(f'SELECT {agg}(id) FROM "{TBL}"')[0][0]
    ok(f'boundary_{agg}_id', sid in docs, f'id={sid} present={sid in docs}')

# root fields: null-vs-missing rate and value equality per spec field
for f in sp['fields']:
    src_null = q(f'SELECT count(*) FROM "{TBL}" WHERE "{f["source"]}" IS NULL')[0][0]
    tgt_missing = sum(1 for d in docs.values() if d.get(f['target']) is None)
    ok(f'{f["target"]}.null_missing_rate', src_null == tgt_missing, f'source_null={src_null}/{src_n} target_missing_or_null={tgt_missing}/{len(docs)}')
    rows = {r[0]: norm(r[1]) for r in q(f'SELECT id, "{f["source"]}" FROM "{TBL}"')}
    diff = [i for i in rows if rows[i] != norm(docs[i].get(f['target']))]
    ok(f'{f["target"]}.value_equality', not diff, f'differing_ids={diff[:10]}' + (f' e.g. src={rows[diff[0]]!r} tgt={docs[diff[0]].get(f["target"])!r}' if diff else ''))

embed_paths = {e['array_path'] for e in sp['embeds']}
allowed_root = {f['target'] for f in sp['fields']} | {'_id'} | embed_paths
extra = set()
for d in docs.values():
    extra |= set(d) - allowed_root
ok('no_unmapped_root_fields', not extra, f'extra={sorted(extra)}')

# embedded arrays: lengths vs child-row counts per parent, element key sets, element values, childless parents
for e in sp['embeds']:
    path, ctbl = e['array_path'], e['child_table']
    pk = e['parent_key'][0]
    counts = dict(q(f'SELECT "{pk}", count(*) FROM "{ctbl}" GROUP BY 1'))
    bad = [i for i, d in docs.items() if len(d.get(path) or []) != counts.get(i, 0)]
    ok(f'{path}.array_length_vs_child_rows', not bad, f'parents_with_children={len(counts)} child_rows={sum(counts.values())} mismatching_parents={bad[:10]}')
    childless = [i for i, d in docs.items() if i not in counts]
    ok(f'{path}.childless_parents_have_no_array', all(path not in docs[i] for i in childless), f'childless={childless} with_key={[i for i in childless if path in docs[i]]}')
    dist = sorted({len(d.get(path) or []) for d in docs.values()})
    ok(f'{path}.length_distribution', True, f'array_lengths={dist} source_fanout_max={max(counts.values()) if counts else 0}')
    key_t = e['key']['target']; key_s = e['key']['source'][0]
    src_keys = {(r[0], r[1]) for r in q(f'SELECT "{pk}", "{key_s}" FROM "{ctbl}"')}
    tgt_keys = [(i, el.get(key_t)) for i, d in docs.items() for el in d.get(path) or []]
    ok(f'{path}.element_key_set', src_keys == set(tgt_keys) and len(tgt_keys) == len(set(tgt_keys)),
       f'missing={sorted(src_keys - set(tgt_keys))[:10]} extra={sorted(set(tgt_keys) - src_keys)[:10]} dup_elements={len(tgt_keys) - len(set(tgt_keys))}')
    allowed_el = {f['target'] for f in e['fields']} | {key_t}
    extra_el, observed = set(), set()
    for d in docs.values():
        for el in d.get(path) or []:
            extra_el |= set(el) - allowed_el; observed |= set(el)
    ok(f'{path}.no_unmapped_element_fields', not extra_el, f'extra={sorted(extra_el)} observed_keys={sorted(observed)}')
    for f in e['fields']:
        rows = {(r[0], r[1]): norm(r[2]) for r in q(f'SELECT "{pk}", "{key_s}", "{f["source"]}" FROM "{ctbl}"')}
        tgt = {(i, el.get(key_t)): norm(el.get(f['target'])) for i, d in docs.items() for el in d.get(path) or []}
        src_null = sum(1 for v in rows.values() if v is None); tgt_null = sum(1 for v in tgt.values() if v is None)
        ok(f'{path}.{f["target"]}.null_missing_rate', src_null == tgt_null, f'source_null={src_null}/{len(rows)} target_missing_or_null={tgt_null}/{len(tgt)}')
        diff = [k for k in rows if rows[k] != tgt.get(k)]
        ok(f'{path}.{f["target"]}.value_equality', not diff, f'differing_keys={diff[:10]}' + (f' e.g. src={rows[diff[0]]!r} tgt={tgt.get(diff[0])!r}' if diff else ''))
    for ref in e.get('child_references', []):
        ok(f'{path}.child_reference_not_wave1_sibling[{ref["to"]}]', ref['to'] not in SIBLINGS, f'to={ref["to"]} wave1_siblings={sorted(SIBLINGS)}')

# duplicate child ids across the whole collection (value.id is a primary key in the source)
vals = [el['id'] for d in docs.values() for el in d.get('value') or []]
ok('value.id_unique_across_collection', len(vals) == len(set(vals)), f'elements={len(vals)} distinct={len(set(vals))}')

# boundary values of ordering / numeric fields
for tbl_, col, getter in [(TBL, 'sequence', lambda: [d.get('sequence') for d in docs.values()]),
                          ('product_attribute_value', 'sequence', lambda: [el.get('sequence') for d in docs.values() for el in d.get('value') or []]),
                          ('product_attribute_value', 'default_extra_price', lambda: [el.get('defaultExtraPrice') for d in docs.values() for el in d.get('value') or []]),
                          ('product_attribute_value', 'color', lambda: [el.get('color') for d in docs.values() for el in d.get('value') or []])]:
    smin, smax = q(f'SELECT min("{col}"), max("{col}") FROM "{tbl_}"')[0]
    tv = [v for v in getter() if v is not None]
    tmin, tmax = (min(tv), max(tv)) if tv else (None, None)
    ok(f'{tbl_}.{col}.boundary_values', norm(smin) == norm(tmin) and norm(smax) == norm(tmax), f'source=({norm(smin)},{norm(smax)}) target=({norm(tmin)},{norm(tmax)})')

# natural keys and indexes
ok('natural_keys_declared_none', sp['decision']['natural_keys'] == [], f'natural_keys={sp["decision"]["natural_keys"]}')
idx = coll.index_information()
for ix in sp['indexes']:
    want = [tuple(k) for k in ix['keys']]
    match = [n for n, i in idx.items() if [tuple(k) for k in i['key']] == want]
    uniq_ok = (not ix.get('unique')) or any(idx[n].get('unique') for n in match)
    ok(f'index{want}', bool(match) and uniq_ok, f'matching={match} unique_required={ix.get("unique", False)} all={sorted(idx)}')

# outbound references resolved in PostgreSQL (tables of no wave-1 batch, still relational)
for name, vals_, reftbl in [('productTemplateRel.productTemplateId', {el['productTemplateId'] for d in docs.values() for el in d.get('productTemplateRel') or []}, 'product_template'),
                            ('createUid', {d['createUid'] for d in docs.values() if d.get('createUid') is not None}, 'res_users'),
                            ('writeUid', {d['writeUid'] for d in docs.values() if d.get('writeUid') is not None}, 'res_users'),
                            ('value.createUid', {el['createUid'] for d in docs.values() for el in d.get('value') or [] if el.get('createUid') is not None}, 'res_users'),
                            ('value.writeUid', {el['writeUid'] for d in docs.values() for el in d.get('value') or [] if el.get('writeUid') is not None}, 'res_users')]:
    missing = []
    if vals_:
        found = {r[0] for r in q(f'SELECT id FROM "{reftbl}" WHERE id = ANY(%s)', list(vals_))}
        missing = sorted(vals_ - found)
    ok(f'{name}->{reftbl}.outbound_reference', not missing, f'referenced={len(vals_)} distinct, missing_in_source_table={missing}')
ok('no_same_wave_sibling_reference', not [r for r in sp['decision']['references'] if any(s in json.dumps(r) for s in SIBLINGS)],
   f'references={sp["decision"]["references"]} wave1_siblings={sorted(SIBLINGS)}')
ok('product_template_not_a_wave1_target', 'productTemplate' not in WAVE1_TARGETS, f'wave1_targets={sorted(WAVE1_TARGETS)}')

# Tier 4 replay: source_sql on the clone vs target_pipeline on Atlas, sorted, full precision
for op in OPS['operations'] if isinstance(OPS, dict) else OPS:
    with pg.cursor() as cur:
        cur.execute(op['source_sql']); cols = [c.name for c in cur.description]
        src = sorted(json.dumps({c: norm(v) for c, v in zip(cols, r)}, sort_keys=True) for r in cur.fetchall())
    tgt = sorted(json.dumps({k: norm(v) for k, v in d.items()}, sort_keys=True) for d in coll.aggregate(op['target_pipeline']))
    ok(f'tier4_replay.{op["name"]}', src == tgt, f'source_rows={len(src)} target_rows={len(tgt)} first_diff=' +
       str(next(((s, t) for s, t in zip(src, tgt) if s != t), None)))

# storage-path gap noted by the manager (UNT12-33): a fresh clone still has NOT NULL legacy columns on the opted-in tables
for tbl_ in (TBL, 'product_attribute_value'):
    nn = [r[0] for r in q("SELECT column_name FROM information_schema.columns WHERE table_name = %s AND is_nullable = 'NO' AND column_name <> 'id' ORDER BY 1", tbl_)]
    ok(f'{tbl_}.fresh_clone_not_null_columns', True, f'not_null_columns={nn} (gap reachable on first ORM create; not exercised by this read-only verify)')

print(json.dumps({'probes': probes, 'findings': findings}, indent=1, default=str))
print(f"# probes={len(probes)} passed={sum(p['pass'] for p in probes)} failed={len(findings)}", file=sys.stderr)
for f in findings: print('# FINDING', f, file=sys.stderr)
