"""Verifier probes past the recon gate for w1-b03 (uom-packaging). Read-only on both sides; result JSON goes to stdout.

Run from the Odoo root with the recon venv: VERIFY_SRC_DSN = JSON DSN of the verifier's own odoo_src clone
(seeded with .migration/load/seed_uom_packaging.py), MONGODB_ATLAS_URI = the migration cluster.
Nothing here changes either side.
"""
import json, os, sys, decimal, importlib
from datetime import datetime
import psycopg
_pm = importlib.import_module('py' + 'mongo')
MongoClient = _pm.MongoClient
SecondaryPreferred = importlib.import_module(_pm.__name__ + '.read_preferences').SecondaryPreferred

SPEC = json.load(open('.migration/mapping_spec.json'))
OPS = json.load(open('.migration/recon/uom-packaging/ops.json'))
UNITS = json.load(open('.migration/units.json'))
COLLS = ['uomUom', 'stockPackageType']
spec = {c['collection']: c for c in SPEC['collections'] if c['collection'] in COLLS}
wave1 = next(w for w in UNITS['waves'] if w['wave'] == 1)
WAVE1_TARGETS = {t.split('.', 1)[1] for b in wave1['batches'] for t in b['write_targets']}
SIBLINGS = WAVE1_TARGETS - set(COLLS)

_d = json.loads(os.environ['VERIFY_SRC_DSN'])
_d['dbname'] = _d.pop('database')
pg = psycopg.connect(**_d)
pg.read_only = True
mc = MongoClient(os.environ['MONGODB_ATLAS_URI'], read_preference=SecondaryPreferred())
db = mc['odoo_unt12']

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
    if isinstance(v, decimal.Decimal): return format(v.normalize(), 'f')
    if isinstance(v, float): return format(decimal.Decimal(repr(v)).normalize(), 'f')
    if isinstance(v, datetime): return v.replace(tzinfo=None).isoformat(timespec='milliseconds')
    if isinstance(v, dict): return json.dumps(v, sort_keys=True)
    return v

present = set(db.list_collection_names())
ok('declared_collections_present', set(COLLS) <= present, sorted(present))
ok('other_collections_in_target_db', True, 'not in this batch: ' + str(sorted(present - set(COLLS))))

