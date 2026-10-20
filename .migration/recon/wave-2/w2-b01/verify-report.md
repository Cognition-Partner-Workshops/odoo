run_id: ticket-385106c940014e95acae82191fc75d86
manifest_sha: ae71ec6a28e6

# Verify report: wave 2, batch w2-b01 (unit account-journal) - **PASS**

Independent verifier; this session migrated none of wave 2 and wrote nothing to `odoo_unt12`.

## What was re-run
- Batch PR: https://github.com/Cognition-Partner-Workshops/odoo/pull/69, head `779e1db28527227574c51569b37815ec9ea7bb5a` (code head `7896d8a`), base `mongo-run/unt12@7fee6d9`. Verifier branch `recon/verify-w2-b01` is cut from that pushed head; no implementation file was changed.
- Mapping `map-draft-2` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc` and tolerances `unt12-3` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea`: committed bytes on the PR head, re-hashed by the verifier, equal to the ticket pins and to the sha256 values recorded in the rerun result.json.
- Plugin/harness pinned at `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (detached worktree, unpatched); canonicalization from `skills/mongo-migration/profiles/postgresql.md`.
- Source: `odoo_src` rebuilt independently with `.migration/fixtures/build_source.sh` (marker `migration.fixture_source=3`, 70 modules), then `createdb -T odoo_src odoo_v42`; `seed_scenario_rows.py` then `seed_account_journal.py` applied to `odoo_v42` through the source tree (`odoo-unt12-src/odoo-bin shell`, PostgreSQL storage only), crons 1 and 19-23 deactivated on the clone only. `odoo_src` untouched.
- Target: `odoo_unt12` on `MONGODB_ATLAS_URI` (class `migration_cluster`), read-only. Collections graded: `accountJournal`, `accountPaymentMethod`, `accountReconcileModel`, `accountReconcileModelLineAccountTaxRel`; ops from `.migration/recon/account-journal/ops.json` as committed.

## Recon rerun (harness verdict)
- Result: `.migration/recon/wave-2/w2-b01/account-journal/result.json` - verdict **PASS**, mode `live`, target_class `migration_cluster`, merge_eligible `True`, generated `2026-10-20T20:48:13.650744+00:00`, warnings `[]`.

| Tier | Name | Checks | Findings | Result |
|---|---|---|---|---|
| 1 | counts_through_mapping | 36 | 0 | PASS |
| 2 | per_field_aggregates | 38 | 0 | PASS |
| 3 | keyed_diffs | 41 | 0 | PASS |
| 4 | app_level_parity | 5 | 0 | PASS |

- Source counts seen by the harness: {"accountJournal": 14, "accountPaymentMethod": 2, "accountReconcileModel": 8, "accountReconcileModelLineAccountTaxRel": 1} - identical to the worker run (`.migration/recon/account-journal/result.json`, 36/38/41/5 checks). One live run was enough: no mismatch, so no source re-read for drift was needed; the probe script re-read the source counts at its end and they were unchanged.

## Probes past the gate
Script `.migration/recon/wave-2/w2-b01/probe_w2_b01.py` (read-only on both sides: PG `default_transaction_read_only`, Atlas `secondaryPreferred`, no write call), evidence `.migration/recon/wave-2/w2-b01/probe-results.json`. 102 probes, 0 FAIL, 0 SKIP.

| Probe family | Probes | Result | What it checked |
|---|---|---|---|
| count | 4 | PASS | document count == source row count per collection; none empty (accountJournal 14/14, accountPaymentMethod 2/2, accountReconcileModel 8/8, accountReconcileModelLineAccountTaxRel 1/1) |
| null_missing | 61 | PASS | per mapped field: no explicit BSON null on the target (null_missing_equiv), and target missing-field count == source NULL count |
| duplicates | 6 | PASS | no duplicate `_id`; no duplicate natural keys (companyId+code, code+paymentType, accountTaxId+accountReconcileModelLineId) |
| boundaries | 3 | PASS | min/max `_id` and min/max of sequence/code equal source;  |
| boundary_doc | 2 | PASS | first and last journal compared field by field against the source row (datetime canonicalized to seconds) |
| embed_lengths | 4 | PASS | per parent: embedded array length == source child-row count; totals and length distributions: accountJournal.accountReconcileModelRel 1/1 dist {'0': 13, '1': 1}; accountPaymentMethod.line 4/4 dist {'2': 2}; accountReconcileModel.resPartnerRel 1/1 dist {'0': 7, '1': 1}; accountReconcileModel.line 10/10 dist {'1': 6, '2': 2} |
| reference | 12 | PASS | outbound references resolve - merged wave-1 collections (accountAccount, accountJournalGroup, accountTax) and same-batch (accountReconcileModel, accountReconcileModel.line.id, accountJournal) only; sibling batch w2-b02 (product-catalog) namespaces never inspected, none referenced: accountJournal.defaultAccountId->accountAccount._id (6 values, 0 dangling), accountJournal.journalGroupId->accountJournalGroup._id (0 values, 0 dangling), accountJournal.lossAccountId->accountAccount._id (2 values, 0 dangling), accountJournal.nonDeductibleAccountId->accountAccount._id (0 values, 0 dangling), accountJournal.profitAccountId->accountAccount._id (2 values, 0 dangling), accountJournal.suspenseAccountId->accountAccount._id (2 values, 0 dangling), accountJournal.accountReconcileModelRel.accountReconcileModelId->accountReconcileModel._id (1 values, 0 dangling), accountPaymentMethod.line.journalId->accountJournal._id (2 values, 0 dangling), accountPaymentMethod.line.paymentAccountId->accountAccount._id (0 values, 0 dangling), accountReconcileModel.line.accountId->accountAccount._id (9 values, 0 dangling), accountReconcileModelLineAccountTaxRel.accountReconcileModelLineId->accountReconcileModel._id (1 values, 0 dangling), accountReconcileModelLineAccountTaxRel.accountTaxId->accountTax._id (1 values, 0 dangling) |
| indexes | 4 | PASS | every index declared by the mapping exists on the live collection (19/4/3/2) |
| ops_replay | 5 | PASS | the 5 app-level parity ops replayed independently (source SQL on the clone vs target pipeline), compared as unordered row sets keyed by column name: journals_by_type_with_reconcile_model_count 14=14 rows, dashboard_journals_per_company_and_type 8=8 rows, payment_method_lines_per_journal 4=4 rows, reconcile_models_with_line_and_partner_counts 8=8 rows, reconcile_model_line_taxes 1=1 rows |
| source_stability | 1 | PASS | source counts re-read after all probes, unchanged |

## Findings
No findings. Nothing in the batch blocks merge; no plugin gap was hit; no tolerance, target or model change is requested.

Observations (not findings):
- The harness printed `RECON_REDACT_SALT is not set` in live mode, as in every run of this engagement so far; the committed artifacts are redacted with unsalted hashes.
- The worker result records `seed: 0`, `snapshot: null`; the rerun does the same (live mode).

## Verdict
**PASS** - graded from the committed rerun `result.json` above, not asserted.
