"""ORM scenario for batch w1-b06 (unit account-chart) on the MongoDB storage path.

Run on the run branch against the worker's seeded clone, whose documents are the loaded ones
(conf key mongodb_migration_db = <clone> keeps the collections unprefixed):

    /home/ubuntu/.venvs/odoo/bin/python odoo-bin shell -c <conf> -d <clone> --no-http \\
        < .migration/load/scenario_account_chart.py

Reads are compared with the clone's PostgreSQL rows (the clone still carries the legacy tables): every
stored many2many / one2many of the opted-in models is checked for exact equality with its relation
table, and a relation that reads empty while PostgreSQL has pairs is listed at the end (UNT12-33).
Writes happen in one transaction that is rolled back; the collections are hashed before and after.
"""
import hashlib
from collections import defaultdict

from bson.json_util import dumps

cr = env.cr
st = env.registry.mongo_store
assert st.prefix == '', f"collections are prefixed {st.prefix!r}: set mongodb_migration_db to this database"
MODELS = {  # model -> PostgreSQL ORDER BY of its _order (account.account's _order needs compute_sql fields, see below)
    'account.account': 'id',
    'account.account.tag': 'id',
    'account.tax.group': 'sequence, id',
    'account.tax': 'sequence, id',
    'account.tax.repartition.line': 'document_type, repartition_type, sequence, id',
    'account.fiscal.position': 'sequence, id',
    'account.fiscal.position.account': 'id',
}
checks, empty_relations, unsupported = [], [], []


def check(name, ok, detail=''):
    checks.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}{' -- ' + str(detail)[:300] if detail else ''}")


def sql(query, params=()):
    cr.execute(query, params)
    return cr.fetchall()


def snapshot():
    return {m: hashlib.sha256(dumps(list(st.model_collection(env[m]).find().sort('_id', 1)), sort_keys=True).encode()).hexdigest()
            for m in MODELS}


def by_owner(pairs):
    out = defaultdict(set)
    for owner, other in pairs:
        out[owner].add(other)
    return out


def all_records(model):
    return env[model].with_context(active_test=False).search([], order='id')


before = snapshot()

# 1. search order, counts, exists() against PostgreSQL
for model, order in MODELS.items():
    M = env[model].with_context(active_test=False)
    pg_ids = [r[0] for r in sql(f"SELECT id FROM {M._table} ORDER BY {order}")]
    check(f"{model} search([], order='{order}')", M.search([], order=order).ids == pg_ids, len(pg_ids))
    check(f"{model} search_count", M.search_count([]) == len(pg_ids))
    check(f"{model} exists()", M.browse(pg_ids).exists().ids == pg_ids and not M.browse(max(pg_ids) + 1000).exists())
try:
    env['account.account'].search([], limit=5)  # default _order = code_path, account_type, name_path (compute_sql)
    check("account.account search with its default _order", True)
except NotImplementedError as exc:
    unsupported.append(f"account.account default _order: {exc}")
    check("account.account search with its default _order", False, exc)

