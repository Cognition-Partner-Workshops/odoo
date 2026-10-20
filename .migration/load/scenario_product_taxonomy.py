"""ORM scenario for batch w1-b02 (unit product-taxonomy) on the MongoDB storage path.

Same harness as scenario_stock_reference.py (w1-b01): run on the run branch against the worker's
seeded clone, whose documents are the loaded ones (conf key mongodb_migration_db = <clone> keeps
the collections unprefixed):

    /home/ubuntu/.venvs/odoo/bin/python odoo-bin shell -c <conf> -d <clone> --no-http \\
        < .migration/load/scenario_product_taxonomy.py

Reads are compared with the clone's PostgreSQL rows (the clone still carries the legacy columns);
every write happens in one transaction that is rolled back at the end, and the documents are
hashed before and after to show the journal left the loaded collections untouched.
"""
import hashlib

from bson.json_util import dumps

from odoo.fields import Command

cr = env.cr
st = env.registry.mongo_store
assert st.prefix == '', f"collections are prefixed {st.prefix!r}: set mongodb_migration_db to this database"
MODELS = {
    'product.category': 'parent_id DESC NULLS FIRST, name->>\'en_US\' COLLATE "C", id',
    'product.removal': 'id',
    'product.tag': 'sequence, id',
    'product.document': 'sequence, id',
    'product.base.unit': 'name->>\'en_US\' COLLATE "C", id',
}
checks = []


def check(name, ok, detail=''):
    checks.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}{' -- ' + str(detail) if detail else ''}")


def snapshot():
    return {m: hashlib.sha256(dumps(list(st.model_collection(env[m]).find().sort('_id', 1)), sort_keys=True).encode()).hexdigest()
            for m in MODELS}


def sql(query, params=None):
    cr.execute(query, params)
    return cr.fetchall()


before = snapshot()

# 1. search order and counts against PostgreSQL
for model, order in MODELS.items():
    M = env[model]
    pg_ids = [r[0] for r in sql(f"SELECT id FROM {M._table} ORDER BY {order}")]
    if model == 'product.document':
        # _order = 'sequence, name': name is the inherited ir.attachment column
        pg_ids = [r[0] for r in sql("SELECT d.id FROM product_document d JOIN ir_attachment a ON a.id = d.ir_attachment_id "
                                    "ORDER BY d.sequence, a.name COLLATE \"C\", d.id")]
    check(f"{model} search([]) order", M.search([]).ids == pg_ids, pg_ids)
    check(f"{model} search_count", M.search_count([]) == len(pg_ids))
    check(f"{model} exists()", M.browse(pg_ids).exists().ids == pg_ids and not M.browse(max(pg_ids) + 1000).exists())

# 2. field values against PostgreSQL rows
rows = sql("SELECT id, name->>'en_US', parent_id, parent_path, removal_strategy_id, packaging_reserve_method FROM product_category ORDER BY id")
cats = env['product.category'].browse([r[0] for r in rows])
check("product.category field values", all(
    (c.name, c.parent_id.id or None, c.parent_path, c.removal_strategy_id.id or None, c.packaging_reserve_method or None) == r[1:]
    for c, r in zip(cats, rows)), [(c.name, c.parent_path) for c in cats][:3])
check("product.category complete_name (recursive compute over the many2one)",
      cats.filtered(lambda c: c.id == 5).complete_name == 'Furniture / Office')
rows = sql("SELECT id, name->>'en_US', method->>'en_US' FROM product_removal ORDER BY id")
removals = env['product.removal'].browse([r[0] for r in rows])
check("product.removal field values (translated name, method)", all((x.name, x.method) == (r[1], r[2]) for x, r in zip(removals, rows)))
rows = sql("SELECT id, name->>'en_US', sequence, color, visible_to_customers FROM product_tag ORDER BY id")
tags = env['product.tag'].browse([r[0] for r in rows])
check("product.tag field values", all((t.name, t.sequence, t.color, t.visible_to_customers) == tuple(r[1:]) for t, r in zip(tags, rows)),
      [(t.name, t.color) for t in tags])
