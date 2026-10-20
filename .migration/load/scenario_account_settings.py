"""ORM scenario for batch w1-b04 (unit account-settings) on the MongoDB storage path.

Run on the run branch against the worker's seeded clone, whose documents are the loaded ones
(conf key mongodb_migration_db = <clone> keeps the collections unprefixed):

    /home/ubuntu/.venvs/odoo/bin/python odoo-bin shell -c <conf> -d <clone> --no-http \\
        < .migration/load/scenario_account_settings.py

Reads are compared with the clone's PostgreSQL rows (the clone still carries the legacy columns);
every write happens in one transaction that is rolled back at the end, and the documents are
hashed before and after to show the journal left the loaded collections untouched. A GAP line is
a storage-path gap reported on the ticket (not patched here); it is not counted as a check.
"""
import hashlib

from bson.json_util import dumps

cr = env.cr
st = env.registry.mongo_store
assert st.prefix == '', f"collections are prefixed {st.prefix!r}: set mongodb_migration_db to this database"
ROOTS = ['account.payment.term', 'account.incoterms', 'account.cash.rounding', 'account.journal.group',
         'account.lock_exception', 'account.report', 'account.report.expression', 'account.report.external.value']
MODELS = {
    'account.payment.term': 'sequence, id',
    'account.payment.term.line': 'id',
    'account.incoterms': 'id',
    'account.cash.rounding': 'sequence, id',
    'account.journal.group': 'id',
    'account.lock_exception': 'id',
    'account.report': 'sequence, id',
    'account.report.line': 'sequence, id',
    'account.report.column': 'sequence, id',
    'account.report.expression': 'id',
    'account.report.external.value': 'date, id',
}
checks = []


def check(name, ok, detail=''):
    checks.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}{' -- ' + str(detail) if detail else ''}")


def gap(name, detail=''):
    print(f"GAP  {name}{' -- ' + str(detail) if detail else ''}")


def snapshot():
    return {m: hashlib.sha256(dumps(list(st.model_collection(env[m]).find().sort('_id', 1)), sort_keys=True).encode()).hexdigest()
            for m in ROOTS}


def sql(query, params=()):
    cr.execute(query, params)
    return cr.fetchall()


def refused(name, action, expect):
    try:
        with cr.savepoint():
            action()
            env.flush_all()
        check(name, False, 'accepted')
    except Exception as exc:  # noqa: BLE001
        check(name, expect(exc), f'{type(exc).__name__}: {str(exc)[:80]}')


before = snapshot()

# 1. search order, counts and exists() against PostgreSQL (active_test off: PostgreSQL rows include inactive ones)
for model, order in MODELS.items():
    M = env[model].with_context(active_test=False)
    pg_ids = [r[0] for r in sql(f"SELECT id FROM {M._table} ORDER BY {order}")]
    check(f"{model} search([]) order", M.search([]).ids == pg_ids, pg_ids)
    check(f"{model} search_count", M.search_count([]) == len(pg_ids))
    check(f"{model} exists()", M.browse(pg_ids).exists().ids == pg_ids and not M.browse(max(pg_ids) + 1000).exists())
Term, Line = env['account.payment.term'], env['account.payment.term.line']
check("active_test on a stored boolean", Term.search_count([]) == sql("SELECT count(*) FROM account_payment_term WHERE active")[0][0])
gap("account.report.search([]) with active_test (compute_sql field 'active' in a domain)",
    f"{env['account.report'].search([]).ids} vs {env['account.report'].with_context(active_test=False).search([]).ids}")

# 2. field values against PostgreSQL rows
rows = sql("SELECT id, name->>'en_US', sequence, company_id, COALESCE(early_discount, false), discount_percentage FROM account_payment_term ORDER BY id")
terms = Term.browse([r[0] for r in rows])
check("account.payment.term field values", all(
    (t.name, t.sequence, t.company_id.id or None, t.early_discount, t.discount_percentage) == (r[1], r[2], r[3], r[4], float(r[5]))
    for t, r in zip(terms, rows)), [(t.name, t.discount_percentage) for t in terms][:2])