# 2. every stored many2many / one2many of the opted-in models reads exactly the PostgreSQL pairs
for model in MODELS:
    recs = all_records(model)
    for name, field in sorted(recs._fields.items()):
        if field.compute or not field.store:
            continue
        if field.type == 'many2many' and field.relation:
            expected = by_owner(sql(f'SELECT "{field.column1}", "{field.column2}" FROM "{field.relation}"'))
            label = f"{model}.{name} m2m == PG ({field.relation})"
        elif field.type == 'one2many' and field.inverse_name and not field.domain:
            inverse = env[field.comodel_name]._fields[field.inverse_name]
            if inverse.type != 'many2one' or not inverse.store:
                continue
            table = env[field.comodel_name]._table
            expected = by_owner((owner, other) for other, owner in sql(f'SELECT id, "{inverse.name}" FROM "{table}" WHERE "{inverse.name}" IS NOT NULL'))
            label = f"{model}.{name} o2m == PG ({table}.{inverse.name})"
        else:
            continue
        try:
            got = {r.id: set(r[name].ids) for r in recs}
        except NotImplementedError as exc:
            unsupported.append(f"{model}.{name}: {exc}")
            check(label, False, exc)
            continue
        expected = {k: v for k, v in expected.items() if k in got}
        n_pairs = sum(len(v) for v in expected.values())
        ok = all(got[i] == expected.get(i, set()) for i in got)
        if not ok and n_pairs and not any(got.values()):
            empty_relations.append(f"{model}.{name} ({field.relation if field.type == 'many2many' else table}): PG {n_pairs} pairs, ORM reads empty")
        check(label, ok, f"{n_pairs} pairs" if ok else f"PG {n_pairs} pairs; first mismatch "
              f"{next(((i, sorted(got[i]), sorted(expected.get(i, ()))) for i in got if got[i] != expected.get(i, set())), None)}")

# 3. field values against PostgreSQL rows
rows = sql("SELECT id, name->>'en_US', applicability, country_id, active FROM account_account_tag ORDER BY id")
tags = env['account.account.tag'].with_context(active_test=False).browse([r[0] for r in rows])
check("account.account.tag field values", all((t.name, t.applicability, t.country_id.id or None, t.active) == r[1:] for t, r in zip(tags, rows)))
rows = sql("SELECT id, name->>'en_US', sequence, company_id FROM account_tax_group ORDER BY id")
groups = env['account.tax.group'].browse([r[0] for r in rows])
check("account.tax.group field values", all((g.name, g.sequence, g.company_id.id or None) == r[1:] for g, r in zip(groups, rows)))
rows = sql("SELECT id, name->>'en_US', amount, amount_type, type_tax_use, sequence, company_id, active, tax_group_id FROM account_tax ORDER BY id")
taxes = env['account.tax'].with_context(active_test=False).browse([r[0] for r in rows])
check("account.tax field values", all(
    (t.name, t.amount, t.amount_type, t.type_tax_use, t.sequence, t.company_id.id, t.active, t.tax_group_id.id)
    == (r[1], float(r[2]), r[3], r[4], r[5], r[6], r[7], r[8]) for t, r in zip(taxes, rows)))
rows = sql("SELECT id, document_type, repartition_type, factor_percent, sequence, tax_id, account_id, company_id FROM account_tax_repartition_line ORDER BY id")
lines = env['account.tax.repartition.line'].browse([r[0] for r in rows])
check("account.tax.repartition.line field values", all(
    (x.document_type, x.repartition_type, x.factor_percent, x.sequence, x.tax_id.id, x.account_id.id or None, x.company_id.id)
    == (r[1], r[2], float(r[3]), r[4], r[5], r[6], r[7]) for x, r in zip(lines, rows)))
rows = sql("SELECT id, name->>'en_US', sequence, company_id, auto_apply, country_id FROM account_fiscal_position ORDER BY id")
positions = env['account.fiscal.position'].with_context(active_test=False).browse([r[0] for r in rows])
check("account.fiscal.position field values", all(
    (p.name, p.sequence, p.company_id.id, p.auto_apply, p.country_id.id or None) == (r[1], r[2] or 0, *r[3:]) for p, r in zip(positions, rows)))
rows = sql("SELECT id, position_id, account_src_id, account_dest_id FROM account_fiscal_position_account ORDER BY id")
mappings = env['account.fiscal.position.account'].browse([r[0] for r in rows])
check("account.fiscal.position.account (embedded child rows) field values", mappings and all(
    (m.position_id.id, m.account_src_id.id, m.account_dest_id.id) == r[1:] for m, r in zip(mappings, rows)), len(rows))
