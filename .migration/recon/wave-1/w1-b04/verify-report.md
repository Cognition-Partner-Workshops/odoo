run_id: ticket-16e483f07e574aeb8173b3b41aadbad8
manifest_sha: b965d1e5f34e

# Wave 1 / w1-b04 (unit account-settings) — independent verify

Verdict: **PASS** (graded from `.migration/recon/wave-1/w1-b04/result.json`; nothing in this report asserts it by hand).

verified_head: 2f418c18d02c5c7e70d320d0b08fe600aebaa9c0

Third verification (2026-10-20) after PR #60 was rebased onto `mongo-run/unt12` `a25acb9` (unified wave-1 loader and seed script, PR #68) and frozen at `2f418c18d02`. Everything below was re-done at that head: fresh clone of `odoo_src` and reseed, one new live recon run scoped with `--collections`, the 455 data probes, and the same read-only ORM storage-path probes as the previous round, this time under a temporary prefix only (Odoo was never run with the batch collections unprefixed; nothing was written to them). Previous rounds verified `1a127143e78` and `b49c07d64e2`.

## What was verified, from where
- Batch PR: https://github.com/Cognition-Partner-Workshops/odoo/pull/60, head `2f418c18d02c5c7e70d320d0b08fe600aebaa9c0` (branch `devin/1792505468-w1-b04-account-settings`, rebased on `mongo-run/unt12` `a25acb9` = PR #68, `git merge-base --is-ancestor` confirmed), into `mongo-run/unt12`. This verify branch `recon/verify-w1-b04` is cut from that head as pushed; no batch code, mapping, or tolerance byte was changed.
- Contracts used (sha256 of the committed bytes, matches the ticket):
  - `.migration/mapping_spec.json` map-draft-2 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc`
  - `.migration/recon_tolerances.json` unt12-3 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea`
- Plugin: `mongo-migration-plugin` at `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (full SHA from `.migration/plugin_sha`, detached worktree, unpatched; `recon selftest PASS: 9 canonicalization rules exercised`).
- Verifier session worked no wave-1 batch ticket and wrote nothing to `odoo_unt12`: the harness ran in `--mode live` (read-only target reads) and the probes open the target with `SecondaryPreferred` reads only.

## Source: independent rebuild and clone
- `odoo_src` rebuilt with `.migration/fixtures/build_source.sh` (PG16 port 5433, source commit `63446015e3c154f552633f54951843dcbb51e9a9`, `-i product,uom,sale,purchase,stock,account --with-demo`, libfaketime instant `2026-10-20 00:00:00`): `migration.fixture_source=3 installed_modules=70`, row counts identical to the committed fixture manifest (product_template 37, product_product 47, uom_uom 30, sale_order 24, purchase_order 16, stock_move 135, account_move 59, account_move_line 171).
- `odoo_src` is the marker-3 rebuild of the previous round (untouched since; read only). Verifier clone `odoo_v_w1b04` = `createdb -p 5433 -T odoo_src odoo_v_w1b04`, dropped and recreated fresh for this round (the previous round's `odoo_v_w1b04_local` was dropped too; no second clone this time).
- Scenario rows seeded on the fresh clone with the committed unified `.migration/load/seed_scenario_rows.py` (PR #68; it also seeds the w1-b01 and w1-b06 rows, which are outside this batch) through the pre-opt-in source tree (`/home/ubuntu/repos/odoo-unt12-src`, so no Mongo write path exists in that process): account_cash_rounding 2, account_journal_group 2, account_lock_exception 1, account_report +1 (id 5, sectioned), account_report_line 2, account_report_expression 3, account_report_external_value 1, account_report_section_rel 2, cash-rounding junction rows 1/3/3. Crons 1,19,20,21,22,23 deactivated so the clone does not move during the run.
- Source DSN: `VERIFY_SRC_DSN`, derived in-process from `secret:personal:ODOO_PG_RO_DSN` with only the database name swapped to the clone; never printed.

## Recon re-run (one live run, inside the source query cap)
```
export PYTHONPATH=/home/ubuntu/plugin-9a584b4/skills/mongo-recon-harness/harness
/home/ubuntu/.venvs/recon/bin/python -m recon.cli run --unit account-settings --family postgresql \
  --mapping .migration/mapping_spec.json \
  --collections accountPaymentTerm,accountIncoterms,accountCashRounding,accountJournalGroup,accountLockException,accountReport,accountReportExpression,accountReportExternalValue \
  --tolerances .migration/recon_tolerances.json \
  --canonicalization /home/ubuntu/plugin-9a584b4/skills/mongo-migration/profiles/postgresql.md \
  --mode live --source-dsn-secret VERIFY_SRC_DSN --target-uri-secret MONGODB_ATLAS_URI \
  --target-db odoo_unt12 --target-class migration_cluster --allowed-targets-file .migration/allowed_targets.json \
  --ops .migration/recon/account-settings/ops.json --out .migration/recon/wave-1/w1-b04