rows = sql("SELECT id, payment_id, value, value_amount, nb_days, delay_type FROM account_payment_term_line ORDER BY id")
lines = Line.browse([r[0] for r in rows])
check("account.payment.term.line (embedded) field values", all(
    (l.payment_id.id, l.value, l.value_amount, l.nb_days, l.delay_type) == (r[1], r[2], float(r[3] or 0), r[4], r[5])
    for l, r in zip(lines, rows)), [(l.payment_id.id, l.value_amount) for l in lines][:3])
check("one2many line_ids from the parent document", all(
    t.line_ids.ids == [r[0] for r in sql("SELECT id FROM account_payment_term_line WHERE payment_id = %s ORDER BY id", (t.id,))]
    for t in terms))
rows = sql("SELECT id, name->>'en_US', rounding, strategy, rounding_method FROM account_cash_rounding ORDER BY id")
roundings = env['account.cash.rounding'].browse([r[0] for r in rows])
check("account.cash.rounding field values", all(
    (x.name, x.rounding, x.strategy, x.rounding_method) == (r[1], float(r[2]), r[3], r[4]) for x, r in zip(roundings, rows)))
check("many2many through embedded relation tables", all(
    sorted(x.currency_ids.ids) == [r[0] for r in sql("SELECT res_currency_id FROM account_cash_rounding_res_currency_rel WHERE account_cash_rounding_id = %s ORDER BY 1", (x.id,))]
    and sorted(x.partner_category_ids.ids) == [r[0] for r in sql("SELECT res_partner_category_id FROM account_cash_rounding_res_partner_category_rel WHERE account_cash_rounding_id = %s ORDER BY 1", (x.id,))]
    and sorted(x.payment_method_line_ids.ids) == [r[0] for r in sql("SELECT account_payment_method_line_id FROM account_cash_rounding_account_payment_method_line_rel WHERE account_cash_rounding_id = %s ORDER BY 1", (x.id,))]
    for x in roundings), [(x.currency_ids.ids, x.partner_category_ids.ids) for x in roundings])
check("company-dependent many2one (profit_account_id)", roundings[0].profit_account_id.id == sql(
    "SELECT (profit_account_id->>%s)::int FROM account_cash_rounding WHERE id = %s", (str(env.company.id), roundings[0].id))[0][0])
rows = sql("SELECT id, reason, lock_date, end_datetime, user_id FROM account_lock_exception ORDER BY id")
exceptions = env['account.lock_exception'].browse([r[0] for r in rows])
check("account.lock_exception field values", all(
    (e.reason, e.lock_date, e.end_datetime, e.user_id.id) == (r[1], r[2], r[3], r[4]) for e, r in zip(exceptions, rows)))
rows = sql("SELECT id, label, engine, formula, subformula, report_line_id FROM account_report_expression ORDER BY id")
expressions = env['account.report.expression'].browse([r[0] for r in rows])
check("account.report.expression field values", all(
    (x.label, x.engine, x.formula, x.subformula or None, x.report_line_id.id) == tuple(r[1:]) for x, r in zip(expressions, rows)))
rows = sql("SELECT id, name, value, date, target_report_expression_id FROM account_report_external_value ORDER BY id")
externals = env['account.report.external.value'].browse([r[0] for r in rows])
check("account.report.external.value field values", all(
    (x.name, x.value, x.date, x.target_report_expression_id.id) == (r[1], float(r[2]), r[3], r[4]) for x, r in zip(externals, rows)))
Report = env['account.report'].with_context(active_test=False)
report1 = Report.browse(1)
check("account.report embedded lines and columns", report1.line_ids.mapped('code') == ['W1B04_SALES', 'W1B04_ADJ']
      and report1.column_ids.mapped('expression_label') == [r[0] for r in sql("SELECT expression_label FROM account_report_column WHERE report_id = 1 ORDER BY sequence, id")]
      and report1.line_ids[1].parent_id == report1.line_ids[0] and report1.line_ids[0].children_ids == report1.line_ids[1]
      and report1.line_ids[0].expression_ids.mapped('label') == ['balance', 'adjustment'])
