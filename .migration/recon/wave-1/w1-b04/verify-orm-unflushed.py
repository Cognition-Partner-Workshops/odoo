"""Verifier probe for the storage path's search after an unflushed create / write / archive. Runs against a scratch
the verifier's temporary prefix odoo_v_w1b04__ on the target database (a copy of the batch collections; the
batch collections themselves are never opened for writing) and the verifier's PostgreSQL clone; rolled back at the end."""
import json

cr = env.cr
st = env.registry.mongo_store
assert st.prefix == 'odoo_v_w1b04__', st.prefix  # every write lands in the temporary prefix, rolled back at the end
out = []
def sql(q, p=()):
    cr.execute(q, p); return cr.fetchall()
def check(name, orm, pg):
    out.append({'probe': name, 'pass': orm == pg, 'orm': orm, 'pg': pg})
Term, Line = env['account.payment.term'], env['account.payment.term.line']
term = Term.create({'name': 'Verify 30/60', 'line_ids': [
    (0, 0, {'value': 'percent', 'value_amount': 40, 'nb_days': 30}),
    (0, 0, {'value': 'percent', 'value_amount': 60, 'nb_days': 60}),
]})
check('search right after unflushed create', Term.search([('name', '=', 'Verify 30/60')]).ids, [term.id])
check('child search right after unflushed create', sorted(Line.search([('payment_id', '=', term.id)]).ids), sorted(term.line_ids.ids))
check('created id is a shadow row (PostgreSQL)', [term.id], [r[0] for r in sql('SELECT id FROM account_payment_term WHERE id = %s', (term.id,))])
term.name = 'Verify renamed'
check('search right after unflushed write finds the new value', Term.search([('name', '=', 'Verify renamed')]).ids, [term.id])
check('search right after unflushed write misses the old value', Term.search([('name', '=', 'Verify 30/60')]).ids, [])
term.active = False
check('search right after unflushed archive excludes the record', Term.search([('name', '=', 'Verify renamed')]).ids, [])
check('search active_test=False right after unflushed archive finds it', Term.with_context(active_test=False).search([('name', '=', 'Verify renamed')]).ids, [term.id])
term.line_ids[0].nb_days = 45
check('child search right after unflushed child write', Line.search([('payment_id', '=', term.id), ('nb_days', '=', 45)]).ids, [term.line_ids[0].id])
Report = env['account.report']
all_reports = Report.with_context(active_test=False).search([], order='id')
Report.browse(4).active = False
check('account.report: unflushed archive via the computed active (inverse) is excluded under active_test',
      Report.search([], order='id').ids, [r.id for r in all_reports if r.active])
check('account.report: archived id not in search([]) / counted', [4 in Report.search([]).ids, Report.search_count([])], [False, len(all_reports) - 1])
check('account.report: archived id found with active_test=False', 4 in all_reports.ids and Report.with_context(active_test=False).search_count([]), len(all_reports))
env.flush_all()
docs = list(st.model_collection(Term).find({'_id': term.id}))
check('after flush, document matches the ORM record', [(d['_id'], d.get('name', {}).get('en_US') if isinstance(d.get('name'), dict) else d.get('name'), d.get('active'), len(d.get('line', []))) for d in docs],
      [(term.id, 'Verify renamed', False, 2)])
cr.rollback()
check('after rollback, no document and no shadow row', [list(st.model_collection(Term).find({'_id': term.id})), sql('SELECT id FROM account_payment_term WHERE id = %s', (term.id,))], [[], []])
print('ORM_UNFLUSHED_JSON=' + json.dumps(out, default=str))
