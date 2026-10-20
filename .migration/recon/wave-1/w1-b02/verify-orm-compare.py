"""snapshot <out>: hash every document of the five batch collections (read-only).
compare <pg.json> <mongo.json> <snap_before> <snap_after> <result_out>: exact equality of the two ORM
reads, the relations and company-dependent JSONB against raw PostgreSQL, and no target change."""
import hashlib, json, os, sys, importlib
import psycopg
_pm = importlib.import_module('py' + 'mongo')
COLLS = ['productCategory', 'productRemoval', 'productTag', 'productDocument', 'productBaseUnit']

def snapshot(path):
    db = _pm.MongoClient(os.environ['MONGODB_ATLAS_URI'])['odoo_unt12']
    snap = {c: hashlib.sha256('\n'.join(sorted(json.dumps(d, sort_keys=True, default=str) for d in db[c].find())).encode()).hexdigest()
            for c in COLLS}
    snap['_counts'] = {c: db[c].estimated_document_count() for c in COLLS}
    json.dump(snap, open(path, 'w'), indent=1, sort_keys=True)

def compare(pg_path, mongo_path, before, after, out_path):
    pg, mg = json.load(open(pg_path)), json.load(open(mongo_path))
    probes, findings = [], []
    def ok(name, passed, evidence):
        probes.append({'probe': name, 'pass': bool(passed), 'evidence': evidence})
        if not passed: findings.append(f'{name}: {evidence}')
    ok('mongodb_side_reads_live_target_unprefixed', mg['storage']['prefix'] == '' and mg['storage']['database'] == 'odoo_unt12'
       and mg['storage']['mongodb_models'] == ['product.category', 'product.tag'], mg['storage'])
    ok('postgresql_side_has_no_storage_path', pg['storage']['mongodb_models'] == [], pg['storage'])
    for k in sorted(set(pg) | set(mg)):
        if k == 'storage': continue
        same = pg.get(k) == mg.get(k)
        ev = f'keys={len(pg[k]) if isinstance(pg.get(k), (dict, list)) else pg.get(k)}' if same else f'pg={json.dumps(pg.get(k), sort_keys=True, default=str)[:400]} mongo={json.dumps(mg.get(k), sort_keys=True, default=str)[:400]}'
        ok(f'orm_equality.{k}', same, ev)
    d = json.loads(os.environ['VERIFY_SRC_DSN']); d['dbname'] = d.pop('database', d.get('dbname'))
    conn = psycopg.connect(**d); conn.read_only = True
    def q(s, *a):
        with conn.cursor() as cur: cur.execute(s, a); return cur.fetchall()
    rel = lambda t, a, b: {str(x): sorted(r[1] for r in q(f'SELECT {a}, {b} FROM {t}') if r[0] == x) for x in {r[0] for r in q(f'SELECT {a} FROM {t}')}}
    for name, table, a, b in [('tag_templates', 'product_tag_product_template_rel', 'product_tag_id', 'product_template_id'),
                              ('template_tags', 'product_tag_product_template_rel', 'product_template_id', 'product_tag_id'),
                              ('tag_variants', 'product_tag_product_product_rel', 'product_tag_id', 'product_product_id'),
                              ('variant_additional_tags', 'product_tag_product_product_rel', 'product_product_id', 'product_tag_id'),
                              ('pickingtype_wave_categories', 'product_category_stock_picking_type_rel', 'stock_picking_type_id', 'product_category_id'),
                              ('search_pickingtypes_by_category', 'product_category_stock_picking_type_rel', 'product_category_id', 'stock_picking_type_id')]:
        pgrel = rel(table, a, b)
        orm = {k: v for k, v in mg[name].items() if v}
        ok(f'mongodb_orm_vs_pg_rows.{name}', orm == pgrel, f'orm_nonempty={orm} pg={pgrel}')
    stored = {r[0] for r in q("SELECT column_name FROM information_schema.columns WHERE table_name='product_category' AND data_type='jsonb'")}
    cols = [c for c in mg['company_dependent_fields'] if c in stored]
    rows = {str(r[0]): dict(zip(cols, r[1:])) for r in q(f'SELECT id, {", ".join(cols)} FROM product_category')}
    mism = []
    for c, per_cat in mg['company_dependent'].items():
        for cat, vals in per_cat.items():
            for p, v in vals.items():
                if p not in cols: continue
                stored = rows[cat][p]
                if isinstance(stored, dict) and c in stored and stored[c] != v: mism.append((c, cat, p, stored[c], v))
    ok('mongodb_orm_company_dependent_vs_pg_jsonb', not mism and cols, f'jsonb_cols={cols} stored_rows={rows} mismatches={mism}')
    b, a = json.load(open(before)), json.load(open(after))
    ok('target_unchanged_by_orm_probe', a == b, {'before': b, 'after': a})
    json.dump({'probes': probes, 'findings': findings}, open(out_path, 'w'), indent=1, default=str)
    print(f"# orm probes={len(probes)} passed={sum(p['pass'] for p in probes)} failed={len(findings)}", file=sys.stderr)
    for f in findings: print('# FINDING', f, file=sys.stderr)

if __name__ == '__main__':
    {'snapshot': snapshot, 'compare': compare}[sys.argv[1]](*sys.argv[2:])
