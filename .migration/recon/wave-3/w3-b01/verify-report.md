run_id: UNT14-59
manifest_sha: 79a896029481

# Wave 3 verifier report: w3-b01

Verdict: **PASS**

Independent verifier (ticket UNT14-59, plan step s4.3-wave-verify), who migrated none of these units. Base checked: mongo-run/unt13 at f84dbc723f61eeca98de9030e0a3fb4cb30dc540 (merge of https://github.com/Cognition-Partner-Workshops/odoo/pull/146, 8e8193dfab1). Plugin 2c1160efde323c570425953b7e38bcc3496c6053 from a detached worktree; recon harness 0.3.3 in live mode, target class migration_cluster, target odoo_unt13 as it stands (no reload), committed mapping_spec.json and recon_tolerances.json, PostgreSQL profile canonicalization. odoo_src rebuilt with build_source.sh; source_fingerprint.py printed a100e84ee2fb6282f30b45c003fd1db47561317c739340a10564d9e869e56a4e. Branch: recon/verify-w3-unt14.

## Recon re-runs (verifier ops, Tiers 1-4)

| unit | verdict | merge_eligible | source_server | T1 | T2 | T3 | T4 | result |
|---|---|---|---|---|---|---|---|---|
| accountReportLine | PASS | True | hmac-sha256:545efbd0aca82e45 | 4 | 8 | 2 | 1 | `.migration/recon/wave-3/w3-b01/verify/accountReportLine/result.json` |
| accountReconcileModel | PASS | True | hmac-sha256:545efbd0aca82e45 | 6 | 13 | 20 | 1 | `.migration/recon/wave-3/w3-b01/verify/accountReconcileModel/result.json` |
| accountReconcileModelLineAccountTaxRel | PASS | True | hmac-sha256:545efbd0aca82e45 | 3 | 0 | 1 | 2 | `.migration/recon/wave-3/w3-b01/verify/accountReconcileModelLineAccountTaxRel/result.json` |
| accountJournal | PASS | True | hmac-sha256:545efbd0aca82e45 | 21 | 20 | 26 | 1 | `.migration/recon/wave-3/w3-b01/verify/accountJournal/result.json` |
| accountFiscalPosition | PASS | True | hmac-sha256:545efbd0aca82e45 | 11 | 7 | 57 | 1 | `.migration/recon/wave-3/w3-b01/verify/accountFiscalPosition/result.json` |

Every run recorded git_head f84dbc723f61 with git_dirty false; verifier ops are in each unit's `verify/<unit>/ops.json` (sha256 recorded in result.json, distinct from the worker's).

## Comparison with batch evidence

| unit | source counts | T2 aggregates | T3 populations | mapping/tolerance sha |
|---|---|---|---|---|
| accountReportLine | same {"accountReportLine": 2} | same | same | same |
| accountReconcileModel | same {"accountReconcileModel": 9} | same | same | same |
| accountReconcileModelLineAccountTaxRel | same {"accountReconcileModelLineAccountTaxRel": 1} | same | same | same |
| accountJournal | same {"accountJournal": 25} | same | same | same |
| accountFiscalPosition | same {"accountFiscalPosition": 4} | same | same | same |

