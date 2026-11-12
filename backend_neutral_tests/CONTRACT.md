# Backend-neutral test contract

Companion to [`SAMPLE.md`](SAMPLE.md) (what to cover). This file says **how** a neutral test may be written and **what harness** enforces it. Pinned to `Cognition-Partner-Workshops/odoo` branch `20.0`, commit `63446015e3c`; file/line references below were checked at that commit. Rules are machine-checked by [`lint_neutral.py`](lint_neutral.py); every example in this file is itself checked by `python3 backend_neutral_tests/lint_neutral.py --self-test`.

Examples are illustrative: they use real models and real symbols from the sample but are not yet the tests the next ticket writes. Code blocks are marked `compliant` or `non-compliant <rule codes>`.

## 1. Definitions

- **Backend**: whatever stores records under `odoo.orm`. Today: PostgreSQL via `odoo/sql_db.py` (psycopg2). Later: possibly MongoDB.
- **Neutral test**: a test tagged `backend_neutral` whose assertions hold for *any* correct backend. It observes the system only through the public ORM API (`create`, `write`, `unlink`, `search`, `search_fetch`, `read`, `_read_group`, `browse`, `exists`, field access, `flush_all`/`invalidate_all`) and the exception classes listed in section 3.
- **Harness**: the small layer the neutral suite imports instead of `odoo.tests.common` directly (`NeutralCase`, `NeutralConcurrencyCase`, the exception aliases, the isolation interface). It is the *only* place in the suite that may know a backend exists.
- **Backend adapter**: the per-backend implementation of the isolation interface (section 4). PostgreSQL's is written first; a new backend supplies its own without touching any test.

The one-sentence rule: **if the assertion would read differently with a different storage engine, it is not neutral.**

## 2. Rules

Codes `A*` are allowed constructs, `F*` are forbidden ones; `BN0xx` are the lint rules that detect the forbidden ones (section 6).

### A1. Assert on ORM results and field values, after a re-read when the value is stored

Compliant: assert on the value the ORM returns, after `invalidate_all()` so the cache cannot hide a storage bug.

```python compliant
def test_quants_merge(self):
    # raw_sql.stock_quant: _merge_quants is raw UPDATE/DELETE today
    quant = self.env['stock.quant']
    quant._update_available_quantity(self.product, self.location, 5)
    quant._update_available_quantity(self.product, self.location, 3)
    quant._merge_quants()
    self.env.invalidate_all()
    quants = quant.search([('product_id', '=', self.product.id), ('location_id', '=', self.location.id)])
    self.assertEqual(len(quants), 1)
    self.assertEqual(quants.quantity, 8)
```

Non-compliant: the same intent asserted by counting rows with SQL.

```python non-compliant BN002 BN006
def test_quants_merge(self):
    self.env['stock.quant']._merge_quants()
    self.env.cr.execute("SELECT count(*) FROM stock_quant WHERE product_id = %s", [self.product.id])
    self.assertEqual(self.env.cr.fetchone()[0], 1)
```

### A2. Assert on exception *classes*, never on their message text or on backend error codes

Allowed classes: `odoo.exceptions.ValidationError`, `UserError`, `AccessError`, `MissingError`, `LockError`, and the two harness aliases `IntegrityError` and `ConcurrencyError` (section 3). Messages are translated and backend-generated; `pgcode`/`diag` are PostgreSQL.

```python compliant
def test_section_line_cannot_have_product(self):
    # integrity.sale_order_line: CHECK constraint keyed on display_type
    with self.assertIntegrityError():
        self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'display_type': 'line_section',
            'product_id': self.product.id,
        })
```

```python non-compliant BN001 BN007
def test_section_line_cannot_have_product(self):
    from psycopg2 import errors
    with mute_logger('odoo.sql_db'), self.assertRaises(errors.CheckViolation) as cm:
        self.env['sale.order.line'].create({'order_id': self.order.id, 'display_type': 'line_section', 'product_id': self.product.id})
    self.assertEqual(cm.exception.pgcode, '23514')
```

### A3. Assert on ordering and grouping results as *values*, compared with a Python replay

`search(order=...)`, `_read_group(...)` and report-model reads are allowed. The expected value must be computed in Python from the same records (or be a literal), not fetched with another query shape.

