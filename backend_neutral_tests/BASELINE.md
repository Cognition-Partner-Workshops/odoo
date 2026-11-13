# Backend-neutral suite: PostgreSQL 16 baseline

This file records the state of the backend-neutral ORM test suite
(`odoo/addons/test_backend_neutral`, tag `backend_neutral`) when the five
category test sets were first combined on top of the harness, and run on
PostgreSQL 16, then re-recorded when the three `core.*` targets (reuse of
`test_base/tests/test_orm`) were added. It is the reference another backend
has to match: the same command, the same tests, the same counts.

- Contract: `backend_neutral_tests/CONTRACT.md`; sample: `backend_neutral_tests/sample.yaml` (`SAMPLE.md`).
- Gate script: `backend_neutral_tests/run_neutral_suite.sh` (lint, contract self-test, coverage reconciliation, suite on a fresh database).
- Coverage reconciliation: `python3 backend_neutral_tests/check_baseline.py` (system `python3`, needs PyYAML) checks the table below against `sample.yaml`.

## Suite composition

| File | Classes | Test methods | Origin |
|---|---|---|---|
| `tests/test_smoke_orm.py`, `test_smoke_integrity.py`, `test_smoke_transactions.py`, `test_lint.py` | 5 | 25 | harness (23 smoke tests on the addon's own `test_backend_neutral.item` model + the lint run as a test, on the addon's tests and on the inherited `test_orm` code) |
| `tests/test_sql_views.py` | 8 | 39 | SQL-view parity |
| `tests/test_raw_sql.py` | 6 | 25 | raw-SQL characterisation (its PR description says 26; the file has 25 `test_` methods and its own standalone run reported `49 tests` = 24 + 25) |
| `tests/test_integrity.py` | 6 | 57 | DB-enforced integrity |
| `tests/test_concurrency.py` | 7 | 31 | concurrency |
| `tests/test_aggregation_hierarchy.py` | 17 | 67 | aggregation / hierarchy |
| `tests/test_core_reuse_as_is.py` | 24 | 71 | `core.reuse_as_is`: subclasses of 12 `test_orm` files (+ the `HttpCase` of `test_check_access.py` copied onto `NeutralCase`) |
| `tests/test_core_reuse_with_edits.py` | 16 | 157 | `core.reuse_with_edits`: subclasses of 10 `test_orm` files, 16 methods overridden with their query guard removed, 4 left out |
| `tests/test_core_reuse_split_by_class.py` | 16 | 179 | `core.reuse_split_by_class`: the behavioural classes of 6 `test_orm` files, 38 methods overridden, 19 left out, `TestSearchAny` / `TestSearchRelated` left out as classes |
| **total** | **105** | **651** | 243 before the `core.*` targets (expected "about 244 (24 + 220)"; the one missing test is the raw-SQL miscount above) + 407 reused `test_orm` tests + the inherited-code lint test |

Odoo prints two counts per run: `odoo.tests.result: ... of N tests` counts test methods
(651) and `odoo.tests.stats: test_backend_neutral: M tests` also counts `subTest`
blocks (861). The baseline figure is the result line. Before the `core.*` targets the
two figures were 243 and 341.

## Baseline runs (PostgreSQL 16, port 5433)

Each run: new, empty database (`createdb`), then

```sh
/home/ubuntu/.venvs/odoo/bin/python odoo-bin -d bn_baseline_runN --db_port=5433 --stop-after-init \
    -i test_backend_neutral --test-enable --test-tags backend_neutral
```

### With the `core.*` targets (current baseline)

Three consecutive runs of `backend_neutral_tests/run_neutral_suite.sh` (lint, inherited-code
lint, contract self-test, coverage reconciliation, then the command above on a fresh
database; the addon now installs `test_base` too, 103 modules):

| Run | Database | Tests (result line) | Tests incl. subtests (stats line) | Test time (post-tests) | Wall time incl. install | Exit |
|---|---|---|---|---|---|---|
| 1 | `bn_baseline_core1` | 0 failed, 0 error(s) of 651 tests | 861 tests | 651 post-tests in 66.28s | 138s | 0 |
| 2 | `bn_baseline_core2` | 0 failed, 0 error(s) of 651 tests | 861 tests | 651 post-tests in 75.99s | 164s | 0 |
| 3 | `bn_baseline_core3` | 0 failed, 0 error(s) of 651 tests | 861 tests | 651 post-tests in 63.74s | 139s | 0 |

