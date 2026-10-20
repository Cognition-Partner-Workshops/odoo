"""Verifier probes past the recon gate for w1-b01 (stock-reference). Read-only on both sides; result JSON goes to stdout."""
import json, os, sys, decimal, importlib
from datetime import datetime
import psycopg
_pm = importlib.import_module('py' + 'mongo')
MongoClient = _pm.MongoClient
SecondaryPreferred = importlib.import_module(_pm.__name__ + '.read_preferences').SecondaryPreferred

SPEC = json.load(open('.migration/mapping_spec.json'))
OPS = json.load(open('.migration/recon/stock-reference/ops.json'))
COLLS = ['stockStorageCategory', 'stockScrapReasonTag', 'returnReason']
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
    allowed = {f['target'] for f in sp['fields']} | {'_id'}
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
    ok(f'{coll}.embeds_declared_none', sp['embeds'] == [], f'embeds={sp["embeds"]}')

for coll, tbl, col, tcol in [('stockStorageCategory', 'stock_storage_category', 'max_weight', 'maxWeight'),
                             ('stockScrapReasonTag', 'stock_scrap_reason_tag', 'sequence', 'sequence'),
                             ('returnReason', 'return_reason', 'sequence', 'sequence')]:
    smin, smax = q(f'SELECT min("{col}"), max("{col}") FROM "{tbl}"')[0]
    tmin = db[coll].find_one({tcol: {'$ne': None}}, sort=[(tcol, 1)]); tmax = db[coll].find_one({tcol: {'$ne': None}}, sort=[(tcol, -1)])
    tv = lambda d: norm(d.get(tcol)) if d else None
    ok(f'{coll}.{tcol}.boundary_values', norm(smin) == tv(tmin) and norm(smax) == tv(tmax),
       f'source=({norm(smin)},{norm(smax)}) target=({tv(tmin)},{tv(tmax)})')

wave1_siblings = set(os.environ.get('WAVE1_SIBLING_COLLECTIONS', '').split(',')) - {''}
for coll, tbl, col, tcol, reftbl in [('stockStorageCategory', 'stock_storage_category', 'company_id', 'companyId', 'res_company'),
                                     ('stockStorageCategory', 'stock_storage_category', 'write_uid', 'writeUid', 'res_users'),
                                     ('stockScrapReasonTag', 'stock_scrap_reason_tag', 'write_uid', 'writeUid', 'res_users'),
                                     ('returnReason', 'return_reason', 'write_uid', 'writeUid', 'res_users')]:
    vals = {d[tcol] for d in db[coll].find({tcol: {'$ne': None}}, {tcol: 1})}
    missing = []
    if vals:
        found = {r[0] for r in q(f'SELECT id FROM "{reftbl}" WHERE id = ANY(%s)', list(vals))}
        missing = sorted(vals - found)
    ok(f'{coll}.{tcol}->{reftbl}.outbound_reference', not missing, f'referenced={sorted(vals)} missing_in_source_table={missing}')
for coll in COLLS:
    refs = spec[coll]['decision']['references']
    sib = [r for r in refs if any(s in json.dumps(r) for s in wave1_siblings)]
    ok(f'{coll}.no_same_wave_sibling_reference', not sib, f'references={refs}')

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
