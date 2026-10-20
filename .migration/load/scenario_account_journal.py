"""ORM scenario for batch w2-b01 (unit account-journal) on the MongoDB storage path.

Run on the run branch against the worker's seeded clone on a prefixed clone (no conf key
mongodb_migration_db names the clone, so the storage path reads ``<clone>__<collection>``: copy the
loaded collections of every opted-in model under that prefix first, so no ORM write reaches the live
collections):

    /home/ubuntu/.venvs/odoo/bin/python odoo-bin shell -d <clone> --db_port=5433 --no-http \\
        < .migration/load/scenario_account_journal.py

Reads are compared with the clone's PostgreSQL rows (the clone still carries the legacy columns).
The rewritten SQL paths of NOTES.md s2.3 (§3a rows 10-12, §3b row 24) are exercised through the
journal dashboard, the payment-method information and the bank statement validity check, and compared
with direct PostgreSQL reads. Every write happens in one transaction that is rolled back at the end,
and the documents are hashed before and after to show the journal left the collections untouched.
"""
import hashlib
import json

from bson.json_util import dumps

from odoo.exceptions import ValidationError

cr = env.cr
st = env.registry.mongo_store
print(f"collection prefix {st.prefix!r}")
assert st.prefix, "collections are unprefixed: run this scenario on a clone the conf does not name as mongodb_migration_db"
Journal = env['account.journal'].with_context(active_test=False)
Method = env['account.payment.method']
Model = env['account.reconcile.model'].with_context(active_test=False)
for model in (Journal, Method, Model, env['account.payment.method.line'], env['account.reconcile.model.line']):
    assert model._storage == 'mongodb', model._name
COLLECTIONS = ('accountJournal', 'accountPaymentMethod', 'accountReconcileModel', 'accountReconcileModelLineAccountTaxRel')
assert st.collection('accountJournal').estimated_document_count(), f"{st.prefix}accountJournal is empty: copy the collections first"

results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'} {name}{' -- ' + str(detail) if detail else ''}")


def collection_hash(name):
    docs = list(st.collection(name).find({}, sort=[('_id', 1)]))
    return hashlib.sha256(dumps(docs, sort_keys=True).encode()).hexdigest()


def rows(sql, params=()):
    cr.execute(sql, params)
    return cr.fetchall()


before = {name: collection_hash(name) for name in COLLECTIONS}
collections_before = set(st.db.list_collection_names())

# -- reads against the clone's legacy rows ---------------------------------------------------------
journals = Journal.search([], order='id')
pg = rows("SELECT id, code, type, company_id, currency_id, default_account_id, name->>'en_US' FROM account_journal ORDER BY id")
check('journal count', len(journals) == len(pg) == st.collection('accountJournal').count_documents({}), len(journals))
check('journal fields', [(j.id, j.code, j.type, j.company_id.id, j.currency_id.id or None, j.default_account_id.id or None, j.name) for j in journals] == pg)
check('journal translated name', Journal.with_context(lang='en_US').browse(pg[0][0]).name == pg[0][6])
check('journal search by type/company', Journal.search([('type', '=', 'bank'), ('company_id', '=', 1)]).ids
      == [r[0] for r in rows("SELECT id FROM account_journal WHERE type = 'bank' AND company_id = 1 ORDER BY id")])
check('journal cross-store search (default account type)', Journal.search([('default_account_id.account_type', '=', 'income')], order='id').ids
      == [r[0] for r in rows("SELECT j.id FROM account_journal j JOIN account_account a ON a.id = j.default_account_id WHERE a.account_type = 'income' ORDER BY j.id")])

methods = Method.search([], order='id')
check('payment methods and lines', [(m.id, m.code, m.payment_type, sorted((l.id, l.journal_id.id, l.sequence) for l in env['account.payment.method.line'].search([('payment_method_id', '=', m.id)]))) for m in methods]
      == [(r[0], r[1], r[2], sorted((x[0], x[1], x[2]) for x in rows("SELECT id, journal_id, sequence FROM account_payment_method_line WHERE payment_method_id = %s", (r[0],))))
          for r in rows("SELECT id, code, payment_type FROM account_payment_method ORDER BY id")])
check('journal inbound/outbound payment method lines', [(j.id, sorted(j.inbound_payment_method_line_ids.ids), sorted(j.outbound_payment_method_line_ids.ids)) for j in journals if j.type == 'bank']
      == [(r[0], [x[0] for x in rows("SELECT l.id FROM account_payment_method_line l JOIN account_payment_method m ON m.id = l.payment_method_id WHERE l.journal_id = %s AND m.payment_type = 'inbound' ORDER BY l.id", (r[0],))],
           [x[0] for x in rows("SELECT l.id FROM account_payment_method_line l JOIN account_payment_method m ON m.id = l.payment_method_id WHERE l.journal_id = %s AND m.payment_type = 'outbound' ORDER BY l.id", (r[0],))])
          for r in rows("SELECT id FROM account_journal WHERE type = 'bank' ORDER BY id")])