```python compliant
def test_subtask_count(self):
    # aggregation.project_task_subtasks: _read_group with __count on parent_id
    parent = self.env['project.task'].create({'name': 'p', 'project_id': self.project.id})
    self.env['project.task'].create([
        {'name': f'c{i}', 'project_id': self.project.id, 'parent_id': parent.id} for i in range(3)
    ])
    parent.invalidate_recordset()
    self.assertEqual(parent.subtask_count, len(parent.child_ids))
    groups = self.env['project.task']._read_group([('parent_id', '=', parent.id)], ['parent_id'], ['__count'])
    self.assertEqual(groups, [(parent, 3)])
```

```python non-compliant BN004
def test_subtask_count(self):
    parent = self.env['project.task'].create({'name': 'p', 'project_id': self.project.id})
    with self.assertQueryCount(1):
        parent.subtask_count
```

### A4. Use the harness for cache and flush control

`self.env.flush_all()`, `self.env.invalidate_all()`, `record.invalidate_recordset()`, `record.invalidate_model()` are allowed; they are ORM concepts. Cursor-level flush (`self.cr.flush()`) is not.

```python compliant
def test_parent_path_after_move(self):
    # sql_views.recursive_cte / hierarchy.parent_store_models
    a, b, c = (self.env['res.partner'].create({'name': n, 'is_company': True}) for n in 'abc')
    b.parent_id = a
    c.parent_id = b
    c.parent_id = a
    self.env.flush_all()
    self.env.invalidate_all()
    self.assertEqual(c.parent_path, f'{a.id}/{c.id}/')
    self.assertEqual(self.env['res.partner'].search([('id', 'child_of', a.id)]), a | b | c)
```

```python non-compliant BN006
def test_parent_path_after_move(self):
    c = self.env['res.partner'].create({'name': 'c'})
    self.cr.flush()
    self.assertTrue(c.parent_path)
```

### A5. Assume about ids only what the ORM documents

Allowed: ids are distinct, truthy, hashable, stable for the life of the record, usable in `browse()` and in `=`/`in`/`child_of` domains; `record.id` of a flushed record is an `int`. Default `_order = 'id'` exists, so a test may order by id and rely on records created *earlier in the same transaction* sorting first.
Not allowed: arithmetic on ids, contiguity, "next id = max id + 1", ordering of ids created by different transactions, id reuse after unlink.

```python compliant
def test_create_order(self):
    recs = self.env['res.partner'].create([{'name': 'x'}, {'name': 'y'}])
    self.assertEqual(self.env['res.partner'].search([('id', 'in', recs.ids)], order='id').mapped('name'), ['x', 'y'])
```

```python non-compliant BN010
def test_create_order(self):
    first = self.env['res.partner'].create({'name': 'x'})
    second = self.env['res.partner'].create({'name': 'y'})
    self.assertEqual(second.id, first.id + 1)
```

### F1. No raw SQL: `cr.execute`, `execute_query`, `SQL(`, `Query(`, SQL text in strings (BN002, BN005, BN009)

```python compliant
def test_duplicate_bill_detection(self):
    # raw_sql.account_move: _fetch_duplicate_reference is a multi-join SELECT today
    bill1 = self._create_bill(ref='INV-1')
    bill2 = self._create_bill(ref='INV-1')
    self.env.invalidate_all()
    self.assertEqual(bill1.duplicated_ref_ids, bill2)
    self.assertEqual(bill2.duplicated_ref_ids, bill1)
```

```python non-compliant BN002 BN005 BN006
def test_duplicate_bill_detection(self):
    bill = self._create_bill(ref='INV-1')
    rows = self.env.execute_query(SQL("SELECT id FROM account_move WHERE ref = %s", 'INV-1'))
    self.assertEqual(len(rows), 1)
    self.env.cr.execute("SELECT 1")
```

### F2. No query-count or query-text assertions: `assertQueryCount`, `assertQueries` (BN004)

Performance is a backend property. Behavioural asserts next to a query guard are kept; the guard is dropped (this is the `core.reuse_with_edits` recipe in `SAMPLE.md`).

```python compliant
def test_one2many_write(self):
    # core.reuse_with_edits: test_one2many.py minus its assertQueryCount guard
    order = self.env['test_orm.order'].create({'line_ids': [(0, 0, {'product': 'a'}), (0, 0, {'product': 'b'})]})
    order.write({'line_ids': [(5, 0, 0)]})
    self.assertFalse(order.line_ids)
```