check("report sections (embedded relation table, owning side)", Report.browse(5).section_report_ids.ids == [2, 3])
gap("inverse side of the embedded relation table (section_main_report_ids)", Report.browse(2).section_main_report_ids.ids)

# 3. domains, read_group, translated search
n = sql("SELECT count(*) FROM account_payment_term WHERE name->>'en_US' ILIKE %s", ('%days%',))[0][0]
check("ilike domain on translated name", Term.with_context(active_test=False).search_count([('name', 'ilike', 'days')]) == n, n)
check("one2many 'any' domain", Term.with_context(active_test=False).search_count([('line_ids', 'any', [('value', '=', 'percent')])])
      == sql("SELECT count(DISTINCT payment_id) FROM account_payment_term_line WHERE value = 'percent'")[0][0])
check("numeric domain on double field", env['account.cash.rounding'].search_count([('rounding', '>', 0.1)]) == 1)
check("date domain", env['account.report.external.value'].search_count([('date', '>=', '2026-01-01')]) == 1
      and env['account.report.external.value'].search_count([('date', '<', '2026-01-01')]) == 0)
check("'in' domain on selection", env['account.report.expression'].search([('engine', 'in', ('domain', 'external'))]).ids == [1, 3])
check("many2one domain on an embedded model", env['account.report.line'].search_count([('report_id', '=', 1), ('parent_id', '=', False)]) == 1)
groups = Term.with_context(active_test=False)._read_group([], ['early_discount'], ['__count'])
check("read_group by boolean", sorted((g[0], g[1]) for g in groups)
      == [(r[0], r[1]) for r in sql("SELECT COALESCE(early_discount, false), count(*) FROM account_payment_term GROUP BY 1 ORDER BY 1")], groups)
Inco = env['account.incoterms']
first = sql("SELECT code, name->>'en_US' FROM account_incoterms ORDER BY id LIMIT 1")[0]
check("translated name search", Inco.search([('name', '=', first[1])]).mapped('code') == [first[0]])
check("name_search by code (_rec_names_search)", first[0] in [r[1].split(' ')[0] for r in Inco.name_search(first[0])] or any(first[0] in r[1] for r in Inco.name_search(first[0])))

# 4. cross-store readers and the rewritten raw-SQL sites (NOTES.md s2.3 rows 14, 17, 22, 32)
Move = env['account.move']
n = sql("SELECT count(*) FROM account_move WHERE invoice_payment_term_id IS NOT NULL")[0][0]
check("account.move domain on many2one into MongoDB", Move.search_count([('invoice_payment_term_id', '!=', False)]) == n, n)
check("account.move domain by payment term name (two-step)", Move.search_count([('invoice_payment_term_id.name', 'ilike', 'immediate')])
      == sql("SELECT count(*) FROM account_move m JOIN account_payment_term t ON t.id = m.invoice_payment_term_id WHERE t.name->>'en_US' ILIKE %s", ('%immediate%',))[0][0])
check("account.journal domain on many2one into MongoDB", env['account.journal'].search_count([('journal_group_id', '!=', False)])
      == sql("SELECT count(*) FROM account_journal WHERE journal_group_id IS NOT NULL")[0][0])
invoice = Move.search([('move_type', '=', 'out_invoice')], limit=1)
result = invoice.get_cash_roundings()
check("row 14 get_cash_roundings (ORM)", result == {'total_length': 2, 'records': [
    {'id': 1, 'display_name': 'Round to 0.05'}, {'id': 2, 'display_name': 'Round to 1.00'}]}, result)