```
Result: `recon PASS: unit=account-settings mode=live target_class=migration_cluster mapping=map-draft-2 tolerances=unt12-3 merge_eligible=True`; `warnings: []`, `error: null`. Tiers 1–4: 39 / 49 / 68 / 5 checks, 0 findings each — identical to the worker's committed `.migration/recon/account-settings/result.json` (the only differing key is `generated_at`). Source counts seen: accountPaymentTerm 11, accountIncoterms 11, accountCashRounding 2, accountJournalGroup 2, accountLockException 1, accountReport 5, accountReportExpression 3, accountReportExternalValue 1. No live mismatch occurred, so no drift re-run was needed.

Artifacts beside this report: `result.json`, `report.md`, `recon.summary.md` (harness), `verify-probes.py` / `verify-probes.json` (data probes below), `verify-orm-probes.py` / `verify-orm-probes.json` and `verify-orm-unflushed.py` / `verify-orm-unflushed.json` (ORM probes), `verify-result.json`. The data probes were run again after the ORM probes and the prefix cleanup: all 455 outcomes and every evidence value identical; the only differing byte is the informational list of *other* collections present in `odoo_unt12` (another worker's temporary prefix `odoo_v_w1b05c__productAttribute` appeared in between), so the ORM session left the 8 batch collections untouched.

## Probes past the gate (`verify-probes.py`, 455 probes, 455 pass)
- Collection presence: all 8 declared collections exist; the other collections in `odoo_unt12` (wave 0 and other wave-1 batches) were only listed, never read.
- Row counts, key sets, min/max `_id` boundary documents: equal on all 8 roots; no empty collection.
- Per-field null/missing rate and value equality for every mapped root field (jsonb translations, Decimal128, dates, company-dependent `profitAccountId`/`lossAccountId` objects, `createDate`/`writeDate` at the fixed instant): 0 differing keys. No unmapped target fields on any root document.
- Embedded arrays vs source child rows — `accountPaymentTerm.line` (13 lines, 11 parents, max 2), `accountCashRounding.resCurrencyRel` (1) / `resPartnerCategoryRel` (3) / `accountPaymentMethodLineRel` (3), `accountReport.column` (8 over 4 reports) / `line` (2) / `sectionRel` (2): array length equals child-row count for every parent, element key sets equal, no empty array field on childless parents, child field values equal for `line` / `column` / `line` child rows, no unmapped element fields.
- Natural keys unique in target (`accountIncoterms.code`, `accountJournalGroup.name`, `accountReportExpression (reportLineId,label)`, etc. as declared); every declared index present with the declared uniqueness.
- Outbound references: declared spec references resolve inside this batch (`accountReport.rootReportId`, `accountReport.sectionRel.subReportId`, `accountReportExpression.reportLineId` → `accountReport.line.id`, `accountReportExternalValue.targetReportExpressionId` / `carryoverOriginReportLineId`, `accountReport.line.parentId` inside the same document). Relational references (`companyId`→res_company, `userId`/`createUid`/`writeUid`→res_users, `countryId`→res_country, junction ids → res_currency / res_partner_category / account_payment_method_line) all resolve in the PostgreSQL source, which still owns those tables. No reference points at any wave-1 sibling batch collection (`cross_batch_reference`: none), and no sibling namespace was queried.
- Boundary values: min/max of `rounding`, `discountPercentage`, `sequence`, `value`, `date`, `lockDate`, `endDatetime`, `loadMoreLimit`, and embedded `line.valueAmount` (30 … 100) equal source min/max.
- Tier 4 replayed by the verifier from `ops.json` (SQL on the clone vs aggregation on the target, canonicalised independently of the harness): all 5 operations equal row-for-row (11, 11, 2, 5, 3 rows).

## Findings
None. (Two probe-script false alarms during development — PostgreSQL `date` vs BSON midnight datetime, and lexicographic sort of Decimal strings — were probe bugs, fixed in `verify-probes.py`; the data matched.)

## ORM storage-path probes for the three first-round findings (read-only, exact equality with PostgreSQL)
Run through `odoo-bin shell` on the run-branch tree at the verified head, conf `/home/ubuntu/verify-w1b04/prefix.conf` (`[options] db_port = 5433` only, so `storage_mongodb` uses the temporary prefix `odoo_v_w1b04__`; both scripts assert `st.prefix == 'odoo_v_w1b04__'`) against the seeded clone. The prefixed namespace `odoo_unt12.odoo_v_w1b04__<collection>` was filled with a driver copy of the 8 batch collections (read on the batch side, inserted on the prefixed side only), used for the probes, then dropped; the batch collections were never opened for writing (hashes of all 8 unprefixed collections equal before/after and equal to the prefixed copy); every probe compares the ORM value with the clone's PostgreSQL rows (which still carry the legacy columns) for exact list/tuple equality. `verify-orm-probes.py`: 49 probes, 49 pass; batch collection documents hashed before and after: unchanged.
1. `section_main_report_ids` inverse of the embedded relation table `account_report_section_rel`: per report, `section_report_ids` (owning side) and `section_main_report_ids` (inverse side) both equal the PostgreSQL rows (`5 -> [2, 3]`, `2 -> [5]`, `3 -> [5]`, others empty); `search([('section_main_report_ids','!=',False)]) == [2, 3]` and `search([('section_report_ids','!=',False)]) == [5]`, matching the table. Fixed at this head.
2. `account.report.search([])` under `active_test` (computed, non-stored `active`): equals `SELECT id FROM account_report WHERE COALESCE((active_selection->>company) = 'True', active_fallback) ORDER BY sequence, id` ([1, 2, 3, 4, 5]), `search_count([]) == 5`, `search([('active','=',False)]) == []`, per-record `active` flags equal the same SQL. Because every seeded report is active, the discriminating case was added on the scratch clone (probe 3 file): archiving report 4 through the computed field, before any flush, drops it from `search([])` ([1, 2, 3, 5]) and `search_count([])` (4) while `active_test=False` still returns all 5. Fixed at this head.
3. Search after an unflushed write: `verify-orm-unflushed.py`, 13 probes, 13 pass, on the verifier clone with the storage path writing only into the temporary prefix `odoo_v_w1b04__` (copy of the 8 batch collections; transaction rolled back, prefix dropped afterwards). Right after an unflushed create the term is found by name and its two embedded lines by `payment_id`; after an unflushed rename it is found under the new name and not the old; after an unflushed archive it is excluded by default and found with `active_test=False`; an unflushed child write is searchable; after flush the document equals the record (`name`, `active`, 2 lines); after rollback there is neither a document nor a shadow row. Fixed at this head.
Also exact-equal with PostgreSQL: `search([])` order and `search_count` for all 11 models of the unit with `active_test=False`, stored-boolean `active_test` on payment terms and cash roundings, and every other relation from both sides (`line_ids`/`payment_id`, `line_ids`/`column_ids`/`expression_ids`/`report_line_id`, `parent_id`/`children_ids`, `root_report_id`, journal group membership from the PostgreSQL-side `account.journal`, the three cash-rounding junction tables, `target_report_expression_id`, lock-exception user/company).
The first round's third item, raw `BulkWriteError` on duplicate unique keys, was not requested for this round and was not probed.

## Plugin / skill gap (report only, plugin untouched)
- `wave-verify` SKILL.md names a `--source-concurrency` flag; the pinned harness CLI at `9a584b4` has no such option, so the run above omits it. The run still fits the source query cap (one live run per unit).
- `RECON_REDACT_SALT` is unset in this environment, so `result.json` is redacted with unsalted hashes (harness warning); same condition as the worker's committed result.
- The snapshot's Odoo venv lacks the Mongo driver pinned in the run branch's `requirements.txt`; importing `odoo.cli` on the run branch fails until it is installed in the venv (`pip install` of the pinned line). Environment gap, not a batch defect.
- `mongo_guard` (pinned plugin) refuses any exec whose text names the driver next to a write verb unless `origin/HEAD` points at the run branch, the exec runs inside the checkout and the text names an allow-listed `--db`; so the prefix copy/cleanup scripts name `--db odoo_unt12` in their exec text and run from the checkout. The guard also rejects an exec that binds the PG read-only secret while its text contains a Mongo collection-drop verb, so the prefix cleanup and the data-probe rerun had to be separate execs. Reported, not routed around.