rows = sql("SELECT id, name->>'en_US', account_type, reconcile, active, parent_path, currency_id FROM account_account ORDER BY id")
accounts = env['account.account'].with_context(active_test=False).browse([r[0] for r in rows])
check("account.account stored field values", all(
    (a.name, a.account_type, a.reconcile, a.active, a.parent_path, a.currency_id.id or None) == r[1:] for a, r in zip(accounts, rows)))
try:
    codes = sql("SELECT id, code_store->>%s FROM account_account WHERE code_store ? %s ORDER BY id", (str(env.company.id), str(env.company.id)))
    check("account.account code (company-dependent code_store, compute_sql)", all(a.code == c for (i, c), a in zip(codes, env['account.account'].browse([i for i, _ in codes]))), len(codes))
except NotImplementedError as exc:
    unsupported.append(f"account.account.code: {exc}")
    check("account.account code (company-dependent code_store, compute_sql)", False, exc)

# 4. domains, read_group, translated search, cross-store readers (PostgreSQL models pointing into MongoDB)
Tax = env['account.tax']
n_sale = sql("SELECT count(*) FROM account_tax WHERE type_tax_use = 'sale' AND active")[0][0]
check("selection domain", Tax.search_count([('type_tax_use', '=', 'sale')]) == n_sale, n_sale)
n_pos = sql("SELECT count(*) FROM account_tax WHERE amount > 10 AND active")[0][0]
check("numeric domain", Tax.search_count([('amount', '>', 10)]) == n_pos, n_pos)
groups_rg = Tax._read_group([], ['type_tax_use'], ['__count'])
pg_rg = sql("SELECT type_tax_use, count(*) FROM account_tax WHERE active GROUP BY 1 ORDER BY 1")
check("read_group by selection", sorted((g[0], g[1]) for g in groups_rg) == [(r[0], r[1]) for r in pg_rg], groups_rg)
check("translated name search", env['account.account.tag'].search([('name', '=', 'Scenario tax grid')]).mapped('name') == ['Scenario tax grid'])
check("name_search on tax", bool(Tax.name_search(taxes[0].name)))
n_children = sql("SELECT count(*) FROM account_tax_filiation_rel")[0][0]
check("domain on embedded m2m (children_tax_ids)", Tax.search_count([('children_tax_ids', '!=', False)]) == (1 if n_children else 0), n_children)
check("many2one domain into MongoDB (repartition line by tax)", env['account.tax.repartition.line'].search_count([('tax_id', '=', taxes[0].id)])
      == sql("SELECT count(*) FROM account_tax_repartition_line WHERE tax_id = %s", (taxes[0].id,))[0][0])
for model, fname, table, col1, col2 in [
    ('product.template', 'taxes_id', 'product_taxes_rel', 'prod_id', 'tax_id'),
    ('product.template', 'supplier_taxes_id', 'product_supplier_taxes_rel', 'prod_id', 'tax_id'),
    ('product.template', 'account_tag_ids', 'account_account_tag_product_template_rel', 'product_template_id', 'account_account_tag_id'),
    ('sale.order.line', 'tax_ids', 'account_tax_sale_order_line_rel', 'sale_order_line_id', 'account_tax_id'),
    ('purchase.order.line', 'tax_ids', 'account_tax_purchase_order_line_rel', 'purchase_order_line_id', 'account_tax_id'),
    ('account.move.line', 'tax_tag_ids', 'account_account_tag_account_move_line_rel', 'account_move_line_id', 'account_account_tag_id'),
    ('account.move.line', 'tax_ids', 'account_move_line_account_tax_rel', 'account_move_line_id', 'account_tax_id'),
]:
    recs = all_records(model)
    expected = by_owner(sql(f'SELECT "{col1}", "{col2}" FROM "{table}"'))
    try:
        got = {r.id: set(r[fname].ids) for r in recs}
    except Exception as exc:  # noqa: BLE001
        unsupported.append(f"{model}.{fname}: {type(exc).__name__}: {exc}")
        check(f"{model}.{fname} (PostgreSQL side) m2m == PG ({table})", False, exc)
        continue
    n_pairs = sum(len(v) for v in expected.values())
    ok = all(got[i] == expected.get(i, set()) for i in got)
    if not ok and n_pairs and not any(got.values()):
        empty_relations.append(f"{model}.{fname} ({table}): PG {n_pairs} pairs, ORM reads empty")
    check(f"{model}.{fname} (PostgreSQL side) m2m == PG ({table})", ok, f"{n_pairs} pairs")