draft = Move.new({'move_type': 'out_invoice', 'company_id': env.company.id, 'invoice_cash_rounding_id': roundings[1].id})
check("row 14 get_cash_roundings puts the invoice's rounding first", [r['id'] for r in draft.get_cash_roundings(limit=1)['records']] == [2])
check("row 32 consolidation_rate on a MongoDB inheritor", externals.mapped('consolidation_rate') == [1.0]
      and externals.with_context(allowed_company_ids=env['res.company'].search([]).ids).mapped('consolidation_rate') == [1.0])
Tag = env['account.account.tag']
tag = Tag.create({'name': 'sum', 'applicability': 'taxes', 'country_id': env.ref('base.us').id})
negated = Tag.create({'name': 'W1B04_ADJ.balance', 'applicability': 'taxes', 'country_id': env.ref('base.us').id})
check("row 22 report_expression_id / balance_negate (ORM)", (tag.report_expression_id.id, tag.balance_negate) == (3, False)
      and (negated.report_expression_id.id, negated.balance_negate) == (2, False)
      and not Tag.new({'name': 'sum'}).report_expression_id, (tag.report_expression_id.id, negated.report_expression_id.id))
check("row 17 _translate_tax_tags runs on the storage path", Tag._translate_tax_tags(langs=['fr_FR'], tag_ids=tag.ids) is None
      and Tag._translate_tax_tags() is None)

# 5. writes through the storage path, then rolled back
term = Term.create({'name': 'Scenario 30/60', 'line_ids': [
    (0, 0, {'value': 'percent', 'value_amount': 40, 'nb_days': 30}),
    (0, 0, {'value': 'percent', 'value_amount': 60, 'nb_days': 60}),
]})
env.flush_all()
doc = st.model_collection(Term).find_one({'_id': term.id})
check("create writes the parent document with its embedded lines + shadow rows",
      doc and doc['name'] == {'en_US': 'Scenario 30/60'} and [e['id'] for e in doc['line']] == term.line_ids.ids
      and type(doc['line'][0]['valueAmount']).__name__ == 'Decimal128' and doc['line'][0]['nbDays'] == 30
      and sql("SELECT count(*) FROM account_payment_term_line WHERE id IN %s", (tuple(term.line_ids.ids),))[0][0] == 2, doc and doc.get('line'))
term.line_ids[0].write({'nb_days': 45})
term.write({'line_ids': [(0, 0, {'value': 'percent', 'value_amount': 0, 'nb_days': 90})]})
env.flush_all()
doc = st.model_collection(Term).find_one({'_id': term.id})
check("write updates an element, a new line is pushed", [e['nbDays'] for e in doc['line']] == [45, 60, 90] and len(term.line_ids) == 3)
term.line_ids[1].unlink()
env.flush_all()
doc = st.model_collection(Term).find_one({'_id': term.id})
check("unlink pulls the element", [e['nbDays'] for e in doc['line']] == [45, 90] and term.line_ids.mapped('nb_days') == [45, 90])
check("search sees the new rows", term in Term.search([('name', 'ilike', 'scenario')]) and Line.search_count([('payment_id', '=', term.id)]) == 2)
rounding = env['account.cash.rounding'].create({'name': 'Scenario rounding', 'rounding': 0.1, 'strategy': 'biggest_tax',
                                                 'rounding_method': 'DOWN', 'currency_ids': [(6, 0, [1])], 'partner_category_ids': [(6, 0, [1, 2])]})
env.flush_all()
doc = st.model_collection(rounding).find_one({'_id': rounding.id})
check("many2many create embeds the relation rows", doc['resCurrencyRel'] == [{'resCurrencyId': 1}]
      and sorted(e['resPartnerCategoryId'] for e in doc['resPartnerCategoryRel']) == [1, 2] and 'accountPaymentMethodLineRel' not in doc, doc)