Lint: `python3 backend_neutral_tests/lint_neutral.py odoo/addons/test_backend_neutral/tests` → `0 finding(s)`.
Inherited code: `/home/ubuntu/.venvs/odoo/bin/python backend_neutral_tests/lint_reused.py` → `56 neutral classes, 64 inherited upstream classes`, `0 finding(s) in inherited code`, 8 module-level findings in the upstream files listed for review (the `psycopg2` imports of `test_fields.py`, `test_properties.py` and `base/tests/test_ir_ui_view.py`, and the module-level `insert`/`select`/`update` SQL helpers of `test_fields.py`, used only by classes that are not reused).

### Before the `core.*` targets (243 tests)

| Run | Database | Tests (result line) | Failed | Errors | Tests incl. subtests (stats line) | Test time (post-tests) | Wall time incl. install of 102 modules | Exit |
|---|---|---|---|---|---|---|---|---|
| 1 | `bn_baseline_run1` | 0 failed, 0 error(s) of 243 tests | 341 tests | 243 post-tests in 42.36s | 110.1s | 0 |
| 2 | `bn_baseline_run2` | 0 failed, 0 error(s) of 243 tests | 341 tests | 243 post-tests in 41.55s | 110.1s | 0 |
| 3 | `bn_baseline_run3` | 0 failed, 0 error(s) of 243 tests | 341 tests | 243 post-tests in 38.99s | 102.6s | 0 |

Runs 1 and 2 shared the machine with the `base` / `test_base` regression runs; run 3 ran alone. Full logs were attached to the PR that introduced this file.

Lint: `python3 backend_neutral_tests/lint_neutral.py odoo/addons/test_backend_neutral/tests` → `0 finding(s)`.
Contract self-test: `python3 backend_neutral_tests/lint_neutral.py --self-test` → `24 example blocks checked, 0 failures`.

### How the reused `TransactionCase` classes run under the contract

Every reused class is `class <Upstream>Neutral(<Upstream>, NeutralCase)` with
`allow_inherited_tests_method = True`, decorated with the neutral tag. In that MRO the
upstream `setUpClass`/`setUp` call `super()`, which reaches `NeutralCase` instead of
`TransactionCase`: the fixtures are built on the environment the backend adapter
provides, and each test runs in the adapter's undoable unit. `cr`, `registry`,
`assertQueryCount`, `assertQueries` stay unavailable (`NotImplementedError`), so an
upstream method that reaches them fails even if the lint is skipped. Methods the lint
flags upstream are overridden in the neutral file (query guard removed, raw SQL
cross-check replaced, `self.registry[model]` replaced by `type(self.env[model])`) or set
to `None`, which Odoo's loader does not collect; the per-method list and reasons are in
the three `test_core_reuse_*.py` files and in the PR that added them.

Harness changes made for this: `_NotNeutral.__get__` returns the descriptor on class
access (Odoo's loader calls `inspect.getmembers(cls)` for `allow_inherited_tests_method`
and must not raise), `NeutralCase.patch_registry(attribute, value)` patches a flag of the
ORM's model registry for the test (`ready`, `uninstalling_modules`; two upstream classes
patch `self.registry` directly), and `harness/lint.py` gained `lint_inherited()`, which
lints the upstream class bodies a neutral class inherits and runs (overridden and
left-out methods excluded); it runs as `TestNeutralLint.test_reused_code_is_neutral`
and as `backend_neutral_tests/lint_reused.py` in the gate script.

One reused test needed an environment edit, for the same reason as the two `res.users`
tests below: `TestRecordset.test_recordset_environment` compares `records.with_user(demo).env`
with `self.env(user=demo)`, and `mail` (installed by the combined addon) overrides
`with_user` to add a context key, so the expected environment is built with
`with_user` too.

### Change needed to make the combined suite green

One test file was edited, nothing else (no harness, no non-test code):

- `tests/test_integrity.py`, `TestIntegrityResUsers.test_login_unique_duplicate_create_refused` and
  `test_login_unique_duplicate_write_refused`: the combined addon depends on `website`, whose
  `res.users._check_login` Python constraint refuses a duplicate login with `ValidationError`
  before the unique index can refuse it. Alone, the integrity branch (without `website`)
  saw the backend's `IntegrityError`. The two tests now accept either class
  (`assertRaises((errors.IntegrityError, errors.ValidationError))`); the assertions on
  the state afterwards are unchanged. First combined run before the edit:
  `0 failed, 2 error(s) of 243 tests`, both from these two tests.

