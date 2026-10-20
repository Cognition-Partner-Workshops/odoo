"""Seed the scenario rows of batch w2-b01 (unit account-journal) on the worker's own PostgreSQL clone.

Run it through the pre-opt-in source tree (the SOURCE_COMMIT worktree build_source.sh keeps at
../odoo-unt12-src), after the shared seed_scenario_rows.py, so every write lands on PostgreSQL:

    /home/ubuntu/.venvs/odoo/bin/python ../odoo-unt12-src/odoo-bin shell -d <clone> --db_port=5433 \\
        --no-http < .migration/load/seed_account_journal.py

1. Deactivates the six cron writers of NOTES.md s2.3 §1 (ids 19-23 and 1) on the clone.
2. The three relation tables of the unit have 0 fixture rows (units.json recon_unverified):
   the fixture's "Bank Fees" model of company 1 gets the company's Bank journal (match_journal_ids ->
   accountJournal.accountReconcileModelRel), one partner (match_partner_ids ->
   accountReconcileModel.resPartnerRel) and its line gets the company's first tax (tax_ids ->
   accountReconcileModelLineAccountTaxRel); create_date/write_date pinned to FIXED_INSTANT (the
   build_source.sh instant), so a verifier reseeding its own clone gets identical rows.
Idempotent: an already seeded clone only gets the cron step again.
"""
FIXED_INSTANT = '2026-10-20 00:00:00'
CRON_IDS = [1, 19, 20, 21, 22, 23]

crons = env['ir.cron'].browse(CRON_IDS).exists()
assert set(crons.ids) == set(CRON_IDS), f"cron ids on this clone: {crons.ids}"
crons.write({'active': False})
print(f"crons deactivated: {sorted(crons.ids)}")

company = env['res.company'].browse(1)
model = env['account.reconcile.model'].search([('company_id', '=', company.id), ('name', '=', 'Bank Fees')], limit=1)
assert model and len(model.line_ids) == 1, f"fixture Bank Fees model of company 1: {model} lines {model.line_ids}"
if model.match_journal_ids:
    print(f"account.reconcile.model {model.id} already seeded: journals {model.match_journal_ids.ids}, "
          f"partners {model.match_partner_ids.ids}, line taxes {model.line_ids.tax_ids.ids}")
else:
    journal = env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'bank')], limit=1)
    partner = env['res.partner'].search([('is_company', '=', True), ('company_id', '=', False)], order='id', limit=1)
    tax = env['account.tax'].search([('company_id', '=', company.id)], order='id', limit=1)
    model.write({'match_journal_ids': [(6, 0, journal.ids)], 'match_partner_ids': [(6, 0, partner.ids)]})
    model.line_ids.write({'tax_ids': [(6, 0, tax.ids)]})
    env.flush_all()
    for table, ids in (('account_reconcile_model', model.ids), ('account_reconcile_model_line', model.line_ids.ids)):
        env.cr.execute(f"UPDATE {table} SET create_date = %s, write_date = %s WHERE id = ANY(%s)", (FIXED_INSTANT, FIXED_INSTANT, ids))
    print(f"account.reconcile.model {model.id} seeded: journal {journal.ids}, partner {partner.ids}, line {model.line_ids.ids} tax {tax.ids}")
env.cr.commit()
for table in ('account_journal_account_reconcile_model_rel', 'account_reconcile_model_res_partner_rel',
              'account_reconcile_model_line_account_tax_rel'):
    env.cr.execute(f"SELECT * FROM {table} ORDER BY 1, 2")
    print(f"{table}:", env.cr.fetchall())