models = Model.search([], order='id')
check('reconcile models, lines, seeded relations',
      [(m.id, m.name, m.rule_type, m.company_id.id, sorted(m.line_ids.ids), sorted(m.match_journal_ids.ids), sorted(m.match_partner_ids.ids), sorted(m.line_ids.tax_ids.ids)) for m in models]
      == [(r[0], r[1], r[2], r[3],
           [x[0] for x in rows("SELECT id FROM account_reconcile_model_line WHERE model_id = %s ORDER BY id", (r[0],))],
           [x[0] for x in rows("SELECT account_journal_id FROM account_journal_account_reconcile_model_rel WHERE account_reconcile_model_id = %s ORDER BY 1", (r[0],))],
           [x[0] for x in rows("SELECT res_partner_id FROM account_reconcile_model_res_partner_rel WHERE account_reconcile_model_id = %s ORDER BY 1", (r[0],))],
           [x[0] for x in rows("SELECT t.account_tax_id FROM account_reconcile_model_line_account_tax_rel t JOIN account_reconcile_model_line l ON l.id = t.account_reconcile_model_line_id WHERE l.model_id = %s ORDER BY 1", (r[0],))])
          for r in rows("SELECT id, name->>'en_US', rule_type, company_id FROM account_reconcile_model ORDER BY id")])
seeded = models.filtered('match_journal_ids')
check('seeded relations present (never UNVERIFIED)', seeded and seeded.match_partner_ids and seeded.line_ids.tax_ids,
      f"model {seeded.ids} journals {seeded.match_journal_ids.ids} partners {seeded.match_partner_ids.ids} taxes {seeded.line_ids.tax_ids.ids}")
check('line amount Decimal128 read as float', all(isinstance(l.amount, float) for l in models.line_ids))

# -- rewritten SQL paths (s2.3 §3a rows 10-12, §3b row 24) ----------------------------------------
all_journals = Journal.search([]).with_context(allowed_company_ids=env.companies.ids)
dashboard = all_journals._get_journal_dashboard_data_batched()
check('dashboard data for every journal (rows 12/24)', set(dashboard) == set(all_journals.ids) and all(dashboard[j.id] for j in all_journals), sorted(dashboard[all_journals[0].id])[:6])
entries = dict(rows("SELECT journal_id, count(*) FROM account_move GROUP BY journal_id"))
check('has_entries / has_posted_entries vs account_move (row 12)',
      all(j.has_entries == (entries.get(j.id, 0) > 0) for j in all_journals)
      and all(j.has_posted_entries == bool(rows("SELECT 1 FROM account_move WHERE journal_id = %s AND state = 'posted' LIMIT 1", (j.id,))) for j in all_journals))
check('entries_count vs account_move', all(j.entries_count == entries.get(j.id, 0) for j in all_journals if j.company_id in env.companies))
bank = all_journals.filtered(lambda j: j.type in ('bank', 'cash', 'credit'))
running = bank._get_journal_dashboard_bank_running_balance()
check('bank running balance per bank journal (row 12)', set(running) == set(bank.ids) and all(isinstance(v[1], float) for v in running.values()))
last = dict(rows("SELECT DISTINCT ON (journal_id) journal_id, id FROM account_bank_statement WHERE first_line_index IS NOT NULL ORDER BY journal_id, first_line_index DESC"))
check('last_statement_id vs account_bank_statement (row 12)', all((j.last_statement_id.id or None) == last.get(j.id) for j in bank))
direct = bank._get_direct_bank_payments()
check('direct bank payments keyed by journal (row 12)', set(direct) == set(bank.ids))
check('activity data per journal (row 12)', all(json.loads(j.json_activity_data)['activities'] is not None for j in all_journals))
info = all_journals._get_journals_payment_method_information()
check('payment method information (row 11)', set(info) == {'pay_methods', 'manage_providers', 'method_information_mapping', 'providers_per_code'}
      and set(info['method_information_mapping']) == set(Method.search([]).ids))
check('available payment methods per bank journal', all(j.available_payment_method_ids for j in bank))
statements = env['account.bank.statement'].search([])
check('invalid statements, all and per statement (row 10)', statements._get_invalid_statement_ids(all_statements=True) == []
      and statements._get_invalid_statement_ids() == [] if statements else statements._get_invalid_statement_ids(all_statements=True) == [])