```python non-compliant BN004
def test_one2many_write(self):
    order = self.env['test_orm.order'].create({'line_ids': [(0, 0, {'product': 'a'})]})
    with self.assertQueries(['''UPDATE "test_orm_order_line" SET "order_id" = NULL WHERE "order_id" IN %s''']):
        order.write({'line_ids': [(5, 0, 0)]})
```

### F3. No direct cursor, savepoint, registry or transaction control (BN003, BN006)

`self.cr`, `self.env.cr`, `env.cr.savepoint()`, `registry.cursor()`, `registry_test_mode()`, `cr.commit()/rollback()` are PostgreSQL transaction plumbing. "Another transaction" is requested from the harness (section 4).

```python compliant
def test_lock_blocks_other_session(self):
    # concurrency.lock_for_update
    p1, p2 = self.env['test_orm.partner'].search([], limit=2)
    p1.lock_for_update()
    with self.concurrent_session() as other:
        recs = (p1 + p2).with_env(other.env)
        with self.assertRaises(LockError):
            recs.lock_for_update()
        self.assertEqual(recs.try_lock_for_update(), recs[1])
```

```python non-compliant BN003 BN006
def test_lock_blocks_other_session(self):
    p1, p2 = self.env['test_orm.partner'].search([], limit=2)
    p1.lock_for_update()
    with self.env.registry.cursor() as cr:
        recs = (p1 + p2).with_env(self.env(cr=cr))
        with self.assertRaises(LockError):
            recs.lock_for_update()
        cr.rollback()
```

### F4. No psycopg2 or `odoo.sql_db` names (BN001)

Covers imports and attribute chains (`psycopg2.errors.LockNotAvailable`, `odoo.sql_db.PG_CONCURRENCY_EXCEPTIONS_TO_RETRY`). Use the aliases from section 3.

```python compliant
def test_no_gap_sequence_second_drawer_fails(self):
    # concurrency.ir_sequence: SELECT ... FOR UPDATE NOWAIT today
    with self.independent_transaction() as t0, self.independent_transaction() as t1:
        n0 = t0.env['ir.sequence'].next_by_code('test_sequence_type_2')
        self.assertTrue(n0)
        with self.assertConcurrencyError():
            t1.env['ir.sequence'].next_by_code('test_sequence_type_2')
```

```python non-compliant BN001 BN007
def test_no_gap_sequence_second_drawer_fails(self):
    import psycopg2.errors
    with mute_logger('odoo.sql_db'), self.assertRaises(psycopg2.errors.LockNotAvailable):
        self.env['ir.sequence'].next_by_code('test_sequence_type_2')
```

### F5. No schema or storage internals: `_table`, `_table_sql`, `_table_objects`, `_auto`, `init()`, `odoo.tools.sql` (BN008)

Report models (`sql_views.*`) are tested through `_read_group`/`search_fetch` on the report model, never by inspecting the view definition.

```python compliant
def test_sale_report_subtotal(self):
    # sql_views.sale_report
    self.order.action_confirm()
    [(order, subtotal)] = self.env['sale.report']._read_group(
        [('order_reference', '=', f'sale.order,{self.order.id}')], ['order_reference'], ['price_subtotal:sum'])
    self.assertEqual(subtotal, self.order.amount_untaxed)
```

```python non-compliant BN008 BN009
def test_sale_report_subtotal(self):
    report = self.env['sale.report']
    self.assertFalse(report._auto)
    self.assertIn('SELECT l.price_subtotal FROM sale_order_line l', str(report._table_sql()))
```

### F6. No silencing of the backend's logger (BN007)

`mute_logger('odoo.sql_db')` names the PostgreSQL driver. The harness helpers (`assertIntegrityError`, `assertConcurrencyError`) mute whatever the active backend logs. `mute_logger` on other loggers (`odoo.models.unlink`, `odoo.addons.base.models.ir_model`) stays allowed.

```python compliant
def test_duplicate_login(self):
    # integrity.res_users: UNIQUE(login)
    self.env['res.users'].create({'name': 'u', 'login': 'dup'})
    with self.assertIntegrityError():
        self.env['res.users'].create({'name': 'v', 'login': 'dup'})
    self.assertEqual(self.env['res.users'].search_count([('login', '=', 'dup')]), 1)
```