rows = sql("SELECT id, name->>'en_US' FROM product_base_unit ORDER BY id")
units = env['product.base.unit'].browse([r[0] for r in rows])
check("product.base.unit field values", all(u.name == r[1] for u, r in zip(units, rows)))
rows = sql("SELECT d.id, d.ir_attachment_id, d.sequence, d.active, a.name, a.res_model, a.res_id FROM product_document d "
           "JOIN ir_attachment a ON a.id = d.ir_attachment_id ORDER BY d.id")
docs = env['product.document'].browse([r[0] for r in rows])
check("product.document values incl. _inherits ir.attachment (PostgreSQL)", all(
    (d.ir_attachment_id.id, d.sequence, d.active, d.name, d.res_model, d.res_id) == tuple(r[1:]) for d, r in zip(docs, rows)),
    [(d.name, d.res_model) for d in docs])

# 3. junction arrays read from both sides
rel = sql("SELECT product_tag_id, product_template_id FROM product_tag_product_template_rel ORDER BY 1, 2")
check("product.tag.product_template_ids (array on the tag document)",
      sorted((t.id, tmpl.id) for t in tags for tmpl in t.product_template_ids) == rel, rel)
check("product.template.product_tag_ids (PostgreSQL side of the array, every template)",
      sorted((tag.id, tmpl.id) for tmpl in env['product.template'].with_context(active_test=False).search([]) for tag in tmpl.product_tag_ids) == rel)
found = sorted(env['product.template'].search([('product_tag_ids', 'in', tags[0].ids)]).ids)
check("product.template domain on tags into MongoDB", found == sorted(r[1] for r in rel if r[0] == tags[0].id), found)
rel = sql("SELECT product_tag_id, product_product_id FROM product_tag_product_product_rel ORDER BY 1, 2")
check("product.tag.product_product_ids", sorted((t.id, p.id) for t in tags for p in t.product_product_ids) == rel, rel)
check("product.product.additional_product_tag_ids (every variant)", sorted(
    (tag.id, p.id) for p in env['product.product'].with_context(active_test=False).search([]) for tag in p.additional_product_tag_ids) == rel)
rel = sql("SELECT product_category_id, stock_picking_type_id FROM product_category_stock_picking_type_rel ORDER BY 1, 2")
PickingType = env['stock.picking.type']
check("stock.picking.type.wave_category_ids (PostgreSQL owner, array on the category document, every picking type)", sorted(
    (c.id, pt.id) for pt in PickingType.with_context(active_test=False).search([]) for c in pt.wave_category_ids) == rel, rel)
check("stock.picking.type domain on wave categories", PickingType.search([('wave_category_ids', 'in', [4])]).ids == [1])

for model, table in (('product.template', 'product_template'), ('product.product', 'product_product')):
    pg_pairs = sql("SELECT a.res_id, d.id FROM product_document d JOIN ir_attachment a ON a.id = d.ir_attachment_id "
                   "WHERE a.res_model = %s AND d.active ORDER BY 1, 2", (model,))
    orm_pairs = sorted((rec.id, d.id) for rec in env[model].with_context(active_test=False).search([]) for d in rec.product_document_ids)
    check(f"{model}.product_document_ids (one2many into MongoDB through the inherited res_id, every record)", pg_pairs and orm_pairs == pg_pairs, len(pg_pairs))
pg_pairs = sql("SELECT parent_id, id FROM product_category WHERE parent_id IS NOT NULL ORDER BY 1, 2")
check("product.category.child_id (one2many, every category)", pg_pairs and sorted((c.id, ch.id) for c in env['product.category'].search([]) for ch in c.child_id) == pg_pairs, pg_pairs)
pg_pairs = sql("SELECT id, categ_id FROM product_template ORDER BY 1")
check("product.template.categ_id (many2one into MongoDB, every template)", pg_pairs and sorted(
    (t.id, t.categ_id.id) for t in env['product.template'].with_context(active_test=False).search([])) == pg_pairs, len(pg_pairs))
