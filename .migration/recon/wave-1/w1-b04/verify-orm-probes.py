"""Verifier ORM probes for w1-b04 on the storage path, read-only: relation inverses (both sides), active_test on
account.report, search orders — each compared for exact equality with the PostgreSQL rows of the verifier's clone.
Run: odoo-bin shell -c <conf with mongodb_migration_db=<clone>> -d <clone> --no-http < this file. Documents are hashed
before and after to show nothing was written."""
import hashlib, json
from bson.json_util import dumps

cr = env.cr
st = env.registry.mongo_store
assert st.prefix == 'odoo_v_w1b04__', st.prefix  # temporary prefix only; the batch collections are never opened for writing
BATCH = ['accountPaymentTerm','accountIncoterms','accountCashRounding','accountJournalGroup','accountLockException','accountReport','accountReportExpression','accountReportExternalValue']
ROOTS = ['account.payment.term', 'account.incoterms', 'account.cash.rounding', 'account.journal.group',
         'account.lock_exception', 'account.report', 'account.report.expression', 'account.report.external.value']
ORDER = {'account.payment.term': 'sequence, id', 'account.payment.term.line': 'id', 'account.incoterms': 'id',
         'account.cash.rounding': 'sequence, id', 'account.journal.group': 'id', 'account.lock_exception': 'id',
         'account.report': 'sequence, id', 'account.report.line': 'sequence, id', 'account.report.column': 'sequence, id',
         'account.report.expression': 'id', 'account.report.external.value': 'date, id'}
out = []
def sql(q, p=()):
    cr.execute(q, p); return cr.fetchall()
def check(name, orm, pg):
    out.append({'probe': name, 'pass': orm == pg, 'orm': orm, 'pg': pg})
def snap():
    return {c: hashlib.sha256(dumps(list(st.db[c].find().sort('_id', 1)), sort_keys=True).encode()).hexdigest() for c in BATCH}
before = snap()

for m, order in ORDER.items():
    M = env[m].with_context(active_test=False)
    check(f'{m}.search([]) active_test=False order', M.search([]).ids, [r[0] for r in sql(f'SELECT id FROM {M._table} ORDER BY {order}')])
    check(f'{m}.search_count([]) active_test=False', M.search_count([]), sql(f'SELECT count(*) FROM {M._table}')[0][0])

# finding: account.report.search([]) under active_test (active is computed; compute_sql = COALESCE(active_selection = 'True', active_fallback))
cid = str(env.company.id)
pg_active = [r[0] for r in sql("SELECT id FROM account_report WHERE COALESCE((active_selection->>%s) = 'True', active_fallback) ORDER BY sequence, id", (cid,))]
pg_inactive = [r[0] for r in sql("SELECT id FROM account_report WHERE NOT COALESCE((active_selection->>%s) = 'True', active_fallback) ORDER BY sequence, id", (cid,))]
check('account.report.search([]) active_test', env['account.report'].search([]).ids, pg_active)
check('account.report.search_count([]) active_test', env['account.report'].search_count([]), len(pg_active))
check("account.report.search([('active','=',False)])", env['account.report'].search([('active', '=', False)]).ids, pg_inactive)
check('account.report active flags', [(r.id, r.active) for r in env['account.report'].with_context(active_test=False).search([], order='id')],
      [(r[0], r[1]) for r in sql("SELECT id, COALESCE((active_selection->>%s) = 'True', active_fallback) FROM account_report ORDER BY id", (cid,))])
check('account.payment.term.search_count([]) active_test (stored boolean)', env['account.payment.term'].search_count([]), sql('SELECT count(*) FROM account_payment_term WHERE active')[0][0])
check('account.cash.rounding.search_count([]) active_test (stored boolean)', env['account.cash.rounding'].search_count([]), sql('SELECT count(*) FROM account_cash_rounding WHERE active')[0][0])

# finding: section_main_report_ids inverse of the embedded relation table account_report_section_rel, both sides, every report
Report = env['account.report'].with_context(active_test=False)
reports = Report.search([], order='id')
pg_sec = sql('SELECT main_report_id, sub_report_id FROM account_report_section_rel ORDER BY 1, 2')
check('account.report.section_report_ids (owning side) per report', [(r.id, sorted(r.section_report_ids.ids)) for r in reports],
      [(i, sorted(s for m, s in pg_sec if m == i)) for i in reports.ids])
check('account.report.section_main_report_ids (inverse side) per report', [(r.id, sorted(r.section_main_report_ids.ids)) for r in reports],
      [(i, sorted(m for m, s in pg_sec if s == i)) for i in reports.ids])
check("search([('section_main_report_ids','!=',False)])", Report.search([('section_main_report_ids', '!=', False)], order='id').ids, sorted({s for m, s in pg_sec}))
check("search([('section_report_ids','!=',False)])", Report.search([('section_report_ids', '!=', False)], order='id').ids, sorted({m for m, s in pg_sec}))

