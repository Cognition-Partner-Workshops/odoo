"""Read-only ORM probe for w1-b02, run twice through `odoo-bin shell` against the same seeded clone:
once on the pre-opt-in tree (PostgreSQL storage) and once on the PR head (MongoDB storage, config
mongodb_migration_db = <clone> so the live odoo_unt12 collections are read unprefixed). The two JSON
outputs must be identical after the `storage` key is dropped. Writes nothing (no write()/create(),
no module update, so no createIndex); verify-orm-compare.py proves that with a before/after snapshot."""
import json, os
cr = env.cr
out = {}
Cat = env['product.category'].sudo()
Tag = env['product.tag'].sudo()
Tmpl = env['product.template'].sudo().with_context(active_test=False)
Prod = env['product.product'].sudo().with_context(active_test=False)
PT = env['stock.picking.type'].sudo().with_context(active_test=False)
companies = env['res.company'].sudo().search([], order='id').ids
PROPS = [f for f in Cat._fields if f.startswith('property_')]
cat_ids = Cat.search([], order='id').ids

def val(v):
    return v.id if hasattr(v, '_name') else v

out['companies'] = companies
out['category_ids'] = cat_ids
out['company_dependent_fields'] = sorted(PROPS)
out['company_dependent'] = {str(c): {str(cat.id): {p: val(cat[p]) for p in PROPS} for cat in Cat.with_company(c).browse(cat_ids)} for c in companies}
out['company_dependent_search'] = {}
for c in companies:
    C = Cat.with_company(c)
    d = {}
    for p in PROPS:
        values = sorted({val(cat[p]) for cat in C.browse(cat_ids)}, key=repr)
        for v in values:
            d[f'{p}={v!r}'] = C.search([(p, '=', v)], order='id').ids
        d[f'{p} set'] = C.search([(p, '!=', False)], order='id').ids
    out['company_dependent_search'][str(c)] = d
out['search_dotted_company_dependent'] = {str(c): {p: Cat.with_company(c).search([(p + '.active', '=', True)], order='id').ids
                                                     for p in PROPS if Cat._fields[p].type == 'many2one' and Cat._fields[p].comodel_name == 'account.account'} for c in companies}
out['search_dotted_plain'] = {str(c): Cat.search([('parent_id.id', '=', c)], order='id').ids for c in cat_ids}
out['search_dotted_plain_name'] = Cat.search([('parent_id.name', 'ilike', 'a')], order='id').ids
try:
    out['get_property_definition'] = env['product.template'].get_property_definition('product_properties.nope')
except Exception as exc:  # noqa: BLE001
    out['get_property_definition'] = f'error: {type(exc).__name__}'

tags = Tag.search([], order='id')
tmpls = Tmpl.search([], order='id'); prods = Prod.search([], order='id'); pts = PT.search([], order='id')
out['tag_templates'] = {str(t.id): sorted(t.product_template_ids.ids) for t in tags}
out['template_tags'] = {str(t.id): sorted(t.product_tag_ids.ids) for t in tmpls}
out['tag_variants'] = {str(t.id): sorted(t.product_product_ids.ids) for t in tags}
out['tag_product_ids'] = {str(t.id): sorted(t.product_ids.ids) for t in tags}
out['variant_additional_tags'] = {str(p.id): sorted(p.additional_product_tag_ids.ids) for p in prods}
out['variant_all_tags'] = {str(p.id): sorted(p.all_product_tag_ids.ids) for p in prods}
out['pickingtype_wave_categories'] = {str(pt.id): sorted(pt.wave_category_ids.ids) for pt in pts}
out['search_pickingtypes_by_category'] = {str(c): sorted(PT.search([('wave_category_ids', 'in', [c])]).ids) for c in cat_ids}
out['search_templates_by_tag'] = {str(t.id): sorted(Tmpl.search([('product_tag_ids', 'in', [t.id])]).ids) for t in tags}
out['search_tags_by_template'] = {str(tm.id): sorted(Tag.search([('product_template_ids', 'in', [tm.id])]).ids) for tm in tmpls}
out['search_variants_by_tag'] = {str(t.id): sorted(Prod.search([('additional_product_tag_ids', 'in', [t.id])]).ids) for t in tags}
out['search_variants_by_all_tags'] = {str(t.id): sorted(Prod.search([('all_product_tag_ids', 'in', [t.id])]).ids) for t in tags}
out['search_tags_by_variant'] = {str(p.id): sorted(Tag.search([('product_product_ids', 'in', [p.id])]).ids) for p in prods}
out['search_tags_without_templates'] = Tag.search([('product_template_ids', '=', False)], order='id').ids
out['search_categories_by_parent'] = {str(c): Cat.search([('parent_id', '=', c)], order='id').ids for c in [False] + cat_ids}
out['search_categories_child_of'] = {str(c): Cat.search([('id', 'child_of', c)], order='id').ids for c in cat_ids}

for model in ['product.category', 'product.removal', 'product.tag', 'product.document', 'product.base.unit']:
    M = env[model].sudo().with_context(active_test=False)
    names = sorted(f.name for f in M._fields.values() if f.store and f.type != 'binary')
    out[f'read:{model}'] = {'fields': names, 'rows': M.search([], order='id').read(names, load=None)}
    out[f'count:{model}'] = M.search_count([])
try:
    from odoo.orm import storage_mongodb as sm
    st = sm.store(Cat)
    out['storage'] = {'prefix': st.prefix, 'database': st.db.name, 'mongodb_models': [m for m in ['product.category', 'product.tag'] if sm.is_mongodb(env[m])]}
except ImportError:
    out['storage'] = {'prefix': None, 'database': None, 'mongodb_models': []}
with open(os.environ['ORM_PROBE_OUT'], 'w') as fh:
    json.dump(out, fh, sort_keys=True, indent=1, default=str)
cr.rollback()