```python non-compliant BN007
def test_duplicate_login(self):
    self.env['res.users'].create({'name': 'u', 'login': 'dup'})
    with mute_logger('odoo.sql_db'), self.assertRaises(self.IntegrityError):
        self.env['res.users'].create({'name': 'v', 'login': 'dup'})
```

### F7. No test-local branching on the backend

A neutral test has no `if backend == 'postgresql'`, no `skipIf(...pg...)`, no `@unittest.expectedFailure` keyed on a backend. If a behaviour legitimately differs it is not neutral and belongs in a backend-specific suite. (Not lint-detectable in general; reviewed by hand. The lint flags string literals `postgres`, `postgresql`, `psycopg`, `mongo` as BN011 to prompt the review.)

```python compliant
def test_unlink_partner_with_user(self):
    # integrity.res_users: partner_id ondelete='restrict'
    user = self.env['res.users'].create({'name': 'u', 'login': 'u'})
    with self.assertIntegrityError():
        user.partner_id.unlink()
    self.assertTrue(user.partner_id.exists())
```

```python non-compliant BN011
def test_unlink_partner_with_user(self):
    user = self.env['res.users'].create({'name': 'u', 'login': 'u'})
    if self.env.registry.db_name.startswith('postgresql'):
        with self.assertIntegrityError():
            user.partner_id.unlink()
```

## 3. Exceptions surfaced neutrally

Today the ORM lets backend exceptions through unchanged at flush time; only the RPC layer (`odoo/http/retrying.py:61-84`) turns `psycopg2.IntegrityError` into `ValidationError` and retries `PG_CONCURRENCY_EXCEPTIONS_TO_RETRY` (`odoo/sql_db.py:87`). Existing tests therefore import psycopg2 (`addons/hr_holidays/tests/test_holidays_flow.py:8`, `odoo/addons/base/tests/test_ir_sequence.py:103`).

The harness exports one module, `backend_neutral.errors`, and tests import only from it:

| Neutral name | Meaning | PostgreSQL adapter maps it to | Raised by (today) |
|---|---|---|---|
| `IntegrityError` | the backend refused a write because of a declared constraint: unique, check, not-null, FK `restrict` | `psycopg2.IntegrityError` (covers `UniqueViolation`, `CheckViolation`, `NotNullViolation`, `ForeignKeyViolation`) | `flush` of `create`/`write`/`unlink` |
| `ConcurrencyError` | another transaction holds a lock or the transaction must be retried | `(psycopg2.errors.LockNotAvailable, psycopg2.errors.SerializationFailure, psycopg2.errors.DeadlockDetected, odoo.exceptions.ConcurrencyError)` | `ir.sequence` no-gap draw, `_increase_rank`, retry loops |
| `LockError` | `lock_for_update` could not lock every record | re-export of `odoo.exceptions.LockError` (already backend-neutral) | `odoo/orm/models.py:5081` |
| `ValidationError`, `UserError`, `AccessError`, `MissingError` | Python-level constraints / access rules | re-exports of `odoo.exceptions.*` (already neutral) | `_check_*` constraints, ir.rule |

Rules for the aliases:

1. The alias is whatever `assertRaises` needs: a class or a tuple of classes. Tests never do `isinstance` chains on it or read attributes of the caught exception.
2. `NeutralCase.assertIntegrityError()` and `assertConcurrencyError()` wrap `assertRaises(alias)` plus the backend adapter's `mute_backend_logs()`; the existing `BaseCase.assertRaises` already wraps the block in a flushing savepoint (`odoo/tests/common.py:789-813`), so pending writes are flushed before the block exits and the test can continue afterwards. Tests use these two helpers instead of `assertRaises(IntegrityError)` so the mute is never spelled out (rule F6).
3. A neutral test asserts the error is raised *before the `with` block exits*; it does not assume whether the backend fails at `create()` time or at flush time. Anything that must be checked after the failure (record not persisted, partner still exists) is asserted after the block, after `invalidate_all()`.
4. **Working assumption, not yet confirmed** (D1/D2 below): one `IntegrityError` alias for all four violation kinds, and one `ConcurrencyError` alias for lock/serialization failures. If a reviewer wants finer-grained aliases (e.g. `UniqueViolation` separate from `CheckViolation`) only `backend_neutral/errors.py` and the table above change; tests written against the coarse alias stay valid.

