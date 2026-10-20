"""Independent verify (w1-b02): unlinking an account.account referenced through product.category's
company-dependent properties must behave the same on both storage paths. Run through `odoo-bin shell`
on a THROWAWAY clone, twice: pre-opt-in tree (PostgreSQL) and the head tree with a prefixed MongoDB
namespace (temporary `<db>__` collections only, dropped afterwards). Outputs must be identical after
the `storage` key is dropped. Every PostgreSQL change is rolled back at the end; the live batch
collections are never touched (the MongoDB side writes only to the prefixed copies)."""
import json
import os

Cat = env['product.category'].sudo().with_context(active_test=False)
Acc = env['account.account'].sudo()
companies = env['res.company'].sudo().search([], order='id')
co, other = companies[0], companies[-1]
cats = Cat.search([], order='id')
cat_a, cat_b = cats[0], cats[-1]
PROPS = sorted(f.name for f in Cat._fields.values() if f.company_dependent and f.type == 'many2one')
ACC_PROPS = [p for p in PROPS if Cat._fields[p].comodel_name == 'account.account']
RESTRICT = [p for p in ACC_PROPS if Cat._fields[p].ondelete == 'restrict']
out = {'companies': companies.ids, 'categories': cats.ids, 'ondelete': {p: Cat._fields[p].ondelete for p in ACC_PROPS}}

try:
    from odoo.orm import storage_mongodb as sm
    st = sm.store(Cat)
    out['storage'] = {'prefix': st.prefix, 'database': st.db.name, 'mongodb': sm.is_mongodb(Cat)}
except ImportError:
    sm = st = None
    out['storage'] = {'prefix': None, 'database': None, 'mongodb': False}


def values():
    Cat.invalidate_model(PROPS)
    return {str(c.id): {str(cat.id): {p: (cat[p].id or False) if cat[p] else False for p in PROPS}
                        for cat in Cat.with_company(c).browse(cats.ids)} for c in companies}


def raw(props):
    """The stored company map of each property: PostgreSQL jsonb column or the MongoDB document field."""
    env.flush_all()
    if st is not None and sm.is_mongodb(Cat):
        paths = {p: st.path(Cat, p) for p in props}
        docs = {d['_id']: d for d in st.model_collection(Cat).find({'_id': {'$in': cats.ids}}, {p: 1 for p in paths.values()})}
        res = {}
        for cat_id in cats.ids:
            d = docs.get(cat_id, {})
            res[str(cat_id)] = {}
            for p, path in paths.items():
                v = d
                for key in path.split('.'):
                    v = v.get(key) if isinstance(v, dict) else None
                res[str(cat_id)][p] = v
        return res
    cols = ', '.join(props)
    env.cr.execute(f'SELECT id, {cols} FROM product_category WHERE id IN %s ORDER BY id', (tuple(cats.ids),))
    rows = env.cr.fetchall()
    return {str(r[0]): {p: r[i + 1] for i, p in enumerate(props)} for r in rows}


def attempt(label, fn):
    try:
        with env.cr.savepoint():
            fn()
            env.flush_all()
        out[label] = {'ok': True}
    except Exception as e:  # noqa: BLE001
        out[label] = {'ok': False, 'type': type(e).__name__, 'msg': str(e)}
    out[label + '.values'] = values()
    out[label + '.raw'] = raw(ACC_PROPS)


out['before.values'] = values()
out['before.raw'] = raw(ACC_PROPS)

acc = Acc.with_company(co).create({'name': 'Verify W1-B02 unlink probe', 'code': '999999VW', 'account_type': 'income_other'})
out['account'] = {'id': acc.id, 'company_ids': sorted(acc.company_ids.ids)}
p_r, p_r2 = RESTRICT[0], RESTRICT[-1]
cat_a.with_company(co)[p_r] = acc
cat_b.with_company(co)[p_r2] = acc
cat_b.with_company(other)[p_r] = acc
env.flush_all()
out['linked.values'] = values()
out['linked.raw'] = raw(ACC_PROPS)
out['linked.search'] = {p: Cat.with_company(c).search([(p, '=', acc.id)], order='id').ids for c in companies for p in (p_r, p_r2)} if False else \
    {f'{c.id}:{p}': Cat.with_company(c).search([(p, '=', acc.id)], order='id').ids for c in companies for p in sorted({p_r, p_r2})}
out['linked.search_dotted'] = {f'{c.id}:{p}': Cat.with_company(c).search([(p + '.code', '=', '999999VW')], order='id').ids for c in companies for p in sorted({p_r, p_r2})}

# 1. restrict: blocked while any company value points at the account
attempt('unlink_restrict', lambda: acc.unlink())
# 2. ir.default fallback protects it even without a direct reference
cat_a.with_company(co)[p_r] = False
cat_b.with_company(co)[p_r2] = False
cat_b.with_company(other)[p_r] = False
env.flush_all()
env['ir.default'].sudo().set('product.category', p_r, acc.id, company_id=co.id)
attempt('unlink_default_fallback', lambda: acc.unlink())
env['ir.default'].sudo().discard_records(acc)
# 3. force_delete: the company values pointing at it become null, the others stay
cat_a.with_company(co)[p_r] = acc
cat_b.with_company(other)[p_r] = acc
env.flush_all()
out['relinked.raw'] = raw(ACC_PROPS)
attempt('unlink_force_delete', lambda: acc.with_context(force_delete=True).unlink())
out['after.exists'] = bool(Acc.browse(acc.id).exists())
out['after.search'] = {f'{c.id}:{p_r}': Cat.with_company(c).search([(p_r, '=', acc.id)], order='id').ids for c in companies}
out['after.search_null'] = {f'{c.id}:{p_r}': Cat.with_company(c).search([(p_r, '=', False)], order='id').ids for c in companies}
# 4. an unreferenced account unlinks cleanly on both paths
acc2 = Acc.with_company(co).create({'name': 'Verify W1-B02 unlink probe 2', 'code': '999998VW', 'account_type': 'income_other'})
attempt('unlink_unreferenced', lambda: acc2.unlink())

with open(os.environ['ORM_PROBE_OUT'], 'w') as fh:
    json.dump(out, fh, sort_keys=True, indent=1, default=str)
env.cr.rollback()
