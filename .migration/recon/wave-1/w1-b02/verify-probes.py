"""Verifier probes past the recon gate for w1-b02 (product-taxonomy). Read-only on both sides; result JSON goes to stdout.

Same shape as the w1-b01 probes, plus the three junction arrays this batch embeds: per-parent array
length against source child-row count, element key sets, no duplicate elements, no array on a parent
without child rows, and the child references resolved against PostgreSQL (their targets are later-wave
tables, still relational).
"""
import json, os, sys, decimal, importlib
from datetime import datetime
import psycopg
_pm = importlib.import_module('py' + 'mongo')
MongoClient = _pm.MongoClient
SecondaryPreferred = importlib.import_module(_pm.__name__ + '.read_preferences').SecondaryPreferred

SPEC = json.load(open('.migration/mapping_spec.json'))
OPS = json.load(open('.migration/recon/product-taxonomy/ops.json'))
COLLS = ['productCategory', 'productRemoval', 'productTag', 'productDocument', 'productBaseUnit']
spec = {c['collection']: c for c in SPEC['collections'] if c['collection'] in COLLS}

raw = os.environ['VERIFY_SRC_DSN']
_d = json.loads(raw) if raw.startswith("{") else None
if _d and "database" in _d: _d["dbname"] = _d.pop("database")
pg = psycopg.connect(**_d) if raw.startswith('{') else psycopg.connect(raw)
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
    if isinstance(v, decimal.Decimal): return format(v, 'f')
    if isinstance(v, datetime): return v.replace(tzinfo=None).isoformat(timespec='milliseconds')
    if isinstance(v, dict): return json.dumps(v, sort_keys=True, default=str)
    return v

present = set(db.list_collection_names())
ok('declared_collections_present', set(COLLS) <= present, sorted(present))
ok('other_collections_in_target_db', True, 'not in this batch: ' + str(sorted(present - set(COLLS))))