pg_pairs = sql("SELECT id, removal_strategy_id FROM stock_location WHERE removal_strategy_id IS NOT NULL ORDER BY 1")
check("stock.location.removal_strategy_id (many2one into MongoDB) matches PostgreSQL", sorted(
    (l.id, l.removal_strategy_id.id) for l in env['stock.location'].with_context(active_test=False).search([('removal_strategy_id', '!=', False)])) == pg_pairs, len(pg_pairs))

# 4. domains, hierarchy, read_group, name search
Cat = env['product.category']
check("child_of on parent_path", Cat.search([('id', 'child_of', 4)]).ids == [r[0] for r in sql(
    "SELECT id FROM product_category WHERE parent_path LIKE '4/%' ORDER BY parent_id DESC NULLS FIRST, name->>'en_US' COLLATE \"C\", id")])
check("parent_of", set(Cat.search([('id', 'parent_of', 5)]).ids) == {4, 5})
check("complete_name search (name match or child_of the matches)", set(Cat.search([('complete_name', 'ilike', 'Furn')]).ids) == {4, 5, 6})
check("name_search", [r[1] for r in Cat.name_search('Outdoor')] == ['Furniture / Outdoor'])
groups = Cat._read_group([], ['parent_id'], ['__count'])
pg_groups = sql("SELECT parent_id, count(*) FROM product_category GROUP BY 1 ORDER BY 1 NULLS FIRST")
check("read_group by many2one", sorted(((g[0].id or 0), g[1]) for g in groups) == sorted((r[0] or 0, r[1]) for r in pg_groups), groups)
Tag = env['product.tag']
check("translated tag name search", Tag.search([('name', '=', 'Seasonal')]).mapped('name') == ['Seasonal'])
check("boolean domain", Tag.search_count([('visible_to_customers', '=', False)]) == sql(
    "SELECT count(*) FROM product_tag WHERE NOT visible_to_customers")[0][0])
Doc = env['product.document']
check("product.document domain on inherited field (ir.attachment name)", Doc.search([('name', '=', docs[0].name)]).ids == [docs[0].id])
check("product.template one2many product_document_ids",
      env['product.template'].browse(docs[0].res_id).product_document_ids.ids == [d.id for d in docs if d.res_model == 'product.template' and d.res_id == docs[0].res_id])

# 5. cross-store readers: product.template -> category (PostgreSQL -> MongoDB), category -> removal (MongoDB -> MongoDB)
Tmpl = env['product.template']
n = sql("SELECT count(*) FROM product_template WHERE categ_id IN (SELECT id FROM product_category WHERE parent_path LIKE '4/%')")[0][0]
check("product.template child_of category domain", Tmpl.search_count([('categ_id', 'child_of', 4)]) == n, n)
check("product.template domain by category name", Tmpl.search_count([('categ_id.name', '=', 'Office')]) == sql(
    "SELECT count(*) FROM product_template t JOIN product_category c ON c.id = t.categ_id WHERE c.name->>'en_US' = 'Office'")[0][0])
check("product.template ordered by many2one into MongoDB", Tmpl.search([], order='categ_id, id').ids == [r[0] for r in sql(
    "SELECT t.id FROM product_template t LEFT JOIN product_category c ON c.id = t.categ_id "
    "ORDER BY c.parent_id DESC NULLS FIRST, c.name->>'en_US' COLLATE \"C\", c.id, t.id")])
check("category.removal_strategy_id (MongoDB -> MongoDB many2one)", all(
    (c.removal_strategy_id.name or None) == (sql("SELECT name->>'en_US' FROM product_removal WHERE id = %s", (c.removal_strategy_id.id,))[0][0]
                                             if c.removal_strategy_id else None) for c in cats))