# other relations, both sides
Term = env['account.payment.term'].with_context(active_test=False)
terms = Term.search([], order='id')
check('account.payment.term.line_ids per term', [(t.id, t.line_ids.ids) for t in terms],
      [(i, [r[0] for r in sql('SELECT id FROM account_payment_term_line WHERE payment_id = %s ORDER BY id', (i,))]) for i in terms.ids])
check('account.payment.term.line.payment_id', [(l.id, l.payment_id.id) for l in env['account.payment.term.line'].search([], order='id')],
      sql('SELECT id, payment_id FROM account_payment_term_line ORDER BY id'))
check('account.report.line_ids per report', [(r.id, r.line_ids.ids) for r in reports],
      [(i, [x[0] for x in sql('SELECT id FROM account_report_line WHERE report_id = %s ORDER BY sequence, id', (i,))]) for i in reports.ids])
check('account.report.column_ids per report', [(r.id, r.column_ids.ids) for r in reports],
      [(i, [x[0] for x in sql('SELECT id FROM account_report_column WHERE report_id = %s ORDER BY sequence, id', (i,))]) for i in reports.ids])
lines = env['account.report.line'].search([], order='id')
check('account.report.line.expression_ids', [(l.id, l.expression_ids.ids) for l in lines],
      [(i, [x[0] for x in sql('SELECT id FROM account_report_expression WHERE report_line_id = %s ORDER BY id', (i,))]) for i in lines.ids])
check('account.report.expression.report_line_id', [(x.id, x.report_line_id.id) for x in env['account.report.expression'].search([], order='id')],
      sql('SELECT id, report_line_id FROM account_report_expression ORDER BY id'))
check('account.report.line.parent_id / children_ids', [(l.id, l.parent_id.id or None, l.children_ids.ids) for l in lines],
      [(i, p, [x[0] for x in sql('SELECT id FROM account_report_line WHERE parent_id = %s ORDER BY sequence, id', (i,))]) for i, p in sql('SELECT id, parent_id FROM account_report_line ORDER BY id')])
check('account.report.root_report_id', [(r.id, r.root_report_id.id or None) for r in reports], sql('SELECT id, root_report_id FROM account_report ORDER BY id'))
groups = env['account.journal.group'].search([], order='id')
Journal = env['account.journal'].with_context(active_test=False)
check('account.journal by journal_group_id (PostgreSQL model -> MongoDB owner)', [(g.id, sorted(Journal.search([('journal_group_id', '=', g.id)]).ids)) for g in groups],
      [(i, [x[0] for x in sql('SELECT id FROM account_journal WHERE journal_group_id = %s ORDER BY id', (i,))]) for i in groups.ids])
check('account.journal.journal_group_id', [(j.id, j.journal_group_id.id or None) for j in Journal.search([], order='id')],
      sql('SELECT id, journal_group_id FROM account_journal ORDER BY id'))
Rounding = env['account.cash.rounding'].with_context(active_test=False)
roundings = Rounding.search([], order='id')
for fname, rel, col in [('currency_ids', 'account_cash_rounding_res_currency_rel', 'res_currency_id'),
                        ('partner_category_ids', 'account_cash_rounding_res_partner_category_rel', 'res_partner_category_id'),
                        ('payment_method_line_ids', 'account_cash_rounding_account_payment_method_line_rel', 'account_payment_method_line_id')]:
    if fname in Rounding._fields:
        check(f'account.cash.rounding.{fname}', [(r.id, sorted(r[fname].ids)) for r in roundings],
              [(i, [x[0] for x in sql(f'SELECT {col} FROM {rel} WHERE account_cash_rounding_id = %s ORDER BY 1', (i,))]) for i in roundings.ids])
    else:
        out.append({'probe': f'account.cash.rounding.{fname}', 'pass': True, 'orm': 'field absent on model', 'pg': 'skipped'})
check('account.report.external.value.target_report_expression_id', [(v.id, v.target_report_expression_id.id) for v in env['account.report.external.value'].search([], order='id')],
      sql('SELECT id, target_report_expression_id FROM account_report_external_value ORDER BY id'))
check('account.lock_exception user/company', [(e.id, e.user_id.id, e.company_id.id) for e in env['account.lock_exception'].search([], order='id')],
      sql('SELECT id, user_id, company_id FROM account_lock_exception ORDER BY id'))

after = snap()
out.append({'probe': 'batch (unprefixed) collections unchanged by the probes', 'pass': before == after, 'orm': after, 'pg': before})
out.append({'probe': 'prefixed copy equals the batch collections', 'pass': True, 'orm': {c: hashlib.sha256(dumps(list(st.db[st.prefix + c].find().sort('_id', 1)), sort_keys=True).encode()).hexdigest() for c in BATCH}, 'pg': after})
out[-1]['pass'] = out[-1]['orm'] == out[-1]['pg']
print('ORM_PROBES_JSON=' + json.dumps(out, default=str))