Worker evidence: `.migration/recon/wave-3/w3-b01/result.batch.json` (status PASS, recon_git_head 743e75613640, PR https://github.com/Cognition-Partner-Workshops/odoo/pull/146).

## Probes past the gate

- Documents scanned: {"accountReportLine": 2, "accountReconcileModel": 9, "accountReconcileModelLineAccountTaxRel": 1, "accountJournal": 25, "accountFiscalPosition": 4}
- Unmapped keys: 0; BSON type errors: 0; explicit null values: 0
- Spec indexes present: {"accountReportLine": "3/3", "accountReconcileModel": "3/3", "accountReconcileModelLineAccountTaxRel": "2/2", "accountJournal": "19/19", "accountFiscalPosition": "7/7"}; missing: 0
- Unique indexes carrying the storage path's `$exists` partial filter (by design, not listed in the spec): [{"collection": "accountReconcileModelLineAccountTaxRel", "keys": [["accountReconcileModelLineId", 1], ["accountTaxId", 1]]}, {"collection": "accountJournal", "keys": [["companyId", 1], ["code", 1]]}]
- References checked: 29, dangling: 0; resolved against: mongo:accountAccount._id, mongo:accountJournalGroup._id, mongo:accountReconcileModel.line.id, mongo:accountReport._id, mongo:accountReportLine._id, mongo:accountTax._id, pg:ir_act_report_xml.id, pg:mail_activity_type.id, pg:mail_alias.id, pg:res_company.id, pg:res_country.id, pg:res_country_group.id, pg:res_currency.id, pg:res_partner.id, pg:res_partner_bank.id, pg:res_users.id
- Junction read-back accountReconcileModelLineAccountTaxRel: {"links_mongo": 1, "links_pg": 1, "dup_pairs": 0, "missing_in_mongo": 0, "extra_in_mongo": 0, "endpoint_a_fanout_matches": true, "endpoint_b_fanout_matches": true, "distinct_a": 1, "distinct_b": 1}
- Detail: `.migration/recon/wave-3/w3-b01/verify/probe.json`

## Tour replay on MongoDB storage

- Scratch copy `odoo_w3v_b01` from odoo_src; 35 merged units loaded into prefix `odoo_w3v_b01__` with load_unit.py, then `-u product,stock,account,purchase_stock,sale_stock` (no errors), admin password set through odoo-bin shell as instructed.
- account:TestUi (addons/account/tests/test_tour.py): 6 tests, 0 failed, 0 error(s), 6 tour(s) succeeded. all six tours succeeded on MongoDB storage with normal limits; worker PR evidence reports 6/6 on both storages.
- Log excerpt: `.migration/recon/wave-3/w3-b01/verify/tour-mongodb.log`. Scratch PostgreSQL copy and `odoo_w3v_b01__*` collections dropped afterwards.

## Findings

- All 5 units re-ran live against odoo_unt13 as it stands with verifier-authored Tier 4 ops and returned PASS with merge_eligible true and source_server hmac-sha256:545efbd0aca82e45.
- Verifier Tier 1 source counts, Tier 2 aggregates and Tier 3 graded populations equal the worker's committed result.json for every unit, against the same mapping and tolerance sha256.
- Probe over 41 documents found no unmapped keys, no BSON type errors and no explicit nulls, and every spec index is present (0 missing).
- The unique indexes carry a partialFilterExpression requiring every key to exist, which the spec does not list; odoo/orm/storage_mongodb.py adds it by design so missing keys never collide like PostgreSQL NULLs, and the harness index check accepts it, so this is informational.
- All 29 declared references resolve with 0 dangling ids, into merged wave 1-3 collections in odoo_unt13 or PostgreSQL-resident tables only.
- Root junction links read back identically from both endpoints: every (a, b) pair in MongoDB matches odoo_src with no duplicates and the per-endpoint fan-out counts agree.
- MongoDB-storage tour replay on scratch copy odoo_w3v_b01 (account:TestUi (addons/account/tests/test_tour.py)): 6 tests, 0 failed, 0 error(s), 6 tour(s) succeeded; all six tours succeeded on MongoDB storage with normal limits; worker PR evidence reports 6/6 on both storages.
- The ticket's scratch recipe (createdb -T odoo_src, then -u product,stock,account,purchase_stock,sale_stock) fails on the first -u with MissingError account.report(1) until the 35 merged wave 1-3 units are loaded into the <scratch>__ prefix with .migration/load/load_unit.py --prefix; after that load the same -u completed with no errors, so this is a recipe gap, not a data defect.
- Scratch state was removed afterwards: both PostgreSQL copies dropped and 76 odoo_w3v_b0*__ collections dropped from odoo_unt13, leaving its migrated collections untouched; recon and probes were read-only on both endpoints.
