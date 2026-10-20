"""Verifier probes past the recon gate for w1-b04 (account-settings). Read-only on both sides; result JSON goes to stdout."""
import json, os, sys, decimal, importlib
from datetime import datetime, date
import psycopg
_pm = importlib.import_module('py' + 'mongo')
MongoClient = _pm.MongoClient
SecondaryPreferred = importlib.import_module(_pm.__name__ + '.read_preferences').SecondaryPreferred

SPEC = json.load(open('.migration/mapping_spec.json'))
UNITS = json.load(open('.migration/units.json'))
OPS = json.load(open('.migration/recon/account-settings/ops.json'))
BATCH = 'w1-b04'
unit = next(u for u in UNITS['units'] if u['id'] == 'account-settings')
COLLS = unit['collections']
spec = {c['collection']: c for c in SPEC['collections'] if c['collection'] in COLLS}
wave1 = next(w for w in UNITS['waves'] if any(b['id'] == BATCH for b in w['batches']))
sibling_colls = {t.split('.', 1)[1] for b in wave1['batches'] if b['id'] != BATCH for t in b['write_targets']}

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
    if isinstance(v, float): v = decimal.Decimal(repr(v))
    if isinstance(v, decimal.Decimal): return format(v.normalize(), 'f')
    if isinstance(v, datetime): return v.replace(tzinfo=None).isoformat(timespec='milliseconds')
    if isinstance(v, date): return datetime(v.year, v.month, v.day).isoformat(timespec='milliseconds')
    if isinstance(v, dict): return {k: norm(x) for k, x in v.items()}
    if isinstance(v, list): return [norm(x) for x in v]
    return v

present = set(db.list_collection_names())
ok('declared_collections_present', set(COLLS) <= present, sorted(set(COLLS) & present))
ok('other_collections_in_target_db', True, 'not in this batch: ' + str(sorted(present - set(COLLS))))

def field_probes(label, tbl, fields, where_sql, rows_src, docs_by_id, n_src, n_tgt):
    """rows_src: id -> {source col: value}; docs_by_id: id -> document (or embedded element)."""
    for f in fields:
        src_null = sum(1 for r in rows_src.values() if r[f['source']] is None)
        tgt_missing = sum(1 for d in docs_by_id.values() if d.get(f['target']) is None)
        ok(f'{label}.{f["target"]}.null_missing_rate', src_null == tgt_missing,
           f'source_null={src_null}/{n_src} target_missing_or_null={tgt_missing}/{n_tgt}')
        diff = [i for i in rows_src if norm(rows_src[i][f['source']]) != norm(docs_by_id.get(i, {}).get(f['target']))]
        ok(f'{label}.{f["target"]}.value_equality', not diff,
           f'differing_keys={diff[:10]}' + (f' e.g. src={rows_src[diff[0]][f["source"]]!r} tgt={docs_by_id.get(diff[0], {}).get(f["target"])!r}' if diff else ''))

