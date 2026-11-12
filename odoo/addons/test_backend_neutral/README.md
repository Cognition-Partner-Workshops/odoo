# Backend-neutral ORM test suite

Tests that assert only on what the ORM API shows (records, field values,
classes of raised exceptions), so that they can run unchanged on another
database backend. The rules are in `backend_neutral_tests/CONTRACT.md` at the
root of the repository.

- `harness/`: the only code that knows the backend. `isolation.py` is the
  `IsolationBackend` interface, `postgresql.py` its PostgreSQL adapter,
  `backends.py` selects the active adapter, `errors.py` holds the neutral
  exception names, `case.py` the base classes `NeutralCase` and
  `NeutralConcurrencyCase`.
- `tests/`: the neutral tests. `test_lint.py` runs
  `backend_neutral_tests/lint_neutral.py` on this directory (not on `harness/`).

## Run

```sh
odoo-bin -d <db> --stop-after-init -i test_backend_neutral --test-enable --test-tags backend_neutral
```

## Write a test

```python
from odoo.addons.test_backend_neutral.harness import NeutralCase
from odoo.addons.test_backend_neutral.harness.errors import LockError


class TestSomething(NeutralCase):

    def test_unique(self):
        with self.assertIntegrityError():
            self.env['test_backend_neutral.item'].create({'name': 'x', 'code': 'taken'})

    def test_other_transaction(self):
        item = self.committed_fixture(lambda env: env['test_backend_neutral.item'].create({'name': 'x'}))
        with self.concurrent_session() as first, self.concurrent_session() as second:
            item.with_env(first.env).lock_for_update()
            with self.assertRaises(LockError):
                item.with_env(second.env).lock_for_update()
```

- `independent_transaction()` and `concurrent_session()` give a `Transaction`
  with `.env`, `.commit_transaction()` and `.rollback_transaction()`. It is
  rolled back when the block exits unless committed. After an expected error
  inside it, roll it back before using it again.
- `committed_fixture(make)` commits the records `make(env)` returns and
  unlinks them at the end of the test (end of the class when called in
  `setUpClass`). `track_committed(records)` does the same for records a test
  committed itself.
- In a `NeutralCase`, `self.env` may not see what other transactions commit.
  Use `NeutralConcurrencyCase` when it must: there `self.env` is a real
  transaction, driven with `self.transaction`.
- Every transaction of the harness waits at most `lock_timeout` (2 s on
  PostgreSQL) for a lock, then fails with `ConcurrencyError`.

## Where each decision lives

| Decision | One place to change |
|---|---|
| active backend | `harness/backends.py` |
| what `IntegrityError` / `ConcurrencyError` accept | `integrity_errors` / `concurrency_errors` of the adapter, exposed by `harness/errors.py` |
| lock timeout | `PostgresqlIsolation.lock_timeout` |
| test tag | `NEUTRAL_TAG` in `harness/case.py` |
| what the lint checks | `tests/test_lint.py` |
| names tests use to commit / roll back | `Transaction` in `harness/isolation.py` |