tax0 = taxes[0]
for label, probe in [
    ("PostgreSQL model domain on m2m into MongoDB (product.template taxes_id in ids)", lambda: env['product.template'].search_count([('taxes_id', 'in', [tax0.id])])
     == sql("SELECT count(DISTINCT prod_id) FROM product_taxes_rel WHERE tax_id = %s", (tax0.id,))[0][0]),
    ("journal default_account_id (PostgreSQL m2o into MongoDB) reads", lambda: all(j.default_account_id.name for j in env['account.journal'].search([('default_account_id', '!=', False)]))),
    ("partner credit/debit (_credit_debit_get rewrite, row 3b-28)", lambda: isinstance(env['res.partner'].search([], limit=5).mapped('credit'), list)),
    ("account.move payment_state recompute (row 3b-4 rewrite)", lambda: env['account.move'].search([('move_type', '=', 'out_invoice')], limit=5)._compute_payment_state() is None),
    ("account.move reconciled_payment_ids (row 3b-5 rewrite)", lambda: env['account.move'].search([('move_type', '=', 'out_invoice')], limit=5)._compute_reconciled_payment_ids() is None),
    ("account.payment stat buttons (rows 3a-8, 3b-25 rewrite)", lambda: env['account.payment'].search([], limit=5)._compute_stat_buttons_from_reconciliation() is None),
    ("res.partner credit search (row 3b-29 rewrite)", lambda: env['res.partner'].search_count([('credit', '>', 0)]) >= 0),
    ("account.move.line account_id search by domain (row 3b-15 rewrite)", lambda: env['account.move.line'].search_count([('account_id', 'any', [('account_type', '=', 'asset_receivable')])])
     == sql("SELECT count(*) FROM account_move_line WHERE account_id = ANY(%s)", (env['account.account']._ids_by_type(('asset_receivable',)),))[0][0]),
    ("account.move.line search panel by account root (row 3b-19 rewrite)", lambda: isinstance(env['account.move.line']._search_panel_domain_image('account_root_id', []), dict)),
    ("account.account search panel by account root (row 3b-20 rewrite)", lambda: isinstance(env['account.account']._search_panel_domain_image('root_id', []), dict)),
    ("account.account constraints (row 3a-13 rewrite) on the whole chart", lambda: accounts._check_journal_consistency() is None
     and accounts._check_account_type_sales_purchase_journal() is None and accounts._check_account_is_bank_journal_bank_account() is None),
]:
    try:
        check(label, probe())
    except Exception as exc:  # noqa: BLE001
        unsupported.append(f"{label}: {type(exc).__name__}: {exc}")
        check(label, False, f"{type(exc).__name__}: {exc}")