# -- writes, in one transaction rolled back at the end ---------------------------------------------
company = seeded[:1].company_id
new_journal = Journal.create({'name': 'Scenario journal', 'code': 'W2B1', 'type': 'general', 'company_id': company.id})
doc = st.collection('accountJournal').find_one({'_id': new_journal.id})
check('journal create: document + shadow row', doc and doc['code'] == 'W2B1' and doc['name'] == {'en_US': 'Scenario journal'}
      and rows("SELECT id FROM account_journal WHERE id = %s", (new_journal.id,)))
try:
    with cr.savepoint():
        Journal.create({'name': 'Dup', 'code': 'W2B1', 'type': 'general', 'company_id': company.id})
    check('journal unique (code, company) constraint', False)
except Exception as exc:
    check('journal unique (code, company) constraint', True, type(exc).__name__)
model = seeded[:1]
other_journal = (bank.filtered(lambda j: j.company_id == model.company_id) - model.match_journal_ids)[:1] or new_journal
model.write({'match_journal_ids': [(4, other_journal.id)]})
env.flush_all()
doc = st.collection('accountJournal').find_one({'_id': other_journal.id})
check('m2m add: element pushed into accountJournal.accountReconcileModelRel', any(e['accountReconcileModelId'] == model.id for e in doc.get('accountReconcileModelRel', [])))
model.write({'match_journal_ids': [(3, other_journal.id)]})
env.flush_all()
doc = st.collection('accountJournal').find_one({'_id': other_journal.id})
check('m2m remove: element pulled', not any(e['accountReconcileModelId'] == model.id for e in doc.get('accountReconcileModelRel', [])))
line = model.line_ids[:1]
tax = env['account.tax'].search([('company_id', '=', model.company_id.id), ('id', 'not in', line.tax_ids.ids)], limit=1)
line.write({'tax_ids': [(4, tax.id)]})
env.flush_all()
rel = st.collection('accountReconcileModelLineAccountTaxRel')
check('relation collection: tax pair inserted', rel.find_one({'accountReconcileModelLineId': line.id, 'accountTaxId': tax.id}) is not None)
line.write({'tax_ids': [(3, tax.id)]})
env.flush_all()
check('relation collection: tax pair removed', rel.find_one({'accountReconcileModelLineId': line.id, 'accountTaxId': tax.id}) is None)
analytic_account = env['account.analytic.account'].search([('company_id', 'in', (False, company.id))], limit=1)
new_model = Model.create({'name': 'Scenario model', 'rule_type': model.rule_type, 'company_id': company.id,
                          'match_partner_ids': [(6, 0, env['res.partner'].search([('is_company', '=', True)], limit=1).ids)],
                          'line_ids': [(0, 0, {'account_id': new_journal.default_account_id.id or env['account.account'].search([('company_ids', 'in', company.id)], limit=1).id, 'amount_type': 'percentage', 'amount_string': '100',
                                               'analytic_distribution': {str(analytic_account.id): 100} if analytic_account else False})]})
doc = st.collection('accountReconcileModel').find_one({'_id': new_model.id})
check('reconcile model create with partner relation and line', doc and len(doc['resPartnerRel']) == 1 and len(doc['line']) == 1 and doc['line'][0]['id'] == new_model.line_ids.id)
if analytic_account:
    # (set at create time: writing a Json field on a MongoDB-stored model fails in storage_mongodb.write_multi,
    #  `unhashable type: 'dict'` -- shared storage-path gap reported on the ticket, not patched here)
    Line = env['account.reconcile.model.line']
    check('analytic_distribution search in / not in / ilike on a MongoDB-stored analytic.mixin',
          Line.search([('analytic_distribution', 'in', [analytic_account.id])]).ids == new_model.line_ids.ids
          and new_model.line_ids not in Line.search([('analytic_distribution', 'not in', [analytic_account.id])])
          and line in Line.search([('analytic_distribution', 'not in', [analytic_account.id])])
          and new_model.line_ids in Line.search([('analytic_distribution', 'ilike', analytic_account.name)]))
new_model.unlink()
new_journal.unlink()
env.flush_all()
check('unlink: documents and shadow rows gone', st.collection('accountReconcileModel').find_one({'_id': new_model.id}) is None
      and st.collection('accountJournal').find_one({'_id': new_journal.id}) is None
      and not rows("SELECT id FROM account_journal WHERE id = %s", (new_journal.id,)))

cr.rollback()
env.invalidate_all()
after = {name: collection_hash(name) for name in COLLECTIONS}
check('collections byte-identical after rollback', after == before, {n: before[n][:12] for n in COLLECTIONS})
check('no collection created outside the unit', set(st.db.list_collection_names()) == collections_before,
      sorted(set(st.db.list_collection_names()) - collections_before))
passed = sum(ok for _, ok in results)
print(f"scenario account-journal: {passed}/{len(results)} checks passed")
assert passed == len(results), [name for name, ok in results if not ok]