## Coverage

One row per target id of `sample.yaml`, in manifest order. Status is one of
`covered`, `partly covered`, `not covered`, `not expressible neutrally`; the
test classes live in `odoo/addons/test_backend_neutral/tests/`. Reasons come
from the category PR descriptions (#200 SQL views, #201 raw SQL, #202
integrity, #203 concurrency, #204 aggregation / hierarchy).

| Target id | Status | Test classes | Reason / notes |
|---|---|---|---|
| `integrity.res_users` | covered | `TestIntegrityResUsers` | distinct logins accepted, duplicate login refused on create and write (unique index, or `_check_login` with `website`), contact without name refused, partner of a user kept on unlink (`restrict`) |
| `integrity.account_move` | covered | `TestIntegrityAccountMove` | partial unique index on posted (name, journal): drafts share a name, posted duplicates refused; one-sided lines, accountable line without account refused, note with a balance refused, `document_tax_mode` check, cascade of lines with their move |
| `integrity.hr_leave` | covered | `TestIntegrityHrLeave` | ordered dates accepted, reversed dates refused on create and write, negative `number_of_days` refused, employee with a leave kept on unlink |
| `integrity.mail_followers` | covered | `TestIntegrityMailFollowers` | subscribe twice keeps one follower, duplicate follower / follower without partner refused, channel member partner-or-guest check, cascade with the partner |
| `integrity.stock_location` | covered | `TestIntegrityStockLocation` | barcode unique per company, inventory frequency check, product / location with a quant kept, duplicate orderpoint refused |
| `integrity.sale_order_line` | covered | `TestIntegritySaleOrderLine` | section / note line checks (no product, no price), product line needs a unit, confirmed order needs a date, cascade of lines with their order, `campaign_id` set null |
| `concurrency.ir_sequence` | covered | `TestSequenceNumbering` | no-gap: concurrent draw gets a retryable `ConcurrencyError`, rolled back number reused, contiguous across 3 sessions after retry; standard: concurrent draws never block, all distinct, rolled back number burnt |
| `concurrency.ir_cron` | partly covered | `TestCronJobClaiming` | job claiming as seen through the ORM: `method_direct_trigger` / `write` / `unlink` on a job held by another session raise `UserError`, work done once per claim, stale session gets `ConcurrencyError` then claims the released job. `_acquire_one_job` / `_get_all_ready_jobs` / `_process_job` take a raw cursor and return raw rows: the scheduler loop itself is a known gap (see below) |
| `concurrency.lock_for_update` | covered | `TestRowLocks`, `TestConcurrentWrites` | `try_lock_for_update` returns the unlocked subset (with `limit`, in order), `lock_for_update` raises `LockError`, locks released by commit, locked row readable, `allow_referencing`; second writer refused until the first ends, no lost update, write vs unlink, two creates of a unique value keep one |
| `concurrency.discuss_channel` | covered | `TestDiscussChannelLastInterest` | `_sync_last_interest_dt` skips a channel held by a writer or a concurrent syncer without losing pending updates, applies each once, converges once the holder commits |
| `concurrency.website_visitor` | covered | `TestWebsiteVisitorUpsert` | two sessions upsert one token: one visitor, loser gets `ConcurrencyError` and converges on retry as `updated`, tracks kept, `visit_count` not double-counted; `_update_visitor_last_visit` / `_update_visitor_timezone` skip a held visitor and apply on the next call |
| `concurrency.stock_orderpoint_retry` | not expressible neutrally | — | `_procure_orderpoint_confirm` retries a lock conflict inside the call and its outcome equals an uncontended run; provoking the conflict needs the other session to release *during* the call, i.e. a thread and a sleep, which the contract forbids (#203). Quant reservation contention next to it is covered by `TestStockQuantReservation` |
| `raw_sql.orm_core` | covered | `TestRawSqlOrmCore` | `_create` / `_write_multi` / `exists` round trip, `_read_group` aggregates, `Many2many` link idempotent and unlink of a non-linked pair a no-op, `_parent_store_compute` rebuild |
| `raw_sql.account_move` | covered | `TestRawSqlAccount` | `_fetch_duplicate_reference` (vendor bill by ref, customer invoice by amount and date), `_get_last_sequence_domain`, `account.account._search` with inactive parents, code ordering vs Python sort, `_credit_debit_get`, `_invoice_total` |
| `raw_sql.mail_followers` | covered | `TestRawSqlMailFollowers` | `_get_recipient_data` / `_get_subscription_data` through `message_post` recipients, `_search_message_is_follower` / `_search_message_partner_ids`, `_filter_accessible_from_query` |
| `raw_sql.website` | covered | `TestRawSqlWebsite`, `TestWebsiteFuzzySearch` | `_is_snippet_used` follows the html content, `_upsert_visitor` idempotent per token (#201); `get_similarity_subquery` through `website._search_with_fuzzy` (#204, see the trigram assumption) |
| `raw_sql.stock_quant` | covered | `TestRawSqlStockQuant` | `_merge_quants` sums duplicates into one, `_unlink_zero_quants`, least-packages removal strategy |
| `raw_sql.sale_project` | covered | `TestRawSqlSaleProjectPos` | `_fetch_duplicate_orders` by reference and origin, `_search_invoice_ids`, `project.task._search_portal_user_names`, `pos.order.search_order_ids` |
| `sql_views.account_invoice_report` | covered | `TestAccountInvoiceReport` | one row per product line, signed amounts, second currency, grouped totals by `move_type` and `invoice_date:month` |
| `sql_views.sale_report` | covered | `TestSaleReport` | one row per non-display line, amounts in company currency (`currency_rate`), cancel state, grouped by order and product. Not asserted: "productless line contributes a row with product False" (a line needs a product unless it is a display line, and display lines are excluded from the view) |
| `sql_views.report_pos_order` | not covered | — | the fixture needs an opened POS session with payment methods / journals; upstream builds it through `TestPoSCommon` → `AccountTestInvoicingCommon`, whose class setup runs on `TransactionCase` and cannot be mixed into `NeutralCase` without a harness hook. A human decision on a follow-up is pending; nothing is built here (#200) |
| `sql_views.project_reports` | covered | `TestProjectTaskReport`, `TestProjectBurndownReport`, `TestProjectTaskStageReport` | all three views; stage durations cannot be backdated neutrally (the view and the duration mixin read the transaction clock), so the tests pin the row set, the ±1 burndown replay and the `duration_tracking` ↔ `time_spent` relation |
| `sql_views.hr_leave_reports` | covered | `TestHrLeaveEmployeeTypeReport`, `TestHrLeaveReport` | allocation / request rows, refuse state, two companies, FIFO remaining balance over overlapping allocations, planned → taken on approval |
| `sql_views.stock_quantity_report` | covered | `TestStockQuantityReport` | one `out` row per confirmed move, none after `_action_done`, second company kept apart, forecast per day and across warehouses |
| `sql_views.recursive_cte` | covered | `TestParentStoreHierarchy`, `TestHasCycle`, `TestRecursiveWalks`, `TestStockQuantities` | not a SQL-view report (recursive CTEs behind ORM methods), so left out of #200 and covered by #204: `parent_path` / `_parent_store_compute`, `_has_cycle`, `_get_subtask_ids_per_task_id`, `_get_inheriting_views`, `stock.location._child_of`, location descendants |
| `sql_views.lateral_rates` | covered | `TestLatestRowPerKey` | same split as above: `res.currency._get_rates` (and `rate` / `rate_date`), `discuss.channel._get_last_messages`, `_get_last_needaction_messages` (#204) |
| `aggregation.read_group_core` | covered | `TestReadGroupCore`, `TestReadGroupPartner`, `TestReadGroupCurrencyRates`, `TestReadGroupProjectTask` | `_read_group` / `formatted_read_group` aggregates, groupby granularities, ordering and limits compared with a Python replay |
| `aggregation.stock_product_quantities` | covered | `TestStockQuantities` | `_compute_quantities_dict` through `qty_available` with `location` / `warehouse_id` context, `_search_field_by_quants`, quants grouped under `child_of`, unlink of a location subtree |
| `aggregation.account_account_hierarchy` | covered | `TestAccountHierarchy` | `current_balance` over a company and its branch, `account_move_count` with child contacts |
| `aggregation.project_task_subtasks` | covered | `TestReadGroupProjectTask` | `subtask_count`, project counts, the `_read_group` override, `group_expand` of personal stages |
| `aggregation.hr_leave_mail_pos` | partly covered | `TestLeaveAllocationNegativeSum`, `TestDiscussChannelCounts` | allocation below taken leaves raises `ValidationError`; `member_count` / `message_count` equal the relation length. Not covered: `pos.session._compute_order_count` / `_compute_total_payments_amount`, which need the POS session fixture ruled out above (#204); the sum-per-parent shape is the one tested on `discuss.channel` and `account.move.line` |
| `hierarchy.parent_store_models` | covered | `TestParentStoreHierarchy`, `TestWebsiteMenuHierarchy`, `TestHierarchyWithoutParentStore` | `res.partner.category`, `res.company`, `product.category`, `stock.location`, `hr.department`, `website.menu`; `child_of` on `res.partner` and `project.task`, which have no parent store (the sample's `res_partner.py:231` `_parent_store` belongs to `res.partner.category`) |
| `core.reuse_as_is` | covered | `TestAccessNeutral`, `TestACLNeutral`, `TestCopyTranslationsNeutral`, `TestCreateNeutral`, `TestPrefetchNeutral`, `TestDefaultViewNeutral`, `TestViewGroupsNeutral`, `TestCheckAccessNeutral`, `TestConfigSettingsNeutral`, `TestJsonFieldNeutral`, `TestCharExportNeutral`, `TestIntegerExportNeutral`, `TestFloatExportNeutral`, `TestCurrencyExportNeutral`, `TestTextExportNeutral`, `TestMany2OneExportNeutral`, `TestImageExportNeutral`, `TestSelectionExportNeutral`, `TestHTMLExportNeutral`, `TestDateExportNeutral`, `TestDatetimeExportNeutral`, `TestDurationExportNeutral`, `TestRelativeDatetimeNeutral`, `TestActionBindingsNeutral` | 71 tests of 12 files collected unchanged by subclassing (`TestACL`: the one test the sample names; `TestExport`: its 13 concrete subclasses); `test_check_access.py` is an `HttpCase`, its fixture and two tests are copied onto `NeutralCase`; left out: `TestAutovacuum.test_api_autovacuum` (runs the cron in `registry_test_mode()`) |
| `core.reuse_with_edits` | covered | `TestDomainNeutral`, `TestDomainComplementNeutral`, `TestDomainOptimizeNeutral`, `TestParentStoreNeutral`, `TestMany2manyCaseNeutral`, `TestOne2manyCaseNeutral`, `TestInheritsLegacyNeutral`, `TestInheritsNeutral`, `TestRulesNeutral`, `TestCompanyCheckNeutral`, `TestSearchOrderNeutral`, `TestSortNeutral`, `TestSudoNeutral`, `TestACLFeedbackNeutral`, `TestIRRuleFeedbackNeutral`, `TestFieldGroupFeedbackNeutral` | 157 tests of all 10 files; 16 methods overridden (query guards removed, the raw `SELECT` cross-checks of `test_empty_int` / `test_empty_char` dropped, `Domain.custom(to_sql=...)` case dropped, registry accesses replaced); left out: `test_inherits.test_access_rights_on_parent`, `TestSearch.test_22_like_folding` (only assertion is the SQL text), `TestRules.test_access_rule_performance`, `TestSort.test_prefetch` (only assertion is a query count) |
| `core.reuse_split_by_class` | partly covered | `TestFieldsParentStoreNeutral`, `TestSelectionOndeleteNeutral`, `TestUnlinkConstraintsNeutral`, `TestRequiredMany2oneNeutral`, `TestCompanyDependentNeutral`, `TestSearchNeutral`, `TestExpressionNeutral`, `TestMany2oneNeutral`, `TestOne2manyNeutral`, `TestMany2manyNeutral`, `TestPrivateReadGroupNeutral`, `TestPublicReadGroupNeutral`, `TestPropertiesCaseNeutral`, `TestPropertiesSearchCaseNeutral`, `TestORMNeutral`, `TestRecordsetNeutral` | 179 tests; the SQL-asserting classes named in the sample (`TestComputeQueries`, `TestModifiedPerformance`, `TestSubqueries`, `TestQueries`, `TestFlushSearch`) are not imported. Not covered: `TestSearchAny` (3 tests) and `TestSearchRelated` (11 tests), every test of theirs asserts the SQL text of a search only; 13 `assertQueries`-only tests of `TestMany2one` / `TestOne2many` / `TestMany2many`; `TestExpression.test_accent`, `PropertiesSearchCase.test_properties_field_search_unaccent` (branch on `registry.has_unaccent`); 4 `test_properties` tests that write invalid documents behind the ORM with a raw `UPDATE`. `TestORM.test_lock_for_update` / `test_try_lock_for_update` use `concurrent_session()` for the second transaction; `TestRecordset.check_cache_consistency` reads the stored values back with `_read_group` instead of one `SELECT` per field |

Classes not attached to a target: the harness smoke classes (`TestSmokeOrm`,
`TestSmokeIntegrity`, `TestSmokeIndependentTransaction`, `TestSmokeConcurrency`,
`TestNeutralLint`), `TestStockQuantReservation` from #203 (quant reservation under contention, next to the `stock_orderpoint_retry` gap), and from #204 `TestTextSearch` (`ilike` / `=ilike` / `not ilike`,
accent and case behaviour of text search) and `TestOrderingWithNulls` (`NULLS FIRST/LAST`
semantics of `order`), which pin ORM behaviour the sample lists under the
aggregation scan but not as a target id.

## Known gaps

1. **`report.pos.order` and the POS session counts** (`sql_views.report_pos_order`,
   the `pos.session` part of `aggregation.hr_leave_mail_pos`): both need an opened POS
   session with payment methods and journals. Upstream builds it through
   `TestPoSCommon` → `AccountTestInvoicingCommon`, whose `setUpClass` runs on
   `TransactionCase` and cannot be mixed into `NeutralCase`. A human decision on a
   follow-up (harness hook or a neutral POS fixture) is pending; nothing is built here.
2. **`concurrency.stock_orderpoint_retry` and the cron scheduler internals**
   (`ir.cron._acquire_one_job`, `_get_all_ready_jobs`, `_process_job`,
   `_procure_orderpoint_confirm`'s retry loop): they take raw cursors or handle the
   conflict inside one call, so observing them needs a second thread releasing a lock
   mid-call and a sleep, or a cursor. Not expressible through the ORM; the observable
   outcomes next to them (job claiming through `method_direct_trigger`, quant
   reservation under contention) are covered.

## Backend assumptions the suite makes

Assertions are on ORM-observable outcomes only, but some outcomes exist because of
how PostgreSQL behaves. A backend that behaves differently here will fail the named
tests even though they contain nothing PostgreSQL-specific.

| Assumption | Where it is relied on | What a different backend would show |
|---|---|---|
| **Snapshot isolation** (Odoo's default `REPEATABLE READ`): a session that read a row gets a retryable error when it writes after another session committed a write to that row | `TestCronJobClaiming.test_job_is_claimed_by_one_session`, `TestDiscussChannelLastInterest.test_sync_skips_a_held_channel_and_converges`, the `TestSequenceNumbering` no-gap retry tests, `TestWebsiteVisitorUpsert` loser-retries tests (`assertConcurrencyError()`) | on read-committed, the retry succeeds without the error and the `assertConcurrencyError()` blocks fail |
| **Blocking row locks surface as a timeout**, not as a successful blocked write: the harness is single-threaded, so "the loser waits" is observed as the harness's bounded `lock_timeout` raising `ConcurrencyError` | all `TestConcurrentWrites`, `TestRowLocks`, `TestStockQuantReservation`, `TestSmokeConcurrency` tests that expect `ConcurrencyError` | a backend without row locks (last-writer-wins) would let both writes through |
| **Uncommitted writes are invisible to other sessions**, and a `committed_fixture()` made after the class transaction started is not visible to `self.env` of a plain `NeutralCase` | `TestSmokeIndependentTransaction`, every concurrency class (fixtures are read back through explicit transactions, `CONTRACT.md` section 4) | a backend showing dirty reads would break "sees only committed data" |
| **Ids are assigned in creation order within one transaction** (no contiguity, arithmetic or cross-transaction ordering assumed) | default `order = 'id'` of models used as a tie-breaker in `TestReadGroupCore`, `TestOrderingWithNulls`, `TestRawSqlAccount` ordering comparisons, `TestSaleReport` / `TestAccountInvoiceReport` row ordering | random or hash ids would reorder the expected lists |
| **Trigram word similarity** (`pg_trgm`, `registry.has_trigram`) when the database has it | `TestWebsiteFuzzySearch`: the resembling word comes from `get_similarity_subquery` when the extension is installed, otherwise from the Python fallback `_search_find_fuzzy_term`; the asserted outcomes hold either way, and the baseline runs took the Python path (the fresh databases have only `plpgsql` installed, see the `test_base` note below) | a backend with a different fuzzy matcher must still return the page and the same resembling word for `bananna` / `smothie` / `carot` |
| **Case-insensitive `ilike` with `unaccent` off** | `TestTextSearch`, `TestRawSqlSaleProjectPos.test_search_tasks_by_portal_user_names` (`ILIKE`) | a backend normalising accents or case differently changes the matched sets |
| **Partial / conditional unique index** semantics: duplicates allowed where the condition does not hold | `TestIntegrityAccountMove` (posted (name, journal) only), `TestIntegrityStockLocation` (barcode per company) | an application-layer check must reproduce the condition exactly |
| **`ondelete` behaviour** (`restrict` raises, `cascade` removes children, `set null` clears) is enforced by the storage at flush time | every `TestIntegrity*` cascade / restrict test, `TestSmokeIntegrity` | a backend without referential actions must emulate them in `unlink` |
| **Nulls sort last ascending / first descending** by default | `TestOrderingWithNulls`, `TestReadGroupCore` groupby with empty values | a backend sorting nulls first ascending reorders the expected rows |
| **Sequence `nextval` is non-transactional** (a rolled back standard-sequence number is burnt) | `TestSequenceNumbering` standard-implementation tests | a transactional counter would reissue the number |
| **Aggregates over `float`/`monetary` keep the database's rounding** | `TestAccountInvoiceReport` (`price_average:avg_currency`), `TestReadGroupCurrencyRates` compared with a Python mean rounded the same way | a backend aggregating decimals differently needs the same rounding |

## Existing `assertQueryCount` / `assertQueries` usage (out of scope)

80 test files in the repository assert on the number or text of SQL queries. They are
not neutral by definition (`CONTRACT.md` rule F2 / BN004) and are **out of the scope
of the neutral suite**: they stay as PostgreSQL-only tests and are not ported.

Recommended replacement performance signal: instead of counting queries, assert on
the number of **ORM round trips observable through the harness**, i.e. the count of
`flush`/`fetch` cycles that `BaseModel._fetch_field` / `_read_group` / `_write_multi`
perform, exposed by the backend adapter as a neutral counter (`backend.round_trips()`
returning an integer that each adapter increments once per storage call, whatever the
storage protocol). Tests would assert `assertLessEqual(round_trips, n)` inside a
`backend.measure()` context manager. It keeps the regression-guard value of
`assertQueryCount` (prefetch and batching regressions show up as extra round trips)
while meaning the same thing on PostgreSQL and on a document store. Wall-clock
thresholds are not recommended (noisy on shared CI); if a timing signal is wanted,
`odoo.tests.common.TransactionCase.profile()` traces per test on PostgreSQL remain
available outside the neutral suite.

Files (`grep -rlE "assertQueryCount|assertQueries" --include=*.py odoo addons`):

- `addons/account/tests/test_account_move_reconcile.py`
- `addons/crm/tests/test_crm_lead_convert_mass.py`
- `addons/crm/tests/test_performances.py`
- `addons/event/tests/test_event_mail_schedule.py`
- `addons/gamification/tests/test_karma_tracking.py`
- `addons/google_calendar/tests/test_sync_odoo2google.py`
- `addons/hr/tests/test_resource.py`
- `addons/hr_holidays/tests/test_company_leave.py`
- `addons/hr_holidays_attendance/tests/test_performance.py`
- `addons/im_livechat/tests/test_chatbot_internals.py`
- `addons/l10n_fr_hr_holidays/tests/test_french_leaves.py`
- `addons/l10n_fr_hr_holidays/tests/test_french_work_entries.py`
- `addons/mail/tests/test_ir_ui_menu.py`
- `addons/mail/tests/test_mail_render.py`
- `addons/marketing_card/tests/test_campaign.py`
- `addons/mass_mailing/tests/common.py`
- `addons/mass_mailing/tests/test_mailing_contact_to_list.py`
- `addons/resource/tests/test_performance.py`
- `addons/resource/tests/test_stress_check_collision.py`
- `addons/sale_stock/tests/test_create_perf.py`
- `addons/sale_timesheet/tests/test_performance.py`
- `addons/survey/tests/common.py`
- `addons/survey/tests/test_survey_performance.py`
- `addons/survey/tests/test_survey_results.py`
- `addons/test_crm_full/tests/test_performance.py`
- `addons/test_discuss_full/tests/test_performance.py`
- `addons/test_discuss_full/tests/test_performance_inbox.py`
- `addons/test_event_full/tests/test_performance.py`
- `addons/test_import_export/tests/test_export.py`
- `addons/test_import_export/tests/test_load.py`
- `addons/test_mail/tests/test_mail_template.py`
- `addons/test_mail/tests/test_mail_thread_internals.py`
- `addons/test_mail/tests/test_performance.py`
- `addons/test_mail_full/tests/test_mail_performance.py`
- `addons/test_mail_sms/tests/test_phone_format.py`
- `addons/test_mail_sms/tests/test_sms_performance.py`
- `addons/test_mass_mailing/tests/test_performance.py`
- `addons/test_resource/tests/test_performance.py`
- `addons/test_resource/tests/test_resource.py`
- `addons/web/tests/test_perf_load_menu.py`
- `addons/website/tests/test_website_visitor.py`
- `addons/website_crm_partner_assign/tests/test_res_partner.py`
- `addons/website_forum/tests/test_forum_internals.py`
- `addons/website_sale/tests/test_performance.py`
- `addons/website_slides/tests/test_gamification_karma.py`
- `odoo/addons/base/tests/test_ir_attachment.py`
- `odoo/addons/base/tests/test_ir_model.py`
- `odoo/addons/base/tests/test_ir_ui_view.py`
- `odoo/addons/base/tests/test_res_currency.py`
- `odoo/addons/base/tests/test_res_lang.py`
- `odoo/addons/base/tests/test_res_partner.py`
- `odoo/addons/base/tests/test_res_users.py`
- `odoo/addons/test_base/tests/test_orm/test_all_models.py`
- `odoo/addons/test_base/tests/test_orm/test_company_checks.py`
- `odoo/addons/test_base/tests/test_orm/test_domain_expression.py`
- `odoo/addons/test_base/tests/test_orm/test_fields.py`
- `odoo/addons/test_base/tests/test_orm/test_indexed_translation.py`
- `odoo/addons/test_base/tests/test_orm/test_inherits.py`
- `odoo/addons/test_base/tests/test_orm/test_ir_rules.py`
- `odoo/addons/test_base/tests/test_orm/test_models.py`
- `odoo/addons/test_base/tests/test_orm/test_one2many.py`
- `odoo/addons/test_base/tests/test_orm/test_performance.py`
- `odoo/addons/test_base/tests/test_orm/test_properties.py`
- `odoo/addons/test_base/tests/test_orm/test_query.py`
- `odoo/addons/test_base/tests/test_orm/test_read_group_private.py`
- `odoo/addons/test_base/tests/test_orm/test_read_grouping_sets.py`
- `odoo/addons/test_base/tests/test_orm/test_search.py`
- `odoo/addons/test_base/tests/test_orm/test_search_order.py`
- `odoo/addons/test_base/tests/test_orm/test_sort.py`
- `odoo/addons/test_base/tests/test_tools/test_translate.py`
- `odoo/addons/test_tests/tests/test_methods.py`
- `odoo/addons/test_tests/tests/test_test_suite.py`
- `odoo/addons/test_web/tests/test_onchange.py`
- `odoo/addons/test_web/tests/test_properties.py`
- `odoo/addons/test_web/tests/test_read_group_formatted.py`
- `odoo/addons/test_web/tests/test_read_grouping_sets.py`
- `odoo/addons/test_web/tests/test_web_group_expand.py`
- `odoo/addons/test_web/tests/test_web_read.py`
- `odoo/addons/test_web/tests/test_web_read_group.py`
- `odoo/tests/common.py`

## Harness no-regression check (`base`, `test_base`)

See the PR that introduced this file for the side-by-side counts of the `base` and
`test_base` suites on the sample branch and on the combined branch (identical
pass/fail/error counts and identical failing tests). The three `test_base` failures
and four `base` errors on both branches are environment-related (no wkhtmltopdf for
the pdf reports, barcode rendering, and `pg_trgm` not installed in the fresh
databases, so `TestSchema.test_index_trigram_attribute` and
`TestIndexedTranslation.test_search_ilike` expect a trigram index that is not there,
and `TestMimeGuessingMagic.test_xlsx_2025` depends on the system `libmagic`).