## 4. Isolation interface

### What `TransactionCase` does today

`odoo/tests/common.py:1305-1490`: one cursor per class, opened in `setUpClass`; each test runs inside a savepoint created in `setUp` and rolled back in cleanup; `cr.commit`/`cr.rollback` are patched to raise (`common.py:1386-1391`); ORM caches get an extra `CacheLayer` per test. "Another transaction" is obtained by `self.env.registry.cursor()`, which inside `registry_test_mode` returns a `TestCursor` *wrapping the same connection* (`common.py:1079-1099`, `odoo/tests/test_cursor.py`), and outside it returns a real second connection that cannot see the test's uncommitted data. Lock tests (`test_models.py:165-197`) and `TestIrSequenceNoGap` (`test_ir_sequence.py:21-27`, which uses `BaseCase` plus committed helper cursors) rely on these PostgreSQL facts directly.

### Interface

Every method takes and returns `odoo.api.Environment` objects; nothing in it mentions cursors.

```text
class IsolationBackend(Protocol):
    name: str                                   # 'postgresql', 'mongodb'; for logging only, never for branching in tests

    # per-class / per-test lifecycle (replaces TransactionCase savepoint + rollback)
    def class_setup(self, dbname) -> Environment        # env whose writes are discarded at class_teardown
    def class_teardown(self) -> None
    def test_setup(self, env) -> None                   # start an undoable unit around one test method
    def test_teardown(self, env) -> None                # undo everything the test wrote, drop caches

    # explicit transactions
    @contextmanager
    def independent_transaction(self) -> Transaction    # a *real* new transaction on the same database;
                                                        # .env, .commit(), .rollback(); rolled back on exit
                                                        # unless committed; sees only committed data
    @contextmanager
    def concurrent_session(self) -> Transaction         # like independent_transaction but guaranteed to run
                                                        # *concurrently* with the test's own transaction
                                                        # (own connection/thread/session), so locks between
                                                        # the two are real; never auto-committed

    # error surfacing
    integrity_errors: type | tuple[type, ...]           # section 3
    concurrency_errors: type | tuple[type, ...]
    @contextmanager
    def mute_backend_logs(self) -> None

    # fixtures that must survive rollback (needed by concurrency tests, see below)
    def committed_fixture(self, make: Callable[[Environment], Recordset]) -> Recordset
                                                        # runs `make` in an independent transaction, commits,
                                                        # registers unlink-and-commit for class_teardown
```

`NeutralCase(TransactionCase)` delegates `setUpClass`/`setUp`/cleanup to the active backend's `class_setup`/`test_setup`/`test_teardown`, exposes `independent_transaction()`, `concurrent_session()`, `committed_fixture()`, `assertIntegrityError()`, `assertConcurrencyError()`, and removes `cr`, `registry` and `assertQueryCount`/`assertQueries` from the public surface (they raise `NotImplementedError('not available in a neutral test')`, so a stray use fails even if the lint is skipped). `NeutralConcurrencyCase(NeutralCase)` is the same but its own transaction is also an `independent_transaction` so that `concurrent_session()` data can be seen after commit; it is for the six `concurrency.*` targets only.

### PostgreSQL adapter

- `class_setup` / `test_setup` / `test_teardown`: exactly today's `TransactionCase` code (class cursor, flushing savepoint, rollback, `CacheLayer`), moved behind the interface. No change in behaviour for PostgreSQL.
- `independent_transaction`: `Registry(dbname).cursor()` *outside* `registry_test_mode`, wrapped in an `Environment` with the test's uid/context; `rollback()` on exit unless `commit()` was called (the `environment()` helper in `test_ir_sequence.py:21-27` is this, minus the auto-commit).
- `concurrent_session`: same as above; a PostgreSQL connection is already an independent session, so locks held by the test's cursor are visible to it. The adapter sets `lock_timeout` on that connection (e.g. 2 s) so a wrong backend answer is a `ConcurrencyError`, not a hang.
- `integrity_errors = psycopg2.IntegrityError`; `concurrency_errors = PG_CONCURRENCY_EXCEPTIONS_TO_RETRY + (odoo.exceptions.ConcurrencyError,)`; `mute_backend_logs = mute_logger('odoo.sql_db')`.
- `committed_fixture`: run `make`, `commit()`, record `(model, ids)`; `class_teardown` unlinks them in a fresh committed transaction (what `drop_sequence` does in `test_ir_sequence.py:30`).