# 6. reports of NOTES.md s2.3 §2 owned by this unit
Avco = env['stock.avco.report']
companies = env['res.company'].sudo().search([])
fifo = {c.id: set(Cat.with_company(c).sudo().search([('property_cost_method', 'in', ('fifo', 'average'))]).ids) for c in companies}
move_rows = sql("SELECT sm.id, sm.company_id, pt.categ_id FROM stock_move sm JOIN product_product pp ON pp.id = sm.product_id "
                "JOIN product_template pt ON pt.id = pp.product_tmpl_id WHERE sm.state = 'done' AND (sm.is_in OR sm.is_out)")
expected = {-r[0] for r in sql("SELECT id FROM product_value WHERE move_id IS NULL")} | {r[0] for r in move_rows if r[2] in fifo.get(r[1], ())}
check("stock.avco.report: cost-method filter moved from the view to _search", set(Avco.search([]).ids) == expected,
      (len(expected), Avco.search_count([])))
if move_rows:
    move_id, company_id, categ_id = move_rows[0]
    with cr.savepoint():
        # a category costed at fifo for one company (company-dependent write on the MongoDB document)
        categ = Cat.browse(categ_id)
        categ.with_company(company_id).write({'property_cost_method': 'fifo'})
        env.flush_all()
        stored = st.model_collection(Cat).find_one({'_id': categ_id}).get('propertyCostMethod')
        check("company-dependent write lands under the string company key and reads back per company",
              stored == {str(company_id): 'fifo'} and categ.with_company(company_id).property_cost_method == 'fifo'
              and all(categ.with_company(c).property_cost_method == 'standard' for c in companies if c.id != company_id), stored)
        fifo_now = {r[0] for r in move_rows if r[1] == company_id and r[2] == categ_id}
        found = set(Avco.search([('res_model_name', '=', 'stock.move')]).ids)
        check("stock.avco.report: fifo category brings exactly its done moves in", fifo_now and found == fifo_now, (len(found), len(fifo_now)))
    with cr.savepoint():
        # the company default (ir.default, PostgreSQL) set to fifo: every category without an explicit
        # value now costs at fifo for that company, so its done moves come in through the fallback branch
        env['ir.default'].sudo().set('product.category', 'property_cost_method', 'fifo', company_id=company_id)
        # expected = every done move of that company whose category now resolves to fifo/average (explicit value or default)
        methods = {c.id: c.with_company(company_id).property_cost_method for c in Cat.search([])}
        fifo_now = {r[0] for r in move_rows if r[1] == company_id and methods[r[2]] in ('fifo', 'average')}
        found = set(Avco.search([('res_model_name', '=', 'stock.move')]).ids)
        check("stock.avco.report: fifo company default brings the done moves in (fallback branch)", fifo_now and found == fifo_now, (len(found), len(fifo_now)))
        check("stock.avco.report: read_group on the filtered rows", sum(
            g[-1] for g in Avco._read_group([], ['product_id'], ['__count'])) == Avco.search_count([]))
VendorDelay = env['vendor.delay.report']
rows = sql("SELECT pol.id, pt.categ_id FROM purchase_order_line pol JOIN stock_move m ON m.purchase_line_id = pol.id "
           "JOIN product_product p ON p.id = m.product_id JOIN product_template pt ON pt.id = p.product_tmpl_id GROUP BY pol.id, pt.categ_id ORDER BY pol.id")
check("vendor.delay.report: category_id from product_template.categ_id (no product_category join)",
      sorted((r['id'], r['category_id'][0] if r['category_id'] else None) for r in VendorDelay.search_read([], ['category_id'])) == rows, len(rows))
check("vendor.delay.report: read_group by category (names from MongoDB)", all(
    g[0].display_name for g in VendorDelay._read_group([], ['category_id'], ['qty_total:sum']) if g[0]))