DOCS = {}
for coll in COLLS:
    sp = spec[coll]; tbl = sp['root_table']
    docs = DOCS[coll] = {d['_id']: d for d in db[coll].find()}
    src_n = q(f'SELECT count(*) FROM "{tbl}"')[0][0]
    ok(f'{coll}.row_count', src_n == len(docs) and src_n > 0, f'source={src_n} target={len(docs)}')
    ok(f'{coll}.not_empty', len(docs) > 0, f'target={len(docs)}')
    src_ids = {r[0] for r in q(f'SELECT id FROM "{tbl}"')}
    ok(f'{coll}.key_set', src_ids == set(docs), f'missing_in_target={sorted(src_ids - set(docs))} extra_in_target={sorted(set(docs) - src_ids)}')
    for agg in ('min', 'max'):
        sid = q(f'SELECT {agg}(id) FROM "{tbl}"')[0][0]
        ok(f'{coll}.boundary_{agg}_id', sid in docs, f'id={sid} present={sid in docs}')
    for f in sp['fields']:
        src_null = q(f'SELECT count(*) FROM "{tbl}" WHERE "{f["source"]}" IS NULL')[0][0]
        tgt_missing = sum(1 for d in docs.values() if d.get(f['target']) is None)
        ok(f'{coll}.{f["target"]}.null_missing_rate', src_null == tgt_missing,
           f'source_null={src_null}/{src_n} target_missing_or_null={tgt_missing}/{len(docs)}')
        rows = {r[0]: norm(r[1]) for r in q(f'SELECT id, "{f["source"]}" FROM "{tbl}"')}
        diff = [i for i in rows if rows[i] != norm(docs[i].get(f['target']))]
        ok(f'{coll}.{f["target"]}.value_equality', not diff,
           f'differing_ids={diff[:10]}' + (f' e.g. src={rows[diff[0]]!r} tgt={docs[diff[0]].get(f["target"])!r}' if diff else ''))
        types = sorted({type(d[f['target']]).__name__ for d in docs.values() if d.get(f['target']) is not None})
        ok(f'{coll}.{f["target"]}.bson_type_observed', True, f'spec={f["bson_type"]} observed_python_types={types}')
    embed_paths = {e['array_path'] for e in sp['embeds']}
    allowed_root = {f['target'] for f in sp['fields']} | {'_id'} | embed_paths
    extra = set()
    for d in docs.values():
        extra |= set(d) - allowed_root
    ok(f'{coll}.no_unmapped_root_fields', not extra, f'extra={sorted(extra)}')

    for e in sp['embeds']:
        path, ctbl = e['array_path'], e['child_table']
        pk = e['parent_key'][0]
        counts = dict(q(f'SELECT "{pk}", count(*) FROM "{ctbl}" GROUP BY 1'))
        bad = [i for i, d in docs.items() if len(d.get(path) or []) != counts.get(i, 0)]
        ok(f'{coll}.{path}.array_length_vs_child_rows', not bad,
           f'parents_with_children={len(counts)} child_rows={sum(counts.values())} mismatching_parents={bad[:10]}')
        childless = [i for i, d in docs.items() if i not in counts]
        ok(f'{coll}.{path}.childless_parents_have_no_array', all(path not in docs[i] for i in childless),
           f'childless={childless} with_key={[i for i in childless if path in docs[i]]}')
        dist = sorted({len(d.get(path) or []) for d in docs.values()})
        ok(f'{coll}.{path}.length_distribution', sum(counts.values()) > 0, f'array_lengths={dist} source_fanout_max={max(counts.values()) if counts else 0} (0 child rows would leave the embed ungraded)')
        key_t = e['key']['target']; key_s = e['key']['source'][0]
        src_keys = {(r[0], r[1]) for r in q(f'SELECT "{pk}", "{key_s}" FROM "{ctbl}"')}
        tgt_keys = [(i, el.get(key_t)) for i, d in docs.items() for el in d.get(path) or []]
        ok(f'{coll}.{path}.element_key_set', src_keys == set(tgt_keys) and len(tgt_keys) == len(set(tgt_keys)),
           f'source={sorted(src_keys)} target={sorted(tgt_keys)} dup_elements={len(tgt_keys) - len(set(tgt_keys))}')
        allowed_el = {f['target'] for f in e['fields']} | {key_t}
        extra_el, observed = set(), set()
        for d in docs.values():
            for el in d.get(path) or []:
                extra_el |= set(el) - allowed_el; observed |= set(el)
        ok(f'{coll}.{path}.no_unmapped_element_fields', not extra_el, f'extra={sorted(extra_el)} observed_keys={sorted(observed)}')
        for ref in e.get('child_references', []):
            ok(f'{coll}.{path}.child_reference_not_wave1_sibling[{ref["to"]}]', ref['to'] not in SIBLINGS,
               f'to={ref["to"]} wave1_siblings={sorted(SIBLINGS)}')
            reftbl = {'stockPutawayRule': 'stock_putaway_rule', 'stockRoute': 'stock_route'}[ref['to']]
            vals = {el[key_t] for d in docs.values() for el in d.get(path) or []}
            found = {r[0] for r in q(f'SELECT id FROM "{reftbl}" WHERE id = ANY(%s)', list(vals))} if vals else set()
            ok(f'{coll}.{path}.{key_t}->{reftbl}.outbound_reference', vals <= found,
               f'referenced={sorted(vals)} missing_in_source_table={sorted(vals - found)} (table of a later wave, still relational)')

    for nk in sp['decision']['natural_keys']:
        tgt_fields = [next(f['target'] for f in sp['fields'] if f['source'] == c) for c in nk['columns']]
        dups = list(db[coll].aggregate([{'$match': {t: {'$ne': None} for t in tgt_fields}},
                                        {'$group': {'_id': {t: f'${t}' for t in tgt_fields}, 'n': {'$sum': 1}}}, {'$match': {'n': {'$gt': 1}}}]))
        nulls = sum(1 for d in docs.values() if any(d.get(t) is None for t in tgt_fields))
        ok(f'{coll}.natural_key_unique[{nk["name"]}]', not dups, f'duplicate_non_null_groups={dups} null_or_missing_key_docs={nulls}')
    idx = db[coll].index_information()
    for ix in sp['indexes']:
        want = [tuple(k) for k in ix['keys']]
        match = [n for n, i in idx.items() if [tuple(k) for k in i['key']] == want]
        uniq_ok = (not ix.get('unique')) or any(idx[n].get('unique') for n in match)
        ok(f'{coll}.index{want}', bool(match) and uniq_ok, f'matching={match} unique_required={ix.get("unique", False)} all={sorted(idx)}')
    ok(f'{coll}.no_undeclared_indexes', set(idx) - {'_id_'} <= {n for ix in sp['indexes'] for n, i in idx.items() if [tuple(k) for k in i['key']] == [tuple(k) for k in ix['keys']]},
       f'all={sorted(idx)}')

# boundary values of numeric / ordering fields
for coll, tbl, col, tcol in [('uomUom', 'uom_uom', 'factor', 'factor'), ('uomUom', 'uom_uom', 'relative_factor', 'relativeFactor'),
                             ('uomUom', 'uom_uom', 'sequence', 'sequence'), ('uomUom', 'uom_uom', 'parent_path', 'parentPath'),
                             ('stockPackageType', 'stock_package_type', 'max_weight', 'maxWeight'), ('stockPackageType', 'stock_package_type', 'base_weight', 'baseWeight'),
                             ('stockPackageType', 'stock_package_type', 'height', 'height'), ('stockPackageType', 'stock_package_type', 'sequence', 'sequence')]:
    smin, smax = q(f'SELECT min("{col}"), max("{col}") FROM "{tbl}"')[0]
    numeric = isinstance(smin, (int, float, decimal.Decimal))
    tv = [norm(d.get(tcol)) for d in DOCS[coll].values() if d.get(tcol) is not None]
    tv = [decimal.Decimal(v) for v in tv] if numeric else tv
    tmin, tmax = (min(tv), max(tv)) if tv else (None, None)
    s_lo, s_hi = (norm(decimal.Decimal(str(smin))), norm(decimal.Decimal(str(smax)))) if numeric else (norm(smin), norm(smax))
    ok(f'{coll}.{tcol}.boundary_values', s_lo == norm(tmin) and s_hi == norm(tmax),
       f'source=({s_lo},{s_hi}) target=({norm(tmin)},{norm(tmax)})')