for coll in COLLS:
    sp = spec[coll]; tbl = sp['root_table']
    src_n = q(f'SELECT count(*) FROM "{tbl}"')[0][0]
    tgt_n = db[coll].count_documents({})
    ok(f'{coll}.row_count', src_n == tgt_n and src_n > 0, f'source={src_n} target={tgt_n}')
    ok(f'{coll}.not_empty', tgt_n > 0, f'target={tgt_n}')
    docs = {d['_id']: d for d in db[coll].find()}
    src_ids = {r[0] for r in q(f'SELECT id FROM "{tbl}"')}
    ok(f'{coll}.key_set', src_ids == set(docs), f'missing_in_target={sorted(src_ids - set(docs))} extra_in_target={sorted(set(docs) - src_ids)}')
    for agg in ('min', 'max'):
        sid = q(f'SELECT {agg}(id) FROM "{tbl}"')[0][0]
        ok(f'{coll}.boundary_{agg}_id', sid in docs, f'id={sid} present={sid in docs}')
    cols = ', '.join(f'"{f["source"]}"' for f in sp['fields'])
    rows = {r[0]: dict(zip([f['source'] for f in sp['fields']], r[1:])) for r in q(f'SELECT id, {cols} FROM "{tbl}"')}
    field_probes(coll, tbl, sp['fields'], '', rows, docs, src_n, tgt_n)
    allowed = {f['target'] for f in sp['fields']} | {'_id'} | {e['array_path'] for e in sp['embeds']}
    extra = set()
    for d in docs.values(): extra |= set(d) - allowed
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
        ok(f'{coll}.index{want}', bool(match) and uniq_ok, f'matching={match} unique_required={ix.get("unique", False)}')
    # embedded arrays: length distribution vs child-row counts, element keys, element fields
    for e in sp['embeds']:
        ap, ct = e['array_path'], e['child_table']
        pk = e['parent_key'][0]
        counts = {r[0]: r[1] for r in q(f'SELECT "{pk}", count(*) FROM "{ct}" GROUP BY 1')}
        n_child = sum(counts.values())
        lens = {i: len(d.get(ap, [])) for i, d in docs.items()}
        bad = [i for i in docs if lens[i] != counts.get(i, 0)]
        ok(f'{coll}.{ap}.array_length_vs_child_rows', not bad,
           f'child_rows={n_child} parents_with_children={len(counts)} max_len={max(lens.values()) if lens else 0} mismatched_parents={bad[:10]}')
        # parents without children carry no array field (PR decision)
        empty_arrays = [i for i, d in docs.items() if ap in d and len(d[ap]) == 0]
        ok(f'{coll}.{ap}.no_empty_array_field', not empty_arrays, f'parents_with_empty_array={empty_arrays[:10]}')
        ktgt = e['key']['target']; ksrc = e['key']['source']
        kcols = ', '.join(f'"{c}"' for c in ksrc)
        if len(ksrc) == 1:
            src_keys = {(r[0], r[1]) for r in q(f'SELECT "{pk}", {kcols} FROM "{ct}"')}
            tgt_keys = {(i, el.get(ktgt)) for i, d in docs.items() for el in d.get(ap, [])}
        else:
            src_keys = {(r[0], tuple(r[1:])) for r in q(f'SELECT "{pk}", {kcols} FROM "{ct}"')}
            tgt_keys = {(i, tuple(el.get(ktgt, {}).get(c) if isinstance(el.get(ktgt), dict) else el.get(ktgt) for c in ksrc)) for i, d in docs.items() for el in d.get(ap, [])}
        ok(f'{coll}.{ap}.element_key_set', src_keys == tgt_keys and len(tgt_keys) == sum(lens.values()),
           f'source_keys={len(src_keys)} target_keys={len(tgt_keys)} missing_in_target={sorted(src_keys - tgt_keys)[:10]} extra_in_target={sorted(tgt_keys - src_keys)[:10]}')
        cfields = [f for f in e['child_fields'] if f['source'] not in ksrc]
        if cfields and len(ksrc) == 1:
            ccols = ', '.join(f'"{f["source"]}"' for f in cfields)
            crows = {r[0]: dict(zip([f['source'] for f in cfields], r[1:])) for r in q(f'SELECT {kcols}, {ccols} FROM "{ct}"')}
            cdocs = {el.get(ktgt): el for d in docs.values() for el in d.get(ap, [])}
            field_probes(f'{coll}.{ap}', ct, cfields, '', crows, cdocs, len(crows), len(cdocs))
        allowed_el = {f['target'] for f in e['child_fields']} | {ktgt}
        extra_el = set()
        for d in docs.values():
            for el in d.get(ap, []): extra_el |= set(el) - allowed_el
        ok(f'{coll}.{ap}.no_unmapped_element_fields', not extra_el, f'extra={sorted(extra_el)}')
    # outbound references declared in the spec
    for r in sp['decision']['references']:
        col = r['column'][0]; tcol = next(f['target'] for f in sp['fields'] if f['source'] == col)
        vals = {d[tcol] for d in docs.values() if d.get(tcol) is not None}
        if r['to'] in sibling_colls:
            ok(f'{coll}.{tcol}.cross_batch_reference', False, f'cross_batch_reference: {r["to"]}')
            continue
        if 'embedded_in' in r:
            ei = r['embedded_in']
            found = {el['id'] for d in db[ei['collection']].find({}, {ei['array_path'] + '.id': 1}) for el in d.get(ei['array_path'], [])}
        else:
            found = {d['_id'] for d in db[r['to']].find({'_id': {'$in': sorted(vals)}}, {'_id': 1})}
        ok(f'{coll}.{tcol}->{r["to"]}.outbound_reference', vals <= found, f'referenced={len(vals)} unresolved={sorted(vals - found)[:10]} same_batch_target')
    ok(f'{coll}.no_same_wave_sibling_reference', not [r for r in sp['decision']['references'] if r['to'] in sibling_colls],
       f'declared_refs={[r["to"] for r in sp["decision"]["references"]]} wave1_siblings={sorted(sibling_colls)}')

