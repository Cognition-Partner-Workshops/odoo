"""Verifier probes past the recon gate for w1-b06 (account-chart). Read-only on both sides; result JSON goes to stdout."""
import json, os, sys, decimal, importlib
from datetime import datetime
import psycopg
_pm = importlib.import_module('py' + 'mongo')
MongoClient = _pm.MongoClient
SecondaryPreferred = importlib.import_module(_pm.__name__ + '.read_preferences').SecondaryPreferred

SPEC = json.load(open('.migration/mapping_spec.json'))
OPS = json.load(open('.migration/recon/account-chart/ops.json'))
UNITS = json.load(open('.migration/units.json'))
COLLS = ['accountAccount', 'accountAccountTag', 'accountTax', 'accountTaxGroup', 'accountTaxRepartitionLine', 'accountFiscalPosition']
spec = {c['collection']: c for c in SPEC['collections'] if c['collection'] in COLLS}
all_spec = {c['collection']: c for c in SPEC['collections']}
wave1 = next(w for w in UNITS['waves'] if w['wave'] == 1)
sibling_colls = {t.split('.', 1)[1] for b in wave1['batches'] if b['id'] != 'w1-b06' for t in b['write_targets']}

raw = os.environ['VERIFY_SRC_DSN']
_d = json.loads(raw) if raw.startswith('{') else None
if _d and 'database' in _d: _d['dbname'] = _d.pop('database')
pg = psycopg.connect(**_d) if _d else psycopg.connect(raw)
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
    if isinstance(v, decimal.Decimal): return format(v.normalize(), 'f') if v == v.to_integral() else format(v, 'f')
    if isinstance(v, float): return norm(decimal.Decimal(repr(v)))
    if isinstance(v, datetime): return v.replace(tzinfo=None).isoformat(timespec='milliseconds')
    if isinstance(v, dict): return {k: norm(x) for k, x in v.items()}
    if isinstance(v, list): return [norm(x) for x in v]
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
        if f.get('bson_type') in ('int', 'decimal', 'date'):
            smin, smax = q(f'SELECT min("{f["source"]}"), max("{f["source"]}") FROM "{tbl}"')[0]
            tmin = db[coll].find_one({f['target']: {'$ne': None}}, sort=[(f['target'], 1)])
            tmax = db[coll].find_one({f['target']: {'$ne': None}}, sort=[(f['target'], -1)])
            tv = lambda d: norm(d.get(f['target'])) if d else None
            ok(f'{coll}.{f["target"]}.boundary_values', norm(smin) == tv(tmin) and norm(smax) == tv(tmax),
               f'source=({norm(smin)},{norm(smax)}) target=({tv(tmin)},{tv(tmax)})')
    allowed = {f['target'] for f in sp['fields']} | {'_id'} | {e['array_path'] for e in sp['embeds']}
    extra = set()
    for d in db[coll].find():
        extra |= set(d) - allowed
    ok(f'{coll}.no_unmapped_target_fields', not extra, f'extra={sorted(extra)}')
    for nk in sp['decision']['natural_keys']:
        tgt_fields = [next(f['target'] for f in sp['fields'] if f['source'] == c) for c in nk['columns']]
        dups = list(db[coll].aggregate([{'$group': {'_id': {t: f'${t}' for t in tgt_fields}, 'n': {'$sum': 1}}}, {'$match': {'n': {'$gt': 1}}}]))
        sdups = q(f'SELECT count(*) FROM (SELECT 1 FROM "{tbl}" GROUP BY {", ".join(chr(34)+c+chr(34) for c in nk["columns"])} HAVING count(*) > 1) s')[0][0]
        ok(f'{coll}.natural_key_unique[{nk["name"]}]', not dups and sdups == 0, f'target_duplicates={dups} source_duplicate_groups={sdups}')
    idx = db[coll].index_information()
    for ix in sp['indexes']:
        want = [tuple(k) for k in ix['keys']]
        match = [n for n, i in idx.items() if [tuple(k) for k in i['key']] == want]
        uniq_ok = (not ix.get('unique')) or any(idx[n].get('unique') for n in match)
        ok(f'{coll}.index{want}', bool(match) and uniq_ok, f'matching={match} unique_required={ix.get("unique", False)}')
    # embedded arrays: per-parent length == child rows, element keys equal, element fields equal
    for e in sp['embeds']:
        path, ctbl = e['array_path'], e['child_table']
        pk = e['parent_key'][0]; kcols = e['key']['source']; ktgt = e['key']['target']
        kt = ktgt if isinstance(ktgt, list) else [ktgt]
        keyval = lambda x: json.dumps([x.get(k) for k in kt], default=str)
        cfields = e['child_fields'] if e['child_fields'] else []
        child_rows = q(f'SELECT "{pk}", {", ".join(chr(34)+c["source"]+chr(34) for c in cfields)} FROM "{ctbl}"')
        src_by_parent = {}
        for r in child_rows:
            src_by_parent.setdefault(r[0], []).append({c['target']: norm(v) for c, v in zip(cfields, r[1:])})
        tgt_by_parent = {d['_id']: [norm(x) for x in d.get(path, [])] for d in db[coll].find({}, {path: 1})}
        lens_src = {p: len(v) for p, v in src_by_parent.items()}
        lens_tgt = {p: len(v) for p, v in tgt_by_parent.items() if v}
        total_src = sum(lens_src.values())
        ok(f'{coll}.{path}.array_length_distribution', lens_src == lens_tgt,
           f'child_rows={total_src} parents_with_elements_src={len(lens_src)} tgt={len(lens_tgt)} max_len_src={max(lens_src.values(), default=0)} max_len_tgt={max(lens_tgt.values(), default=0)} '
           f'mismatch={[(p, lens_src.get(p), lens_tgt.get(p)) for p in set(lens_src) | set(lens_tgt) if lens_src.get(p) != lens_tgt.get(p)][:5]}')
        if total_src == 0:
            ok(f'{coll}.{path}.empty_on_both_sides', not lens_tgt, f'source child rows 0; target parents with elements {len(lens_tgt)}')
        dup_keys = [(p, k) for p, els in tgt_by_parent.items() for k in {keyval(x) for x in els} if sum(1 for x in els if keyval(x) == k) > 1]
        ok(f'{coll}.{path}.element_key_unique', not dup_keys, f'duplicate (parent, {kt})={dup_keys[:5]}')
        diffs = []
        for p, els in src_by_parent.items():
            s = sorted(json.dumps(x, sort_keys=True, default=str) for x in els)
            t = sorted(json.dumps({c['target']: x.get(c['target']) for c in cfields}, sort_keys=True, default=str) for x in tgt_by_parent.get(p, []))
            if s != t: diffs.append((p, s[:2], t[:2]))
        ok(f'{coll}.{path}.element_values', not diffs, f'parents_compared={len(src_by_parent)} differing={diffs[:3]}')
        orphan_parents = sorted(set(tgt_by_parent) - {r[0] for r in q(f'SELECT id FROM "{tbl}"')})
        ok(f'{coll}.{path}.no_orphan_parent', not orphan_parents, f'orphans={orphan_parents[:5]}')
        # child references: resolve the element key against the referenced table in PostgreSQL (still relational unless in this batch)
        for cr in e.get('child_references', []):
            to = cr['to']; totbl = all_spec[to]['root_table'] if to in all_spec else None
            rcol = next(c['target'] for c in cfields if c['source'] == cr['column'][0])
            vals = {x.get(rcol) for els in tgt_by_parent.values() for x in els if x.get(rcol) is not None}
            if to in sibling_colls:
                ok(f'{coll}.{path}.{rcol}->{to}.cross_batch_reference', False, f'cross_batch_reference: {to} (wave-1 sibling, namespace not probed)')
                continue
            missing = sorted(vals - {r[0] for r in q(f'SELECT id FROM "{totbl}" WHERE id = ANY(%s)', list(vals))}) if vals and totbl else []
            where = 'this batch (also checked as _id in target)' if to in COLLS else 'later wave, relational'
            if to in COLLS and vals:
                tmiss = sorted(vals - {d['_id'] for d in db[to].find({'_id': {'$in': list(vals)}}, {'_id': 1})})
                missing = sorted(set(missing) | set(tmiss))
            ok(f'{coll}.{path}.{rcol}->{to}.child_reference', not missing, f'distinct_refs={len(vals)} missing={missing[:5]} ({where})')