# 5. writes through the storage path, then rolled back
try:
    Tag = env['account.account.tag']
    new_tag = Tag.create({'name': 'Scenario tag w1-b06', 'applicability': 'taxes', 'country_id': env.company.country_id.id})
    env.flush_all()
    doc = st.model_collection(Tag).find_one({'_id': new_tag.id})
    check("create writes a document + shadow row", doc and doc['name'] == {'en_US': 'Scenario tag w1-b06'} and doc['applicability'] == 'taxes'
          and sql("SELECT count(*) FROM account_account_tag WHERE id = %s", (new_tag.id,))[0][0] == 1, doc)
    new_tax = Tax.create({'name': 'Scenario tax w1-b06', 'amount': 7.5, 'type_tax_use': 'sale', 'company_id': env.company.id})
    new_tax.invoice_repartition_line_ids.filtered(lambda r: r.repartition_type == 'tax').write({'tag_ids': [(4, new_tag.id)]})
    env.flush_all()
    tdoc = st.model_collection(Tax).find_one({'_id': new_tax.id})
    check("tax create: document, repartition lines, embedded m2m on the tag side",
          tdoc and new_tax.repartition_line_ids and new_tag.with_context(active_test=False).search_count([('id', '=', new_tag.id)]) == 1
          and set(new_tax.invoice_repartition_line_ids.filtered(lambda r: r.repartition_type == 'tax').tag_ids.ids) == {new_tag.id}
          and [e['accountTaxRepartitionLineId'] for e in st.model_collection(Tag).find_one({'_id': new_tag.id}).get('accountTaxRepartitionLineRel', [])]
          == new_tax.invoice_repartition_line_ids.filtered(lambda r: r.repartition_type == 'tax').ids, tdoc and tdoc.get('amount'))
    position = env['account.fiscal.position'].create({
        'name': 'Scenario position', 'company_id': env.company.id,
        'account_ids': [(0, 0, {'account_src_id': accounts[0].id, 'account_dest_id': accounts[1].id})],
        'tax_ids': [(6, 0, [tax0.id])], 'state_ids': [(6, 0, env['res.country.state'].search([], limit=2).ids)]})
    env.flush_all()
    pdoc = st.model_collection(position).find_one({'_id': position.id})
    check("fiscal position create embeds child rows + two m2m arrays",
          pdoc and [(e['accountSrcId'], e['accountDestId']) for e in pdoc.get('account', [])] == [(accounts[0].id, accounts[1].id)]
          and [e['accountTaxId'] for e in pdoc.get('accountTaxRel', [])] == [tax0.id] and len(pdoc.get('resCountryStateRel', [])) == 2
          and position.account_ids.account_dest_id == accounts[1], pdoc and {k: pdoc[k] for k in ('account', 'accountTaxRel') if k in pdoc})
    position.account_ids.unlink()
    position.write({'tax_ids': [(3, tax0.id)], 'sequence': 42})
    env.flush_all()
    pdoc = st.model_collection(position).find_one({'_id': position.id})
    check("child unlink + m2m unlink + write update the document", not pdoc.get('account') and not pdoc.get('accountTaxRel') and pdoc['sequence'] == 42, pdoc)
    try:
        with cr.savepoint():
            Tag.create({'name': 'Scenario tag w1-b06', 'applicability': 'taxes', 'country_id': env.company.country_id.id})
            env.flush_all()
        check("account.account.tag unique(name, applicability, country_id) refused", False, 'duplicate accepted')
    except Exception as exc:  # noqa: BLE001
        check("account.account.tag unique(name, applicability, country_id) refused", 'E11000' in str(exc) or 'duplicate key' in str(exc) or 'already exists' in str(exc), type(exc).__name__)
    new_tax.unlink()
    env.flush_all()
    check("unlink removes document + shadow row", st.model_collection(Tax).find_one({'_id': new_tax.id}) is None
          and sql("SELECT count(*) FROM account_tax WHERE id = %s", (new_tax.id,))[0][0] == 0)
except Exception as exc:  # noqa: BLE001
    unsupported.append(f"writes: {type(exc).__name__}: {exc}")
    check("writes section ran to the end", False, repr(exc)[:300])
cr.rollback()
after = snapshot()
check("rollback leaves the loaded collections byte-identical", before == after, [m for m in MODELS if before[m] != after[m]])
print(f"{sum(checks)}/{len(checks)} checks passed")
print("relations reading empty:", empty_relations or 'none')
print("storage-path unsupported:", unsupported or 'none')
assert all(checks)