What the interface deliberately does **not** promise: isolation level, whether uncommitted writes of the test transaction are visible to `concurrent_session` (they are not on PostgreSQL and tests must not rely on either answer), savepoint nesting depth, or that `independent_transaction` is cheap. Concurrency tests therefore create the records both sessions touch with `committed_fixture`, and assert the *end state* through a third `independent_transaction` after both have committed or rolled back.

## 5. Selecting and running the suite

- **Tag**: every neutral class is decorated `@tagged('backend_neutral', 'post_install', '-at_install')` (tags inherit, so putting it on `NeutralCase` is enough; `odoo/tests/common.py:3137`). `standard` stays, so the suite also runs in the normal full run on PostgreSQL.
- **Location (proposal, see Q3)**: a test addon `odoo/addons/test_backend_neutral/` holding `harness/` (interface, PostgreSQL adapter, `errors.py`) and `tests/` grouped by `SAMPLE.md` category (`test_integrity.py`, `test_concurrency.py`, `test_raw_sql.py`, `test_sql_views.py`, `test_aggregation_hierarchy.py`, `test_core_reuse.py`). It `depends` on the sample spread (`account`, `stock`, `sale`, `mail`, `website`, `hr_holidays`, `point_of_sale`, `project`, `test_base`) so one install gives every fixture. `backend_neutral_tests/` at the repo root keeps the documents, the manifest and the lint; it is not importable by Odoo on purpose.
- **Run on PostgreSQL** (from the repo root, after `sudo pg_ctlcluster 16 main start`):

  ```sh
  /home/ubuntu/.venvs/odoo/bin/python odoo-bin -d neutral --db_port=5433 --stop-after-init \
      -i test_backend_neutral --with-demo --test-enable --test-tags backend_neutral
  ```

  Subsequent runs on the built database: replace `-i ... --with-demo` with `-u test_backend_neutral`. One category: `--test-tags backend_neutral/test_backend_neutral:TestIntegrity`. Another backend runs the identical command with its own database options; the tag spec, the test files and the assertions do not change.
- **Reuse of `test_orm` tests** (`core.*` in `SAMPLE.md`): the neutral addon *subclasses* the kept classes (`class TestAccessNeutral(TestAccess)` with the tag) for `reuse_as_is`, and *copies* the method bodies for `reuse_with_edits`/`reuse_split_by_class` with the query guards removed; `test_base` itself is not edited (see Q4).
- **Lint gate**: `python3 backend_neutral_tests/lint_neutral.py <paths>` exits non-zero on any finding; it runs on the neutral addon's `tests/` (never on `harness/`, which is the one place allowed to name psycopg2). Suggested wiring: a `test_lint`-style test in the neutral addon (`odoo/addons/test_lint/tests/test_sql_injection.py` is the precedent for an AST checker run as a test) and/or a CI step on the PR; the first test ticket picks one (Q5).

## 6. Lint rules (`lint_neutral.py`)

AST-based, no Odoo import needed, Python 3.10+. A finding is `path:line: BNxxx message`. Suppress one line with `# neutral: allow BNxxx` (reserved for the harness; a suppression inside `tests/` is itself a review finding).