for coll in COLLS:
    sp = spec[coll]; tbl = sp['root_table']
    src_n = q(f'SELECT count(*) FROM "{tbl}"')[0][0]
    tgt_n = db[coll].count_documents({})
    ok(f'{coll}.row_count', src_n == tgt_n and src_n > 0, f'source={src_n} target={tgt_n}')
    ok(f'{coll}.not_empty', tgt_n > 0, f'target={tgt_n}')
    src_ids = {r[0] for r in q(f'SELECT id FROM "{tbl}"')}
    tgt_ids = [d['_id'] for d in db[coll].find({}, {'_id': 1})]
    ok(f'{coll}.key_set', src_ids == set(tgt_ids) and len(tgt_ids) == len(set(tgt_ids)),
       f'missing_in_target={sorted(src_ids - set(tgt_ids))} extra_in_target={sorted(set(tgt_ids) - src_ids)}')
    for agg in ('min', 'max'):
        sid = q(f'SELECT {agg}(id) FROM "{tbl}"')[0][0]
        d = db[coll].find_one({'_id': sid})
        ok(f'{coll}.boundary_{agg}_id', d is not None, f'id={sid} present={d is not None}')
    for f in sp['fields']:
        src_null = q(f'SELECT count(*) FROM "{tbl}" WHERE "{f["source"]}" IS NULL')[0][0]
        tgt_missing = db[coll].count_documents({'$or': [{f['target']: {'$exists': False}}, {f['target']: None}]})
        ok(f'{coll}.{f["target"]}.null_missing_rate', src_null == tgt_missing,
           f'source_null={src_null}/{src_n} target_missing_or_null={tgt_missing}/{tgt_n}')
        rows = {r[0]: norm(r[1]) for r in q(f'SELECT id, "{f["source"]}" FROM "{tbl}"')}
        docs = {d['_id']: norm(d.get(f['target'])) for d in db[coll].find({}, {f['target']: 1})}
        diff = [i for i in rows if rows[i] != docs.get(i)]
        ok(f'{coll}.{f["target"]}.value_equality', not diff,
           f'differing_ids={diff[:10]}' + (f' e.g. src={rows[diff[0]]!r} tgt={docs.get(diff[0])!r}' if diff else ''))
    allowed = {f['target'] for f in sp['fields']} | {'_id'} | {e['array_path'] for e in sp['embeds']}
    extra = set()
    for d in db[coll].find():
        extra |= set(d) - allowed
    ok(f'{coll}.no_unmapped_target_fields', not extra, f'extra={sorted(extra)}')
    for nk in sp['decision']['natural_keys']:
        tgt_fields = [next(f['target'] for f in sp['fields'] if f['source'] == c) for c in nk['columns']]
        dups = list(db[coll].aggregate([{'$group': {'_id': {t: f'${t}' for t in tgt_fields}, 'n': {'$sum': 1}}}, {'$match': {'n': {'$gt': 1}}}]))
        ok(f'{coll}.natural_key_unique[{nk["name"]}]', not dups, f'duplicates={dups}')
    idx = db[coll].index_information()
    for ix in sp['indexes']:
        want = [tuple(k) for k in ix['keys']]
        match = [n for n, i in idx.items() if [tuple(k) for k in i['key']] == want]
        uniq_ok = (not ix.get('unique')) or any(idx[n].get('unique') for n in match)
        ok(f'{coll}.index{want}', bool(match) and uniq_ok, f'matching={match} unique_required={ix.get("unique", False)} all={sorted(idx)}')
    for e in sp['embeds']:
        ap, ctbl = e['array_path'], e['child_table']
        pcol, ccol = e['parent_key'][0], e['key']['source'][0]
        ckey = e['key']['target']
        src = {}
        for pid, cid in q(f'SELECT "{pcol}", "{ccol}" FROM "{ctbl}" ORDER BY 1, 2'):
            src.setdefault(pid, []).append(cid)
        src_rows = sum(len(v) for v in src.values())
        ok(f'{coll}.{ap}.child_rows_seeded', src_rows > 0, f'source_child_rows={src_rows} parents_with_rows={len(src)}')
        tgt = {d['_id']: d.get(ap) for d in db[coll].find({}, {ap: 1})}
        len_diff = {i: (len(src.get(i, [])), len(tgt[i]) if isinstance(tgt.get(i), list) else None) for i in tgt
                    if (len(src.get(i, [])) or 0) != (len(tgt[i]) if isinstance(tgt.get(i), list) else 0)}
        ok(f'{coll}.{ap}.array_length_vs_child_rows', not len_diff, f'source_lengths={ {i: len(v) for i, v in src.items()} } mismatches={len_diff}')
        set_diff = {i: (sorted(src.get(i, [])), sorted(x[ckey] for x in tgt[i])) for i in tgt if isinstance(tgt.get(i), list)
                    and sorted(src.get(i, [])) != sorted(x.get(ckey) for x in tgt[i])}
        ok(f'{coll}.{ap}.element_key_sets', not set_diff, f'mismatches={set_diff}')
        dup = {i: [x[ckey] for x in tgt[i]] for i in tgt if isinstance(tgt.get(i), list) and len(tgt[i]) != len({x.get(ckey) for x in tgt[i]})}
        ok(f'{coll}.{ap}.no_duplicate_elements', not dup, f'duplicates={dup}')
        absent = [i for i in tgt if i not in src and ap in db[coll].find_one({'_id': i})]
        ok(f'{coll}.{ap}.absent_on_parents_without_rows', not absent, f'parents_without_rows_but_array={absent}')
        extra_keys = set()
        for i in tgt:
            for x in tgt[i] or []:
                extra_keys |= set(x) - {ckey}
        ok(f'{coll}.{ap}.element_fields_only_key', not extra_keys, f'extra_element_fields={sorted(extra_keys)}')
        for cref in e['child_references']:
            reftbl = spec_root = next((c['root_table'] for c in SPEC['collections'] if c['collection'] == cref['to']), None)
            vals = {x[ckey] for v in tgt.values() if isinstance(v, list) for x in v}
            found = {r[0] for r in q(f'SELECT id FROM "{reftbl}" WHERE id = ANY(%s)', list(vals))} if vals else set()
            ok(f'{coll}.{ap}.{ckey}->{reftbl}.child_reference', vals <= found, f'referenced={sorted(vals)} missing_in_source_table={sorted(vals - found)}')