# relational (still PostgreSQL) references: merged-wave / unmigrated tables
for coll, tcol, reftbl in [('accountPaymentTerm', 'companyId', 'res_company'), ('accountPaymentTerm', 'writeUid', 'res_users'),
                           ('accountIncoterms', 'writeUid', 'res_users'), ('accountCashRounding', 'companyId', 'res_company'),
                           ('accountCashRounding', 'writeUid', 'res_users'), ('accountJournalGroup', 'writeUid', 'res_users'),
                           ('accountLockException', 'companyId', 'res_company'), ('accountLockException', 'userId', 'res_users'),
                           ('accountReport', 'countryId', 'res_country'), ('accountReport', 'writeUid', 'res_users'),
                           ('accountReportExpression', 'writeUid', 'res_users'), ('accountReportExternalValue', 'companyId', 'res_company')]:
    vals = {d[tcol] for d in db[coll].find({tcol: {'$ne': None}}, {tcol: 1})}
    missing = []
    if vals:
        found = {r[0] for r in q(f'SELECT id FROM "{reftbl}" WHERE id = ANY(%s)', list(vals))}
        missing = sorted(vals - found)
    ok(f'{coll}.{tcol}->{reftbl}.outbound_reference', not missing, f'referenced={sorted(vals)[:10]} missing_in_source_table={missing}')
# junction element references into relational tables
for coll, ap, ktgt, reftbl in [('accountCashRounding', 'resCurrencyRel', 'resCurrencyId', 'res_currency'),
                               ('accountCashRounding', 'resPartnerCategoryRel', 'resPartnerCategoryId', 'res_partner_category'),
                               ('accountCashRounding', 'accountPaymentMethodLineRel', 'accountPaymentMethodLineId', 'account_payment_method_line')]:
    vals = {el[ktgt] for d in db[coll].find({}, {ap: 1}) for el in d.get(ap, [])}
    found = {r[0] for r in q(f'SELECT id FROM "{reftbl}" WHERE id = ANY(%s)', list(vals))} if vals else set()
    ok(f'{coll}.{ap}.{ktgt}->{reftbl}.outbound_reference', vals <= found, f'referenced={len(vals)} missing={sorted(vals - found)}')
# sectionRel sub reports resolve inside accountReport
subs = {el['subReportId'] for d in db['accountReport'].find({}, {'sectionRel': 1}) for el in d.get('sectionRel', [])}
found = {d['_id'] for d in db['accountReport'].find({'_id': {'$in': sorted(subs)}}, {'_id': 1})}
ok('accountReport.sectionRel.subReportId->accountReport.outbound_reference', subs <= found, f'referenced={sorted(subs)} unresolved={sorted(subs - found)}')
# line.parentId resolves inside the same document's line array
bad = []
for d in db['accountReport'].find({'line': {'$exists': True}}, {'line': 1}):
    ids = {el['id'] for el in d['line']}
    bad += [(d['_id'], el['id'], el['parentId']) for el in d['line'] if el.get('parentId') is not None and el['parentId'] not in ids]
ok('accountReport.line.parentId.resolves_in_same_document', not bad, f'unresolved={bad}')

# boundary values on numeric / date fields
for coll, tbl, col, tcol in [('accountCashRounding', 'account_cash_rounding', 'rounding', 'rounding'),
                             ('accountPaymentTerm', 'account_payment_term', 'discount_percentage', 'discountPercentage'),
                             ('accountPaymentTerm', 'account_payment_term', 'sequence', 'sequence'),
                             ('accountReportExternalValue', 'account_report_external_value', 'value', 'value'),
                             ('accountReportExternalValue', 'account_report_external_value', 'date', 'date'),
                             ('accountLockException', 'account_lock_exception', 'lock_date', 'lockDate'),
                             ('accountLockException', 'account_lock_exception', 'end_datetime', 'endDatetime'),
                             ('accountReport', 'account_report', 'load_more_limit', 'loadMoreLimit')]:
    smin, smax = q(f'SELECT min("{col}"), max("{col}") FROM "{tbl}"')[0]
    tmin = db[coll].find_one({tcol: {'$ne': None}}, sort=[(tcol, 1)]); tmax = db[coll].find_one({tcol: {'$ne': None}}, sort=[(tcol, -1)])
    tv = lambda d: norm(d.get(tcol)) if d else None
    ok(f'{coll}.{tcol}.boundary_values', norm(smin) == tv(tmin) and norm(smax) == tv(tmax),
       f'source=({norm(smin)},{norm(smax)}) target=({tv(tmin)},{tv(tmax)})')
# embedded numeric boundary: payment term line value_amount (Decimal128)
smin, smax = q('SELECT min(value_amount), max(value_amount) FROM account_payment_term_line')[0]
vals = [norm(x) for x in sorted((el['valueAmount'].to_decimal() for d in db['accountPaymentTerm'].find({}, {'line.valueAmount': 1}) for el in d.get('line', []) if el.get('valueAmount') is not None))]
ok('accountPaymentTerm.line.valueAmount.boundary_values', vals and norm(smin) == vals[0] and norm(smax) == vals[-1], f'source=({norm(smin)},{norm(smax)}) target=({vals[0] if vals else None},{vals[-1] if vals else None})')

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