| Code | Detects | Contract rule |
|---|---|---|
| BN001 | `import psycopg2`, `from psycopg2...`, `odoo.sql_db`, `odoo.tools.sql`, attribute chains rooted at `psycopg2`, `.pgcode`/`.pgerror`/`.diag` | F4 |
| BN002 | calls to `.execute`, `.executemany`, `.execute_values`, `.execute_query`, `.execute_query_dict`, `.fetchone/fetchall/fetchmany/dictfetchall` | F1 |
| BN003 | calls to `.savepoint`, `.cursor`, `.commit`, `.rollback`, `.registry_test_mode`, `.enter_registry_test_mode`, `.flush` on `cr` | F3 |
| BN004 | `assertQueryCount`, `assertQueries`, `_patchExecute`, `warmup`, `profile` | F2 |
| BN005 | calls to `SQL(`, `Query(`, `_as_query(`, `_where_calc(`, `_flush_search(` | F1 |
| BN006 | attribute access `.cr`, `._cr`, `.registry` on any object | F3 |
| BN007 | `mute_logger(...)` whose argument starts with `odoo.sql_db` | F6 |
| BN008 | attribute access `._table`, `._table_sql`, `._table_objects`, `._auto`, `._sql_constraints`, `.init(` on a model | F5 |
| BN009 | string literal that looks like SQL (`SELECT .. FROM`, `INSERT INTO`, `UPDATE .. SET`, `DELETE FROM`, `FOR UPDATE`, `SAVEPOINT`, `nextval(`) | F1 |
| BN010 | arithmetic (`+`, `-`) with an operand that is `.id` or `.ids[...]`, or `max(...ids) + n` | A5 |
| BN011 | string literal containing `postgres`, `psycopg`, `mongo` (review prompt, not a hard rule) | F7 |

`--self-test` extracts every ```` ```python compliant ```` / ```` ```python non-compliant BN... ```` block from this file, lints it, and fails if a compliant block has findings or a non-compliant block misses one of its listed codes. That keeps the examples honest when the rules change.

## 7. Open decisions (need a human; nothing below is decided here)

- **D1 (from SAMPLE.md). One integrity alias or several?** Working assumption used throughout: a single `backend_neutral.errors.IntegrityError` mapped to `psycopg2.IntegrityError` on PostgreSQL. Alternative: four aliases (unique / check / not-null / FK). Cost of the coarse alias: a backend that raises a unique violation where a check violation was expected still passes. Confirm or split.
- **D2 (from SAMPLE.md). Concurrency alias.** Working assumption: a single `ConcurrencyError` alias covering `LockNotAvailable`, `SerializationFailure`, `DeadlockDetected`. **Naming conflict found while writing this**: `odoo.exceptions.ConcurrencyError` already exists (`odoo/exceptions.py:108`) and is retried by `odoo/http/retrying.py:63`. Options: (a) keep the name in the harness namespace and include the Odoo class in the tuple (what section 3 does), (b) rename the alias `ConcurrencyFailure` to avoid shadowing. Also decide whether `LockError` (raised by `lock_for_update`, `models.py:5081`) stays separate (section 3 keeps it separate because today's tests assert it specifically).
- **Q3. Where the suite lives.** Proposal: a new test addon `odoo/addons/test_backend_neutral` with the harness inside it. Alternative: harness in `odoo/tests/neutral.py` (touches core test infrastructure) or per-addon `tests/neutral/` packages (eight install targets instead of one). The board rule "do not change production behaviour" is satisfied by all three; the first changes least.
- **Q4. How `test_orm` tests are reused.** Proposal: subclass as-is classes and copy edited ones into the neutral addon, leaving `odoo/addons/test_base` untouched. Alternative: add the `backend_neutral` tag and remove query guards in place, which edits ~20 existing test files and changes what the normal suite checks.
- **Q5. Where the lint runs.** Options: a `test_lint`-style test inside the neutral addon (runs with every Odoo test run, fails the suite), a GitHub Actions step on PRs touching the neutral addon, or both.
- **Q6. Is "order by id equals creation order within one transaction" part of the contract?** A5 assumes yes because `_order = 'id'` is the ORM default and much of `test_orm` relies on it. A document store that allocates ids from a counter can honour it; one that uses ObjectIds cannot without a mapping. If the answer is no, A5 drops that sentence and the affected tests sort by an explicit field.
- **Q7. Should `IntegrityError` also accept `ValidationError`?** If a future backend enforces declared constraints in the application layer it would naturally raise `ValidationError`. Accepting both makes the alias `(IntegrityError, ValidationError)` and weakens every integrity assertion on PostgreSQL. Proposal: no; the adapter translates its native error into the alias instead.
- **Q8. `parent_path` contents.** A4's example asserts the `"<id>/<id>/"` string. It is an ORM-defined field (`_parent_store_compute`, `models.py:2423`) but computed with a recursive CTE today. Keep the assertion (the ORM uses the string for `child_of`), or assert only through `child_of`/`parent_of` searches?