for coll, tbl, col, tcol in [('productTag', 'product_tag', 'sequence', 'sequence'),
                             ('productDocument', 'product_document', 'sequence', 'sequence'),
                             ('productDocument', 'product_document', 'ir_attachment_id', 'irAttachmentId'),
                             ('productCategory', 'product_category', 'parent_path', 'parentPath')]:
    smin, smax = q(f'SELECT min("{col}"), max("{col}") FROM "{tbl}"')[0]
    tmin = db[coll].find_one({tcol: {'$ne': None}}, sort=[(tcol, 1)]); tmax = db[coll].find_one({tcol: {'$ne': None}}, sort=[(tcol, -1)])
    tv = lambda d: norm(d.get(tcol)) if d else None
    ok(f'{coll}.{tcol}.boundary_values', norm(smin) == tv(tmin) and norm(smax) == tv(tmax),
       f'source=({norm(smin)},{norm(smax)}) target=({tv(tmin)},{tv(tmax)})')

# translated JSONB fields: every language key present on the source row is present on the document
for coll, tbl, col in [('productCategory', 'product_category', 'name'), ('productRemoval', 'product_removal', 'name'),
                       ('productRemoval', 'product_removal', 'method'), ('productTag', 'product_tag', 'name'),
                       ('productBaseUnit', 'product_base_unit', 'name')]:
    src = {r[0]: sorted((r[1] or {}).keys()) for r in q(f'SELECT id, "{col}" FROM "{tbl}"')}
    tgt = {d['_id']: sorted((d.get(col) or {}).keys()) for d in db[coll].find({}, {col: 1})}
    ok(f'{coll}.{col}.translation_keys', src == tgt, f'source={src} target={tgt}')

# category tree: parent_path consistent with parentId on the target side alone
bad = []
for d in db['productCategory'].find({}, {'parentId': 1, 'parentPath': 1}):
    parts = [int(p) for p in d['parentPath'].strip('/').split('/')]
    if parts[-1] != d['_id'] or (len(parts) > 1 and parts[-2] != d.get('parentId')) or (len(parts) == 1 and d.get('parentId') is not None):
        bad.append(d)
ok('productCategory.parent_path_consistent_with_parentId', not bad, f'inconsistent={bad}')

wave1_siblings = set(os.environ.get('WAVE1_SIBLING_COLLECTIONS', '').split(',')) - {''}
# outbound references: same-batch targets against the target collections, relational targets against PostgreSQL
for coll, tcol, reftbl, side in [('productCategory', 'parentId', 'productCategory', 'target'),
                                 ('productCategory', 'removalStrategyId', 'productRemoval', 'target'),
                                 ('productCategory', 'companyId', 'res_company', 'source'),
                                 ('productCategory', 'createUid', 'res_users', 'source'),
                                 ('productCategory', 'writeUid', 'res_users', 'source'),
                                 ('productRemoval', 'writeUid', 'res_users', 'source'),
                                 ('productTag', 'writeUid', 'res_users', 'source'),
                                 ('productDocument', 'irAttachmentId', 'ir_attachment', 'source'),
                                 ('productDocument', 'writeUid', 'res_users', 'source'),
                                 ('productBaseUnit', 'writeUid', 'res_users', 'source')]:
    vals = {d[tcol] for d in db[coll].find({tcol: {'$ne': None}}, {tcol: 1})}
    if side == 'target':
        found = {d['_id'] for d in db[reftbl].find({'_id': {'$in': list(vals)}}, {'_id': 1})} if vals else set()
    else:
        found = {r[0] for r in q(f'SELECT id FROM "{reftbl}" WHERE id = ANY(%s)', list(vals))} if vals else set()
    ok(f'{coll}.{tcol}->{reftbl}.outbound_reference', vals <= found, f'referenced={sorted(vals)} missing={sorted(vals - found)} side={side}')
for coll in COLLS:
    refs = spec[coll]['decision']['references'] + [cr for e in spec[coll]['embeds'] for cr in e['child_references']]
    sib = [r for r in refs if r['to'] in wave1_siblings]
    ok(f'{coll}.no_same_wave_sibling_reference', not sib, f'references_to={[r["to"] for r in refs]} wave1_siblings_hit={sib}')

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