Purchase = env['purchase.report']
rows = sql("SELECT pol.id, pt.categ_id FROM purchase_order_line pol JOIN product_product p ON p.id = pol.product_id "
           "JOIN product_template pt ON pt.id = p.product_tmpl_id WHERE pol.display_type IS NULL ORDER BY pol.id")
check("purchase.report: category_id per line equals product_template.categ_id",
      sorted((r['id'], r['category_id'][0] if r['category_id'] else None) for r in Purchase.search_read([], ['category_id'])) == rows, len(rows))
groups = Purchase._read_group([], ['category_id'], ['__count'])
check("purchase.report: read_group by category", sorted((g[0].id, g[1]) for g in groups) == sorted(
    (r[0], r[1]) for r in sql("SELECT pt.categ_id, count(*) FROM purchase_order_line pol JOIN product_product p ON p.id = pol.product_id "
                              "JOIN product_template pt ON pt.id = p.product_tmpl_id WHERE pol.display_type IS NULL GROUP BY 1")), groups)

# 7. writes through the storage path, then rolled back
new_cat = Cat.create({'name': 'Scenario shelf', 'parent_id': 5, 'removal_strategy_id': removals[0].id})
env.flush_all()
doc = st.model_collection(Cat).find_one({'_id': new_cat.id})
check("category create: document + shadow row + parent_path", doc and doc['name'] == {'en_US': 'Scenario shelf'}
      and doc['parentPath'] == f'4/5/{new_cat.id}/' and doc['removalStrategyId'] == removals[0].id
      and sql("SELECT count(*) FROM product_category WHERE id = %s", (new_cat.id,))[0][0] == 1, doc)
check("category create: complete_name through two MongoDB parents", new_cat.complete_name == 'Furniture / Office / Scenario shelf')
new_cat.write({'parent_id': 7})
env.flush_all()
check("category write: parent change recomputes parent_path", st.model_collection(Cat).find_one({'_id': new_cat.id})['parentPath'] == f'7/{new_cat.id}/'
      and Cat.search([('id', 'child_of', 7)]).ids == [7, new_cat.id])
tmpl = env['product.template'].browse(1)
new_tag = Tag.create({'name': 'Scenario tag', 'sequence': 1, 'color': '3', 'product_template_ids': [Command.link(tmpl.id)]})
env.flush_all()
doc = st.model_collection(Tag).find_one({'_id': new_tag.id})
check("tag create with a template link writes the array element", doc and doc['productTemplateRel'] == [{'productTemplateId': tmpl.id}]
      and new_tag in tmpl.product_tag_ids, doc)
tmpl.write({'product_tag_ids': [Command.unlink(new_tag.id), Command.link(tags[2].id)]})
env.flush_all()
check("PostgreSQL side write updates the arrays", (st.model_collection(Tag).find_one({'_id': new_tag.id}).get('productTemplateRel') or []) == []
      and {'productTemplateId': tmpl.id} in st.model_collection(Tag).find_one({'_id': tags[2].id})['productTemplateRel'])
pt1 = PickingType.browse(1)
pt1.write({'wave_category_ids': [Command.set([new_cat.id])]})
env.flush_all()
check("wave_category_ids set from the PostgreSQL owner moves the elements between category documents",
      st.model_collection(Cat).find_one({'_id': new_cat.id})['stockPickingTypeRel'] == [{'stockPickingTypeId': 1}]
      and all(not st.model_collection(Cat).find_one({'_id': i}).get('stockPickingTypeRel') for i in (1, 4))
      and pt1.wave_category_ids == new_cat)
try:
    with cr.savepoint():
        Tag.create({'name': 'Fragile'})
        env.flush_all()
    check("unique tag name refused", False)