rounding.write({'partner_category_ids': [(3, 1)], 'currency_ids': [(5,)]})
env.flush_all()
doc = st.model_collection(rounding).find_one({'_id': rounding.id})
check("many2many write pulls relation rows", [e['resPartnerCategoryId'] for e in doc.get('resPartnerCategoryRel', [])] == [2]
      and not doc.get('resCurrencyRel') and rounding.partner_category_ids.ids == [2] and not rounding.currency_ids, doc)
exception = env['account.lock_exception'].create({'company_id': env.company.id, 'user_id': env.uid, 'reason': 'Scenario',
                                                  'lock_date_field': 'tax_lock_date', 'lock_date': '2026-03-31'})
env.flush_all()
edoc = st.model_collection(exception).find_one({'_id': exception.id})
check("create lock exception document + shadow row", edoc and edoc['reason'] == 'Scenario' and edoc['lockDateField'] == 'tax_lock_date'
      and sql("SELECT count(*) FROM account_lock_exception WHERE id = %s", (exception.id,))[0][0] == 1, edoc)
report = Report.create({'name': 'Scenario report', 'section_report_ids': [(6, 0, [1])],
                        'column_ids': [(0, 0, {'name': 'Balance', 'expression_label': 'balance'})],
                        'line_ids': [(0, 0, {'name': 'Scenario line', 'code': 'SCN', 'expression_ids': [
                            (0, 0, {'label': 'balance', 'engine': 'external', 'formula': 'sum'})]})]})
env.flush_all()
rdoc = st.model_collection(report).find_one({'_id': report.id})
check("report create embeds sections, columns and lines; expressions are a root collection",
      rdoc['sectionRel'] == [{'subReportId': 1}] and [c['expressionLabel'] for c in rdoc['column']] == ['balance']
      and [l['code'] for l in rdoc['line']] == ['SCN'] and report.line_ids.expression_ids.report_line_id == report.line_ids
      and st.model_collection(env['account.report.expression']).find_one({'_id': report.line_ids.expression_ids.id})['formula'] == 'sum', rdoc)
refused("unique natural key refused (journal group name)", lambda: env['account.journal.group'].create({'name': 'IFRS ledger'}),
        lambda exc: 'E11000' in str(exc) or 'duplicate key' in str(exc))
refused("unique (report_line_id, label) refused", lambda: env['account.report.expression'].create(
    {'report_line_id': 1, 'label': 'balance', 'engine': 'external', 'formula': 'sum'}), lambda exc: 'E11000' in str(exc) or 'duplicate key' in str(exc))
refused("domain engine without subformula refused (CHECK mirrored by _check_domain_engine_subformula)", lambda: env['account.report.expression'].create(
    {'report_line_id': 1, 'label': 'scn', 'engine': 'domain', 'formula': '[]'}), lambda exc: type(exc).__name__ == 'ValidationError')
refused("duplicate line code per report refused (unique mirrored by _check_code_uniq)", lambda: env['account.report.line'].create(
    {'report_id': 1, 'name': 'Dup', 'code': 'W1B04_ADJ'}), lambda exc: type(exc).__name__ == 'ValidationError')
refused("duplicate column label per report refused (unique mirrored by _check_expression_label_uniq)", lambda: env['account.report.column'].create(
    {'report_id': 1, 'name': 'Dup', 'expression_label': report1.column_ids[0].expression_label}), lambda exc: type(exc).__name__ == 'ValidationError')
term_id, line_ids = term.id, term.line_ids.ids
term.unlink()
env.flush_all()
check("unlink removes the document, its lines and the shadow rows", st.model_collection(Term).find_one({'_id': term_id}) is None
      and not Line.browse(line_ids).exists()
      and sql("SELECT count(*) FROM account_payment_term WHERE id = %s", (term_id,))[0][0] == 0
      and sql("SELECT count(*) FROM account_payment_term_line WHERE id IN %s", (tuple(line_ids),))[0][0] == 0)
cr.rollback()
after = snapshot()
check("rollback leaves the loaded collections byte-identical", before == after, after)
print(f"{sum(checks)}/{len(checks)} checks passed")
assert all(checks)