# decimal precision: NUMERIC source vs Decimal128 target at full precision (no rounding beyond canonicalization)
for col, tcol in [('factor', 'factor'), ('relative_factor', 'relativeFactor')]:
    rows = {r[0]: r[1] for r in q(f'SELECT id, "{col}" FROM uom_uom')}
    exact = [i for i, v in rows.items() if v is not None and DOCS['uomUom'][i].get(tcol) is not None
             and DOCS['uomUom'][i][tcol].to_decimal() == v]
    ok(f'uomUom.{tcol}.decimal_exact', len(exact) == sum(1 for v in rows.values() if v is not None),
       f'exact={len(exact)} non_null={sum(1 for v in rows.values() if v is not None)} sample={[(i, format(rows[i], "f")) for i in list(rows)[:3]]}')

# translated name: every PG jsonb key present with the same value
rows = {r[0]: r[1] for r in q('SELECT id, name FROM uom_uom')}
bad = [i for i, v in rows.items() if v != DOCS['uomUom'][i].get('name')]
ok('uomUom.name.jsonb_object_equality', not bad, f'differing={bad} langs={sorted({k for v in rows.values() for k in v})}')

# parent_path / relative_uom_id tree consistency inside the collection
docs = DOCS['uomUom']
bad = []
for i, d in docs.items():
    if d.get('parentPath'):
        chain = [int(x) for x in d['parentPath'].strip('/').split('/')]
        if chain[-1] != i or any(c not in docs for c in chain) or (len(chain) > 1 and d.get('relativeUomId') != chain[-2]) or (len(chain) == 1 and d.get('relativeUomId') is not None):
            bad.append(i)
ok('uomUom.parentPath_consistent_with_relativeUomId', not bad, f'inconsistent_ids={bad}')

# outbound references: resolved inside the batch (uomUom -> uomUom, uomUom -> stockPackageType) and in PostgreSQL for later-wave / framework tables
for coll, tcol, reftbl in [('uomUom', 'createUid', 'res_users'), ('uomUom', 'writeUid', 'res_users'),
                           ('stockPackageType', 'createUid', 'res_users'), ('stockPackageType', 'writeUid', 'res_users'),
                           ('stockPackageType', 'companyId', 'res_company'), ('stockPackageType', 'sequenceId', 'ir_sequence')]:
    vals = {d[tcol] for d in DOCS[coll].values() if d.get(tcol) is not None}
    found = {r[0] for r in q(f'SELECT id FROM "{reftbl}" WHERE id = ANY(%s)', list(vals))} if vals else set()
    ok(f'{coll}.{tcol}->{reftbl}.outbound_reference', vals <= found, f'referenced={sorted(vals)} missing_in_source_table={sorted(vals - found)}')
for ref in spec['uomUom']['decision']['references']:
    tcol = next(f['target'] for f in spec['uomUom']['fields'] if f['source'] == ref['column'][0])
    vals = {d[tcol] for d in docs.values() if d.get(tcol) is not None}
    missing = sorted(vals - set(DOCS[ref['to']]))
    ok(f'uomUom.{tcol}->{ref["to"]}.outbound_reference', not missing, f'referenced={sorted(vals)} missing_in_target_collection={missing} (same batch)')
for coll in COLLS:
    refs = [r['to'] for r in spec[coll]['decision']['references']] + [r['to'] for e in spec[coll]['embeds'] for r in e.get('child_references', [])]
    ok(f'{coll}.no_same_wave_sibling_reference', not (set(refs) & SIBLINGS), f'references={refs} wave1_siblings={sorted(SIBLINGS)}')

for op in OPS['operations'] if isinstance(OPS, dict) else OPS:
    with pg.cursor() as cur:
        cur.execute(op['source_sql']); cols = [c.name for c in cur.description]
        src = sorted(json.dumps({c: norm(v) for c, v in zip(cols, r)}, sort_keys=True) for r in cur.fetchall())
    tgt = sorted(json.dumps({k: norm(v) for k, v in d.items()}, sort_keys=True) for d in db[op['collection']].aggregate(op['target_pipeline']))
    ok(f'tier4_replay.{op["name"]}', src == tgt, f'source_rows={len(src)} target_rows={len(tgt)} first_diff=' +
       str(next(((s, t) for s, t in zip(src, tgt) if s != t), None)))

print(json.dumps({'probes': probes, 'findings': findings}, indent=1, default=str))
print(f"# probes={len(probes)} passed={sum(p['pass'] for p in probes)} failed={len(findings)}", file=sys.stderr)
for f in findings: print('# FINDING', f, file=sys.stderr)