except Exception as exc:  # noqa: BLE001
    # a duplicate-key refusal (E11000) and nothing else counts; it surfaces as the driver's error, not a ValidationError
    check("unique tag name refused", 'E11000' in str(exc) or 'duplicate key' in str(exc), type(exc).__name__)
new_doc = Doc.create({'name': 'scenario.txt', 'raw': b'hello', 'res_model': 'product.template', 'res_id': tmpl.id})
env.flush_all()
ddoc = st.model_collection(Doc).find_one({'_id': new_doc.id})
check("document create: ir.attachment row on PostgreSQL, document in MongoDB", ddoc and ddoc['irAttachmentId'] == new_doc.ir_attachment_id.id
      and sql("SELECT name FROM ir_attachment WHERE id = %s", (new_doc.ir_attachment_id.id,))[0][0] == 'scenario.txt'
      and new_doc in tmpl.product_document_ids, ddoc)
new_doc.unlink()
env.flush_all()
check("document unlink removes document, shadow row and attachment", st.model_collection(Doc).find_one({'_id': new_doc.id}) is None
      and sql("SELECT count(*) FROM product_document WHERE id = %s", (new_doc.id,))[0][0] == 0)
definition = [{'name': 'scenario_colour', 'type': 'char', 'string': 'Scenario colour'}]
cats[0].write({'product_properties_definition': definition})
env.flush_all()
found = env['product.template'].get_property_definition('product_properties.scenario_colour')
check("get_property_definition reads product_properties_definition from the category document",
      found.get('name') == 'scenario_colour' and found.get('type') == 'char' and found.get('string') == 'Scenario colour'
      and env['product.template'].get_property_definition('product_properties.nope') == {}, found)
new_unit = env['product.base.unit'].create({'name': 'Scenario unit'})
new_unit.write({'name': 'Scenario unit renamed'})
env.flush_all()
check("base unit create + write", st.model_collection(new_unit).find_one({'_id': new_unit.id})['name'] == {'en_US': 'Scenario unit renamed'})

# 8. merge helpers rewritten for MongoDB-stored referrers (NOTES.md s2.3 §3a row 15 / §3c row 1)
wiz = env['base.partner.merge.automatic.wizard'].new()
src, dst = removals[0], removals[1]
referrers = Cat.search([('removal_strategy_id', '=', src.id)])
wiz._update_foreign_keys_generic('product.removal', src, dst)
check("_update_foreign_keys_generic repoints MongoDB many2ones (product.category.removal_strategy_id)",
      referrers and all(c.removal_strategy_id == dst for c in referrers) and not Cat.search_count([('removal_strategy_id', '=', src.id)]), referrers.ids)
account = env['account.account'].sudo().search([], limit=1)
other_account = env['account.account'].sudo().search([('id', '!=', account.id)], limit=1)
cats[0].with_company(companies[0]).write({'property_account_income_categ_id': account.id})
env.flush_all()
check("company-dependent account field write lands under the string company key",
      st.model_collection(Cat).find_one({'_id': cats[0].id}).get('propertyAccountIncomeCategId') == {str(companies[0].id): account.id})
# what _action_unmerge's _update_mongodb_references does for a company-dependent field: search as the company, write
Cat.with_company(companies[0]).search([('property_account_income_categ_id', '=', account.id)]).write({'property_account_income_categ_id': other_account.id})
env.flush_all()
check("company-dependent account field rewritten through the ORM (the _action_unmerge path)",
      cats[0].with_company(companies[0]).property_account_income_categ_id == other_account
      and Cat.with_company(companies[0]).search([('property_account_income_categ_id', '=', other_account.id)]) == cats[0]
      and not Cat.with_company(companies[0]).search_count([('property_account_income_categ_id', '=', account.id)]))

cr.rollback()
after = snapshot()
check("rollback leaves the loaded collections byte-identical", before == after, {m: (before[m][:12], after[m][:12]) for m in after if before[m] != after[m]})
print(f"{sum(checks)}/{len(checks)} checks passed")
assert all(checks)