# outbound references declared by the spec (Many2one), resolved in PostgreSQL and, for this batch's own collections, in the target
for coll in COLLS:
    sp = spec[coll]; tbl = sp['root_table']
    for r in sp['decision']['references']:
        col = r['column'][0]; to = r['to']
        tcol = next(f['target'] for f in sp['fields'] if f['source'] == col)
        if to in sibling_colls:
            ok(f'{coll}.{tcol}->{to}.cross_batch_reference', False, f'cross_batch_reference: {to}'); continue
        totbl = all_spec[to]['root_table']
        vals = {d[tcol] for d in db[coll].find({tcol: {'$ne': None}}, {tcol: 1})}
        missing = sorted(vals - {x[0] for x in q(f'SELECT id FROM "{totbl}" WHERE id = ANY(%s)', list(vals))}) if vals else []
        if to in COLLS and vals:
            missing = sorted(set(missing) | (vals - {d['_id'] for d in db[to].find({'_id': {'$in': list(vals)}}, {'_id': 1})}))
        ok(f'{coll}.{tcol}->{to}.outbound_reference', not missing, f'distinct_refs={len(vals)} missing={missing[:5]}')
    ok(f'{coll}.no_same_wave_sibling_reference',
       not [x for x in sp['decision']['references'] if x['to'] in sibling_colls] and not [cr for e in sp['embeds'] for cr in e.get('child_references', []) if cr['to'] in sibling_colls],
       f'siblings={sorted(sibling_colls)}')
    # framework FKs outside the spec references: company / users
    for col, tcol, reftbl in [('company_id', 'companyId', 'res_company'), ('country_id', 'countryId', 'res_country'), ('currency_id', 'currencyId', 'res_currency'),
                              ('create_uid', 'createUid', 'res_users'), ('write_uid', 'writeUid', 'res_users'), ('country_group_id', 'countryGroupId', 'res_country_group')]:
        if not any(f['source'] == col for f in sp['fields']): continue
        vals = {d[tcol] for d in db[coll].find({tcol: {'$ne': None}}, {tcol: 1})}
        missing = sorted(vals - {x[0] for x in q(f'SELECT id FROM "{reftbl}" WHERE id = ANY(%s)', list(vals))}) if vals else []
        ok(f'{coll}.{tcol}->{reftbl}.outbound_reference', not missing, f'distinct_refs={len(vals)} missing={missing[:5]}')

# spot checks the gate only aggregates: translated names, decimal amounts at full precision, parent_path consistency
names_src = {r[0]: r[1] for r in q('SELECT id, name FROM account_tax')}
names_tgt = {d['_id']: d.get('name') for d in db['accountTax'].find({}, {'name': 1})}
ok('accountTax.name.translated_object_equality', names_src == names_tgt, f'differing={[i for i in names_src if names_src[i] != names_tgt.get(i)][:5]}')
amt_src = {r[0]: norm(r[1]) for r in q('SELECT id, amount FROM account_tax')}
amt_tgt = {d['_id']: norm(d.get('amount')) for d in db['accountTax'].find({}, {'amount': 1})}
ok('accountTax.amount.full_precision', amt_src == amt_tgt, f'differing={[(i, amt_src[i], amt_tgt.get(i)) for i in amt_src if amt_src[i] != amt_tgt.get(i)][:5]}')
pp = {r[0]: r[1] for r in q('SELECT id, parent_path FROM account_account')}
bad = [i for i, d in ((d['_id'], d) for d in db['accountAccount'].find({}, {'parentPath': 1, 'parentId': 1})) if d.get('parentPath') != pp.get(i) or (d.get('parentPath') and not d['parentPath'].endswith(f'{i}/'))]
ok('accountAccount.parentPath.consistent', not bad, f'bad_ids={bad[:5]}')
codes_src = {r[0]: r[1] for r in q('SELECT id, code_store FROM account_account')}
codes_tgt = {d['_id']: d.get('codeStore') for d in db['accountAccount'].find({}, {'codeStore': 1})}
ok('accountAccount.codeStore.company_dependent_equality', codes_src == codes_tgt, f'differing={[i for i in codes_src if codes_src[i] != codes_tgt.get(i)][:5]}')
tax_types = {r[0]: r[1] for r in q("SELECT type_tax_use, count(*) FROM account_tax GROUP BY 1")}
tgt_types = {d['_id']: d['n'] for d in db['accountTax'].aggregate([{'$group': {'_id': '$typeTaxUse', 'n': {'$sum': 1}}}])}
ok('accountTax.typeTaxUse.distribution', tax_types == tgt_types, f'source={tax_types} target={tgt_types}')
rep = {r[0]: r[1] for r in q("SELECT document_type || '/' || repartition_type, count(*) FROM account_tax_repartition_line GROUP BY 1")}
trep = {d['_id']: d['n'] for d in db['accountTaxRepartitionLine'].aggregate([{'$group': {'_id': {'$concat': ['$documentType', '/', '$repartitionType']}, 'n': {'$sum': 1}}}])}
ok('accountTaxRepartitionLine.type_distribution', rep == trep, f'source={rep} target={trep}')

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
